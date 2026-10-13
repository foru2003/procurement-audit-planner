import warnings
warnings.filterwarnings("ignore")
import datetime, difflib, json, os, re, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import normalise_supplier

OUT = "outputs/analytics-full"
TAGS = ["general_procurement", "care_or_education_placement", "grant", "agency_staff", "premises_non_procurement"]
CAVEAT = ("contracts.csv holds published notices, not a contract register. It holds awards published on Contracts Finder in "
          "roughly the last five years. A contract awarded earlier (e.g. long-running waste or highways contracts), one advertised "
          "only on Find a Tender, a framework call-off recorded under another buyer, or an exempt placement will have no notice here. "
          "\"No notice found\" is therefore an indicator to check against the council's contract register, never evidence of off-contract spend.")

rules = json.load(open("outputs/rules.json"))
log = json.load(open(OUT + "/cleaning-log.json"))
sp = pd.read_csv(OUT + "/spend-clean.csv", dtype={"supplier_norm": str}, keep_default_na=False, na_values=[""])
sp["supplier_norm"] = sp["supplier_norm"].fillna("")
sp["Narrative"] = sp["Narrative"].fillna("")
sp["date"] = pd.to_datetime(sp["pay_date"], format="%Y-%m-%d")
months = log["months_covered"]
FACTOR = 12.0 / months
contracts_present = bool(log.get("contracts_present"))
register_present = bool(log.get("register_present"))
notices = pd.read_csv(OUT + "/notices-clean.csv", keep_default_na=False, na_values=[""], dtype={"supplier_norm": str}) if contracts_present else None
if notices is not None:
    for c in ("start", "end", "awarded_date", "published"):
        notices[c] = pd.to_datetime(notices[c])
    notices["supplier_norm"] = notices["supplier_norm"].fillna("")

skipped = []
min_amount = float(sp["amount"].min())


def r2(x):
    return round(float(x), 2)


def tagsplit(df, tagcol, gbpcol=None):
    out = {}
    for t in TAGS:
        m = df[tagcol] == t
        d = {"count": int(m.sum())}
        if gbpcol:
            d["gbp"] = r2(df.loc[m, gbpcol].sum())
        out[t] = d
    return out


def jclean(o):
    if isinstance(o, dict):
        return {str(k): jclean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jclean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o != o) else float(o)
    if isinstance(o, (pd.Timestamp, datetime.date)):
        return str(o)[:10]
    if o is pd.NaT:
        return None
    return o


# ---------------- thresholds from rules.json ----------------
params = rules.get("parameters", {})
byval = {}
param_rules = {}
for rl in rules["rules"]:
    comp_text = bool(re.search(r"three|five|tender|invitation", rl.get("required_action", ""), re.I))
    comp = rl.get("type") in ("procedure", "advertising") and comp_text
    for role in ("threshold_low", "threshold_high"):
        t = rl.get(role) or {}
        v = t.get("value")
        if v is not None:
            e = byval.setdefault(v, {"rule_ids": [], "comp_rules": [], "incl": {}, "comp_incl": []})
            e["rule_ids"].append(rl["rule_id"])
            e["incl"][rl["rule_id"] + ":" + role] = t.get("inclusive")
            if comp:
                e["comp_rules"].append(rl["rule_id"])
                e["comp_incl"].append((role, t.get("inclusive")))
        p = t.get("parameter")
        if p:
            param_rules.setdefault(p, []).append(rl["rule_id"])
thresholds = []
for v in sorted(byval):
    e = byval[v]
    incl = None
    if e["comp_incl"]:
        lows = [i for r, i in e["comp_incl"] if r == "threshold_low" and i is not None]
        incl = lows[0] if lows else e["comp_incl"][0][1]
    else:
        vals = [i for i in e["incl"].values() if i is not None]
        incl = vals[0] if vals else False
    thresholds.append({"value": v, "inclusive": bool(incl), "competition_triggering": bool(e["comp_rules"]),
                       "rule_ids": sorted(set(e["rule_ids"])), "competition_rule_ids": sorted(set(e["comp_rules"])),
                       "inclusive_by_citation": e["incl"], "skipped_band_below_min_payment": bool(v <= min_amount)})
comp_thr = [t for t in thresholds if t["competition_triggering"]]
quote_thr = min(t["value"] for t in comp_thr)
quote_incl = [t for t in comp_thr if t["value"] == quote_thr][0]["inclusive"]
null_params = [p for p, v in params.items() if v is None]
for p in params:
    param_rules.setdefault(p, [])
