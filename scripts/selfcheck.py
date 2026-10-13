import csv, json, sys
from collections import defaultdict
from datetime import date

OUT = "outputs/analytics-full/"
A = json.load(open("outputs/analytics.json"))
T = A["tests"]
fails = 0


def check(name, got, exp, tol=0.011):
    global fails
    if isinstance(got, (int, float)) and isinstance(exp, (int, float)):
        ok = abs(got - exp) <= tol
    else:
        ok = got == exp
    if not ok:
        fails += 1
    print("%s %s: analytics=%s rederived=%s" % ("PASS" if ok else "FAIL", name, got, exp))


def rd(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d(s):
    y, m, dd = s[:10].split("-")
    return date(int(y), int(m), int(dd))


spend = rd(OUT + "/spend-clean.csv")
excl = rd(OUT + "/spend-excluded.csv")
byid = dict((r["row_id"], r) for r in spend)
months = A["population"]["months_covered"]
fac = 12.0 / months

# population arithmetic
check("rows_raw = kept + excluded", A["population"]["rows_raw"], len(spend) + len(excl))
check("rows_after_exclusions = spend-clean rows", A["population"]["rows_after_exclusions"], len(spend))
check("excluded rows by category sum", sum(v["rows"] for v in A["population"]["excluded"].values()), len(excl))

# test 1
t1 = T["threshold_clustering"]["per_threshold"]
p = [x for x in t1 if x["band_count"] > 0][0]
Tv, inc = p["threshold"], p["inclusive"]
cnt = 0
tot = 0.0
for r in spend:
    a = float(r["amount"])
    if a >= 0.9 * Tv and ((a < Tv) if inc else (a <= Tv)):
        cnt += 1
        tot += a
check("threshold_clustering T=%s band count" % Tv, p["band_count"], cnt)
check("threshold_clustering T=%s band gbp" % Tv, p["band_gbp"], tot)
row = p["top20"][0]
src = byid[row["row_id"]]
check("threshold_clustering top row %s amount" % row["row_id"], row["amount"], float(src["amount"]))
for x in t1:
    check("threshold_clustering T=%s tag counts sum" % x["threshold"], sum(v["count"] for v in x["by_tag"].values()), x["band_count"])

# test 2
t2 = T["split_purchases"]["per_threshold"]
for x in t2:
    check("split_purchases T=%s tag counts sum" % x["threshold"], sum(v["count"] for v in x["by_tag"].values()), x["windows"])
x = [y for y in t2 if y["windows"] > 0][0]
w = x["top20"][0]
ids = w["row_ids"]
rows = [byid[i] for i in ids]
sup = set(r["supplier_norm"] for r in rows)
dates = sorted(d(r["pay_date"]) for r in rows)
check("split_purchases %s window total" % ids[0], w["window_total"], sum(float(r["amount"]) for r in rows))
check("split_purchases %s same supplier" % ids[0], len(sup), 1)
check("split_purchases %s span<30 days" % ids[0], (dates[-1] - dates[0]).days < 30, True)
check("split_purchases %s all payments < T and total >= T" % ids[0],
      all(float(r["amount"]) < x["threshold"] for r in rows) and sum(float(r["amount"]) for r in rows) >= x["threshold"], True)
# by-hand check that no other row of that supplier lies in the window
nm = list(sup)[0]
inwin = [r for r in spend if r["supplier_norm"] == nm and dates[0] <= d(r["pay_date"]) <= dates[-1] and float(r["amount"]) < x["threshold"]]
check("split_purchases %s n payments" % ids[0], w["n_payments"], len(inwin))

# test 3
t3 = T["high_value_suppliers"]
s0 = t3["top20_general_procurement"][0]
mine = [r for r in spend if r["supplier_norm"] == s0["supplier_norm"]]
tot = sum(float(r["amount"]) for r in mine)
check("high_value_suppliers %s annualised" % s0["row_ids"][0], s0["annualised_estimate"], tot * fac)
check("high_value_suppliers %s n payments" % s0["row_ids"][0], s0["n_payments"], len(mine))
check("high_value_suppliers tag counts sum", sum(v["count"] for v in t3["by_tag"].values()), t3["suppliers_at_or_above_quote_threshold"])
qt = t3["parameters"]["quote_threshold"]
sums = defaultdict(float)
for r in spend:
    if r["supplier_norm"]:
        sums[r["supplier_norm"]] += float(r["amount"])
n_hv = sum(1 for v in sums.values() if v * fac >= qt)
check("high_value_suppliers count at/above quote threshold", t3["suppliers_at_or_above_quote_threshold"], n_hv)

# test 5
t5 = T["duplicates"]["tiers"]
for tier, v in t5.items():
    check("duplicates %s tag group counts sum" % tier, sum(y["groups"] for y in v["by_tag"].values()), v["groups"])
    if not v["top20"]:
        continue
    g = v["top20"][0]
    rows = [byid[i] for i in g["row_ids"]]
    amts = set(r["amount"] for r in rows)
    sps = set(r["supplier_norm"] for r in rows)
    dts = sorted(d(r["pay_date"]) for r in rows)
    stamps = set(r["timestamp"] for r in rows)
    check("duplicates %s %s same amount+supplier" % (tier, g["row_ids"][0]), len(amts) + len(sps), 2)
    check("duplicates %s %s within 7 days" % (tier, g["row_ids"][0]), (dts[-1] - dts[0]).days <= 7, True)
    check("duplicates %s %s tier by timestamps" % (tier, g["row_ids"][0]), "same_timestamp" if len(stamps) == 1 else "different_time", tier)
    check("duplicates %s %s gbp beyond first" % (tier, g["row_ids"][0]), g["gbp_beyond_first"], float(rows[0]["amount"]) * (len(rows) - 1))

# notices-based
if "skipped" not in T["off_contract"]:
    notices = rd(OUT + "/notices-clean.csv")
    ws = A["population"]["date_min"]
    active_names = set()
    for n in notices:
        if (n["end"] == "" or n["end"][:10] >= ws) and (n["start"] == "" or n["start"][:10] <= A["population"]["date_max"]):
            active_names.add(n["supplier_norm"])
    oc = T["off_contract"]
    check("off_contract groups sum to suppliers classed", sum(v["count"] for v in oc["groups"].values()), oc["suppliers_classed"])
    u = oc["unmatched_general_procurement_top20"][0]
    mine = [r for r in spend if r["supplier_norm"] == u["supplier_norm"]]
    check("off_contract unmatched %s annualised" % u["row_ids"][0], u["annualised_estimate"], sum(float(r["amount"]) for r in mine) * fac)
    check("off_contract unmatched %s not an exact active notice name" % u["row_ids"][0], u["supplier_norm"] in active_names, False)
    check("off_contract unmatched %s above quote threshold" % u["row_ids"][0], u["annualised_estimate"] >= qt, True)
    if oc["candidates_top20_for_auditor_to_confirm"]:
        c = oc["candidates_top20_for_auditor_to_confirm"][0]
        check("off_contract candidate %s is not exact" % c["row_ids"][0], c["supplier_norm"] in active_names, False)
        check("off_contract candidate %s candidate name is active notice supplier" % c["row_ids"][0], c["candidate_notice_supplier"] in active_names, True)

if "skipped" not in T["expired_notice_spend"]:
    e = T["expired_notice_spend"]
    check("expired_notice_spend tag counts sum", sum(v["count"] for v in e["by_tag"].values()), e["suppliers"])
    r0 = e["top20"][0]
    mine = [n for n in notices if n["supplier_norm"] == r0["supplier_norm"]]
    all_ended = all(n["end"] != "" and n["end"][:10] < ws for n in mine)
    check("expired_notice_spend %s every notice ended before window" % r0["row_ids"][0], all_ended, True)
    check("expired_notice_spend %s latest end" % r0["row_ids"][0], r0["latest_notice_end"], max(n["end"][:10] for n in mine))
    sp_ = [r for r in spend if r["supplier_norm"] == r0["supplier_norm"]]
    check("expired_notice_spend %s annualised" % r0["row_ids"][0], r0["annualised_estimate"], sum(float(r["amount"]) for r in sp_) * fac)

if "skipped" not in T["spend_vs_award"]:
    s = T["spend_vs_award"]
    check("spend_vs_award tag counts sum", sum(v["count"] for v in s["by_tag"].values()), s["flagged_ratio_ge_1_25"])
    r0 = s["top20"][0]
    n = [n for n in notices if n["notice_id"] == r0["notice_id"] and n["supplier_norm"] == r0["supplier_norm"]][0]
    yrs = (d(n["end"]) - d(n["start"])).days / 365.25
    rate = float(n["awarded_value"]) / yrs
    sp_ = [r for r in spend if r["supplier_norm"] == r0["supplier_norm"]]
    ann = sum(float(r["amount"]) for r in sp_) * fac
    check("spend_vs_award %s ratio" % r0["row_ids"][0], r0["ratio"], ann / rate, tol=0.001)
    check("spend_vs_award %s ratio >= 1.25" % r0["row_ids"][0], r0["ratio"] >= 1.25, True)

sys.exit(1 if fails else 0)
