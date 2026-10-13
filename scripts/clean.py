import warnings; warnings.filterwarnings("ignore")
import glob, json, os, re, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import normalise_supplier

OUT = "outputs/analytics-full"
os.makedirs(OUT, exist_ok=True)
log = {}
EXPECTED = ["Service", "Expenditure category", "Narrative", "Date", "Net amount", "Supplier name"]


def stop(msg):
    print("STOP: " + msg)
    sys.exit(1)


# ---------- spend ----------
files = sorted(glob.glob("data/spend/*.xlsx") + glob.glob("data/spend/*.csv"))
if not files:
    stop("no spend files")
frames = []
log["files"] = []
for f in files:
    base = os.path.basename(f)
    raw = pd.read_excel(f, header=None, sheet_name="Data to publish")
    hdr = None
    for i in range(min(len(raw), 30)):
        if str(raw.iloc[i, 0]).strip() == "Service":
            hdr = i
            break
    if hdr is None:
        stop("header row not found in " + base)
    df = pd.read_excel(f, header=hdr, sheet_name="Data to publish")
    df.columns = [str(c).strip() for c in df.columns]
    if list(df.columns) != EXPECTED:
        stop("columns mismatch in %s: %s" % (base, list(df.columns)))
    df["source_file"] = base
    df["row_id"] = [base + ":" + str(hdr + 2 + k) for k in range(len(df))]
    log["files"].append({"file": base, "header_row_0based": hdr, "rows": len(df)})
    frames.append(df)
sp = pd.concat(frames, ignore_index=True)
log["rows_raw"] = int(len(sp))


def parse_date(v):
    if not isinstance(v, str):
        return pd.Timestamp(v)
    s = v.strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%m/%d/%y %H:%M:%S", "%m/%d/%y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass
    return pd.NaT


sp["_dt"] = sp["Date"].map(parse_date)
if sp["_dt"].isna().any():
    stop("%d dates failed to parse" % int(sp["_dt"].isna().sum()))
sp["Net amount"] = pd.to_numeric(sp["Net amount"], errors="coerce")
if sp["Net amount"].isna().any():
    stop("amount failed to parse or null")
if sp["Supplier name"].isna().any() or sp["Service"].isna().any():
    stop("null supplier or service")
if (sp["Net amount"] < 0).any():
    stop("negative amounts: %d rows" % int((sp["Net amount"] < 0).sum()))