for t in thresholds:
    if t["skipped_band_below_min_payment"]:
        skipped.append({"test": "threshold_clustering", "tier": "T=%s" % t["value"],
                        "reason": "band lies below the smallest published payment (%.2f); population contains payments over 500 only" % min_amount,
                        "rule_ids": t["rule_ids"]})
for p in null_params:
    for tst in ("threshold_clustering", "split_purchases", "high_value_suppliers"):
        skipped.append({"test": tst, "tier": "parameter " + p,
                        "reason": "%s is null in rules.json; tier not run" % p, "rule_ids": sorted(set(param_rules[p]))})
run_thr = [t for t in thresholds if not t["skipped_band_below_min_payment"]]


def below(a, T, incl):
    return (a < T) if incl else (a <= T)


def atleast(a, T, incl):
    return (a >= T) if incl else (a > T)


tests = {}
sp["annual_factor"] = FACTOR

# ---------------- supplier table ----------------
def dominant(series_vals, weights):
    s = pd.Series(weights.values, index=series_vals.values).groupby(level=0).sum()
    return s.idxmax()


g = sp.groupby("supplier_norm")
sup = g.agg(total=("amount", "sum"), n_payments=("amount", "size"), supplier=("supplier", lambda s: s.value_counts().index[0]),
            n_tags=("tag", "nunique")).reset_index()
tag_gbp = sp.groupby(["supplier_norm", "tag"])["amount"].sum().reset_index().sort_values(["supplier_norm", "amount"], ascending=[True, False])
dom_tag = tag_gbp.drop_duplicates("supplier_norm").set_index("supplier_norm")["tag"]
nar_gbp = sp.groupby(["supplier_norm", "Narrative"])["amount"].sum().reset_index().sort_values(["supplier_norm", "amount"], ascending=[True, False])
dom_nar = nar_gbp.drop_duplicates("supplier_norm").set_index("supplier_norm")["Narrative"]
svc_gbp = sp.groupby(["supplier_norm", "Service"])["amount"].sum().reset_index().sort_values(["supplier_norm", "amount"], ascending=[True, False])
dom_svc = svc_gbp.drop_duplicates("supplier_norm").set_index("supplier_norm")["Service"]
sup["dominant_tag"] = sup["supplier_norm"].map(dom_tag)
sup["dominant_narrative"] = sup["supplier_norm"].map(dom_nar)
sup["dominant_service"] = sup["supplier_norm"].map(dom_svc)
sup["spans_several_tags"] = sup["n_tags"] > 1
sup["total"] = sup["total"].round(2)
sup["annualised_estimate"] = (sup["total"] * FACTOR).round(2)
rid_top = sp.sort_values("amount", ascending=False).groupby("supplier_norm")["row_id"].apply(lambda s: list(s)).to_dict()

# ---------------- supplier matching ----------------
GENERIC = set("AND OF THE SERVICES SERVICE GROUP CARE COMPANY HOMES HOME HOUSE UNIVERSITY COUNCIL TRUST SOLUTIONS CONSULTANCY CONSULTING "
              "ASSOCIATES PARTNERSHIP NETWORK CENTRE CENTER TRAVEL CARS COACHES TAXIS CONSTRUCTION HEALTHCARE HEALTH SCHOOL SCHOOLS "
              "EDUCATION SUPPORT LIVING CHILDREN CHILDRENS SEN BERKSHIRE WEST SOUTH NORTH EAST READING NEWBURY THATCHAM HUNGERFORD "
              "SOUTHERN SYSTEMS SOFTWARE HOUSING SECURITY CLEANING FOSTERING COMMUNITY BUSINESS MANAGEMENT FACILITIES SUPPLIES "
              "CATERING TRANSPORT ENGINEERING HIRE PROPERTY PROPERTIES VALLEY".split())


def distinctive(name):
    return frozenset(t for t in name.split() if t not in GENERIC and len(t) >= 3)


