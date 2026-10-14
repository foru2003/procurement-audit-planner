"""The tools an agent can call. Every tool is bound to one session workspace.

Agents never get a shell or arbitrary code execution: run_builder runs only the
Part A scripts named in BUILDERS, with arguments checked against an allowlist.
"""
import json
import os
import shutil
import subprocess
import sys
import time

from .config import ROOT, _secret
from .llm import Tool
from .workspace import Workspace

sys.path.insert(0, str(ROOT / "scripts"))
import pdftext_cache  # noqa: E402

try:  # Linux only; used to report the peak memory of a script run
    import resource
except ImportError:  # pragma: no cover
    resource = None

# name -> (script, flags the agent may pass, adds --outputs/--data/--full itself)
BUILDERS = {
    "clean": ("scripts/clean.py", set(), False),
    "analyse": ("scripts/analyse.py", set(), False),
    "verify_quotes": (".claude/skills/extract-rules/verify_quotes.py", {"--pdf"}, False),
    "verify_history": ("scripts/verify_history.py", {"--committee"}, False),
    "build_register": (".claude/skills/risk-assessment/build_register.py",
                       {"--ratings", "--rules", "--analytics", "--history", "--out-dir"}, False),
    "build_pack": (".claude/skills/audit-program/build_pack.py",
                   {"--gate", "--rules", "--analytics", "--ratings", "--register", "--comments", "--full", "--out-dir"}, False),
    "run_checks": ("scripts/checks/run_checks.py", set(), True),
    "signoff_report": ("scripts/signoff.py", set(), True),
}
SPEND_SCRIPTS = ("clean", "analyse")
SCRIPT_TIMEOUT = 150
MAX_WRITE = 300_000
MAX_READ = 15_000
READ_AREAS = ("data", "outputs")
WRITE_EXT = (".json", ".md", ".csv")


def child_peak_mb():
    if resource is None:
        return None
    return round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0, 0)  # KB on Linux