log["date_type_counts"] = {k: int(v) for k, v in sp["Date"].map(lambda x: type(x).__name__).value_counts().items()}
sp["timestamp"] = sp["_dt"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
sp["pay_date"] = sp["_dt"].dt.strftime("%Y-%m-%d")
sp["Net amount"] = sp["Net amount"].round(2)
sp["supplier_norm"] = sp["Supplier name"].map(normalise_supplier)
sp = sp.drop(columns=["Date", "_dt"])
sp = sp.rename(columns={"Net amount": "amount", "Supplier name": "supplier", "Expenditure category": "exp_category"})

# repeated rows / overlap checks
keycols = ["Service", "exp_category", "Narrative", "timestamp", "amount", "supplier"]
dupmask = sp.duplicated(subset=keycols, keep=False)
log["rows_identical_in_all_six_columns"] = int(dupmask.sum())
log["rows_identical_beyond_first"] = int(sp.duplicated(subset=keycols, keep="first").sum())
tmp = sp[dupmask].fillna("<null>")
cross = tmp.groupby(keycols)["source_file"].nunique() if len(tmp) else pd.Series(dtype=int)
log["identical_rows_across_files_groups"] = int((cross > 1).sum())
if (cross > 1).any():
    json.dump(log, open(OUT + "/cleaning-log.json", "w"), indent=2, default=str)
    stop("rows identical across workbooks: %d groups" % int((cross > 1).sum()))
rng = sp.groupby("source_file")["pay_date"].agg(["min", "max"]).sort_values("min")
log["file_date_ranges"] = {k: [r["min"], r["max"]] for k, r in rng.iterrows()}
ov = []
rl = list(rng.itertuples())
for a, b in zip(rl, rl[1:]):
    if b.min <= a.max:
        ov.append([a.Index, b.Index])
log["overlapping_consecutive_workbooks"] = ov
log["months_covered"] = int(sp["pay_date"].str[:7].nunique())
log["date_min"] = sp["pay_date"].min()
log["date_max"] = sp["pay_date"].max()
log["min_amount"] = float(sp["amount"].min())

# exclusions
CAT_PENS = re.compile(r"LGPS|PENSION|SUPERANNUATION", re.I)
SUP_INTER = re.compile(r"\b(COUNCIL|BOROUGH|COUNTY|CNCL|NHS|POLICE|FIRE AUTHORITY|FIRE AND RESCUE|HMRC|HM REVENUE|DEPARTMENT FOR|MINISTRY OF)\b", re.I)
NAR_JOINT = re.compile(r"JOINT ARRANGEMENTS", re.I)
nar = sp["Narrative"].fillna("").astype(str)
sup = sp["supplier"].astype(str)
cat = pd.Series("", index=sp.index)


def assign(mask, name):
    m = mask & (cat == "")
    cat[m] = name


assign(sup.str.strip().str.upper() == "REDACTED", "redacted_supplier")
assign(nar.str.contains(CAT_PENS), "pension_statutory")
assign((sup.str.contains(SUP_INTER) | nar.str.contains(NAR_JOINT)) & (nar.str.strip() != "Private Contractors"), "inter_authority")
acc = sp["exp_category"].isna() | nar.str.strip().isin(["ASC Deferred Debt", "Rent Rebates"])
assign(acc, "non_procurement_accounting")
reasons = {
    "redacted_supplier": "Supplier is the label 'Redacted': many payees under one label, unusable for supplier-level tests",
    "pension_statutory": "Narrative matches LGPS|PENSION|SUPERANNUATION: statutory pension contributions",
    "inter_authority": "Supplier is another public body (council/NHS/police/fire/HMRC/department) or narrative is joint arrangements, and not Private Contractors",
    "non_procurement_accounting": "Expenditure category null, or Narrative ASC Deferred Debt / Rent Rebates: control accounts and benefit rebates, not purchases",
}
ex = {}
for k, why in reasons.items():
    m = cat == k
    ex[k] = {"rows": int(m.sum()), "gbp": round(float(sp.loc[m, "amount"].sum()), 2), "reason": why}
log["exclusions"] = ex
log["non_procurement_accounting_narratives"] = {str(k): int(v) for k, v in sp.loc[cat == "non_procurement_accounting", "Narrative"].fillna("<null>").value_counts().head(30).items()}
sp["exclusion"] = cat
excl = sp[cat != ""].copy()
keep = sp[cat == ""].drop(columns=["exclusion"]).copy()
assert len(keep) + len(excl) == log["rows_raw"]

# tags
PLACE_SVC = re.compile(r"^(Adult Social Care|Children['’]s Social Care|Education)", re.I)
PLACE_NAR = {"Private Contractors", "Other agencies", "Voluntary Associations", "Direct Payment", "Allowances for provision care", "Adult Placement Allowances"}
RX_GRANT = re.compile(r"GRANT", re.I)
RX_AGENCY = re.compile(r"AGENCY", re.I)
RX_PREM = re.compile(r"RENT|RATES|WATER RATES|LEASE", re.I)
kn = keep["Narrative"].fillna("").astype(str).str.strip()
ks = keep["Service"].astype(str)
tag = pd.Series("general_procurement", index=keep.index)
done = pd.Series(False, index=keep.index)
for name, m in [
    ("care_or_education_placement", ks.str.contains(PLACE_SVC) & kn.isin(PLACE_NAR)),
    ("grant", kn.str.contains(RX_GRANT)),
    ("agency_staff", kn.str.contains(RX_AGENCY)),
    ("premises_non_procurement", kn.str.contains(RX_PREM)),
]:
    mm = m & ~done
    tag[mm] = name
    done = done | mm
keep["tag"] = tag
log["tag_regexes"] = {
    "care_or_education_placement": "Service " + PLACE_SVC.pattern + " AND Narrative in " + str(sorted(PLACE_NAR)),
    "grant": RX_GRANT.pattern, "agency_staff": RX_AGENCY.pattern, "premises_non_procurement": RX_PREM.pattern,
}
log["tag_counts"] = {k: int(v) for k, v in tag.value_counts().items()}
log["rows_kept"] = int(len(keep))
keep.to_csv(OUT + "/spend-clean.csv", index=False)
excl.to_csv(OUT + "/spend-excluded.csv", index=False)

# ---------- contracts ----------
log["contracts_present"] = os.path.exists("data/contracts.csv")
log["register_present"] = os.path.exists("data/contract-register.csv")
win_start = pd.Timestamp(log["date_min"])
win_end = pd.Timestamp(log["date_max"])
if log["contracts_present"]:
    c = pd.read_csv("data/contracts.csv", dtype=str, keep_default_na=False)
    log["contracts_rows_in_file"] = int(len(c))
    org = c["Organisation Name"].str.strip().str.lower()
    m = org.isin(["west berkshire council", "west berkshire"])
    log["contracts_rows_dropped"] = int((~m).sum())
    log["contracts_orgs_kept"] = {k: int(v) for k, v in c.loc[m, "Organisation Name"].value_counts().items()}
    c = c[m].copy()
    log["contracts_rows_for_council"] = int(len(c))
    if len(c) < 20:
        log["contracts_present"] = False
        log["contracts_treated_absent_reason"] = "fewer than 20 council notices"
    else:
        supcol = [x for x in c.columns if x.startswith("Supplier [")][0]
        rows = []
        for _, r in c.iterrows():
            blocks = [b for b in re.split(r"\]\s*\[", r[supcol].strip()) if b.strip()]
            for b in blocks:
                b = b.strip().lstrip("[").rstrip("]")
                parts = b.split("|")
                nm = parts[0].strip()
                if not nm:
                    continue
                ch = parts[3].strip() if len(parts) > 3 and parts[2].strip() == "COMPANIES_HOUSE" else ""
                rows.append({"notice_id": r["Notice Identifier"], "title": r["Title"], "procedure": r["OJEU Procedure Type"],
                             "awarded_value": r["Awarded Value"], "supplier": nm, "supplier_norm": normalise_supplier(nm),
                             "companies_house": ch, "suppliers_on_notice": len(blocks),
                             "start": r["Contract start date"], "end": r["Contract end date"],
                             "awarded_date": r["Awarded Date"], "published": r["Published Date"]})
        n = pd.DataFrame(rows)

        def dparse(s, fmt=None):
            s = s.fillna("").astype(str).str.strip()
            out = pd.to_datetime(s.where(s != "", None), format=fmt, errors="coerce")
            bad = (s != "") & out.isna()
            if bad.any():
                stop("%d unparseable notice dates" % int(bad.sum()))
            return out

        for col in ("start", "end", "awarded_date"):
            n[col] = dparse(n[col], "%d/%m/%Y")
        n["published"] = dparse(n["published"].str[:10], "%Y-%m-%d")
        n["awarded_value"] = pd.to_numeric(n["awarded_value"].str.replace(",", ""), errors="coerce")
        n["ended"] = n["end"].notna() & (n["end"] < win_start)
        n["starts_after_window"] = n["start"].notna() & (n["start"] > win_end)
        n["active"] = (~n["ended"]) & (~n["starts_after_window"])
        log["notices"] = int(n["notice_id"].nunique())
        log["notice_supplier_pairs"] = int(len(n))
        log["distinct_normalised_suppliers"] = int(n["supplier_norm"].nunique())
        log["pairs_active"] = int(n["active"].sum())
        log["pairs_ended_before_window"] = int(n["ended"].sum())
        log["pairs_starting_after_window_ignored"] = int(n["starts_after_window"].sum())
        log["notices_missing_start_or_end"] = int(n.drop_duplicates("notice_id")[["start", "end"]].isna().any(axis=1).sum())
        nz = n.drop_duplicates("notice_id")
        log["zero_value_awards"] = int((nz["awarded_value"].fillna(0) == 0).sum())
        log["rows_per_publication_year"] = {str(k): int(v) for k, v in nz["published"].dt.year.value_counts().sort_index().items()}
        log["published_range"] = [str(nz["published"].min().date()), str(nz["published"].max().date())]
        w = []
        if log["contracts_rows_in_file"] == 1000:
            w.append("file has exactly 1,000 rows: possible export cap")
        ys = log["rows_per_publication_year"]
        if ys:
            mx = max(ys.values())
            mid = [y for y in ys if y not in (min(ys), max(ys))]
            thin = [y for y in mid if ys[y] < 0.25 * mx]
            if thin:
                w.append("implausibly thin years: " + ",".join(thin))
        log["contracts_warnings"] = w
        n.to_csv(OUT + "/notices-clean.csv", index=False)
if log["register_present"]:
    log["register_note"] = "register file present: header must be inspected and mapped manually"
json.dump(log, open(OUT + "/cleaning-log.json", "w"), indent=2, default=str)
print("clean ok: raw=%d kept=%d excluded=%d months=%d contracts_present=%s" % (log["rows_raw"], len(keep), len(excl), log["months_covered"], log["contracts_present"]))