def match_supplier(name, notice_names, notice_dist):
    if name in notice_names:
        return "exact", name, "exact"
    best = (0.0, None)
    for nn in notice_names:
        sm = difflib.SequenceMatcher(None, name, nn)
        if sm.real_quick_ratio() < 0.85 or sm.quick_ratio() < 0.85:
            continue
        r = sm.ratio()
        if r >= 0.85 and r > best[0]:
            best = (r, nn)
    if best[1] is not None:
        return "near_ratio", best[1], "ratio=%.3f" % best[0]
    d = distinctive(name)
    if d:
        for nn in notice_names:
            e = notice_dist[nn]
            if not e:
                continue
            if d == e:
                return "near_contain", nn, "distinctive sets equal"
            small, big = (d, e) if len(d) <= len(e) else (e, d)
            if len(small) >= 2 and small <= big:
                return "near_contain", nn, "smaller distinctive set (>=2 tokens) contained in larger"
    return "none", "", ""


match_df = None
if contracts_present or register_present:
    act = notices[notices["active"]]
    notice_names = sorted(set(act["supplier_norm"]) - {""})
    notice_dist = dict((n, distinctive(n)) for n in notice_names)
    nid_by = act.groupby("supplier_norm")["notice_id"].apply(lambda s: sorted(set(s))).to_dict()
    recs = []
    for nm in sup["supplier_norm"]:
        cls, cand, how = match_supplier(nm, set(notice_names), notice_dist) if nm else ("none", "", "")
        recs.append({"supplier_norm": nm, "match_class": cls, "candidate_notice_supplier": cand, "rule_fired": how,
                     "candidate_notice_ids": ";".join(nid_by.get(cand, [])) if cand else ""})
    match_df = pd.DataFrame(recs).merge(sup[["supplier_norm", "supplier", "total", "annualised_estimate", "dominant_tag"]], on="supplier_norm")
    match_df.to_csv(OUT + "/supplier-match.csv", index=False)
    match_df[match_df["match_class"].isin(["near_ratio", "near_contain"])].to_csv(OUT + "/near-matches.csv", index=False)
    matching = {"exact": int((match_df.match_class == "exact").sum()), "near_ratio": int((match_df.match_class == "near_ratio").sum()),
                "near_contain": int((match_df.match_class == "near_contain").sum()), "none": int((match_df.match_class == "none").sum()),
                "near_matches_file": OUT + "/near-matches.csv", "suppliers_matched_against": "active notice suppliers only"}
else:
    matching = {"exact": 0, "near_ratio": 0, "near_contain": 0, "none": 0, "near_matches_file": None}

# ---------------- test 1: threshold clustering ----------------
t1 = {"parameters": {"band": "0.9*T <= amount < T (boundary adjusted for inclusivity)", "comparator_band": "T <= amount < 1.1*T",
                     "baseline": "0.5*T <= amount < 1.5*T", "population": "spend-clean.csv (redacted supplier rows excluded)"},
      "rule_ids": sorted(set(r for t in run_thr for r in t["rule_ids"])), "per_threshold": []}
flag_rows = []
for t in run_thr:
    T = t["value"]
    inc = t["inclusive"]
    a = sp["amount"]
    band = (a >= 0.9 * T) & below(a, T, inc)
    comp = (atleast(a, T, inc)) & (a < 1.1 * T)
    base = (a >= 0.5 * T) & (a < 1.5 * T)
    b = sp[band].copy()
    b["threshold"] = T
    flag_rows.append(b)
    conc = b.groupby("supplier_norm").agg(count=("amount", "size"), gbp=("amount", "sum"), supplier=("supplier", "first")).reset_index().sort_values(["count", "gbp"], ascending=False).head(20)
    ts = tagsplit(b, "tag", "amount")
    assert sum(v["count"] for v in ts.values()) == int(band.sum())
    top = b.sort_values("amount", ascending=False).head(20)
    t1["per_threshold"].append({
        "threshold": T, "inclusive": inc, "rule_ids": t["rule_ids"], "competition_triggering": t["competition_triggering"],
        "band_count": int(band.sum()), "band_gbp": r2(a[band].sum()),
        "comparator_count": int(comp.sum()), "comparator_gbp": r2(a[comp].sum()),
        "baseline_count": int(base.sum()), "baseline_gbp": r2(a[base].sum()),
        "by_tag": ts,
        "supplier_concentration_top20": [{"supplier": r.supplier, "supplier_norm": r.supplier_norm, "count": int(r.count), "gbp": r2(r.gbp)} for r in conc.itertuples()],
        "top20": [{"row_id": r.row_id, "supplier": r.supplier, "amount": r2(r.amount), "pay_date": r.pay_date, "service": r.Service,
                   "narrative": r.Narrative, "tag": r.tag} for r in top.itertuples()]})
