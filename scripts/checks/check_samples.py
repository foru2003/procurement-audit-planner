#!/usr/bin/env python3
"""QA check: samples.

Every transaction in outputs/samples/*.csv and every row ID in audit-program.md
must exist in spend-clean.csv and, at its sheet row, in the council's workbook
(data/spend/<file>, sheet "Data to publish"), with the same supplier and amount.
The audit-program.md table is checked against the workbook as well, so the
printed supplier and amount match the source.

A row ID is "<workbook file name>:<sheet row>".

Usage: check_samples.py [--outputs DIR] [--data DIR] [--full DIR]
Exit 0 pass, 1 fail, 2 could not run. The check never changes a file.
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHEET = "Data to publish"
PROGRAM_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*([\d-]+)\s*\|\s*(.*?)\s*\|\s*£([\d,]+(?:\.\d+)?)\s*\|")


def read_workbook_rows(path, wanted):
    """{sheet row: (supplier, amount)} for the wanted sheet rows of one workbook."""
    import openpyxl
    out = {}
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb[SHEET] if SHEET in wb.sheetnames else wb[wb.sheetnames[0]]
    top = max(wanted)
    for n, row in enumerate(ws.iter_rows(min_row=1, max_row=top, values_only=True), 1):
        if n in wanted and row is not None and len(row) >= 6:
            out[n] = (str(row[5]).strip() if row[5] is not None else "", row[4])
    wb.close()
    return out


def split_id(rid):
    f, _, n = rid.rpartition(":")
    return (f, int(n)) if f and n.isdigit() else (None, None)


def same_amount(a, b):
    try:
        return abs(float(str(a).replace(",", "")) - float(str(b).replace(",", ""))) < 0.005
    except (TypeError, ValueError):
        return False


def run(outputs, data, full=None):
    outputs, data = Path(outputs), Path(data)
    full = Path(full) if full else outputs / "analytics-full"
    sdir, prog, clean = outputs / "samples", outputs / "audit-program.md", full / "spend-clean.csv"
    miss = [str(p) for p in (prog, clean) if not p.exists()]
    if not sdir.is_dir() or not list(sdir.glob("*.csv")):
        miss.append(str(sdir) + "/*.csv")
    if miss:
        return ["missing input: " + m for m in miss], "inputs missing"
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        return ["openpyxl is not installed; cannot read the workbooks"], "cannot run"
    with open(clean, newline="", encoding="utf-8") as f:
        spend = {r["row_id"]: r for r in csv.DictReader(f)}
    fails, want = [], defaultdict(set)   # workbook file -> sheet rows
    items = []                           # (where, row_id, supplier, amount)
    for p in sorted(sdir.glob("*.csv")):
        with open(p, newline="", encoding="utf-8") as f:
            for i, r in enumerate(csv.DictReader(f), 2):
                items.append(("%s row %d" % (p.name, i), r.get("row_id", ""), r.get("supplier", ""), r.get("amount", "")))
                f_, n_ = split_id(r.get("row_id", ""))
                if n_ is not None and str(n_) != str(r.get("sheet_row", n_)):
                    fails.append("%s row %d: sheet_row %s does not match row ID %s" % (p.name, i, r.get("sheet_row"), r.get("row_id")))
    nprog = 0
    for n, line in enumerate(prog.read_text(encoding="utf-8").splitlines(), 1):
        m = PROGRAM_ROW.match(line)
        if m:
            nprog += 1
            items.append(("audit-program.md:%d" % n, m.group(1), m.group(3), m.group(4)))
    for where, rid, sup, amt in items:
        f_, n_ = split_id(rid)
        if f_ is None:
            fails.append("%s: %r is not a row ID of the form file:row" % (where, rid))
            continue
        s = spend.get(rid)
        if s is None:
            fails.append("%s: row %s does not exist in spend-clean.csv" % (where, rid))
        else:
            if s.get("supplier", "").strip() != sup.strip():
                fails.append("%s: row %s supplier %r differs from spend-clean.csv %r" % (where, rid, sup, s.get("supplier")))
            if not same_amount(s.get("amount"), amt):
                fails.append("%s: row %s amount %s differs from spend-clean.csv %s" % (where, rid, amt, s.get("amount")))
        want[f_].add(n_)
    nwb = 0
    cells = {}
    for f_, rows in want.items():
        wbp = data / "spend" / f_
        if not wbp.exists():
            fails.append("workbook not found: %s (needed for %d rows)" % (wbp, len(rows)))
            continue
        nwb += 1
        cells[f_] = read_workbook_rows(wbp, rows)
    for where, rid, sup, amt in items:
        f_, n_ = split_id(rid)
        if f_ is None or f_ not in cells:
            continue
        got = cells[f_].get(n_)
        if got is None:
            fails.append("%s: workbook %s has no row %d" % (where, f_, n_))
            continue
        if got[0] != sup.strip():
            fails.append("%s: row %s supplier %r differs from the workbook %r" % (where, rid, sup, got[0]))
        if not same_amount(got[1], amt):
            fails.append("%s: row %s amount %s differs from the workbook %s" % (where, rid, amt, got[1]))
    return fails, "%d transactions in %d sample files and %d audit-program rows checked against spend-clean.csv and %d workbooks" % (
        len(items) - nprog, len(list(sdir.glob("*.csv"))), nprog, nwb)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--full")
    a = ap.parse_args(argv)
    fails, summary = run(a.outputs, a.data, a.full)
    for f in fails:
        print("FAIL  " + f)
    print("%s: samples: %s" % ("FAIL" if fails else "PASS", summary))
    return 2 if summary == "cannot run" else (1 if fails else 0)


if __name__ == "__main__":
    sys.exit(main())
