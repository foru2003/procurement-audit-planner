#!/usr/bin/env python3
"""QA check: traceability.

1. Every rule in rules.json is cited by a rated risk (risk-ratings.json), a
   control or a test (audit-plan.json), or is listed in rules_not_tested with a
   reason.
2. Every approved, in-scope risk has a control with a test in the plan, and
   appears in risk-control-matrix.md and audit-program.md.
3. Every High risk (matrix label High or Extreme) is in scope, or its exclusion
   is recorded with a reason.
4. challenges.md exists, every row cites evidence, and none is open.

Usage: check_trace.py [--outputs DIR]
Exit 0 pass, 1 fail, 2 could not run. The check never changes a file.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / ".claude" / "skills" / "audit-program" / "build_pack.py"
RULE_TAG = re.compile(r"\[?rule:(CPR-\d+)\]?")
EVIDENCE = re.compile(r"\bCPR-\d+\b|\$\.[\w.\[\]-]+|\b(?:AO|FU|IS|LS|MX|BD|EL|AP|OR|DI|GA)-\d+\b|\b[TC]-\d+\.\d+\b|\bR-\d+\b")
STATUSES = {"resolved", "declined", "for the auditor"}


def load_builder():
    spec = importlib.util.spec_from_file_location("build_pack_for_qa", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table_rows(text):
    """Rows of the first markdown table that has Evidence and Status columns."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if "evidence" in cells and "status" in cells:
            ei, si = cells.index("evidence"), cells.index("status")
            out = []
            for l in lines[i + 2:]:
                if not l.strip().startswith("|"):
                    break
                c = [x.strip() for x in l.strip().strip("|").split("|")]
                if len(c) > max(ei, si):
                    out.append((c[0], c[ei], c[si].lower()))
            return out
    return None


def run(outputs):
    outputs = Path(outputs)
    needed = ["rules.json", "risk-ratings.json", "risk-register.md", "auditor-comments.md", "audit-plan.json",
              "risk-control-matrix.md", "audit-program.md", "planning-memo.md", "challenges.md"]
    miss = [n for n in needed if not (outputs / n).exists()]
    fails = ["missing input: outputs/%s" % n for n in miss]
    if any(n in miss for n in needed[:5]):
        return fails, "inputs missing"
    bp = load_builder()
    rules = json.loads((outputs / "rules.json").read_text(encoding="utf-8"))["rules"]
    ids = [r["rule_id"] for r in rules]
    ratings = json.loads((outputs / "risk-ratings.json").read_text(encoding="utf-8"))
    plan = json.loads((outputs / "audit-plan.json").read_text(encoding="utf-8"))
    reg, rev, applied = bp.read_register(outputs / "risk-register.md")
    dec = bp.read_decisions(outputs / "auditor-comments.md")

    # 1 rule coverage
    cited = set(RULE_TAG.findall(json.dumps(ratings.get("risks", []))))
    cited |= set(RULE_TAG.findall(json.dumps(plan.get("risks", []))))
    not_tested = {}
    for g in plan.get("rules_not_tested") or []:
        for x in g.get("rule_ids") or []:
            not_tested[x] = (g.get("reason") or "").strip()
    for x, why in not_tested.items():
        if not why:
            fails.append("rule %s is listed as not tested with no reason" % x)
        if x not in ids:
            fails.append("rules_not_tested names %s, which is not in rules.json" % x)
    gone = [x for x in ids if x not in cited and x not in not_tested]
    if gone:
        fails.append("%d rules are neither cited by a risk, control or test nor listed as not tested: %s" % (len(gone), ", ".join(gone)))

    # 2 approved risks traced through plan, matrix, program
    approved, out_scope = [], {}
    for rid, v in dec["rows"].items():
        d = bp.decision_word(v["decision"])
        if d in ("approve", "amend"):
            approved.append(rid)
        elif d == "reject":
            out_scope[rid] = v
    planned = {r["id"]: r for r in plan.get("risks", [])}
    matrix = (outputs / "risk-control-matrix.md").read_text(encoding="utf-8") if "risk-control-matrix.md" not in miss else ""
    program = (outputs / "audit-program.md").read_text(encoding="utf-8") if "audit-program.md" not in miss else ""
    for rid in approved:
        r = planned.get(rid)
        if not r:
            fails.append("%s is approved and in scope but has no plan entry" % rid)
            continue
        controls, tests = r.get("controls") or [], r.get("tests") or []
        if not controls:
            fails.append("%s has no control" % rid)
        for c in controls:
            if not any(t.get("control") == c.get("id") for t in tests):
                fails.append("%s: control %s has no test" % (rid, c.get("id")))
        if not re.search(r"^\| %s:" % re.escape(rid), matrix, re.M):
            fails.append("%s does not appear in risk-control-matrix.md" % rid)
        if not re.search(r"^## %s:" % re.escape(rid), program, re.M):
            fails.append("%s does not appear in audit-program.md" % rid)

    # 3 High risks in scope or exclusion recorded with a reason
    excl = {x.get("id"): x for x in ratings.get("excluded", []) if x.get("id")}
    high = [rid for rid, v in reg.items() if v["label"] in ("High", "Extreme")]
    for rid in high:
        if rid in approved:
            continue
        reason = (excl.get(rid) or {}).get("reason") or (out_scope.get(rid) or {}).get("comment") or ""
        if not reason.strip():
            fails.append("%s is rated High but is not in scope and no exclusion reason is recorded" % rid)
    for rid in out_scope:
        if not ((excl.get(rid) or {}).get("reason") or out_scope[rid]["comment"]).strip():
            fails.append("%s is out of scope with no reason recorded" % rid)

    # 4 challenges
    nrows = 0
    if "challenges.md" not in miss:
        text = (outputs / "challenges.md").read_text(encoding="utf-8")
        rows = table_rows(text)
        if rows is None:
            fails.append("challenges.md has no table with Evidence and Status columns")
        elif not rows and not re.search(r"no challenges?|no weak spots|sound", text, re.I):
            fails.append("challenges.md has an empty table and does not say no challenge was needed")
        else:
            for num, ev, st in rows:
                nrows += 1
                if not EVIDENCE.search(ev):
                    fails.append("challenges.md row %s cites no evidence (a rule ID, metric path, history ID or test or control ID)" % num)
                if st == "open":
                    fails.append("challenges.md row %s is still open" % num)
                elif st not in STATUSES:
                    fails.append("challenges.md row %s has status %r (expected resolved, declined or for the auditor)" % (num, st))
    return fails, "%d rules traced; %d approved risks traced; %d High risks checked; %d challenge rows closed" % (len(ids), len(approved), len(high), nrows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    a = ap.parse_args(argv)
    fails, summary = run(a.outputs)
    for f in fails:
        print("FAIL  " + f)
    print("%s: trace: %s" % ("FAIL" if fails else "PASS", summary))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