fl = pd.concat(flag_rows) if flag_rows else pd.DataFrame()
fl.drop(columns=["annual_factor"], errors="ignore").to_csv(OUT + "/threshold-clustering.csv", index=False)
t1["total_band_rows"] = int(len(fl))
tests["threshold_clustering"] = t1

# ---------------- test 2: split purchases ----------------
t2 = {"parameters": {"window_days": 30, "rule": "same normalised supplier, >=2 payments dated within 30 days (anchor payment date to +29 days), every payment below T, window total reaches T; overlapping windows de-duplicated keeping the highest total per supplier per T"},
      "rule_ids": sorted(set(r for t in comp_thr for r in t["competition_rule_ids"]) | {"CPR-14"}), "per_threshold": [],
      "limitations": ["Data covers %d months (%s to %s); a split across a period the data does not cover is invisible." % (months, log["date_min"], log["date_max"]),
                      "Population is payments over 500 only: results are lower bounds.",
                      "Identical repeated rows are kept and can inflate windows; see duplicates test.",
                      "Periodic care-placement fees legitimately recur; headline is general_procurement."]}
all_windows = []
for t in comp_thr:
    if t["skipped_band_below_min_payment"]:
        continue
    T = t["value"]
    inc = t["inclusive"]
    sub = sp[below(sp["amount"], T, inc)].copy()
    tot = sub.groupby("supplier_norm")["amount"].transform("sum")
    sub = sub[atleast(tot, T, inc) & (sub["supplier_norm"] != "")]
    wins = []
    for nm, grp in sub.groupby("supplier_norm"):
        grp = grp.sort_values(["date", "row_id"]).reset_index(drop=True)
        days = grp["date"].map(lambda d: d.toordinal()).values
        amts = grp["amount"].values
        cand = []
        for i in range(len(grp)):
            j = int(np.searchsorted(days, days[i] + 30, side="left"))
            n = j - i
            if n >= 2:
                total = float(amts[i:j].sum())
                if atleast(total, T, inc):
                    cand.append((total, i, j))
        cand.sort(key=lambda x: (-x[0], x[1]))
        acc = []
        for total, i, j in cand:
            s0, e0 = days[i], days[j - 1]
            if all(e0 < days[ai] or s0 > days[aj - 1] for _, ai, aj in acc):
                acc.append((total, i, j))
        for total, i, j in acc:
            w = grp.iloc[i:j]
            tg = w.groupby("tag")["amount"].sum().idxmax()
            wins.append({"threshold": T, "supplier": w["supplier"].value_counts().index[0], "supplier_norm": nm,
                         "window_start": w["pay_date"].min(), "window_end": w["pay_date"].max(), "n_payments": int(len(w)),
                         "window_total": r2(total), "distinct_amounts": int(w["amount"].nunique()),
                         "services": ";".join(sorted(w["Service"].unique())), "dominant_tag": tg,
                         "tags_in_window": ";".join(sorted(w["tag"].unique())), "row_ids": ";".join(w["row_id"])})
    wd = pd.DataFrame(wins)
    if len(wd):
        all_windows.append(wd)
        ts = tagsplit(wd, "dominant_tag", "window_total")
        assert sum(v["count"] for v in ts.values()) == len(wd)
        top = wd.sort_values("window_total", ascending=False).head(20)
        item = {"threshold": T, "inclusive": inc, "rule_ids": t["rule_ids"], "windows": int(len(wd)), "distinct_suppliers": int(wd["supplier_norm"].nunique()),
                "window_gbp": r2(wd["window_total"].sum()), "by_tag": ts,
                "headline_general_procurement": ts["general_procurement"],
                "top20": [dict(r._asdict(), row_ids=r.row_ids.split(";")) for r in top.drop(columns=["supplier_norm"]).itertuples(index=False)]}
    else:
        ts = {tg: {"count": 0, "gbp": 0.0} for tg in TAGS}
        item = {"threshold": T, "inclusive": inc, "rule_ids": t["rule_ids"], "windows": 0, "distinct_suppliers": 0, "window_gbp": 0.0,
                "by_tag": ts, "headline_general_procurement": ts["general_procurement"], "top20": []}
    t2["per_threshold"].append(item)
if all_windows:
    pd.concat(all_windows).to_csv(OUT + "/split-purchases.csv", index=False)
else:
    pd.DataFrame().to_csv(OUT + "/split-purchases.csv", index=False)
tests["split_purchases"] = t2