class Toolbox:
    """Builds the Tool list for one agent turn."""

    def __init__(self, ws: Workspace, team_log=None):
        self.ws = ws
        self.team_log = team_log if team_log is not None else []
        self.failures = []
        self.spend = {"path": None, "secs": 0.0, "peak_mb": None, "reason": ""}

    # ---- run_builder -------------------------------------------------
    def _check_arg(self, name, arg, flags):
        if arg in flags:
            return
        if arg.startswith("-"):
            raise ValueError("flag %s is not allowed for %s (allowed: %s)" % (arg, name, sorted(flags) or "none"))
        self.ws.resolve(arg, READ_AREAS)  # positional / flag value: a workspace path

    def run_builder(self, name, args=None):
        if name not in BUILDERS:
            raise ValueError("unknown builder %r; use one of %s" % (name, sorted(BUILDERS)))
        script, flags, adds_dirs = BUILDERS[name]
        args = [str(a) for a in (args or [])]
        for a in args:
            self._check_arg(name, a, flags)
        res = self._run_spend(name, script, args) if name in SPEND_SCRIPTS else self._exec(name, script, args, adds_dirs)
        if res.get("exit_code") != 0:
            self.failures.append({"builder": name, "args": args, "exit_code": res.get("exit_code"),
                                  "tail": (res.get("output") or res.get("error") or "")[-300:]})
        return res

    def _exec(self, name, script, args, adds_dirs):
        cmd = [sys.executable, str(ROOT / script)]
        if name == "signoff_report":
            cmd.append("report")
        cmd += args
        if adds_dirs:
            cmd += ["--outputs", str(self.ws.outputs), "--data", str(self.ws.data),
                    "--full", str(self.ws.outputs / "analytics-full")]
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=self.ws.root, capture_output=True, timeout=SCRIPT_TIMEOUT, env=env)
        except subprocess.TimeoutExpired:
            return {"exit_code": None, "error": "timed out after %ds" % SCRIPT_TIMEOUT}
        out = (p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")).strip()
        if len(out) > 6000:
            out = out[:3000] + "\n... [truncated] ...\n" + out[-3000:]
        return {"exit_code": p.returncode, "seconds": round(time.time() - t0, 1), "output": out}

    def _run_spend(self, name, script, args):
        """clean.py / analyse.py: run for real, else fall back to the precomputed analytics."""
        if self.spend["path"] == "precomputed":
            return {"exit_code": 0, "output": "precomputed analytics are already loaded; nothing to run"}
        if _secret("SPEND_MODE", "auto") == "precomputed":
            return self._precomputed("SPEND_MODE is set to precomputed")
        before = child_peak_mb()
        res = self._exec(name, script, args, False)
        self.spend["secs"] += res.get("seconds") or 0
        after = child_peak_mb()
        if after is not None:
            self.spend["peak_mb"] = max(after, self.spend["peak_mb"] or 0)
        if res.get("exit_code") != 0:
            return self._precomputed("%s failed (%s)" % (name, res.get("error") or "exit %s" % res.get("exit_code")), res)
        if name == "analyse":
            self.spend["path"] = "live"
        return res

    def _precomputed(self, reason, failed=None):
        src = ROOT / "outputs"
        shutil.copy(src / "analytics.json", self.ws.outputs / "analytics.json")
        dst = self.ws.outputs / "analytics-full"
        dst.mkdir(exist_ok=True)
        for f in (src / "analytics-full").glob("*"):
            shutil.copy(f, dst / f.name)
        self.spend.update(path="precomputed", reason=reason)
        msg = "The live analysis could not run (%s). The precomputed analytics from Part A were loaded into outputs/ instead; continue by reading outputs/analytics.json." % reason
        return {"exit_code": 0, "output": msg, "failed_run": (failed or {}).get("output", "")[:1500]}

    # ---- files -------------------------------------------------------
    def read_file(self, path, offset=0, max_chars=MAX_READ):
        p = self.ws.resolve(path, READ_AREAS)
        if p.suffix.lower() in (".pdf", ".xlsx"):
            raise ValueError("%s is binary; use read_pdf_page for PDFs, query_csv on analytics-full/spend-clean.csv for spend" % path)
        if not p.is_file():
            raise FileNotFoundError("%s does not exist" % path)
        text = p.read_text(encoding="utf-8", errors="replace")
        offset, n = max(0, int(offset)), min(int(max_chars), MAX_READ)
        return {"path": path, "total_chars": len(text), "offset": offset, "text": text[offset:offset + n],
                "more": offset + n < len(text)}

    def read_pdf_page(self, file, page, layout=False):
        pdf = self.ws.resolve(file, ("data",))
        info = pdftext_cache.load(pdf)
        page = int(page)
        if not 1 <= page <= info["pages"]:
            raise ValueError("%s has pages 1 to %d" % (file, info["pages"]))
        return {"file": file, "page": page, "pages": info["pages"],
                "text": info["layout" if layout else "plain"][page - 1][:MAX_READ]}

    def query_csv(self, path, mode="head", columns=None, filters=None, group_by=None, agg=None, sort_by=None,
                  descending=True, limit=20):
        import pandas as pd  # noqa: PLC0415
        p = self.ws.resolve(path, READ_AREAS)
        if p.suffix.lower() != ".csv":
            raise ValueError("query_csv reads .csv files only")
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        limit = max(1, min(int(limit), 50))
        for f in filters or []:
            col, op, val = f["column"], f["op"], f["value"]
            if col not in df.columns:
                raise ValueError("no column %r; columns are %s" % (col, list(df.columns)))
            s = df[col]
            if op == "contains":
                df = df[s.str.contains(str(val), case=False, regex=False)]
            elif op in ("==", "!="):
                df = df[(s == str(val)) == (op == "==")]
            elif op in (">", ">=", "<", "<="):
                num = pd.to_numeric(s, errors="coerce")
                v = float(val)
                df = df[{">": num > v, ">=": num >= v, "<": num < v, "<=": num <= v}[op]]
            else:
                raise ValueError("op must be one of ==, !=, >, >=, <, <=, contains")
        if mode == "info":
            return {"rows": len(df), "columns": list(df.columns)}
        if mode == "agg":
            agg = {a["column"]: a["fn"] for a in (agg or [])} if isinstance(agg, list) else (agg or {})
            if not group_by:
                return {"rows": len(df), "sum": {c: float(pd.to_numeric(df[c], errors="coerce").sum()) for c in agg if c in df.columns}}
            work = df.copy()
            spec = {}
            for col, fn in agg.items():
                if fn not in ("sum", "count", "mean", "min", "max"):
                    raise ValueError("agg functions: sum, count, mean, min, max")
                if fn != "count":
                    work[col] = pd.to_numeric(work[col], errors="coerce")
                spec[col] = fn
            if not spec:
                spec = {group_by[0]: "count"}
            g = work.groupby(group_by).agg(spec).reset_index()
            if sort_by and sort_by in g.columns:
                g = g.sort_values(sort_by, ascending=not descending)
            return {"groups": len(g), "rows": g.head(limit).to_dict("records")}
        if columns:
            df = df[[c for c in columns if c in df.columns]]
        if sort_by and sort_by in df.columns:
            num = pd.to_numeric(df[sort_by], errors="coerce")
            df = df.assign(_k=num).sort_values("_k", ascending=not descending).drop(columns="_k") if num.notna().any() \
                else df.sort_values(sort_by, ascending=not descending)
        out = json.dumps(df.head(limit).to_dict("records"))[:MAX_READ]
        return {"rows_matching": len(df), "returned": min(limit, len(df)), "records_json": out}

    def write_output(self, path, content, allowed):
        rel = str(path).replace("\\", "/")
        if rel not in allowed:
            raise PermissionError("you may write only: %s" % ", ".join(sorted(allowed)))
        if not rel.endswith(WRITE_EXT):
            raise ValueError("only .json, .md and .csv files can be written")
        if len(content) > MAX_WRITE:
            raise ValueError("file too large (%d chars; limit %d)" % (len(content), MAX_WRITE))
        if rel.endswith(".json"):
            json.loads(content)  # reject invalid JSON now rather than in a builder
        p = self.ws.resolve(rel, ("outputs",))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return "wrote %s (%d chars)" % (rel, len(content))

    def send_message(self, sender, to, text, members):
        if to not in members:
            raise ValueError("to must be one of %s" % sorted(members))
        self.team_log.append({"from": sender, "to": to, "text": text})
        return "sent to %s" % to

    # ---- tool specs --------------------------------------------------
    def tools_for(self, names, write_paths=(), sender=None, members=()):
        all_tools = {
            "read_file": Tool("read_file", "Read a text file under data/ or outputs/ (JSON, CSV, Markdown). Returns a slice of up to %d characters; use offset to continue." % MAX_READ,
                              {"type": "object", "properties": {"path": {"type": "string"}, "offset": {"type": "integer"}, "max_chars": {"type": "integer"}}, "required": ["path"]},
                              self.read_file),
            "read_pdf_page": Tool("read_pdf_page", "Text of one PDF page (1-based) from data/, e.g. data/contract-rules.pdf. Set layout true for table columns.",
                                  {"type": "object", "properties": {"file": {"type": "string"}, "page": {"type": "integer"}, "layout": {"type": "boolean"}}, "required": ["file", "page"]},
                                  self.read_pdf_page),
            "query_csv": Tool("query_csv", "Inspect a CSV without loading it into your context. mode head (default), info (row count and columns) or agg (group_by + agg like [{column: amount, fn: sum}]; fn is sum, count, mean, min or max). filters: [{column, op, value}] with op ==, !=, >, >=, <, <=, contains. At most 50 rows returned.",
                              {"type": "object", "properties": {"path": {"type": "string"}, "mode": {"type": "string"}, "columns": {"type": "array", "items": {"type": "string"}},
                                                              "filters": {"type": "array", "items": {"type": "object", "properties": {"column": {"type": "string"}, "op": {"type": "string"}, "value": {"type": "string"}}, "required": ["column", "op", "value"]}},
                                                              "group_by": {"type": "array", "items": {"type": "string"}}, "agg": {"type": "array", "items": {"type": "object", "properties": {"column": {"type": "string"}, "fn": {"type": "string"}}, "required": ["column", "fn"]}}, "sort_by": {"type": "string"},
                                                              "descending": {"type": "boolean"}, "limit": {"type": "integer"}}, "required": ["path"]},
                              self.query_csv),
            "write_output": Tool("write_output", "Write a whole file (replaces it). Allowed paths for you: %s. JSON must be valid." % ", ".join(sorted(write_paths)) if write_paths else "Write a file (not allowed for this agent).",
                                 {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
                                 lambda path, content: self.write_output(path, content, set(write_paths))),
            "run_builder": Tool("run_builder", "Run one approved Part A script. name is one of: %s. args are the script's flags/paths (workspace-relative). Returns exit code and output." % ", ".join(sorted(BUILDERS)),
                                {"type": "object", "properties": {"name": {"type": "string"}, "args": {"type": "array", "items": {"type": "string"}}}, "required": ["name"]},
                                self.run_builder),
            "send_message": Tool("send_message", "Send a message to a teammate (%s). Use the exact message formats in your instructions." % ", ".join(sorted(members)),
                                 {"type": "object", "properties": {"to": {"type": "string"}, "text": {"type": "string"}}, "required": ["to", "text"]},
                                 lambda to, text: self.send_message(sender, to, text, set(members))),
        }
        return [all_tools[n] for n in names]
