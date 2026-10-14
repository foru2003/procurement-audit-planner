"""Skeleton probe: proves a Vercel Python function can read the bundled files.

GET /api/probe returns JSON with, for each check, ok true/false and the detail:
  - data file:   data/pdf-text/contract-rules.json (precomputed PDF text)
  - skill file:  .claude/skills/risk-assessment/build_register.py (read, hashed, compiled)
  - agent file:  .claude/agents/planner.md
  - verifier:    the Part A quote verifier run in-process on outputs/rules.json,
                 reading the bundled PDF text (this host has no pdftotext)
Only the standard library is used.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE_ROOTS = [HERE.parent, Path.cwd(), Path("/var/task")]


def find_root():
    for r in CANDIDATE_ROOTS:
        if (r / "data").is_dir():
            return r
    return HERE.parent


def check(name, fn, out):
    try:
        out[name] = {"ok": True, **fn()}
    except Exception as exc:  # report, never crash the probe
        out[name] = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def run_probe():
    root = find_root()
    out = {"root": str(root), "cwd": str(Path.cwd()), "python": sys.version.split()[0],
           "pdftotext_on_path": bool(shutil.which("pdftotext"))}

    def data_file():
        d = json.loads((root / "data/pdf-text/contract-rules.json").read_text(encoding="utf-8"))
        return {"pages": d["pages"], "page1_chars": len(d["plain"][0])}

    def skill_file():
        p = root / ".claude/skills/risk-assessment/build_register.py"
        src = p.read_bytes()
        compile(src, str(p), "exec")
        return {"bytes": len(src), "sha1": hashlib.sha1(src).hexdigest()[:12], "compiles": True}

    def agent_file():
        t = (root / ".claude/agents/planner.md").read_text(encoding="utf-8")
        return {"chars": len(t), "first_line": t.splitlines()[0]}

    def verifier():
        sys.path.insert(0, str(root / ".claude/skills/extract-rules"))
        import verify_quotes
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = verify_quotes.main([str(root / "outputs/rules.json"),
                                       "--pdf", str(root / "data/contract-rules.pdf")])
        lines = buf.getvalue().strip().splitlines()
        return {"exit_code": code, "result": lines[-1] if lines else ""}

    check("data_file", data_file, out)
    check("skill_file", skill_file, out)
    check("agent_file", agent_file, out)
    check("quote_verifier", verifier, out)
    checks = [v for v in out.values() if isinstance(v, dict) and "ok" in v]
    out["all_ok"] = all(c["ok"] for c in checks) and out["quote_verifier"].get("exit_code") == 0
    return out


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(run_probe(), indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2))