# ---------------- test 3: high value suppliers ----------------
hv = sup[atleast(sup["annualised_estimate"], quote_thr, quote_incl) & (sup["supplier_norm"] != "")].copy()
hv = hv.sort_values("annualised_estimate", ascending=False)
hv["row_ids"] = hv["supplier_norm"].map(lambda k: ";".join(rid_top[k]))
hv.to_csv(OUT + "/high-value-suppliers.csv", index=False)
ts3 = {}
for tg in TAGS:
    m = hv["dominant_tag"] == tg
    ts3[tg] = {"count": int(m.sum()), "total_gbp": r2(hv.loc[m, "total"].sum()), "annualised_estimate_gbp": r2(hv.loc[m, "annualised_estimate"].sum()),
               "spanning_several_tags": int((m & hv["spans_several_tags"]).sum())}
assert sum(v["count"] for v in ts3.values()) == len(hv)


def hv_rows(df, n=20):
    return [{"supplier": r.supplier, "supplier_norm": r.supplier_norm, "annualised_estimate": r2(r.annualised_estimate), "total_gbp": r2(r.total),
             "n_payments": int(r.n_payments), "dominant_tag": r.dominant_tag, "spans_several_tags": bool(r.spans_several_tags),
             "dominant_narrative": r.dominant_narrative, "dominant_service": r.dominant_service,
             "row_ids": rid_top[r.supplier_norm][:10], "row_ids_truncated": len(rid_top[r.supplier_norm]) > 10}
            for r in df.head(n).itertuples()]


t3 = {"parameters": {"quote_threshold": quote_thr, "inclusive": quote_incl, "basis": "annualised estimate = total x (12/%d)" % months,
                     "annualisation_factor": FACTOR, "note": "population for contract-evidence request in fieldwork (PBC list)"},
      "rule_ids": [t for t in comp_thr if t["value"] == quote_thr][0]["competition_rule_ids"],
      "suppliers_at_or_above_quote_threshold": int(len(hv)), "by_tag": ts3,
      "headline_general_procurement": ts3["general_procurement"],
      "top20_general_procurement": hv_rows(hv[hv["dominant_tag"] == "general_procurement"]),
      "other_groups_top20": dict((tg, hv_rows(hv[hv["dominant_tag"] == tg])) for tg in TAGS[1:]),
      "unrun_tiers": [s for s in skipped if s["test"] == "high_value_suppliers"]}
tests["high_value_suppliers"] = t3

# ---------------- test 5: duplicates ----------------
d5 = sp[sp["supplier_norm"] != ""].copy()
d5["dord"] = d5["date"].map(lambda d: d.toordinal())
groups = []
gid = 0
for (nm, amt), grp in d5.groupby(["supplier_norm", "amount"]):
    if len(grp) < 2:
        continue
    grp = grp.sort_values(["dord", "row_id"])
    start = None
    cur = []
    clusters = []
    for r in grp.itertuples():
        if start is None or r.dord - start > 7:
            if len(cur) >= 2:
                clusters.append(cur)
            cur = [r]
            start = r.dord
        else:
            cur.append(r)
    if len(cur) >= 2:
        clusters.append(cur)
    for cl in clusters:
        gid += 1
        stamps = set(x.timestamp for x in cl)
        tier = "same_timestamp" if len(stamps) == 1 else "different_time"
        tg = pd.Series([x.tag for x in cl]).value_counts().index[0]
        groups.append({"group_id": gid, "tier": tier, "supplier": cl[0].supplier, "supplier_norm": nm, "amount": r2(amt), "n_rows": len(cl),
                       "distinct_timestamps": len(stamps), "first_date": min(x.pay_date for x in cl), "last_date": max(x.pay_date for x in cl),
                       "gbp_beyond_first": r2(amt * (len(cl) - 1)), "dominant_tag": tg, "services": ";".join(sorted(set(x.Service for x in cl))),
                       "row_ids": ";".join(x.row_id for x in cl)})
gd = pd.DataFrame(groups)
gd.to_csv(OUT + "/duplicates.csv", index=False)
t5 = {"parameters": {"rule": "non-redacted rows, same normalised supplier, same amount to the penny, calendar dates within 7 days (cluster anchored on earliest payment)",
                     "tiers": "same_timestamp = all rows in the group share one Date timestamp (includes rows repeated in all six columns); different_time = group has >=2 distinct timestamps (higher signal)"},
      "rule_ids": ["CPR-39"], "tiers": {},
      "note": "Repeated rows (identical in all six columns) found by clean.py: %d rows involved, %d beyond first instance." % (log["rows_identical_in_all_six_columns"], log["rows_identical_beyond_first"])}
