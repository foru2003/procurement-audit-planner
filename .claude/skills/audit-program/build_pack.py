#!/usr/bin/env python3
"""Validate outputs/audit-plan.json and render the audit planning pack.

Usage: build_pack.py [PLAN_JSON] [--gate]
       [--rules outputs/rules.json] [--analytics outputs/analytics.json]
       [--ratings outputs/risk-ratings.json] [--register outputs/risk-register.md]
       [--comments outputs/auditor-comments.md] [--full outputs/analytics-full]
       [--out-dir outputs]

--gate only checks the auditor gate: every risk in the register has a
decision and the register is a revision that applied them. It prints the
approved scope and exits 0, or names what is missing and exits 1.

Otherwise the plan is validated and rendered:
  scope      every planned risk is approved (Approve or Amend) and every
             approved risk is planned; nothing else.
  citations  [rule:ID] and [metric:$.path] resolve; {{$.path}} placeholders
             are filled from analytics.json; literal figures typed in prose
             are failures.
  samples    each test's sample recipe is drawn deterministically from a
             file in analytics-full/ and every transaction it yields exists
             in spend-clean.csv; the rows go to outputs/samples/<test>.csv.
  trace      every rule in rules.json is cited by a risk, a control or a
             test, or is listed in rules_not_tested with a reason; every
             planned risk has at least one control and one test.
Renders planning-memo.md, risk-control-matrix.md and audit-program.md
(ending with the PBC list) and writes pack-figures.json, the list of every
figure the builder itself computed, so the QA number check can trace them.
Exit 0 when no failures; exit 1 otherwise; exit 2 when an input is missing.

Reads the register and comments in the formats build_register.py writes: the
register's "## Revision N" heading, its Summary table and its "Auditor
decisions" table; the comments file's Risk | Statement | Rating | Decision |
Comment table. An optional "Reviewer:" or "Date:" line in the comments file
is carried into the pack when present.
"""
import argparse
import csv
import datetime
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

CITE_RE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")
PH_RE = re.compile(r"\{\{(\$[^}]+)\}\}")
NUM_RE = re.compile(r"£\s?\d|\b\d{3,}\b")
GATE_DECISIONS = {"approve", "amend", "reject"}
# Sample size follows the risk's score: (lowest score, items sampled). Fewer items
# are drawn only when the source file holds fewer (the description says so).
SAMPLE_BY_SCORE = ((9, 10), (0, 5))
LANG_RE = re.compile(r"\b(fraud\w*|illegal\w*|unlawful\w*|corrupt\w*|misconduct|embezzl\w*|theft|stolen|"
                     r"breach(?:ed|es)?|violat\w+|non-?complian\w+)\b", re.I)


def sample_size(score):
    for floor, n in SAMPLE_BY_SCORE:
        if score is not None and score >= floor:
            return n
    return SAMPLE_BY_SCORE[-1][1]


RATING_RE = re.compile(r"L(\d) × I(\d) = (\d+) · (.*?) · (.*)$")


def jpath(obj, path):
    """Resolve $.a.b[0].c against obj; return (found, value)."""
    if not path.startswith("$"):
        return False, None
    cur = obj
    for key, idx in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", path[1:]):
        try:
            cur = cur[int(idx)] if idx else cur[key]
        except (KeyError, IndexError, TypeError):
            return False, None
    return True, cur


def fmt(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, float):
        return "{:,.2f}".format(v) if v != int(v) else "{:,}".format(int(v))
    if isinstance(v, int):
        return "{:,}".format(v)
    return str(v)


def gbp(v):
    try:
        return "£{:,.2f}".format(float(v))
    except (TypeError, ValueError):
        return str(v)


