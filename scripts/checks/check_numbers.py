#!/usr/bin/env python3
"""QA check: numbers.

Every figure of three or more digits, or with a pound sign, in
planning-memo.md, risk-control-matrix.md and audit-program.md must be a value in
analytics.json, pack-figures.json, rules.json or outputs/samples/*.csv.

A figure matches a source value when the value rounded to the figure's own
number of decimals (0 to 2) equals it, so 3,333,218 matches 3333218.21.
Skipped: text in backticks (row IDs, file names), rule, test, control and risk
IDs, dates, years, version tags, and clause, section, page, table and appendix
references.

Usage: check_numbers.py [--outputs DIR]
Exit 0 pass, 1 fail, 2 could not run. The check never changes a file.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ("planning-memo.md", "risk-control-matrix.md", "audit-program.md")
FIG = re.compile(r"£\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d{3,}(?:\.\d+)?\b")
ANYNUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
SKIP = [
    re.compile(r"`[^`]*`"),
    re.compile(r"\b[A-Z]{1,4}-\d[\w.]*"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* \d{4}\b"),
    re.compile(r"\b(?:19|20)\d{2}\b"),
    re.compile(r"\bv\d+\b"),
    re.compile(r"\b(?:clauses?|sections?|pages?|tables?|figures?|appendix|rows?|rules?|part)\s+[\dA-C][\w.]*", re.I),
]


def keys(v):
    """Rounded string keys a source value can match: (decimals, text)."""
    return {(d, "%.*f" % (d, v)) for d in (0, 1, 2)}


def collect(obj, out):
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        out |= keys(float(obj))
    elif isinstance(obj, str):
        for t in ANYNUM.findall(obj):
            try:
                out |= keys(float(t.replace(",", "")))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for k, v in obj.items():
            collect(k, out)
            collect(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect(v, out)


def run(outputs):
    outputs = Path(outputs)
    fails, allowed = [], set()
    docs = [outputs / d for d in DOCS]
    missing = [str(p) for p in docs + [outputs / "analytics.json", outputs / "pack-figures.json", outputs / "rules.json"] if not p.exists()]
    if missing:
        return ["missing input: " + m for m in missing], "inputs missing"
    for name in ("analytics.json", "pack-figures.json", "rules.json"):
        collect(json.loads((outputs / name).read_text(encoding="utf-8")), allowed)
    nsamples = 0
    for p in sorted((outputs / "samples").glob("*.csv")) if (outputs / "samples").is_dir() else []:
        nsamples += 1
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                for cell in row:
                    collect(cell, allowed)
    checked = 0
    for doc in docs:
        for n, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            text = line
            for rx in SKIP:
                text = rx.sub(" ", text)
            for tok in FIG.findall(text):
                checked += 1
                v = float(tok.replace("£", "").replace(",", "").strip())
                d = len(tok.split(".")[1]) if "." in tok else 0
                if d > 2 or (d, "%.*f" % (d, v)) not in allowed:
                    fails.append("%s:%d: figure %s is not a value in analytics.json, pack-figures.json, rules.json or the samples" % (doc.name, n, tok.strip()))
    return fails, "%d figures checked in %d documents against %d source values and %d sample files" % (checked, len(docs), len(allowed) // 3, nsamples)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    a = ap.parse_args(argv)
    fails, summary = run(a.outputs)
    for f in fails:
        print("FAIL  " + f)
    print("%s: numbers: %s" % ("FAIL" if fails else "PASS", summary))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