for tier in ("same_timestamp", "different_time"):
    x = gd[gd["tier"] == tier] if len(gd) else gd
    ts = {}
    for tg in TAGS:
        m = x["dominant_tag"] == tg if len(x) else pd.Series([], dtype=bool)
        ts[tg] = {"groups": int(m.sum()), "rows": int(x.loc[m, "n_rows"].sum()) if len(x) else 0,
                  "gbp_beyond_first": r2(x.loc[m, "gbp_beyond_first"].sum()) if len(x) else 0.0}
    assert sum(v["groups"] for v in ts.values()) == len(x)
    top = x.sort_values("amount", ascending=False).head(20) if len(x) else x
    t5["tiers"][tier] = {"groups": int(len(x)), "rows": int(x["n_rows"].sum()) if len(x) else 0,
                         "gbp_beyond_first": r2(x["gbp_beyond_first"].sum()) if len(x) else 0.0, "by_tag": ts,
                         "headline_general_procurement": ts["general_procurement"],
                         "top20": [dict(r._asdict(), row_ids=r.row_ids.split(";")) for r in top.itertuples(index=False)] if len(x) else []}
tests["duplicates"] = t5

# ---------------- notice-based tests ----------------
for nm_ in ("off_contract", "expired_notice_spend", "spend_vs_award"):
    pass
if contracts_present or register_present:
    hvm = hv.merge(match_df[["supplier_norm", "match_class", "candidate_notice_supplier", "rule_fired", "candidate_notice_ids"]], on="supplier_norm", how="left")
    hvm.to_csv(OUT + "/off-contract.csv", index=False)
    grp = {}
    for cls, key in (("exact", "matched_exact"), ("candidates", "candidates"), ("none", "unmatched")):
        m = hvm["match_class"].isin(["near_ratio", "near_contain"]) if cls == "candidates" else hvm["match_class"] == cls
        x = hvm[m]
        grp[key] = {"count": int(len(x)), "total_gbp": r2(x["total"].sum()), "annualised_estimate_gbp": r2(x["annualised_estimate"].sum()),
                    "by_tag": dict((tg, {"count": int((x["dominant_tag"] == tg).sum()), "annualised_estimate_gbp": r2(x.loc[x["dominant_tag"] == tg, "annualised_estimate"].sum())}) for tg in TAGS)}
    assert grp["matched_exact"]["count"] + grp["candidates"]["count"] + grp["unmatched"]["count"] == len(hvm)
    un = hvm[hvm["match_class"] == "none"]
    cd = hvm[hvm["match_class"].isin(["near_ratio", "near_contain"])]

    def oc_rows(df, n=20, cand=False):
        out = []
        for r in df.head(n).itertuples():
            d = {"supplier": r.supplier, "supplier_norm": r.supplier_norm, "annualised_estimate": r2(r.annualised_estimate), "total_gbp": r2(r.total),
                 "n_payments": int(r.n_payments), "dominant_tag": r.dominant_tag, "row_ids": rid_top[r.supplier_norm][:10]}
            if cand:
                d.update({"match_class": r.match_class, "candidate_notice_supplier": r.candidate_notice_supplier, "rule_fired": r.rule_fired, "candidate_notice_ids": r.candidate_notice_ids})
            out.append(d)
        return out

    tests["off_contract"] = {
        "parameters": {"quote_threshold": quote_thr, "population": "suppliers with annualised estimate at or above the quote threshold only; only exact counts as a match",
                       "matched_against": "active notice suppliers"},
        "rule_ids": t3["rule_ids"], "contracts_present": contracts_present, "register_present": register_present, "caveat": CAVEAT,
        "suppliers_classed": int(len(hvm)), "groups": grp,
        "unmatched_general_procurement_top20": oc_rows(un[un["dominant_tag"] == "general_procurement"]),
        "candidates_top20_for_auditor_to_confirm": oc_rows(cd, cand=True),
        "candidates_file": OUT + "/off-contract.csv"}