def short(text, n=150):
    t = re.sub(r"\s+", " ", text or "").replace("|", "/")
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def read_decisions(path):
    """Decisions in auditor-comments.md: id -> {title, now, decision, comment, gone}."""
    out = {"reviewer": "", "date": "", "rows": OrderedDict()}
    if not path.exists():
        return out
    text = read(path)
    m = re.search(r"^Reviewer:[ \t]*(.*)$", text, re.M)
    out["reviewer"] = m.group(1).strip() if m else ""
    m = re.search(r"^Date:[ \t]*(.*)$", text, re.M)
    out["date"] = m.group(1).strip() if m else ""
    for line in text.splitlines():
        cells = [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if len(cells) >= 5 and re.fullmatch(r"R-\d+", cells[0]):
            out["rows"][cells[0]] = {"title": cells[1], "now": cells[2], "decision": cells[3].lower(),
                                     "comment": cells[4], "gone": False}
        elif len(cells) == 3 and re.fullmatch(r"R-\d+", cells[0]):
            out["rows"][cells[0]] = {"title": "", "now": "", "decision": cells[1].lower(), "comment": cells[2], "gone": True}
    return out


def decision_word(text):
    t = re.sub(r"[^a-z]", "", (text or "").lower())
    for w in ("approve", "amend", "reject"):
        if t.startswith(w):
            return w
    return t


def read_register(path):
    """Summary rows of risk-register.md, its revision number and its applied-decisions table."""
    rows, rev, applied = OrderedDict(), None, {}
    if not path.exists():
        return rows, rev, applied
    text = read(path)
    m = re.search(r"^## Revision (\d+)\s*$", text, re.M)
    rev = int(m.group(1)) if m else None
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line.strip()
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section == "## Summary" and len(cells) >= 6 and re.fullmatch(r"R-\d+", cells[0]):
            rm = RATING_RE.search(cells[3])
            rows[cells[0]] = {"theme": cells[1], "title": cells[2],
                              "score": int(rm.group(3)) if rm else None,
                              "label": rm.group(4) if rm else "", "band": rm.group(5) if rm else "",
                              "rating": cells[3]}
        elif section == "## Auditor decisions" and len(cells) >= 5 and re.fullmatch(r"R-\d+", cells[0]):
            applied[cells[0]] = cells[3]
    return rows, rev, applied


def scope_check(reg, rev, applied, dec, ratings, fails):
    """The approved scope, or failures explaining why the gate is not closed."""
    if not reg:
        fails.append("gate: risk-register.md has no summary table")
        return OrderedDict(), OrderedDict()
    undecided = [rid for rid in reg if not dec["rows"].get(rid, {}).get("decision", "")]
    if undecided:
        fails.append("gate not closed: no decision for %s in auditor-comments.md" % ", ".join(undecided))
    bad = [rid for rid, v in dec["rows"].items() if v["decision"] and decision_word(v["decision"]) not in GATE_DECISIONS]
    if bad:
        fails.append("gate: decision not approve/amend/reject for %s" % ", ".join(bad))
    if rev is None:
        fails.append("gate: the register is not a revision; re-run the risk-assessor so the decisions are applied")
    unapplied = [rid for rid, v in dec["rows"].items() if v["decision"] and not re.fullmatch(r"\d+", applied.get(rid, ""))]
    if unapplied:
        fails.append("gate: decisions not yet applied in the register for %s; re-run the risk-assessor" % ", ".join(unapplied))
    rat = {r["id"]: r for r in ratings.get("risks", [])}
    excl = {x.get("id"): x for x in ratings.get("excluded", []) if x.get("id")}
    approved, out_of_scope = OrderedDict(), OrderedDict()
    for rid, v in dec["rows"].items():
        d = decision_word(v["decision"])
        if d in ("approve", "amend"):
            if rid not in reg or rid not in rat:
                fails.append("gate: %s is %sd but not in the current register" % (rid, d))
                continue
            approved[rid] = dict(reg[rid], decision=d, comment=v["comment"],
                                 override=bool(rat[rid].get("auditor_override")),
                                 sample_source=rat[rid].get("sample_source", ""))
        elif d == "reject":
            if rid in reg:
                fails.append("gate: %s was rejected but is still in the register; re-run the risk-assessor" % rid)
            reason = (excl.get(rid) or {}).get("reason") or v["comment"] or "rejected at the gate"
            out_of_scope[rid] = {"title": v["title"] or (reg.get(rid) or {}).get("title", ""), "score": None, "label": "",
                                 "band": "", "decision": d, "comment": v["comment"], "reason": reason}
    return approved, out_of_scope


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def sheet_row(row_id):
    return row_id.rsplit(":", 1)[-1] if ":" in row_id else ""


def draw_sample(spec, tid, full, spend_by_id, spend_rows, fails, drawn=None):
    """Apply a sample recipe to a file in analytics-full/. Returns (rows, describe).
    drawn: {test id: {"suppliers": set, "row_ids": set}} for tests already sampled."""
    drawn = drawn or {}
    kind = spec.get("kind", "rows")
    if kind == "none":
        return [], spec.get("note", "no transaction sample; document or enquiry test")
    src = full / spec.get("source", "")
    if not src.exists():
        fails.append("%s: sample source not found %s" % (tid, spec.get("source")))
        return [], ""
    rows = load_csv(src)
    where = spec.get("where") or {}
    for col, want in where.items():
        if rows and col not in rows[0]:
            fails.append("%s: sample where-column %r not in %s" % (tid, col, spec["source"]))
            return [], ""
        wants = want if isinstance(want, list) else [want]
        rows = [r for r in rows if r[col] in [str(w) for w in wants]
                or (to_num(r[col]) is not None and any(to_num(r[col]) == to_num(w) for w in wants))]
    for col, lo in (spec.get("where_min") or {}).items():
        rows = [r for r in rows if to_num(r.get(col)) is not None and to_num(r[col]) >= float(lo)]
    for col, hi in (spec.get("where_max") or {}).items():
        rows = [r for r in rows if to_num(r.get(col)) is not None and to_num(r[col]) <= float(hi)]
    for col, pat in (spec.get("where_not_match") or {}).items():
        try:
            rx = re.compile(pat, re.I)
        except re.error:
            fails.append("%s: where_not_match pattern for %r is not a valid regex" % (tid, col))
            return [], ""
        rows = [r for r in rows if not rx.search(r.get(col, ""))]
    excl_sup, excl_ids = set(), set()
    for other in spec.get("exclude_drawn_in") or []:
        if other not in drawn:
            fails.append("%s: exclude_drawn_in names %s, which has not been sampled before this test" % (tid, other))
            return [], ""
        excl_sup |= drawn[other]["suppliers"]
        excl_ids |= drawn[other]["row_ids"]
    if excl_sup and rows and "supplier_norm" in rows[0]:
        rows = [r for r in rows if r.get("supplier_norm") not in excl_sup]
    order = spec.get("order_by")
    if order:
        if rows and order not in rows[0]:
            fails.append("%s: sample order_by column %r not in %s" % (tid, order, spec["source"]))
            return [], ""
        rows.sort(key=lambda r: (to_num(r[order]) if to_num(r[order]) is not None else 0, r[order]),
                  reverse=bool(spec.get("descending", True)))
    if spec.get("distinct_by"):
        col, seen, uniq = spec["distinct_by"], set(), []
        if rows and col not in rows[0]:
            fails.append("%s: distinct_by column %r not in %s" % (tid, col, spec["source"]))
            return [], ""
        for r in rows:
            if r[col] not in seen:
                seen.add(r[col])
                uniq.append(r)
        rows = uniq
    n = int(spec.get("n", 10))
    picked = rows[:n]
    per = int(spec.get("per_group_n", 0) or 0)
    out = []
    for i, r in enumerate(picked, 1):
        if kind == "rows":
            ids, key = [r.get("row_id", "")], r.get("row_id", "")
        elif kind == "groups":
            ids = [x for x in re.split(r"[;,]\s*", r.get(spec.get("ids_column", "row_ids"), "")) if x]
            if per:
                ids.sort(key=lambda x: -(to_num((spend_by_id.get(x) or {}).get("amount")) or 0))
                ids = ids[:per]
            kcols = spec.get("key") or ("group_id" if "group_id" in r else None)
            if isinstance(kcols, str):
                kcols = [kcols]
            if kcols and any(c not in r for c in kcols):
                fails.append("%s: group key column(s) %s not in %s" % (tid, kcols, spec["source"]))
                return [], ""
            key = "|".join(r[c] for c in kcols) if kcols else str(i)
        elif kind == "suppliers":
            sup = r.get("supplier_norm", "")
            pay = [s for s in spend_rows if s.get("supplier_norm") == sup]
            pay.sort(key=lambda s: -(to_num(s.get("amount")) or 0))
            ids = [s["row_id"] for s in (pay[:per] if per else pay)]
            key = sup
        else:
            fails.append("%s: unknown sample kind %r" % (tid, kind))
            return [], ""
        for rid in ids:
            if rid in excl_ids:
                continue
            s = spend_by_id.get(rid)
            if not s:
                fails.append("%s: sampled row_id %s not found in spend-clean.csv" % (tid, rid))
                continue
            out.append({"test": tid, "item": i, "group": key, "row_id": rid, "source_file": s.get("source_file", ""),
                        "sheet_row": sheet_row(rid), "pay_date": s.get("pay_date", ""),
                        "supplier": s.get("supplier", ""), "amount": s.get("amount", ""),
                        "service": s.get("Service", ""), "narrative": s.get("Narrative", "")})
    parts = ["%d %s from `%s`" % (len(picked), "item" if len(picked) == 1 else "items", spec["source"])]
    conds = ["%s = %s" % (c, v) for c, v in where.items()] \
        + ["%s ≥ %s" % (c, v) for c, v in (spec.get("where_min") or {}).items()] \
        + ["%s ≤ %s" % (c, v) for c, v in (spec.get("where_max") or {}).items()]
    if conds:
        parts.append("where " + ", ".join(conds))
    if order:
        parts.append("largest %s first" % order if spec.get("descending", True) else "smallest %s first" % order)
    if kind == "suppliers":
        parts.append("%s payments per supplier" % ("all" if not per else per))
    if kind == "groups" and per:
        parts.append("largest %d payments per item" % per)
    if spec.get("distinct_by"):
        parts.append("one item per %s" % spec["distinct_by"])
    if spec.get("where_not_match"):
        parts.append("excluding " + ", ".join("%s matching /%s/" % (c, p) for c, p in spec["where_not_match"].items()))
    if spec.get("exclude_drawn_in"):
        parts.append("excluding suppliers and rows already drawn in " + ", ".join(spec["exclude_drawn_in"]))
    if len(rows) < n:
        parts.append("(only %d available)" % len(rows))
    return out, ", ".join(parts) + "; %d transactions" % len(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", nargs="?", default="outputs/audit-plan.json")
    ap.add_argument("--gate", action="store_true", help="only check the auditor gate and print the scope")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--ratings", default="outputs/risk-ratings.json")
    ap.add_argument("--register", default="outputs/risk-register.md")
    ap.add_argument("--comments", default="outputs/auditor-comments.md")
    ap.add_argument("--full", default="outputs/analytics-full")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args(argv)

    fails, warns, figures = [], [], OrderedDict()
    try:
        rules = json.loads(read(a.rules))
        an = json.loads(read(a.analytics))
        ratings = json.loads(read(a.ratings))
    except (OSError, ValueError) as exc:
        print("cannot run: %s" % exc)
        return 2
    rule_ids = OrderedDict((r["rule_id"], r) for r in rules["rules"])
    reg, rev, applied = read_register(Path(a.register))
    dec = read_decisions(Path(a.comments))
    approved, out_of_scope = scope_check(reg, rev, applied, dec, ratings, fails)

    if a.gate:
        for f in fails:
            print("FAIL ", f)
        if not fails:
            print("gate closed: register revision %s, %d decisions · approved, in scope: %d · not in scope: %s" % (
                rev, len(dec["rows"]), len(approved),
                ", ".join("%s (%s)" % (rid, v["decision"]) for rid, v in out_of_scope.items()) or "none"))
        return 1 if fails else 0

    try:
        P = json.loads(read(a.plan))
    except (OSError, ValueError) as exc:
        print("cannot run: %s" % exc)
        return 2
    full = Path(a.full)
    spend_rows = load_csv(full / "spend-clean.csv") if (full / "spend-clean.csv").exists() else []
    spend_by_id = {r["row_id"]: r for r in spend_rows}
    if not spend_by_id:
        fails.append("%s/spend-clean.csv missing: samples cannot be verified" % full)

    cited_rules = OrderedDict()

    def resolve(text, where):
        ok = 0
        for kind, ref in CITE_RE.findall(text or ""):
            ref = ref.strip()
            if kind == "rule":
                if ref in rule_ids:
                    ok += 1
                    cited_rules.setdefault(ref, set()).add(where.split(".")[0])
                else:
                    fails.append("%s: unknown rule %s" % (where, ref))
            elif kind == "metric":
                found, val = jpath(an, ref)
                if found and not isinstance(val, (dict, list)):
                    ok += 1
                elif found:
                    fails.append("%s: metric %s is not a scalar" % (where, ref))
                else:
                    fails.append("%s: metric path not found %s" % (where, ref))
            else:
                ok += 1
        return ok

    def fill(text, where):
        def sub(m):
            found, val = jpath(an, m.group(1))
            if not found or isinstance(val, (dict, list)):
                fails.append("%s: placeholder not resolvable %s" % (where, m.group(1)))
                return "«unresolved»"
            return fmt(val)
        out = PH_RE.sub(sub, text or "")
        stripped = CITE_RE.sub("", PH_RE.sub("", text or ""))
        if NUM_RE.search(stripped):
            fails.append("%s: literal figure typed in prose; use a {{metric}} placeholder: %r" % (where, stripped[:70]))
        m = LANG_RE.search(stripped)
        if m:
            warns.append("%s: uses the word %r; describe the pattern the test checks, not what it implies" % (where, m.group(0)))
        return out

    def cite_list(cites, where):
        for c in cites or []:
            resolve("[%s]" % c, where)
        return ", ".join(c.split(":", 1)[1] if c.startswith("rule:") else c for c in cites or [])

    planned = OrderedDict((r["id"], r) for r in P.get("risks", []))
    for rid in planned:
        if rid not in approved:
            fails.append("scope: %s is planned but is not an approved risk" % rid)
    for rid in approved:
        if rid not in planned:
            fails.append("scope: %s is approved but has no plan entry" % rid)
    for r in ratings.get("risks", []):
        for kind, ref in CITE_RE.findall(json.dumps(r)):
            if kind == "rule" and ref in rule_ids:
                cited_rules.setdefault(ref, set()).add(r["id"])

    samples_dir = Path(a.out_dir) / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    for old in samples_dir.glob("T-*.csv"):
        old.unlink()
    all_samples, pbc, drawn = [], OrderedDict(), OrderedDict()
    n_controls = n_tests = 0
    for rid, r in planned.items():
        controls, tests = r.get("controls") or [], r.get("tests") or []
        if not controls:
            fails.append("%s: no expected control" % rid)
        if not tests:
            fails.append("%s: no test step" % rid)
        cids = set()
        for c in controls:
            n_controls += 1
            cids.add(c.get("id"))
            if not c.get("cites"):
                fails.append("%s.%s: control cites no rule" % (rid, c.get("id")))
            c["_cites"] = cite_list(c.get("cites"), "%s.%s" % (rid, c.get("id")))
            c["_text"] = fill(c.get("control", ""), "%s.%s" % (rid, c.get("id")))
        tested = set()
        for t in tests:
            n_tests += 1
            tid = t.get("id", "?")
            if t.get("control") not in cids:
                fails.append("%s.%s: test refers to control %r which is not defined for this risk" % (rid, tid, t.get("control")))
            tested.add(t.get("control"))
            if not t.get("cites"):
                fails.append("%s.%s: test cites no rule or metric" % (rid, tid))
            t["_cites"] = cite_list(t.get("cites"), "%s.%s" % (rid, tid))
            t["_step"] = fill(t.get("step", ""), "%s.%s" % (rid, tid))
            t["_evidence"] = fill(t.get("evidence", ""), "%s.%s" % (rid, tid))
            spec = dict(t.get("sample") or {"kind": "none", "note": "no sample specified"})
            if spec.get("kind", "rows") != "none":
                want = sample_size((approved.get(rid) or {}).get("score"))
                if "n" in spec and to_num(spec["n"]) != want:
                    fails.append("%s.%s: sample size follows the risk's score: %d items for score %s, not %s (omit n to take the rule)" % (
                        rid, tid, want, (approved.get(rid) or {}).get("score"), spec["n"]))
                spec["n"] = want
            rows, desc = draw_sample(spec, tid, full, spend_by_id, spend_rows, fails, drawn)
            t["_rows"], t["_desc"] = rows, desc
            drawn[tid] = {"suppliers": {(spend_by_id.get(s["row_id"]) or {}).get("supplier_norm") for s in rows},
                          "row_ids": {s["row_id"] for s in rows}}
            if spec.get("kind", "rows") != "none" and not rows:
                fails.append("%s.%s: sample recipe yielded no transactions" % (rid, tid))
            if rows:
                with open(samples_dir / ("%s.csv" % tid), "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    w.writeheader()
                    w.writerows(rows)
                all_samples += rows
            for item in t.get("pbc") or []:
                pbc.setdefault(rid, OrderedDict()).setdefault(item, []).append(tid)
        for c in controls:
            if c.get("id") not in tested:
                fails.append("%s.%s: control has no test" % (rid, c.get("id")))

    not_tested = OrderedDict()
    for grp in P.get("rules_not_tested") or []:
        if not grp.get("reason"):
            fails.append("rules_not_tested: a group has no reason")
        for x in grp.get("rule_ids") or []:
            if x not in rule_ids:
                fails.append("rules_not_tested: unknown rule %s" % x)
            not_tested[x] = grp.get("reason", "")
    uncovered = [x for x in rule_ids if x not in cited_rules and x not in not_tested]
    if uncovered:
        fails.append("trace: %d rules neither cited by a risk, control or test nor listed as not tested: %s%s" % (
            len(uncovered), ", ".join(uncovered[:12]), "…" if len(uncovered) > 12 else ""))
    both = [x for x in not_tested if x in cited_rules]
    if both:
        warns.append("rules listed as not tested but also cited: %s" % ", ".join(both))

    M = P.get("memo") or {}
    memo = {k: [fill(p, "memo.%s" % k) for p in (M.get(k) if isinstance(M.get(k), list) else [M.get(k, "")])]
            for k in ("purpose", "background", "approach", "limitations")}
    for k in ("purpose", "background", "approach"):
        if not any(s.strip() for s in memo[k]):
            fails.append("memo.%s is empty" % k)

    recipe_values = set()
    for floor, size in SAMPLE_BY_SCORE:
        recipe_values.update((floor, size))
    for r in planned.values():
        for t in r.get("tests") or []:
            spec = t.get("sample") or {}
            for key in ("n", "per_group_n"):
                if to_num(spec.get(key)) is not None:
                    recipe_values.add(to_num(spec.get(key)))
            for cond in ("where", "where_min", "where_max"):
                for v in (spec.get(cond) or {}).values():
                    for x in (v if isinstance(v, list) else [v]):
                        if to_num(x) is not None:
                            recipe_values.add(to_num(x))
    figures["sample_recipe_values"] = sorted(recipe_values)
    figures.update({
        "approved_in_scope": len(approved), "not_in_scope": len(out_of_scope), "register_risks": len(reg),
        "controls": n_controls, "tests": n_tests, "sampled_transactions": len(all_samples),
        "sampled_gbp": round(sum(to_num(s["amount"]) or 0 for s in all_samples), 2),
        "rules_total": len(rule_ids), "rules_cited": len([x for x in rule_ids if x in cited_rules]),
        "rules_not_tested": len([x for x in rule_ids if x not in cited_rules and x in not_tested]),
        "register_revision": rev, "decisions": len(dec["rows"]),
        "pbc_items": sum(len(v) for v in pbc.values()),
    })

    today = P.get("generated_at") or str(datetime.date.today())
    who = " by %s" % dec["reviewer"] if dec["reviewer"] else ""
    when = " dated %s" % dec["date"] if dec["date"] else ""
    head_note = ("*Generated %s by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision %s), "
                 "`auditor-comments.md`%s%s, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review "
                 "and auditor sign-off.*\n" % (today, rev, who, when))
    indic = ("**Indicators, not findings.** Every test below checks a control against a pattern in public data. "
             "Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.\n")

    def risk_line(rid, v):
        sc = "%s (%s; %s)" % (v["score"], v["label"], v["band"]) if v.get("score") is not None else "not rated"
        return "%s: %s [%s]" % (rid, short(v.get("title", ""), 110), sc)

    md = ["# Procurement audit: planning memo\n", head_note, indic, "## Purpose\n", *memo["purpose"],
          "\n## Background\n", *memo["background"], "\n## Scope\n"]
    n_out = figures["not_in_scope"]
    md.append("The register lists %d rated risks. The auditor recorded %d decisions%s%s: %d risks are approved and in scope, "
              "and %d %s not.\n" % (figures["register_risks"], figures["decisions"], who, when, figures["approved_in_scope"],
                                    n_out, "is" if n_out == 1 else "are"))
    md.append("| ID | Risk | Score | Band | Decision | Auditor comment |\n|---|---|---|---|---|---|")
    for rid, v in approved.items():
        note = short(v["comment"], 160) + (" (auditor override applied)" if v["override"] else "")
        md.append("| %s | %s | %s | %s | %s | %s |" % (rid, short(v["title"], 120), v["score"], v["band"], v["decision"], note))
    if out_of_scope:
        md.append("\n**Not in scope**\n")
        for rid, v in out_of_scope.items():
            md.append("- %s: %s: %s; %s" % (rid, short(v["title"], 110), v["decision"], v["reason"]))
    md += ["\n## Approach\n", *memo["approach"]]
    md.append("\nThe programme holds %d expected controls and %d test steps, with %d sampled transactions worth £%s, each "
              "traceable to its row in the council's published workbooks (see `audit-program.md` and `outputs/samples/`)." % (
                  figures["controls"], figures["tests"], figures["sampled_transactions"], "{:,.2f}".format(figures["sampled_gbp"])))
    md.append("\n## Rules coverage\n")
    md.append("%d of %d rules in `rules.json` are cited by a risk, a control or a test. The remaining %d are not tested in this "
              "audit, for these reasons:\n" % (figures["rules_cited"], figures["rules_total"], figures["rules_not_tested"]))
    by_reason = OrderedDict()
    for x, why in not_tested.items():
        if x not in cited_rules:
            by_reason.setdefault(why, []).append(x)
    for why, xs in by_reason.items():
        md.append("- %s: %s" % (why, ", ".join(xs)))
    if any(s.strip() for s in memo["limitations"]):
        md.append("\n## Limitations\n")
        for line in memo["limitations"]:
            if line.strip():
                md.append("- %s" % line)
    md.append("\n## Review and sign-off\n")
    md.append("The challenger's points and their status are in `challenges.md`; points marked *for the auditor* need a decision "
              "at sign-off. The QA reviewer's checks and verdict are in `review.md`, which ends with the sign-off block.")
    out = Path(a.out_dir)
    (out / "planning-memo.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    md = ["# Risk-control matrix\n", head_note, indic,
          "| Risk | Score | Expected control | Rules | Tests |\n|---|---|---|---|---|"]
    for rid, r in planned.items():
        v = approved.get(rid, {})
        for c in r.get("controls") or []:
            tests = ", ".join(t.get("id", "?") for t in r.get("tests") or [] if t.get("control") == c.get("id"))
            md.append("| %s: %s | %s (%s) | %s: %s | %s | %s |" % (rid, short(v.get("title", ""), 90), v.get("score", ""), v.get("band", ""),
                                                                c.get("id"), c["_text"], c["_cites"], tests))
    (out / "risk-control-matrix.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    md = ["# Audit program\n", head_note, indic,
          "%d risks in scope, %d controls, %d tests, %d sampled transactions. Samples are drawn by the builder from "
          "`analytics-full/` by the recipe stated under each test, and every transaction is listed with its workbook row.\n" % (
              figures["approved_in_scope"], figures["controls"], figures["tests"], figures["sampled_transactions"])]
    for rid, r in planned.items():
        v = approved.get(rid, {})
        md.append("\n## %s\n" % risk_line(rid, v))
        if r.get("objective"):
            md.append("**Audit objective.** %s\n" % fill(r["objective"], "%s.objective" % rid))
        for c in r.get("controls") or []:
            md.append("**%s. Expected control.** %s [%s]%s\n" % (c.get("id"), c["_text"], c["_cites"],
                                                              " Owner: %s." % c["owner"] if c.get("owner") else ""))
            for t in r.get("tests") or []:
                if t.get("control") != c.get("id"):
                    continue
                md.append("**%s. Test.** %s [%s]  \n**Evidence to inspect:** %s  \n**Sample:** %s\n" % (
                    t.get("id"), t["_step"], t["_cites"], t["_evidence"], t["_desc"]))
                if t["_rows"]:
                    md.append("| # | Row ID | Date | Supplier | Amount | Service |\n|---|---|---|---|---|---|")
                    for s in t["_rows"]:
                        md.append("| %s | `%s` | %s | %s | %s | %s |" % (s["item"], s["row_id"], s["pay_date"], s["supplier"],
                                                                       gbp(s["amount"]), s["service"]))
                    md.append("")
    md.append("\n## Prepared-by-client (PBC) request list\n")
    md.append("Derived from the test steps above. Each item names the tests that need it.\n")
    md.append("| # | Risk | Item requested | For tests |\n|---|---|---|---|")
    n = 0
    for rid, items in pbc.items():
        for item, tids in items.items():
            n += 1
            md.append("| %d | %s | %s | %s |" % (n, rid, item, ", ".join(tids)))
    (out / "audit-program.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "pack-figures.json").write_text(json.dumps({"generated_at": today, "figures": figures}, indent=2) + "\n", encoding="utf-8")

    for w in warns:
        print("WARN ", w)
    for f in fails:
        print("FAIL ", f)
    print("\nscope: %d approved risks planned, %d not in scope; controls: %d; tests: %d; sampled transactions: %d; "
          "rules cited: %d/%d; warnings: %d; failures: %d" % (len(approved), len(out_of_scope), n_controls, n_tests, len(all_samples),
                                                              figures["rules_cited"], figures["rules_total"], len(warns), len(fails)))
    for name in ("planning-memo.md", "risk-control-matrix.md", "audit-program.md", "pack-figures.json"):
        print("written: %s" % Path(a.out_dir, name))
    print("written: %s/ (%d files)" % (samples_dir, len(list(samples_dir.glob("T-*.csv")))))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
