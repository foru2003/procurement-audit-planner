#!/usr/bin/env python3
"""Final steps of the Phase 3 lead procedure: the team-done report, and the
auditor's sign-off recorded in outputs/review.md.

Usage:
    signoff.py report
        Print the two-line team-done report. Every figure is read from the pack
        files and from a fresh run of the four QA checks; nothing is typed.
        Run it after the three teammates have reported done and been shut down.

    signoff.py record --name "Full Name" [--decision sign-off|return]
                      [--date YYYY-MM-DD] [--comment TEXT] [--replace]
        Record the auditor's decision in the sign-off block at the end of
        review.md and print one line. It refuses (exit 1, file untouched) unless
        the checks print READY FOR SIGN-OFF and review.md's verdict says so. It
        never invents a name: --name is required. The date defaults to today. A
        block that already holds a different entry is replaced only with
        --replace; the same entry again is accepted and changes nothing.

Options for both: --outputs DIR, --data DIR, --full DIR (as for run_checks.py).
Exit 0 done, 1 refused or blocked, 2 could not run.
"""
import argparse
import datetime
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ROOT / "scripts" / "checks"
BLOCK = re.compile(r"(Reviewer:)[^\n]*?(\s+Date:)[^\n]*\n(\s*\n)?(Decision:)[^\n]*", re.M)
WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
         10: "Ten", 11: "Eleven", 12: "Twelve"}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verdict(outputs, data, full):
    rc = load(CHECKS / "run_checks.py", "rc_for_signoff")
    results = rc.run_all(outputs, data, full)
    passed = sum(1 for _, fails, _ in results if not fails)
    failing = [n for n, fails, _ in results if fails]
    return passed, len(results), failing


def word(n):
    return WORDS.get(n, str(n))


def read_pack(outputs):
    review = (outputs / "review.md")
    figs = json.loads((outputs / "pack-figures.json").read_text(encoding="utf-8"))["figures"]
    ver = re.search(r"^Pack version: (v\d+)", review.read_text(encoding="utf-8"), re.M)
    tr = load(CHECKS / "check_trace.py", "ct_for_signoff")
    rows = tr.table_rows((outputs / "challenges.md").read_text(encoding="utf-8")) or []
    for_auditor = sum(1 for _, _, st in rows if st == "for the auditor")
    return figs, (ver.group(1) if ver else "v?"), for_auditor


def report(outputs, data, full):
    for need in ("review.md", "pack-figures.json", "challenges.md"):
        if not (outputs / need).exists():
            print("cannot run: %s is missing" % (outputs / need))
            return 2
    passed, total, failing = verdict(outputs, data, full)
    figs, ver, n = read_pack(outputs)
    ready = not failing
    print("PLANNER DONE %s · CHALLENGER DONE · QA DONE: %s (%d/%d)" % (
        ver, "READY FOR SIGN-OFF" if ready else "BLOCKED", passed, total))
    risks, tests, tx = figs["approved_in_scope"], figs["tests"], figs["sampled_transactions"]
    if ready:
        chall = ("no challenges are" if n == 0 else "%s challenge%s %s" % (word(n).lower(), "" if n == 1 else "s", "is" if n == 1 else "are"))
        print("⏺ Team shut down. %s risk%s, %d tests, %d sampled transactions; %s for you. Ready for your sign-off in outputs/review.md." % (
            word(risks), "" if risks == 1 else "s", tests, tx, chall))
    else:
        print("⏺ Team shut down. The pack is BLOCKED: %s failing. It goes back to the team, not to you." % ", ".join(failing))
    return 0 if ready else 1


def record(outputs, data, full, name, decision, date, comment, replace):
    review = outputs / "review.md"
    if not review.exists():
        print("cannot run: %s is missing" % review)
        return 2
    name = (name or "").strip()
    if not name or re.fullmatch(r"<.*>", name):
        print("not recorded: a real reviewer name is required")
        return 1
    text = review.read_text(encoding="utf-8")
    if not re.search(r"^## Verdict\s*\nREADY FOR SIGN-OFF\s*$", text, re.M):
        print("not recorded: review.md does not carry the verdict READY FOR SIGN-OFF")
        return 1
    passed, total, failing = verdict(outputs, data, full)
    if failing:
        print("not recorded: the checks are not all passing now (%s failing); the pack goes back to the team" % ", ".join(failing))
        return 1
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print("not recorded: date must be YYYY-MM-DD")
        return 1
    box = ("[x] Signed off      [ ] Returned for rework" if decision == "sign-off"
           else "[ ] Signed off      [x] Returned for rework")
    m = re.search(r"Reviewer:(.*?)\s+Date:(.*)\n", text)
    filled = m and m.group(1).strip().strip("_") != ""
    new_block = "Reviewer: %s    Date: %s\n\nDecision:   %s" % (name, date, box)
    cur = BLOCK.search(text)
    if not cur:
        print("cannot run: the sign-off block in review.md is not in the expected form")
        return 2
    if filled and cur.group(0).strip() != new_block.strip() and not replace:
        print("not recorded: the sign-off block already holds a different entry; use --replace to overwrite it")
        return 1
    text = text[:cur.start()] + new_block + text[cur.end():]
    if comment:
        text = re.sub(r"(Comments:)[^\n]*", lambda mm: "Comments: " + comment.strip(), text, count=1)
    review.write_text(text, encoding="utf-8")
    if decision == "sign-off":
        print("Sign-off recorded in outputs/review.md. The pack is complete.")
    else:
        print("Return for rework recorded in outputs/review.md. The pack goes back to the team.")
    return 0


def main(argv=None):
    try:  # the report holds characters a Windows console cannot encode by default
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("report", "record"):
        p = sub.add_parser(n)
        p.add_argument("--outputs", default=str(ROOT / "outputs"))
        p.add_argument("--data", default=str(ROOT / "data"))
        p.add_argument("--full")
        if n == "record":
            p.add_argument("--name", required=True)
            p.add_argument("--decision", choices=("sign-off", "return"), default="sign-off")
            p.add_argument("--date", default=str(datetime.date.today()))
            p.add_argument("--comment", default="")
            p.add_argument("--replace", action="store_true")
    a = ap.parse_args(argv)
    outputs = Path(a.outputs)
    if a.cmd == "report":
        return report(outputs, a.data, a.full)
    return record(outputs, a.data, a.full, a.name, a.decision, a.date, a.comment, a.replace)


if __name__ == "__main__":
    sys.exit(main())