if contracts_present:
    ncouncil = notices
    spend_sup = sup.set_index("supplier_norm")
    # test 6
    g6 = ncouncil[ncouncil["supplier_norm"] != ""].groupby("supplier_norm")
    exp = []
    for nm, grp_ in g6:
        if nm not in spend_sup.index:
            continue
        if grp_["active"].any():
            continue
        if not grp_["ended"].all():
            continue
        last = grp_.sort_values("end").iloc[-1]
        s = spend_sup.loc[nm]
        exp.append({"supplier": s["supplier"], "supplier_norm": nm, "total_gbp": s["total"], "annualised_estimate": s["annualised_estimate"],
                    "n_payments": int(s["n_payments"]), "dominant_tag": s["dominant_tag"], "latest_notice_end": str(last["end"])[:10],
                    "latest_notice_id": last["notice_id"], "notice_ids": ";".join(sorted(set(grp_["notice_id"]))),
                    "above_quote_threshold": bool(atleast(s["annualised_estimate"], quote_thr, quote_incl)), "row_ids": ";".join(rid_top[nm])})
    ed = pd.DataFrame(exp)
    ed.to_csv(OUT + "/expired-notice-spend.csv", index=False)
    rule_e = [r for r in rules["rules"] if r["clause"] == "Appendix C row D"]
    ts = dict((tg, {"count": int((ed["dominant_tag"] == tg).sum()) if len(ed) else 0,
                    "annualised_estimate_gbp": r2(ed.loc[ed["dominant_tag"] == tg, "annualised_estimate"].sum()) if len(ed) else 0.0}) for tg in TAGS)
    assert sum(v["count"] for v in ts.values()) == len(ed)
    tests["expired_notice_spend"] = {
        "parameters": {"match": "exact normalised name against all council notices; no active notice; every matching notice ended before %s" % log["date_min"],
                       "applies_to": "suppliers of any size"},
        "rule_ids": [r["rule_id"] for r in rule_e], "rule_note": "Appendix C row D requires S151 approval for extensions. A newer contract may exist with no notice here.",
        "caveat": CAVEAT, "suppliers": int(len(ed)), "annualised_estimate_gbp": r2(ed["annualised_estimate"].sum()) if len(ed) else 0.0,
        "total_gbp": r2(ed["total_gbp"].sum()) if len(ed) else 0.0,
        "of_which_above_quote_threshold": int(ed["above_quote_threshold"].sum()) if len(ed) else 0,
        "by_tag": ts, "headline_general_procurement": ts["general_procurement"],
        "top20": [dict(r._asdict(), row_ids=r.row_ids.split(";")[:10]) for r in ed.sort_values("annualised_estimate", ascending=False).head(20).drop(columns=["notice_ids"]).itertuples(index=False)] if len(ed) else []}
    # test 7
    rows7 = []
    act = notices[notices["active"]]
    nunique = act.groupby("supplier_norm")["notice_id"].nunique()
    n_skipped_years = 0
    for nm, grp_ in act[act["supplier_norm"] != ""].groupby("supplier_norm"):
        if nm not in spend_sup.index or nunique[nm] != 1:
            continue
        r = grp_.iloc[0]
        if r["suppliers_on_notice"] != 1 or not (r["awarded_value"] > 0):
            continue
        yrs = (r["end"] - r["start"]).days / 365.25 if pd.notna(r["end"]) and pd.notna(r["start"]) else 0
        if yrs <= 0:
            n_skipped_years += 1
            continue
        s = spend_sup.loc[nm]
        rate = r["awarded_value"] / yrs
        rows7.append({"supplier": s["supplier"], "supplier_norm": nm, "notice_id": r["notice_id"], "awarded_value": r2(r["awarded_value"]),
                      "contract_start": str(r["start"])[:10], "contract_end": str(r["end"])[:10], "contract_years": round(yrs, 4),
                      "award_annual_rate": r2(rate), "annualised_estimate": s["annualised_estimate"], "ratio": round(float(s["annualised_estimate"] / rate), 4),
                      "dominant_tag": s["dominant_tag"], "n_payments": int(s["n_payments"]), "row_ids": ";".join(rid_top[nm])})
    sd = pd.DataFrame(rows7)
    sd.to_csv(OUT + "/spend-vs-award.csv", index=False)
    fl7 = sd[sd["ratio"] >= 1.25] if len(sd) else sd
    ts = dict((tg, {"count": int((fl7["dominant_tag"] == tg).sum()) if len(fl7) else 0,
                    "annualised_estimate_gbp": r2(fl7.loc[fl7["dominant_tag"] == tg, "annualised_estimate"].sum()) if len(fl7) else 0.0}) for tg in TAGS)
    assert sum(v["count"] for v in ts.values()) == len(fl7)
    rule_v = [r["rule_id"] for r in rules["rules"] if r["clause"] == "Appendix C row E"]
    tests["spend_vs_award"] = {
        "parameters": {"match": "exact normalised name to exactly one active, single-supplier notice with Awarded Value > 0", "ratio_flag": 1.25,
                       "award_annual_rate": "Awarded Value / contract years ((end-start) days / 365.25)"},
        "rule_ids": rule_v, "rule_note": "Appendix C row E requires approval of variations. Award values may be estimates or maxima, so a high ratio is an indicator only.",
        "caveat": CAVEAT, "suppliers_compared": int(len(sd)), "notices_skipped_nonpositive_term": n_skipped_years,
        "flagged_ratio_ge_1_25": int(len(fl7)), "flagged_annualised_estimate_gbp": r2(fl7["annualised_estimate"].sum()) if len(fl7) else 0.0,
        "by_tag": ts, "headline_general_procurement": ts["general_procurement"],
        "top20": [dict(r._asdict(), row_ids=r.row_ids.split(";")[:10]) for r in fl7.sort_values("ratio", ascending=False).head(20).itertuples(index=False)] if len(fl7) else []}
