#!/usr/bin/env python3
"""QA check: quotes.

1. Runs the extract-rules verifier on rules.json against the Contract Rules PDF
   (every quote on its stated page, schema, coverage).
2. Checks every rule excerpt in risk-register.md matches rules.json: each
   "rule ID . clause C . action" evidence line must carry the clause and the
   required_action of that rule exactly, and every [rule:ID] tag must exist.

Usage: check_quotes.py [--outputs DIR] [--data DIR] [--rules FILE] [--pdf FILE]
Exit 0 pass, 1 fail, 2 could not run. The check never changes a file.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / ".claude" / "skills" / "extract-rules" / "verify_quotes.py"
EXCERPT = re.compile(r"rule (CPR-\d+) · clause (.+?) · (.+?)\s*$")
TAG = re.compile(r"\[rule:([^\]]+)\]")


def run(outputs, data, rules=None, pdf=None):
    """Return (failures, summary)."""
    outputs, data = Path(outputs), Path(data)
    rules = Path(rules) if rules else outputs / "rules.json"
    pdf = Path(pdf) if pdf else data / "contract-rules.pdf"
    fails = []
    for p in (rules, pdf, VERIFIER, outputs / "risk-register.md"):
        if not p.exists():
            return ["missing input: %s" % p], "inputs missing"
    proc = subprocess.run([sys.executable, "-I", str(VERIFIER), str(rules), "--pdf", str(pdf)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    last = [l for l in out.splitlines() if l.strip()][-1:] or ["no output"]
    if proc.returncode != 0:
        errs = [l for l in out.splitlines() if l.startswith("ERROR") or l.startswith("cannot")]
        fails += ["rules.json: " + (l[6:] if l.startswith("ERROR ") else l) for l in (errs or last)]
    rj = json.loads(rules.read_text(encoding="utf-8"))
    by_id = {r["rule_id"]: r for r in rj["rules"]}
    text = (outputs / "risk-register.md").read_text(encoding="utf-8")
    text = re.sub(r"<!-- build_register:state .*? -->", "", text, flags=re.S)  # machine state, not register content
    matched = 0
    for n, line in enumerate(text.splitlines(), 1):
        m = EXCERPT.search(line)
        if m:
            rid, clause, action = m.group(1), m.group(2).strip(), m.group(3).strip()
            r = by_id.get(rid)
            if not r:
                fails.append("risk-register.md:%d: rule %s is not in rules.json" % (n, rid))
            elif clause != r["clause"]:
                fails.append("risk-register.md:%d: %s clause is %r in the register, %r in rules.json" % (n, rid, clause, r["clause"]))
            elif action != r["required_action"].strip():
                fails.append("risk-register.md:%d: %s excerpt does not match rules.json required_action" % (n, rid))
            else:
                matched += 1
        for tag in TAG.findall(line):
            if tag.strip() not in by_id:
                fails.append("risk-register.md:%d: [rule:%s] is not in rules.json" % (n, tag))
    if matched == 0 and not any("excerpt" in f for f in fails):
        fails.append("risk-register.md holds no rule excerpts to check")
    verdict = re.sub(r"^(PASS|FAIL):\s*", "", last[0].strip())[:80]
    return fails, "verifier: %s; %d register rule excerpts match rules.json" % (verdict, matched)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--rules")
    ap.add_argument("--pdf")
    a = ap.parse_args(argv)
    fails, summary = run(a.outputs, a.data, a.rules, a.pdf)
    for f in fails:
        print("FAIL  " + f)
    print("%s: quotes: %s" % ("FAIL" if fails else "PASS", summary))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
