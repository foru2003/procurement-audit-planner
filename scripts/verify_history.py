#!/usr/bin/env python3
"""Verify outputs/history.json against the committee PDFs.

Usage:
    python scripts/verify_history.py [history.json] [--committee data/committee]

Exit code 0 = every check passed, 1 = at least one error, 2 = could not run.
Warnings never fail the run. Each finding starts with a code.

  E-SCHEMA   top-level keys, field names, types, enums, unexpected fields
  E-SOURCE   sources list: file exists, page count right, every PDF listed;
             every item's source file is listed and its page is in range
  E-ID       item ids are unique and run AO-01, AO-02, ... within a section
  E-QUOTE    every quote fragment is on the stated pdf_page of the stated file
  E-FIELD    a value the item reports (opinion, title, label, range ...) is
             not inside that item's own quote, i.e. it was not copied
  E-DISC     a discrepancy lacks quotes for what it compares, or carries a
             resolution field (discrepancies are recorded, never resolved)
  E-GAP      a gap is malformed or names a file that was not searched
  E-METHOD   the scoring method is marked found but a block is missing

Quotes are compared with whitespace collapsed and curly quotes and dashes
straightened, against both plain and -layout pdftotext output of the stated
page (pdftotext -enc UTF-8, one page at a time). A quote is a string or a list
of fragments, each at least 3 characters, 20 or more joined. Fragments may be
table cells copied from either extraction.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOP = ["generated_on", "sources", "audit_opinions", "follow_ups",
       "advisory_work", "agreed_actions", "risk_themes", "scoring_method",
       "discrepancies", "gaps"]
PAIRING = {"text", "visual"}
DISC_KINDS = {"contradiction", "inconsistency", "apparent-typo"}
METHOD_STATUS = {"found", "not_found"}

# section -> (id prefix, required fields, fields whose strings must be quoted,
#             fields that are dicts whose string values must be quoted)
ITEMS = {
    "audit_opinions": ("AO", ["period", "directorate", "audit_title", "opinion", "pairing"],
                       ["audit_title", "opinion"], []),
    "follow_ups": ("FU", ["period", "directorate", "audit_title", "report_opinion",
                          "implementation_progress", "pairing"],
                   ["audit_title", "report_opinion", "implementation_progress"], []),
    "advisory_work": ("AW", ["period", "directorate", "review_title", "pairing"],
                      ["review_title"], []),
    "agreed_actions": ("AA", ["period", "theme", "due_date", "status", "pairing"],
                       ["theme", "due_date", "status"], []),
    "risk_themes": ("RT", ["theme", "how_referenced", "pairing"], ["theme"], []),
}
NULLABLE = {"directorate", "due_date", "status"}
METHOD = {
    "evaluation_levels": ("EL", ["name", "description", "pairing"], ["name", "description"], []),
    "impact_scale": ("IS", ["rating", "label", "dimensions", "pairing"], ["label"], ["dimensions"]),
    "likelihood_scale": ("LS", ["rating", "label", "incident", "probability", "pairing"],
                         ["label", "incident", "probability"], []),
    "matrix": ("MX", ["impact", "cells", "pairing"], [], []),
    "bands": ("BD", ["level", "colour", "score_range", "escalation", "response", "pairing"],
              ["level", "colour", "score_range", "escalation", "response"], []),
    "appetite": ("AP", ["category", "levels", "pairing"], ["category"], ["levels"]),
    "other_rules": ("OR", ["topic", "pairing"], [], []),
}
REQUIRED_BLOCKS = ["evaluation_levels", "impact_scale", "likelihood_scale",
                   "matrix", "bands", "appetite"]


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, code, msg):
        self.errors.append("%s %s" % (code, msg))

    def warn(self, code, msg):
        self.warnings.append("%s %s" % (code, msg))


def norm(s):
    s = (s.replace(" ", " ").replace("­", "")
         .replace("‘", "'").replace("’", "'")
         .replace("“", '"').replace("”", '"')
         .replace("–", "-").replace("—", "-"))
    return re.sub(r"\s+", " ", s).strip()


def run_tool(args):
    out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise RuntimeError("%s failed: %s" % (args[0], out.stderr.decode("utf-8", "replace").strip()))
    return out.stdout.decode("utf-8", "replace")


class Committee:
    """The PDFs in a folder, with per-page normalised text."""

    def __init__(self, folder):
        for tool in ("pdftotext", "pdfinfo"):
            if not shutil.which(tool):
                raise RuntimeError("%s not found on PATH (install poppler)" % tool)
        self.folder = Path(folder)
        self.files = sorted(p.name for p in self.folder.glob("*.pdf"))
        if not self.files:
            raise RuntimeError("no PDFs in %s" % folder)
        self.pages, self._cache = {}, {}
        for f in self.files:
            m = re.search(r"^Pages:\s+(\d+)", run_tool(["pdfinfo", str(self.folder / f)]), re.M)
            if not m:
                raise RuntimeError("pdfinfo gave no page count for %s" % f)
            self.pages[f] = int(m.group(1))

    def hay(self, f, page):
        key = (f, page)
        if key not in self._cache:
            texts = []
            for layout in (False, True):
                cmd = ["pdftotext", "-enc", "UTF-8", "-f", str(page), "-l", str(page)]
                if layout:
                    cmd.append("-layout")
                texts.append(norm(run_tool(cmd + [str(self.folder / f), "-"])))
            self._cache[key] = texts
        return self._cache[key]

    def find(self, f, needle):
        for p in range(1, self.pages[f] + 1):
            if any(needle in h for h in self.hay(f, p)):
                return p
        return None


def is_str(x):
    return isinstance(x, str) and x.strip() != ""


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def fragments(q):
    if is_str(q):
        return [q]
    if isinstance(q, list) and q and all(is_str(x) for x in q):
        return q
    return None


def check_source(rep, com, who, src, sources):
    """Return (file, page) if the source is well formed, else None."""
    if not isinstance(src, dict) or set(src) != {"file", "pdf_page"}:
        rep.err("E-SOURCE", "%s: source must be {file, pdf_page}" % who)
        return None
    f, p = src["file"], src["pdf_page"]
    if f not in sources:
        rep.err("E-SOURCE", "%s: file %r is not in sources" % (who, f))
        return None
    if not is_int(p) or not 1 <= p <= com.pages[f]:
        rep.err("E-SOURCE", "%s: pdf_page %r is not an integer 1-%d for %s" % (who, p, com.pages[f], f))
        return None
    return f, p


def check_quote(rep, com, code, who, f, p, quote):
    """Verify fragments on (f, p). Returns the normalised joined text or None."""
    frags = fragments(quote)
    if frags is None:
        rep.err("E-SCHEMA", "%s: quote must be a non-empty string or list of strings" % who)
        return None
    ok = True
    for frag in frags:
        n = norm(frag)
        if len(n) < 3:
            rep.err(code, "%s: quote fragment %r is shorter than 3 characters" % (who, n))
            ok = False
        elif "..." in n or "…" in n:
            rep.err(code, "%s: quote contains an ellipsis; use a list of fragments" % who)
            ok = False
        elif not any(n in h for h in com.hay(f, p)):
            elsewhere = com.find(f, n)
            where = ("it is on page %d" % elsewhere) if elsewhere else "it is not in that file"
            rep.err(code, "%s: quote not found on %s page %d (%s): %r" % (who, f, p, where, n[:70]))
            ok = False
    joined = norm(" ".join(frags))
    if len(joined) < 20:
        rep.err(code, "%s: quote is %d characters; at least 20 are needed to prove anything" % (who, len(joined)))
        ok = False
    return joined if ok else None


def must_be_quoted(rep, who, field, value, joined):
    if value is None:
        return
    if not is_str(value):
        rep.err("E-SCHEMA", "%s: %s must be text" % (who, field))
    elif norm(value).lower() not in joined.lower():
        rep.err("E-FIELD", "%s: %s %r is not inside the item's quote" % (who, field, norm(value)[:60]))


def check_item(rep, com, sources, section, item, spec, expect_id):
    prefix, required, quoted, dict_fields = spec
    who = item.get("id", "%s item" % section) if isinstance(item, dict) else "%s item" % section
    if not isinstance(item, dict):
        rep.err("E-SCHEMA", "%s: not an object" % who)
        return
    allowed = {"id", "source", "quote"} | set(required)
    miss = [k for k in ["id", "source", "quote"] + required if k not in item]
    extra = [k for k in item if k not in allowed]
    if miss:
        rep.err("E-SCHEMA", "%s: missing fields %s" % (who, miss))
    if extra:
        rep.err("E-SCHEMA", "%s: unexpected fields %s" % (who, extra))
    if miss:
        return
    if item["id"] != expect_id:
        rep.err("E-ID", "%s: expected %s at this position" % (who, expect_id))
    for k in required:
        v = item[k]
        if k == "pairing":
            if v not in PAIRING:
                rep.err("E-SCHEMA", "%s: pairing %r not in %s" % (who, v, sorted(PAIRING)))
        elif k in dict_fields:
            if not isinstance(v, dict) or not v or not all(is_str(x) for x in v.values()):
                rep.err("E-SCHEMA", "%s: %s must be a non-empty object of text values" % (who, k))
        elif k in ("rating", "impact"):
            if not is_int(v) or not 1 <= v <= 5:
                rep.err("E-SCHEMA", "%s: %s must be an integer 1-5" % (who, k))
        elif k == "cells":
            good = (isinstance(v, list) and len(v) == 5 and all(
                isinstance(c, dict) and set(c) == {"likelihood", "score", "label"}
                and is_int(c["likelihood"]) and is_int(c["score"]) and is_str(c["label"]) for c in v))
            if not good:
                rep.err("E-SCHEMA", "%s: cells must be 5 objects {likelihood, score, label}" % who)
        elif k in NULLABLE:
            if v is not None and not is_str(v):
                rep.err("E-SCHEMA", "%s: %s must be text or null" % (who, k))
        elif not is_str(v):
            rep.err("E-SCHEMA", "%s: %s must be non-empty text" % (who, k))
    loc = check_source(rep, com, who, item["source"], sources)
    if not loc:
        return
    joined = check_quote(rep, com, "E-QUOTE", who, loc[0], loc[1], item["quote"])
    if joined is None:
        return
    for k in quoted:
        must_be_quoted(rep, who, k, item[k], joined)
    for k in dict_fields:
        if isinstance(item[k], dict):
            for dk, dv in item[k].items():
                must_be_quoted(rep, who, "%s.%s" % (k, dk), dv, joined)
    if "cells" in item and isinstance(item["cells"], list):
        for c in item["cells"]:
            if isinstance(c, dict) and is_str(c.get("label")):
                must_be_quoted(rep, who, "cells.label", c["label"], joined)


def check_section(rep, com, sources, name, items, spec):
    if not isinstance(items, list):
        rep.err("E-SCHEMA", "%s must be a list" % name)
        return
    seen = set()
    for i, it in enumerate(items):
        eid = "%s-%02d" % (spec[0], i + 1)
        check_item(rep, com, sources, name, it, spec, eid)
        iid = it.get("id") if isinstance(it, dict) else None
        if iid in seen:
            rep.err("E-ID", "%s: duplicate id %s" % (name, iid))
        seen.add(iid)


def check_method(rep, com, sources, sm):
    if not isinstance(sm, dict) or "status" not in sm:
        rep.err("E-SCHEMA", "scoring_method must be an object with a status")
        return
    if sm["status"] not in METHOD_STATUS:
        rep.err("E-SCHEMA", "scoring_method.status %r not in %s" % (sm["status"], sorted(METHOD_STATUS)))
        return
    allowed = {"status", "note"} | set(METHOD)
    extra = [k for k in sm if k not in allowed]
    if extra:
        rep.err("E-SCHEMA", "scoring_method: unexpected fields %s" % extra)
    if sm["status"] == "not_found":
        if not is_str(sm.get("note")):
            rep.err("E-METHOD", "scoring_method not_found needs a note saying where was searched")
        for b in METHOD:
            if sm.get(b):
                rep.err("E-METHOD", "scoring_method not_found but %s has entries" % b)
        return
    for b in REQUIRED_BLOCKS:
        if not isinstance(sm.get(b), list) or not sm[b]:
            rep.err("E-METHOD", "scoring_method is 'found' but block %s is missing or empty" % b)
    for b, spec in METHOD.items():
        if b in sm:
            check_section(rep, com, sources, "scoring_method.%s" % b, sm[b], spec)


def check_discrepancies(rep, com, sources, items):
    if not isinstance(items, list):
        rep.err("E-SCHEMA", "discrepancies must be a list")
        return
    for i, d in enumerate(items):
        who = "DI-%02d" % (i + 1)
        if not isinstance(d, dict) or set(d) != {"id", "kind", "text", "quotes"}:
            rep.err("E-DISC", "%s must have exactly id, kind, text, quotes (no resolution field)" % who)
            continue
        if d["id"] != who:
            rep.err("E-ID", "%s: expected %s at this position" % (d["id"], who))
        if d["kind"] not in DISC_KINDS:
            rep.err("E-DISC", "%s: kind %r not in %s" % (who, d["kind"], sorted(DISC_KINDS)))
        if not is_str(d["text"]):
            rep.err("E-DISC", "%s: text must say what differs" % who)
        qs = d["quotes"]
        need = 1 if d["kind"] == "apparent-typo" else 2
        if not isinstance(qs, list) or len(qs) < need:
            rep.err("E-DISC", "%s: needs at least %d quoted passages" % (who, need))
            continue
        for j, q in enumerate(qs):
            w2 = "%s.quotes[%d]" % (who, j)
            if not isinstance(q, dict) or set(q) != {"file", "pdf_page", "quote"}:
                rep.err("E-DISC", "%s must be {file, pdf_page, quote}" % w2)
                continue
            loc = check_source(rep, com, w2, {"file": q["file"], "pdf_page": q["pdf_page"]}, sources)
            if loc:
                check_quote(rep, com, "E-QUOTE", w2, loc[0], loc[1], q["quote"])


def check_gaps(rep, items, sources):
    if not isinstance(items, list):
        rep.err("E-SCHEMA", "gaps must be a list")
        return
    for i, g in enumerate(items):
        who = "GA-%02d" % (i + 1)
        if not isinstance(g, dict) or set(g) != {"id", "topic", "searched", "note"}:
            rep.err("E-GAP", "%s must have exactly id, topic, searched, note" % who)
            continue
        if g["id"] != who:
            rep.err("E-ID", "%s: expected %s at this position" % (g["id"], who))
        if not is_str(g["topic"]) or not is_str(g["note"]):
            rep.err("E-GAP", "%s: topic and note must be non-empty text" % who)
        s = g["searched"]
        if not isinstance(s, list) or not s or not all(isinstance(x, str) for x in s):
            rep.err("E-GAP", "%s: searched must list the files looked in" % who)
        else:
            for f in s:
                if f not in sources:
                    rep.err("E-GAP", "%s: searched file %r is not in sources" % (who, f))
    if not items:
        rep.warn("W-GAP", "gaps is empty; check that every missing item is listed")


def check_sources(rep, com, srcs):
    names = {}
    if not isinstance(srcs, list) or not srcs:
        rep.err("E-SOURCE", "sources must be a non-empty list")
        return names
    for s in srcs:
        if not isinstance(s, dict) or set(s) != {"file", "pdf_pages", "title", "report_date"}:
            rep.err("E-SOURCE", "each source needs exactly file, pdf_pages, title, report_date")
            continue
        f = s["file"]
        if f not in com.pages:
            rep.err("E-SOURCE", "source file %r is not a PDF in %s" % (f, com.folder))
            continue
        if s["pdf_pages"] != com.pages[f]:
            rep.err("E-SOURCE", "%s: pdf_pages is %r, the PDF has %d" % (f, s["pdf_pages"], com.pages[f]))
        if s["title"] is not None and not is_str(s["title"]):
            rep.err("E-SCHEMA", "%s: title must be text or null" % f)
        if s["report_date"] is not None and not is_str(s["report_date"]):
            rep.err("E-SCHEMA", "%s: report_date must be text or null" % f)
        names[f] = s
    for f in com.files:
        if f not in names:
            rep.err("E-SOURCE", "PDF %s is in the folder but not in sources" % f)
    return names


def verify(data, com):
    rep = Report()
    if not isinstance(data, dict):
        rep.err("E-SCHEMA", "top level must be an object with keys %s" % TOP)
        return rep
    miss = [k for k in TOP if k not in data]
    extra = [k for k in data if k not in TOP]
    if miss or extra:
        rep.err("E-SCHEMA", "top-level keys: missing %s, unexpected %s" % (miss, extra))
        if miss:
            return rep
    if not (is_str(data["generated_on"]) and re.match(r"^\d{4}-\d{2}-\d{2}$", data["generated_on"])):
        rep.err("E-SCHEMA", "generated_on must be YYYY-MM-DD")
    sources = check_sources(rep, com, data["sources"])
    for name, spec in ITEMS.items():
        check_section(rep, com, sources, name, data[name], spec)
    check_method(rep, com, sources, data["scoring_method"])
    check_discrepancies(rep, com, sources, data["discrepancies"])
    check_gaps(rep, data["gaps"], sources)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("history", nargs="?", default="outputs/history.json")
    ap.add_argument("--committee", default="data/committee")
    a = ap.parse_args(argv)
    try:
        data = json.loads(Path(a.history).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("cannot read %s: %s" % (a.history, exc))
        return 2
    try:
        com = Committee(a.committee)
        rep = verify(data, com)
    except (OSError, RuntimeError) as exc:
        print("cannot run: %s" % exc)
        return 2
    for w in rep.warnings:
        print("WARN  " + w)
    for e in rep.errors:
        print("ERROR " + e)
    counts = ", ".join("%d %s" % (len(data.get(k, [])), k) for k in
                       ("audit_opinions", "follow_ups", "advisory_work", "agreed_actions",
                        "risk_themes", "discrepancies", "gaps") if isinstance(data.get(k), list))
    print("%s: %s, %d errors, %d warnings" % (
        "FAIL" if rep.errors else "PASS", counts, len(rep.errors), len(rep.warnings)))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