else:
    for t_ in ("expired_notice_spend", "spend_vs_award"):
        tests[t_] = {"skipped": True, "reason": "no usable contracts.csv"}
        skipped.append({"test": t_, "reason": "no usable contracts.csv"})
if not (contracts_present or register_present):
    tests["off_contract"] = {"skipped": True, "reason": "no contracts.csv or contract register in data/"}
    skipped.append({"test": "off_contract", "reason": "no contracts.csv or contract register in data/"})
if not register_present:
    pass

# ---------------- population & output ----------------
pop_tags = {}
for tg in TAGS:
    m = sp["tag"] == tg
    pop_tags[tg] = {"rows": int(m.sum()), "gbp": r2(sp.loc[m, "amount"].sum()), "suppliers": int(sp.loc[m, "supplier_norm"].nunique())}
assert sum(v["rows"] for v in pop_tags.values()) == len(sp)
ex = log["exclusions"]
rows_excl = sum(v["rows"] for v in ex.values())
assert len(sp) + rows_excl == log["rows_raw"]
warn = []
if log.get("overlapping_consecutive_workbooks"):
    warn.append("Date ranges overlap between consecutive workbooks: %s (no row is identical across files)" % log["overlapping_consecutive_workbooks"])
if log["rows_identical_beyond_first"]:
    warn.append("%d rows are repeats of an identical row (all six columns) within a workbook; kept, reported in duplicates same_timestamp tier" % log["rows_identical_beyond_first"])
warn += log.get("contracts_warnings", [])
cb = {"contracts_present": contracts_present, "register_present": register_present, "rows_in_file": log.get("contracts_rows_in_file", 0),
      "rows_for_council": log.get("contracts_rows_for_council", 0), "notice_supplier_pairs": log.get("notice_supplier_pairs", 0),
      "distinct_suppliers": log.get("distinct_normalised_suppliers", 0), "active_in_window": log.get("pairs_active", 0),
      "ended_before_window": log.get("pairs_ended_before_window", 0), "starting_after_window_ignored": log.get("pairs_starting_after_window_ignored", 0),
      "zero_value_awards": log.get("zero_value_awards", 0), "rows_per_year": log.get("rows_per_publication_year", {}),
      "published_range": log.get("published_range", ["", ""]), "warnings": log.get("contracts_warnings", []), "caveat": CAVEAT}
res = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"), "scripts": ["scripts/clean.py", "scripts/analyse.py", "scripts/common.py"],
       "population": {"files": [f["file"] for f in log["files"]], "rows_raw": log["rows_raw"], "rows_after_exclusions": int(len(sp)),
                      "date_min": log["date_min"], "date_max": log["date_max"], "months_covered": months, "annualisation_factor": FACTOR,
                      "total_gbp": r2(sp["amount"].sum()), "excluded": ex, "tags": pop_tags,
                      "limitations": ["population is expenditure over £500 only", "Date is a payment-run timestamp"],
                      "data_quality_warnings": warn},
       "thresholds": thresholds, "null_parameters": dict((p, param_rules[p]) for p in null_params), "quote_threshold": quote_thr,
       "skipped": skipped, "contracts": cb, "matching": matching, "tests": tests}
json.dump(jclean(res), open("outputs/analytics.json", "w"), indent=1)
print("analyse ok")
