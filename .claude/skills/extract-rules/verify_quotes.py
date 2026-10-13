#!/usr/bin/env python3
"""Verify outputs/rules.json against data/contract-rules.pdf.

Usage:
    python verify_quotes.py [rules.json] [--pdf data/contract-rules.pdf]

Exit code 0 = every check passed, 1 = at least one error, 2 = could not run.
Warnings never fail the run. Each finding starts with a code (E-QUOTE, ...) so
tests and the agent can tell the checks apart.

Checks
  E-SCHEMA    top-level keys, field names and types, enums, threshold objects
  E-ID        rule_id values are CPR-01, CPR-02, ... in order, no gaps or repeats
  E-PARAM     every parameter a rule uses is declared; every value is null
  E-QUOTE     every quote fragment appears on the page the entry states
  E-FIGURE    every threshold amount is printed in that rule's quote
  E-COVERAGE  every numbered clause and appendix row is in rules or excluded
  E-EXCLUDED  excluded entries have a clause, a page and a one-line reason
  E-NOTE      notes are well formed and their quotes appear on their page

The PDF text comes from pdftotext (xpdf/poppler) run page by page with
-enc UTF-8; without that flag the pound sign is lost. Quotes are compared after
collapsing whitespace and straightening curly quotes and dashes, nothing else.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Document structure this verifier relies on (Contract Rules, Part 8). If the
# council re-issues the PDF with different appendices, update these.
APPENDIX_ROWS = {
    "Appendix A": ["row 1", "row 2", "row 3", "row 4"],
    "Appendix B": ["row A", "row B1", "row B2", "row C", "row D", "notes"],
    "Appendix C": ["row A", "row B", "row C", "row D", "row E", "row F",
                   "closing paragraph"],
}
APPENDIX_START = re.compile(r"^Contract Rules - Appendix A", re.M)

RULE_TYPES = {"procedure", "approval", "exception", "advertising",
              "anti-avoidance", "documentation", "legal-form"}
CONTRACT_TYPES = {"goods", "services", "works", "concession", "light_touch",
                  "all"}
EVIDENCE = {"clause", "appendix-table", "appendix-note"}
NOTE_KINDS = {"contradiction", "gap"}
RULE_FIELDS = ["rule_id", "clause", "page", "type", "scope", "threshold_low",
               "threshold_high", "required_action", "approver",
               "evidence_source", "quote"]
TOP_KEYS = ["source", "parameters", "rules", "excluded", "notes"]
NUM_CLAUSE = re.compile(r"^\d+(\.\d+)+$")
APP_CLAUSE = re.compile(r"^Appendix [ABC] (row \S+|notes|closing paragraph)$")
TOKEN = re.compile(r"(?:(?<=\s)|^)(\d{1,2}(?:\.\d{1,3}){1,4})(?=\s|$)", re.M)
PARAM_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, code, msg):
        self.errors.append("%s %s" % (code, msg))

    def warn(self, code, msg):
        self.warnings.append("%s %s" % (code, msg))


# ---------------------------------------------------------------- PDF text
def run_tool(args):
    out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise RuntimeError("%s failed: %s" % (args[0], out.stderr.decode("utf-8", "replace").strip()))
    return out.stdout.decode("utf-8", "replace")


def norm(s):
    s = (s.replace(" ", " ").replace("­", "")
         .replace("‘", "'").replace("’", "'")
         .replace("“", '"').replace("”", '"')
         .replace("–", "-").replace("—", "-"))
    return re.sub(r"\s+", " ", s).strip()


class Pdf:
    def __init__(self, path):
        for tool in ("pdftotext", "pdfinfo"):
            if not shutil.which(tool):
                raise RuntimeError("%s not found on PATH (install poppler)" % tool)
        info = run_tool(["pdfinfo", str(path)])
        m = re.search(r"^Pages:\s+(\d+)", info, re.M)
        if not m:
            raise RuntimeError("pdfinfo did not report a page count")
        self.path, self.pages = str(path), int(m.group(1))
        self._cache = {}

    def raw(self, page, layout=False):
        key = (page, layout)
        if key not in self._cache:
            cmd = ["pdftotext", "-enc", "UTF-8", "-f", str(page), "-l", str(page)]
            if layout:
                cmd.append("-layout")
            self._cache[key] = run_tool(cmd + [self.path, "-"])
        return self._cache[key]

    def haystacks(self, page):
        """Plain and layout text for a page, normalised."""
        return [norm(self.raw(page)), norm(self.raw(page, True))]

    def find_page(self, needle):
        for p in range(1, self.pages + 1):
            if any(needle in h for h in self.haystacks(p)):
                return p
        return None

    def clause_tokens(self):
        """Dotted clause numbers on the numbered-clause pages (before App. A)."""
        tokens, first_appendix = {}, self.pages + 1
        for p in range(1, self.pages + 1):
            if APPENDIX_START.search(self.raw(p)):
                first_appendix = p
                break
        for p in range(1, first_appendix):
            for t in TOKEN.findall(self.raw(p)):
                tokens.setdefault(t, p)
        return tokens, first_appendix


# ---------------------------------------------------------------- helpers
def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def is_str(x):
    return isinstance(x, str) and x.strip() != ""


def quote_list(q):
    if is_str(q):
        return [q]
    if isinstance(q, list) and q and all(is_str(x) for x in q):
        return q
    return None


def figure_forms(v):
    """Ways the PDF might print an amount (see SKILL.md for the 24,999.99 case)."""
    forms = ["£{:,}".format(v), "£{:,.2f}".format(v - 0.01)]
    if v >= 1000000 and v % 100000 == 0:
        forms.append("£%gmillion" % (v / 1e6))
        forms.append("£%g million" % (v / 1e6))
    return forms


def check_quote(rep, pdf, code, who, page, quote):
    frags = quote_list(quote)
    if frags is None:
        rep.err("E-SCHEMA", "%s: quote must be a non-empty string or list of strings" % who)
        return
    if not is_int(page) or not 1 <= page <= pdf.pages:
        rep.err("E-SCHEMA", "%s: page %r is not an integer 1-%d" % (who, page, pdf.pages))
        return
    hay = pdf.haystacks(page)
    for frag in frags:
        n = norm(frag)
        if len(n) < 12:
            rep.err(code, "%s: quote fragment %r is too short to prove anything" % (who, n))
        elif "..." in n or "…" in n:
            rep.err(code, "%s: quote contains an ellipsis; use a list of fragments" % who)
        elif not any(n in h for h in hay):
            elsewhere = pdf.find_page(n)
            where = ("it is on page %d" % elsewhere) if elsewhere else "it is not in the PDF"
            rep.err(code, "%s: quote not found on page %d (%s): %r" % (who, page, where, n[:70]))


# ---------------------------------------------------------------- checks
def check_threshold(rep, who, name, t, declared, used):
    if not isinstance(t, dict) or set(t) != {"value", "parameter", "inclusive"}:
        rep.err("E-SCHEMA", "%s: %s must be an object with exactly value, parameter, inclusive" % (who, name))
        return None
    v, p, inc = t["value"], t["parameter"], t["inclusive"]
    if v is not None and p is not None:
        rep.err("E-SCHEMA", "%s: %s has both a value and a parameter" % (who, name))
    if v is None and p is None:
        if inc is not None:
            rep.err("E-SCHEMA", "%s: %s has no bound but inclusive is not null" % (who, name))
        return None
    if not isinstance(inc, bool):
        rep.err("E-SCHEMA", "%s: %s.inclusive must be true or false" % (who, name))
    if v is not None and (not is_int(v) or v < 0):
        rep.err("E-SCHEMA", "%s: %s.value must be a non-negative integer (GBP), got %r" % (who, name, v))
        v = None
    if p is not None:
        if not isinstance(p, str):
            rep.err("E-PARAM", "%s: %s.parameter must be a string" % (who, name))
        elif p not in declared:
            rep.err("E-PARAM", "%s: %s uses undeclared parameter %r" % (who, name, p))
        else:
            used.add(p)
    return v


def check_rules(rep, pdf, data):
    rules, declared, used = data["rules"], data["parameters"], set()
    if not isinstance(rules, list) or not rules:
        rep.err("E-SCHEMA", "rules must be a non-empty list")
        return
    for i, r in enumerate(rules):
        who = "rules[%d]" % i
        if not isinstance(r, dict):
            rep.err("E-SCHEMA", "%s is not an object" % who)
            continue
        rid = r.get("rule_id")
        who = rid if is_str(rid) else who
        missing = [f for f in RULE_FIELDS if f not in r]
        extra = [f for f in r if f not in RULE_FIELDS]
        if missing:
            rep.err("E-SCHEMA", "%s: missing fields %s" % (who, missing))
        if extra:
            rep.err("E-SCHEMA", "%s: unexpected fields %s" % (who, extra))
        if missing:
            continue
        if rid != "CPR-%02d" % (i + 1):
            rep.err("E-ID", "%s: expected CPR-%02d at position %d" % (who, i + 1, i + 1))
        clause = r["clause"]
        if not (is_str(clause) and (NUM_CLAUSE.match(clause) or APP_CLAUSE.match(clause))):
            rep.err("E-SCHEMA", "%s: clause %r is not a dotted number (e.g. 6.16) or 'Appendix B row B1'" % (who, clause))
        if r["type"] not in RULE_TYPES:
            rep.err("E-SCHEMA", "%s: type %r not in %s" % (who, r["type"], sorted(RULE_TYPES)))
        sc = r["scope"]
        if (not isinstance(sc, dict) or set(sc) != {"contract_types", "condition"}
                or not isinstance(sc["contract_types"], list) or not sc["contract_types"]
                or not set(sc["contract_types"]) <= CONTRACT_TYPES or not is_str(sc["condition"])):
            rep.err("E-SCHEMA", "%s: scope must be {contract_types: non-empty subset of %s, condition: text}" % (who, sorted(CONTRACT_TYPES)))
        lo = check_threshold(rep, who, "threshold_low", r["threshold_low"], declared, used)
        hi = check_threshold(rep, who, "threshold_high", r["threshold_high"], declared, used)
        if lo is not None and hi is not None and lo > hi:
            rep.err("E-SCHEMA", "%s: threshold_low %d is above threshold_high %d" % (who, lo, hi))
        if not is_str(r["required_action"]):
            rep.err("E-SCHEMA", "%s: required_action must be non-empty text" % who)
        if r["approver"] is not None and not is_str(r["approver"]):
            rep.err("E-SCHEMA", "%s: approver must be text or null" % who)
        if r["evidence_source"] not in EVIDENCE:
            rep.err("E-SCHEMA", "%s: evidence_source %r not in %s" % (who, r["evidence_source"], sorted(EVIDENCE)))
        check_quote(rep, pdf, "E-QUOTE", who, r["page"], r["quote"])
        frags = quote_list(r["quote"])
        if frags:
            text = norm(" ".join(frags))
            for v in (lo, hi):
                if v is not None and not any(norm(f) in text for f in figure_forms(v)):
                    rep.err("E-FIGURE", "%s: amount %s is not printed in the quote" % (who, "{:,}".format(v)))
        if (is_str(clause) and NUM_CLAUSE.match(clause) and is_int(r["page"])
                and 1 <= r["page"] <= pdf.pages):
            if clause not in TOKEN.findall(pdf.raw(r["page"])):
                rep.warn("W-PAGE", "%s: clause number %s does not start on page %d (fine if the clause runs over a page)" % (who, clause, r["page"]))
    unused = sorted(set(declared) - used)
    if unused:
        rep.warn("W-PARAM", "declared but unused parameters: %s" % unused)
    if not any(isinstance(r, dict) and r.get("type") == "anti-avoidance" for r in rules):
        rep.warn("W-ANTI", "no rule has type anti-avoidance (the no-splitting rule, 6.16, should)")


def check_parameters(rep, params):
    if not isinstance(params, dict):
        rep.err("E-SCHEMA", "parameters must be an object")
        return {}
    for k, v in params.items():
        if not PARAM_NAME.match(k):
            rep.err("E-PARAM", "parameter name %r must be snake_case" % k)
        if v is not None:
            rep.err("E-PARAM", "parameter %s = %r: values must stay null, the PDF does not print them" % (k, v))
    return params


def check_excluded(rep, pdf, excluded):
    if not isinstance(excluded, list):
        rep.err("E-SCHEMA", "excluded must be a list")
        return
    for i, e in enumerate(excluded):
        who = "excluded[%d]" % i
        if not isinstance(e, dict) or set(e) != {"clause", "page", "reason"}:
            rep.err("E-EXCLUDED", "%s must have exactly clause, page, reason" % who)
            continue
        who = "excluded %s" % e["clause"]
        c = e["clause"]
        if not (is_str(c) and (NUM_CLAUSE.match(c) or APP_CLAUSE.match(c))):
            rep.err("E-EXCLUDED", "%s: clause must be a dotted number or 'Appendix X row Y'" % who)
        if not is_int(e["page"]) or not 1 <= e["page"] <= pdf.pages:
            rep.err("E-EXCLUDED", "%s: page %r is not an integer 1-%d" % (who, e["page"], pdf.pages))
        r = e["reason"]
        if not is_str(r) or "\n" in r or len(r) > 200:
            rep.err("E-EXCLUDED", "%s: reason must be one non-empty line of at most 200 characters" % who)


def check_coverage(rep, pdf, rules, excluded):
    tokens, first_app = pdf.clause_tokens()
    listed, seen = [], set()
    for kind, items in (("rules", rules), ("excluded", excluded)):
        for e in items if isinstance(items, list) else []:
            c = e.get("clause") if isinstance(e, dict) else None
            if not is_str(c):
                continue
            if c in seen:
                rep.err("E-COVERAGE", "clause %s is listed more than once (second time in %s)" % (c, kind))
            seen.add(c)
            listed.append(c)
    for c in listed:
        if NUM_CLAUSE.match(c) and c not in tokens:
            rep.err("E-COVERAGE", "clause %s is not a clause number in the PDF" % c)
    for t in sorted(tokens, key=lambda s: [int(x) for x in s.split(".")]):
        if not any(t == c or t.startswith(c + ".") for c in listed if NUM_CLAUSE.match(c)):
            rep.err("E-COVERAGE", "clause %s (page %d) is in neither rules nor excluded" % (t, tokens[t]))
    for app, rows in APPENDIX_ROWS.items():
        for row in rows:
            if "%s %s" % (app, row) not in seen:
                rep.err("E-COVERAGE", "'%s %s' is in neither rules nor excluded" % (app, row))
    if first_app > pdf.pages:
        rep.warn("W-APPX", "no 'Contract Rules - Appendix A' heading found; clause scan covered every page")


def check_notes(rep, pdf, notes):
    if not isinstance(notes, list):
        rep.err("E-NOTE", "notes must be a list")
        return
    for i, n in enumerate(notes):
        who = "notes[%d]" % i
        if (not isinstance(n, dict) or not {"kind", "clauses", "text"} <= set(n)
                or not set(n) <= {"kind", "clauses", "text", "quotes"}):
            rep.err("E-NOTE", "%s must have kind, clauses, text and optionally quotes" % who)
            continue
        if n["kind"] not in NOTE_KINDS:
            rep.err("E-NOTE", "%s: kind %r not in %s" % (who, n["kind"], sorted(NOTE_KINDS)))
        if not (isinstance(n["clauses"], list) and n["clauses"] and all(is_str(c) for c in n["clauses"])):
            rep.err("E-NOTE", "%s: clauses must be a non-empty list of clause names" % who)
        if not is_str(n["text"]):
            rep.err("E-NOTE", "%s: text must be non-empty" % who)
        qs = n.get("quotes", [])
        if n["kind"] == "contradiction" and not qs:
            rep.err("E-NOTE", "%s: a contradiction needs quotes for both sides" % who)
        if not isinstance(qs, list):
            rep.err("E-NOTE", "%s: quotes must be a list" % who)
            continue
        for j, q in enumerate(qs):
            if not isinstance(q, dict) or set(q) != {"page", "quote"}:
                rep.err("E-NOTE", "%s.quotes[%d] must be {page, quote}" % (who, j))
                continue
            check_quote(rep, pdf, "E-NOTE", "%s.quotes[%d]" % (who, j), q["page"], q["quote"])


def verify(data, pdf):
    rep = Report()
    if not isinstance(data, dict):
        rep.err("E-SCHEMA", "top level must be an object with keys %s" % TOP_KEYS)
        return rep
    miss = [k for k in TOP_KEYS if k not in data]
    extra = [k for k in data if k not in TOP_KEYS]
    if miss or extra:
        rep.err("E-SCHEMA", "top-level keys: missing %s, unexpected %s" % (miss, extra))
        if miss:
            return rep
    if not is_str(data["source"]):
        rep.err("E-SCHEMA", "source must name the PDF")
    data["parameters"] = check_parameters(rep, data["parameters"])
    check_rules(rep, pdf, data)
    check_excluded(rep, pdf, data["excluded"])
    check_coverage(rep, pdf, data["rules"], data["excluded"])
    check_notes(rep, pdf, data["notes"])
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rules", nargs="?", default="outputs/rules.json")
    ap.add_argument("--pdf", default="data/contract-rules.pdf")
    a = ap.parse_args(argv)
    try:
        data = json.loads(Path(a.rules).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("cannot read %s: %s" % (a.rules, exc))
        return 2
    try:
        pdf = Pdf(a.pdf)
        rep = verify(data, pdf)
    except (OSError, RuntimeError) as exc:
        print("cannot run: %s" % exc)
        return 2
    for w in rep.warnings:
        print("WARN  " + w)
    for e in rep.errors:
        print("ERROR " + e)
    n = len(data["rules"]) if isinstance(data.get("rules"), list) else 0
    print("%s: %d rules, %d errors, %d warnings" % (
        "FAIL" if rep.errors else "PASS", n, len(rep.errors), len(rep.warnings)))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
