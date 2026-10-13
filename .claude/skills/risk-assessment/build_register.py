#!/usr/bin/env python3
"""Build outputs/risk-register.md and outputs/auditor-comments.md from the
risk-assessor's judgments (outputs/risk-ratings.json).

Usage:
    python build_register.py [--ratings F] [--rules F] [--analytics F]
                             [--history F] [--out-dir D]

The agent judges (levels, justifications, citations); this script computes:
every {{$.path}} placeholder, every score, matrix label and band, and it
checks the revision after an auditor gate. Exit codes: 0 clean, 3 warnings
only (files written), 1 failures (only risk-register.draft.md is written, and
the last clean register and comments are left alone), 2 could not run.

Citations in justifications: [rule:CPR-14]  [metric:$.tests.x.y[0].z]
[history:AO-12]. Figures in prose: {{$.path}} or {{$.path|gbp}} (formats:
gbp, gbp0, int, dp1, dp2). The score comes from the council's matrix in
history.json (or the fallback scale when it holds none); a risk whose
likelihood or impact justification has no resolvable citation is dropped.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

THEMES = {
    "T01": "Splitting and threshold avoidance",
    "T02": "Competition not evidenced for high-value suppliers",
    "T03": "Spend after, or beyond, a contract notice",
    "T04": "Duplicate payments",
    "T05": "Exceptions and waivers not observable in the data",
    "T06": "Contract register and publication completeness",
    "T07": "Care placements and direct payments",
    "T08": "Grants treated as contracts",
    "T09": "Delegated approval and Key Decisions",
}
# likelihood signal -> (base score, distinct tests that must show the indicator)
SIGNALS = {
    "none": (1, 0),
    "unobservable": (2, 0),
    "outside_headline": (2, 0),
    "headline_single": (3, 1),
    "headline_corroborated": (4, 2),
    "headline_broad": (5, 3),
}
HEADLINE = {"headline_single", "headline_corroborated", "headline_broad"}
# Only flagged-item metrics from the six indicator tests count as evidence of an
# indicator. Population lists (high_value_suppliers), matched or candidate groups,
# suppliers_compared and the contracts/matching/population sections do not.
INDICATOR_PATHS = [re.compile(p) for p in (
    r"^\$\.tests\.threshold_clustering\.per_threshold\[\d+\]\.(band_count|band_gbp|by_tag\.\w+\.(count|gbp))$",
    r"^\$\.tests\.split_purchases\.per_threshold\[\d+\]\.(windows|window_gbp|distinct_suppliers|"
    r"headline_general_procurement\.(count|gbp)|by_tag\.\w+\.(count|gbp|windows|window_gbp))$",
    r"^\$\.tests\.duplicates\.tiers\.(same_timestamp|different_time)\.(groups|rows|gbp_beyond_first|"
    r"headline_general_procurement\.(groups|rows|gbp_beyond_first)|by_tag\.\w+\.[\w]+)$",
    r"^\$\.tests\.off_contract\.groups\.unmatched\.(count|total_gbp|annualised_estimate_gbp|by_tag\.\w+\.[\w]+)$",
    r"^\$\.tests\.expired_notice_spend\.(suppliers|annualised_estimate_gbp|total_gbp|of_which_above_quote_threshold|"
    r"headline_general_procurement\.\w+|by_tag\.\w+\.\w+)$",
    r"^\$\.tests\.spend_vs_award\.(flagged_ratio_ge_1_25|flagged_annualised_estimate_gbp|"
    r"headline_general_procurement\.\w+|by_tag\.\w+\.\w+)$",
)]


def is_indicator(path):
    return any(p.match(path) for p in INDICATOR_PATHS)
ADVERSE = ("limited assurance", "weak", "unsatisfactory", "no assurance")
CHANGE_ACTIONS = {"amended", "rejected", "added"}
FALLBACK_LABELS = {1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Very high"}

CITE_RE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")
PH_RE = re.compile(r"\{\{\s*(\$[^}|]*?)\s*(?:\|\s*(\w+))?\s*\}\}")
TOKEN_RE = re.compile(r"\.([A-Za-z_][\w-]*|\d+)|\[(\d+)\]")
FIG_OK = re.compile(r"\b(?:Table|Figure|Appendix|clause|Clause|section|Section|rule|Rule)\s+[\dA-Z][\w.]*|5x5|\b5 T")
FIG_RE = re.compile(r"[£$]?\d[\d,]*(?:\.\d+)?%?")
LANG_RE = re.compile(r"\b(fraud\w*|illegal\w*|unlawful\w*|corrupt\w*|misconduct|embezzl\w*|theft|stolen|"
                     r"breach(?:ed|es)?|violat\w+|non-?complian\w+)\b", re.I)
STATE_RE = re.compile(r"<!-- build_register:state (\{.*\}) -->", re.S)
RISK_KEYS = {"id", "theme", "statement", "likelihood", "impact", "repeat_finding",
             "proposed_focus", "sample_source", "auditor_override"}
TOP_KEYS = {"schema", "generated_on", "risks", "excluded", "revision"}


class Findings:
    def __init__(self):
        self.fails, self.warns, self.dropped = [], [], {}

    def fail(self, code, msg, rid=None, drop=False):
        self.fails.append("%s%s: %s" % (code, " " + rid if rid else "", msg))
        if drop and rid:
            self.dropped.setdefault(rid, []).append(code)

    def warn(self, code, msg, rid=None):
        self.warns.append("%s%s: %s" % (code, " " + rid if rid else "", msg))


# ------------------------------------------------------------------ helpers
def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("cannot read %s: %s" % (path, exc))
        sys.exit(2)


def resolve(root, path):
    """Return (found, node) for a $.a.b[0].c path."""
    if not isinstance(path, str) or not path.startswith("$"):
        return False, None
    rest, pos, node = path[1:], 0, root
    while pos < len(rest):
        m = TOKEN_RE.match(rest, pos)
        if not m:
            return False, None
        key, idx = m.group(1), m.group(2)
        if key is not None:
            if not isinstance(node, dict) or key not in node:
                return False, None
            node = node[key]
        else:
            if not isinstance(node, list) or int(idx) >= len(node):
                return False, None
            node = node[int(idx)]
        pos = m.end()
    return True, node


def is_scalar(v):
    return isinstance(v, (int, float, str, bool)) and v is not None


def fmt_value(v, path, fmt):
    last = re.split(r"[.\[]", path.rstrip("]"))[-1].lower()
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, str):
        return v
    if fmt == "int":
        return "{:,}".format(int(round(v)))
    if fmt == "gbp0":
        return "£{:,.0f}".format(v)
    if fmt == "gbp":
        return "£{:,.2f}".format(v)
    if fmt == "dp1":
        return "{:,.1f}".format(v)
    if fmt == "dp2":
        return "{:,.2f}".format(v)
    if isinstance(v, int):
        return "£{:,}".format(v) if re.search(r"(gbp|estimate|rate|value|amount)", last) else "{:,}".format(v)
    if re.search(r"(gbp|estimate|rate|value|amount)", last):
        return "£{:,.2f}".format(v)
    return "{:,.2f}".format(v)


def walk_ids(node, out):
    if isinstance(node, dict):
        if isinstance(node.get("id"), str):
            out.setdefault(node["id"], node)
        for v in node.values():
            walk_ids(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_ids(v, out)


def collect_suppliers(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "supplier" and isinstance(v, str) and len(v) >= 6:
                out.add(v.upper())
            else:
                collect_suppliers(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_suppliers(v, out)


def parse_range(text):
    t = text.replace("–", "-").replace("—", "-")
    m = re.search(r"up to\s+(\d+)", t, re.I)
    if m:
        return 0, int(m.group(1))
    m = re.search(r"(\d+)\s*-\s*(\d+)", t)
    return (int(m.group(1)), int(m.group(2))) if m else None


def joined(q):
    return " ".join(q) if isinstance(q, list) else str(q)


# --------------------------------------------------------------- the scale
class Scale:
    def __init__(self, hist, F):
        self.fallback, self.notes, self.conflict = True, [], None
        sm = hist.get("scoring_method", {})
        self.status = sm.get("status")
        self.L = dict(FALLBACK_LABELS)
        self.I = dict(FALLBACK_LABELS)
        self.Lid, self.Iid, self.cells, self.bands = {}, {}, {}, []
        self.crr_used = self.crr_other = None
        if self.status != "found":
            self.notes.append("FALLBACK SCALE: history.json reports no usable council scoring method "
                              "(scoring_method.status is %r). Likelihood and impact use 1-5 Very low to "
                              "Very high, score = likelihood x impact, and no band is assigned." % self.status)
            return
        try:
            self.L = {i["rating"]: i["label"] for i in sm["likelihood_scale"]}
            self.Lid = {i["rating"]: i["id"] for i in sm["likelihood_scale"]}
            self.I = {i["rating"]: i["label"] for i in sm["impact_scale"]}
            self.Iid = {i["rating"]: i["id"] for i in sm["impact_scale"]}
            for row in sm["matrix"]:
                for c in row["cells"]:
                    self.cells[(row["impact"], c["likelihood"])] = (c["score"], c["label"], row["id"])
            for b in sm["bands"]:
                rng = parse_range(b["score_range"])
                if rng is None:
                    F.fail("E-SCALE", "band %s score_range %r cannot be read" % (b["id"], b["score_range"]))
                else:
                    self.bands.append((rng[0], rng[1], b))
        except (KeyError, TypeError) as exc:
            F.fail("E-SCALE", "history.json scoring_method is malformed (%s)" % exc)
            return
        if sorted(self.L) != [1, 2, 3, 4, 5] or sorted(self.I) != [1, 2, 3, 4, 5] or len(self.cells) != 25:
            F.fail("E-SCALE", "the council scale is incomplete (needs 5 likelihood, 5 impact, 25 matrix cells)")
            return
        self.fallback = False
        for (i, l), (score, label, rid) in sorted(self.cells.items()):
            if score != i * l:
                F.warn("W-SCALE", "matrix cell impact %d x likelihood %d prints score %d, not %d (%s)" % (i, l, score, i * l, rid))
        for s in sorted({i * l for i in range(1, 6) for l in range(1, 6)}):
            if not [1 for lo, hi, b in self.bands if lo <= s <= hi]:
                F.fail("E-SCALE", "no band covers score %d" % s)
            elif len([1 for lo, hi, b in self.bands if lo <= s <= hi]) > 1:
                self.notes.append("Overlapping bands: score %d falls in more than one band; the first listed is used." % s)
        self._conflicts(sm, hist)

    def _conflicts(self, sm, hist):
        for lo, hi, b in self.bands:
            if re.search(r"corporate risk register", b.get("escalation", ""), re.I):
                self.crr_used = (lo, b)
        for o in sm.get("other_rules", []):
            if "corporate risk register" in o.get("topic", "").lower():
                m = re.search(r"Score\s+(\d+)\s+or above", joined(o.get("quote", "")))
                if m:
                    self.crr_other = (int(m.group(1)), o)
        if self.crr_used and self.crr_other and self.crr_used[0] != self.crr_other[0]:
            di = next((d["id"] for d in hist.get("discrepancies", []) if "corporate risk register" in d.get("text", "").lower()), None)
            self.conflict = (self.crr_used, self.crr_other)
            self.notes.append(
                "CONFLICT IN THE COUNCIL'S SCORING METHOD: Table 4 (%s) sends scores %d and above to the Corporate "
                "Risk Register; the escalation figure (%s) lists risks that score %d or above. This register USES the "
                "Table 4 band (%d and above) for bands and escalation, and MARKS (‡) any risk that meets only the "
                "other criterion (score %d to %d). It is not resolved here%s." % (
                    self.crr_used[1]["id"], self.crr_used[0], self.crr_other[1]["id"], self.crr_other[0],
                    self.crr_used[0], self.crr_other[0], self.crr_used[0] - 1,
                    "; the papers' own discrepancy record is %s" % di if di else ""))
        pairs = {}
        for (i, l), (score, label, rid) in self.cells.items():
            b = self.band(score)
            if b and label.strip().lower() != b["level"].strip().lower():
                pairs[(label, b["level"])] = True
        for label, level in sorted(pairs):
            self.notes.append("NAMING: the matrix labels some cells '%s' where the bands table names the band '%s'. "
                              "Both are shown; the band name comes from the bands table." % (label, level))

    def band(self, score):
        for lo, hi, b in self.bands:
            if lo <= score <= hi:
                return b
        return None

    def score(self, impact, likelihood):
        if self.fallback:
            return impact * likelihood, None
        s, label, _ = self.cells[(impact, likelihood)]
        return s, label


# --------------------------------------------------------- text processing
class Ctx:
    def __init__(self, rules, analytics, hist, scale, F):
        self.rules = {r["rule_id"]: r for r in rules.get("rules", [])}
        self.analytics, self.hist, self.scale, self.F = analytics, hist, scale, F
        self.hist_ids = {}
        walk_ids(hist, self.hist_ids)
        self.suppliers = set()
        collect_suppliers(analytics, self.suppliers)

    def cite(self, kind, ref):
        """Return (resolved?, evidence line)."""
        if kind == "rule":
            r = self.rules.get(ref)
            return (True, "rule %s · clause %s · %s" % (ref, r["clause"], r["required_action"])) if r else (False, None)
        if kind == "history":
            h = self.hist_ids.get(ref)
            if h is None:
                return False, None
            label = (h.get("audit_title") or h.get("review_title") or h.get("topic") or h.get("label")
                     or h.get("level") or h.get("category") or h.get("name") or h.get("text") or "")
            op = h.get("opinion") or h.get("report_opinion") or ""
            prog = h.get("implementation_progress") or ""
            extra = " · %s" % op if op else ""
            extra += " (implementation: %s)" % prog if prog else ""
            return True, "history %s · %s%s" % (ref, str(label)[:90], extra)
        ok, v = resolve(self.analytics, ref)
        if not ok:
            return False, None
        if is_scalar(v):
            return True, "metric %s = %s" % (ref, fmt_value(v, ref, None))
        return True, "metric %s (%s, %d %s)" % (ref, type(v).__name__, len(v), "items" if isinstance(v, list) else "keys")

    def fill(self, text, rid, field):
        def sub(m):
            ok, v = resolve(self.analytics, m.group(1))
            if not ok or not is_scalar(v):
                self.F.fail("E-PLACEHOLDER", "%s: %s does not resolve to a single value in analytics.json" % (field, m.group(0)), rid, drop=True)
                return m.group(0)
            return fmt_value(v, m.group(1), m.group(2))
        return PH_RE.sub(sub, text)


def tags_in(text):
    return [(m.group(1), m.group(2)) for m in CITE_RE.finditer(text)]


def check_prose(ctx, rid, field, text):
    F = ctx.F
    bare = FIG_OK.sub(" ", PH_RE.sub(" ", CITE_RE.sub(" ", text)))
    figs = FIG_RE.findall(bare)
    if figs:
        F.warn("W-FIGURE", "%s has typed figure(s) %s; use a {{$.path}} placeholder" % (field, ", ".join(figs[:4])), rid)
    m = LANG_RE.search(bare)
    if m:
        F.warn("W-LANGUAGE", "%s uses the word %r; describe the indicator, not what it implies" % (field, m.group(0)), rid)
    up = bare.upper()
    for s in ctx.suppliers:
        if s in up:
            F.warn("W-NAME", "%s names a supplier; keep names out of risk statements and justifications" % field, rid)
            break


def adverse_item(item):
    vals = [str(item.get(k, "")).lower() for k in ("opinion", "report_opinion", "implementation_progress")]
    return any(any(a == v or v.startswith(a) for a in ADVERSE) for v in vals if v)


# ---------------------------------------------------------- risk validation
def validate_risk(ctx, scale, r, revision_open):
    """Return an output dict for a risk or None if it is dropped."""
    F = ctx.F
    rid = r.get("id") if isinstance(r, dict) else None
    if not isinstance(r, dict) or not isinstance(rid, str) or not re.match(r"^R-\d{2,}$", rid):
        F.fail("E-SCHEMA", "a risk has no valid id (R-01, R-02, ...)", rid if isinstance(rid, str) else None)
        return None
    miss = [k for k in ("id", "theme", "statement", "likelihood", "impact", "repeat_finding", "proposed_focus") if k not in r]
    extra = [k for k in r if k not in RISK_KEYS]
    if miss or extra:
        F.fail("E-SCHEMA", "missing %s, unexpected %s" % (miss, extra), rid, drop=True)
        return None
    if r["theme"] not in THEMES:
        F.fail("E-SCHEMA", "theme %r is not one of %s" % (r["theme"], sorted(THEMES)), rid, drop=True)
        return None
    lk, im = r["likelihood"], r["impact"]
    if (not isinstance(lk, dict) or set(lk) != {"score", "signal", "signal_metrics", "justification"}
            or not isinstance(im, dict) or set(im) != {"score", "justification"}):
        F.fail("E-SCHEMA", "likelihood needs score, signal, signal_metrics, justification; impact needs score, justification", rid, drop=True)
        return None
    for name, v in (("likelihood.score", lk["score"]), ("impact.score", im["score"])):
        if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5:
            F.fail("E-SCHEMA", "%s must be an integer 1-5" % name, rid, drop=True)
            return None
    for name, v in (("statement", r["statement"]), ("likelihood.justification", lk["justification"]),
                    ("impact.justification", im["justification"]), ("proposed_focus", r["proposed_focus"])):
        if not isinstance(v, str) or not v.strip():
            F.fail("E-SCHEMA", "%s must be non-empty text" % name, rid, drop=True)
            return None
    ov = r.get("auditor_override")
    ov_fields = set()
    if ov is not None:
        if (not isinstance(ov, dict) or not {"fields", "note"} <= set(ov) or not set(ov) <= {"fields", "note", "agent_rating"}
                or not isinstance(ov["fields"], list) or not ov["fields"] or not set(ov["fields"]) <= {"likelihood", "impact"}
                or not isinstance(ov["note"], str) or not ov["note"].strip()):
            F.fail("E-SCHEMA", "auditor_override must be {fields: [likelihood|impact], note, agent_rating?}", rid, drop=True)
            return None
        if not revision_open:
            F.fail("E-OVERRIDE", "auditor_override on a risk outside a revision", rid, drop=True)
            return None
        ov_fields = set(ov["fields"])

    # citations
    fields = [("statement", r["statement"]), ("likelihood.justification", lk["justification"]),
              ("impact.justification", im["justification"]), ("proposed_focus", r["proposed_focus"])]
    rf = r["repeat_finding"]
    if rf is not None:
        if (not isinstance(rf, dict) or set(rf) != {"applies", "history_ids", "note"} or not isinstance(rf["applies"], bool)
                or not isinstance(rf["history_ids"], list) or not isinstance(rf["note"], str)):
            F.fail("E-SCHEMA", "repeat_finding must be null or {applies, history_ids, note}", rid, drop=True)
            return None
        fields.append(("repeat_finding.note", rf["note"]))
    evidence, bad = [], False
    resolved_by_field = {}
    for fname, text in fields:
        ok_here = 0
        for kind, ref in tags_in(text):
            ok, line = ctx.cite(kind, ref)
            if ok:
                ok_here += 1
                if line not in evidence:
                    evidence.append(line)
            else:
                F.fail("E-CITE", "%s cites [%s:%s], which does not exist" % (fname, kind, ref), rid)
                bad = True
        resolved_by_field[fname] = ok_here
        check_prose(ctx, rid, fname, text)
    for fname in ("likelihood.justification", "impact.justification"):
        if resolved_by_field[fname] == 0:
            F.fail("E-NOCITE", "%s has no resolvable citation; the risk is dropped" % fname, rid, drop=True)
            bad = True
    if bad and rid in F.dropped:
        return None

    # likelihood rubric
    base, uplift = lk["score"], 0
    sig = lk["signal"]
    if sig not in SIGNALS:
        F.fail("E-RUBRIC", "likelihood.signal %r not in %s" % (sig, sorted(SIGNALS)), rid, drop=True)
        return None
    if "likelihood" not in ov_fields:
        want, need_tests = SIGNALS[sig]
        if base != want:
            F.fail("E-RUBRIC", "signal %s means a base likelihood of %d, not %d" % (sig, want, base), rid)
        sm = lk["signal_metrics"]
        if not isinstance(sm, list) or not all(isinstance(p, str) for p in sm):
            F.fail("E-RUBRIC", "signal_metrics must be a list of $.paths", rid)
        else:
            cited = {ref for kind, ref in tags_in(lk["justification"]) if kind == "metric"}
            vals, tests = [], set()
            for p in sm:
                ok, v = resolve(ctx.analytics, p)
                if not ok or isinstance(v, bool) or not isinstance(v, (int, float)):
                    F.fail("E-RUBRIC", "signal_metrics %s does not resolve to a number" % p, rid)
                    continue
                if p not in cited:
                    F.fail("E-RUBRIC", "signal_metrics %s is not cited in the likelihood justification" % p, rid)
                if not is_indicator(p):
                    F.fail("E-RUBRIC", "signal_metrics %s is not an indicator metric: population lists (high_value_suppliers), "
                           "matched or candidate groups and context counts do not count; use a flagged-item count from "
                           "threshold_clustering, split_purchases, duplicates, off_contract (unmatched), expired_notice_spend "
                           "or spend_vs_award" % p, rid)
                vals.append((p, v))
                m = re.match(r"\$\.tests\.([\w-]+)", p)
                if m and v > 0:
                    tests.add(m.group(1))
            if sig == "none" and not any(v == 0 for p, v in vals):
                F.fail("E-RUBRIC", "signal none needs a cited metric equal to zero", rid)
            if sig == "none" and any(v > 0 for p, v in vals):
                F.fail("E-RUBRIC", "signal none but a cited metric is above zero", rid)
            if sig == "unobservable" and (sm or not any(k == "rule" for k, _ in tags_in(lk["justification"]))):
                F.fail("E-RUBRIC", "signal unobservable takes no metrics and must cite a rule", rid)
            if sig == "outside_headline" and not any(v > 0 for p, v in vals):
                F.fail("E-RUBRIC", "signal outside_headline needs a cited metric above zero", rid)
            if sig in HEADLINE:
                if len(tests) < need_tests:
                    F.fail("E-RUBRIC", "signal %s needs %d distinct tests above zero in signal_metrics, found %d" % (sig, need_tests, len(tests)), rid)
                if not any("general_procurement" in p for p, v in vals):
                    F.fail("E-RUBRIC", "signal %s needs a signal_metrics path for the general_procurement headline" % sig, rid)
    # repeat finding
    if rf and rf["applies"] and "likelihood" not in ov_fields:
        ids = rf["history_ids"]
        adv = [i for i in ids if i in ctx.hist_ids and adverse_item(ctx.hist_ids[i]) and re.match(r"^(AO|FU)-", i)]
        if not ids or not adv:
            F.fail("E-REPEAT", "the repeat-finding uplift must cite an audit (AO-/FU- item) with an adverse opinion (%s); "
                   "cited: %s" % (", ".join(ADVERSE), ids or "none"), rid)
        for i in ids:
            if i not in ctx.hist_ids:
                F.fail("E-REPEAT", "history id %s does not exist" % i, rid)
            elif ("history", i) not in tags_in(lk["justification"]):
                F.fail("E-REPEAT", "history id %s must be cited as [history:%s] in the likelihood justification" % (i, i), rid)
        if not re.search(r"repeat", lk["justification"], re.I):
            F.fail("E-REPEAT", "the likelihood justification must say the repeat-finding uplift was applied", rid)
        uplift = 1 if adv else 0
    # impact anchor
    if not scale.fallback and "impact" not in ov_fields:
        anchors = [ref for kind, ref in tags_in(im["justification"]) if kind == "history" and ref == scale.Iid.get(im["score"])]
        if not anchors:
            F.fail("E-IMPACT", "impact %d must cite its scale entry [history:%s] in the impact justification" % (im["score"], scale.Iid.get(im["score"])), rid)
    # score
    if "likelihood" in ov_fields:
        final_l = base
    else:
        final_l = min(5, base + uplift)
    score, mlabel = scale.score(im["score"], final_l)
    band = scale.band(score) if not scale.fallback else None
    crr = None
    if scale.conflict:
        (used, _), (other, _) = scale.conflict
        crr = ("meets the Table 4 criterion (score %d or above)" % used if score >= used else
               ("‡ meets only the escalation-figure criterion (score %d or above), not Table 4 (%d or above)" % (other, used) if score >= other else ""))
    out = {
        "id": rid, "theme": r["theme"], "statement": ctx.fill(r["statement"], rid, "statement"),
        "base": base, "uplift": uplift, "L": final_l, "I": im["score"], "score": score, "matrix_label": mlabel,
        "band": band, "crr": crr,
        "l_text": ctx.fill(lk["justification"], rid, "likelihood.justification"),
        "i_text": ctx.fill(im["justification"], rid, "impact.justification"),
        "focus": ctx.fill(r["proposed_focus"], rid, "proposed_focus"),
        "repeat": (rf if rf and rf["applies"] else None),
        "repeat_text": ctx.fill(rf["note"], rid, "repeat_finding.note") if rf and rf["applies"] else "",
        "evidence": evidence, "sample_source": r.get("sample_source"), "override": ov,
    }
    return None if rid in F.dropped else out


# -------------------------------------------------- comments and revisions
def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip())
    return [c.replace("\\|", "|").strip() for c in cells[1:-1]]


def parse_comments(path):
    """Return ({id: (decision_word, comment)}, removed_rows, raw_decisions)."""
    p = Path(path)
    main, removed = {}, {}
    if not p.exists():
        return main, removed
    for line in p.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*R-\d+\s*\|", line):
            continue
        cells = split_row(line)
        if len(cells) >= 5:
            main[cells[0]] = (cells[3], cells[4])
        elif len(cells) == 3:
            removed[cells[0]] = (cells[1], cells[2])
    return main, removed


def decision_word(text):
    t = re.sub(r"[^a-z]", "", text.lower())
    for w in ("approve", "amend", "reject"):
        if t.startswith(w):
            return w
    return None


def load_state(register_path):
    p = Path(register_path)
    if not p.exists():
        return None
    m = STATE_RE.search(p.read_text(encoding="utf-8"))
    return json.loads(m.group(1)) if m else None


def check_revision(F, ratings, risks_raw, excluded, state, comments):
    """Returns (revision number, applied decisions, changes list, new decisions)."""
    rev = ratings.get("revision")
    prior_rev = state["revision"] if state else 0
    applied = dict(state["applied"]) if state else {}
    # normalise decisions
    decisions = {}
    for rid, (word, comment) in comments.items():
        if not word.strip():
            continue
        w = decision_word(word)
        if w is None:
            F.fail("E-DECISION", "%s: decision %r is not Approve, Amend or Reject" % (rid, word))
            continue
        if w in ("amend", "reject") and not comment.strip():
            F.fail("E-DECISION", "%s: an %s decision needs a Comment saying what or why" % (rid, w))
            continue
        decisions[rid] = (w, comment)
    if decisions and not state:
        F.fail("E-REVISION", "auditor decisions exist but there is no earlier register to apply them to")
        return 0, applied, [], {}
    new = {rid: dc for rid, dc in decisions.items()
           if applied.get(rid) is None or (applied[rid]["decision"], applied[rid]["comment"]) != dc}
    if state:
        for rid in new:
            if rid not in state["risks"]:
                F.fail("E-DECISION", "%s: a decision refers to a risk that was not in the last register" % rid)
    if not state:
        if rev is not None:
            F.fail("E-REVISION", "revision block present on a first build; it must be null")
        return 0, applied, [], {}
    if not new and prior_rev == 0 and not applied:
        # No auditor decision has ever been applied: the register is still a draft,
        # so the ratings may change freely. Only a revision block is not allowed yet.
        if rev is not None:
            F.fail("E-REVISION", "no auditor decisions yet, so the revision block must be null")
        return 0, applied, [], {}
    prior = state["risks"]
    cur = {r["id"]: r for r in risks_raw if isinstance(r, dict) and "id" in r}
    changed = {i for i in cur if i in prior and cur[i] != prior[i]}
    added = {i for i in cur if i not in prior}
    removed = {i for i in prior if i not in cur}
    diff = changed | added | removed
    want_rev = prior_rev + 1 if new else prior_rev
    if new:
        if not isinstance(rev, dict) or rev.get("number") != want_rev:
            F.fail("E-REVISION", "new auditor decisions need a revision block with number %d" % want_rev)
    else:
        if rev is not None and (not isinstance(rev, dict) or rev.get("number") != prior_rev):
            F.fail("E-REVISION", "no new auditor decisions, so the revision block must be null or stay at revision %d" % prior_rev)
        if diff:
            F.fail("E-UNASKED", "ratings changed with no new auditor decision: %s" % ", ".join(sorted(diff)))
        return prior_rev, applied, (rev or {}).get("changes", []), {}
    # apply each new decision
    for rid, (w, comment) in sorted(new.items()):
        if rid not in prior:
            continue
        if w == "approve" and rid in diff:
            F.fail("E-UNASKED", "%s was approved but its rating changed" % rid)
        if w == "amend" and rid not in changed:
            F.fail("E-UNAPPLIED", "%s: the Amend decision was not applied (the risk is unchanged)" % rid)
        if w == "reject":
            if rid not in removed:
                F.fail("E-UNAPPLIED", "%s: the Reject decision was not applied (the risk is still rated)" % rid)
            elif not any(isinstance(e, dict) and e.get("id") == rid for e in excluded):
                F.fail("E-UNAPPLIED", "%s: a rejected risk must move to excluded with its id and the auditor's reason" % rid)
    amend_or_reject = {rid for rid, (w, c) in new.items() if w in ("amend", "reject")}
    changes = rev.get("changes") if isinstance(rev, dict) else None
    if not isinstance(changes, list):
        F.fail("E-REVISION", "revision.changes must list every risk that changed")
        changes = []
    listed = {}
    for ch in changes:
        if (not isinstance(ch, dict) or set(ch) != {"id", "action", "note"} or ch["action"] not in CHANGE_ACTIONS
                or not isinstance(ch["note"], str) or not ch["note"].strip()):
            F.fail("E-REVISION", "each revision change needs id, action (%s) and a note" % "/".join(sorted(CHANGE_ACTIONS)))
            continue
        listed[ch["id"]] = ch
    for rid in sorted(diff):
        kind = "amended" if rid in changed else ("rejected" if rid in removed else "added")
        if kind in ("amended", "rejected") and rid not in amend_or_reject:
            F.fail("E-UNASKED", "%s %s without an Amend or Reject decision from the auditor" % (rid, kind))
        if kind == "added":
            ch = listed.get(rid)
            asked = ch and any(i in comments and comments[i][1].strip() and i in ch["note"] for i in comments)
            if not asked:
                F.fail("E-UNASKED", "%s is a new risk; the revision note must name the auditor comment (by risk id) that asked for it" % rid)
        if rid not in listed:
            F.fail("E-REVISION", "%s changed (%s) but is missing from revision.changes" % (rid, kind))
        elif listed[rid]["action"] != kind:
            F.fail("E-REVISION", "%s is listed as %s but it was %s" % (rid, listed[rid]["action"], kind))
    for rid in listed:
        if rid not in diff:
            F.fail("E-REVISION", "%s is listed in revision.changes but did not change" % rid)
    for rid, r in cur.items():
        if isinstance(r, dict) and r.get("auditor_override") and rid not in changed and rid not in added:
            if prior.get(rid, {}).get("auditor_override") != r["auditor_override"]:
                F.fail("E-OVERRIDE", "%s carries an auditor_override that was not part of an applied decision" % rid)
    for rid, (w, c) in new.items():
        applied[rid] = {"decision": w, "comment": c, "revision": want_rev}
    return want_rev, applied, changes, new


# ------------------------------------------------------------------ render
def bname(b):
    """Band name with its colour, unless the paper printed no separate colour word."""
    return b["level"] if b["colour"].strip().lower() == b["level"].strip().lower() else "%s (%s)" % (b["level"], b["colour"])


def risk_title(o):
    return o["statement"].split("\n")[0]


def rating_cell(o, scale):
    band = bname(o["band"]) if o["band"] else "n/a"
    return "L%d × I%d = %d · %s · %s" % (o["L"], o["I"], o["score"], o["matrix_label"] or "no label", band)


def render_register(ctx, scale, ratings, kept, excluded, revision_no, changes, decisions, applied, state_blob, F, draft):
    a, h = ctx.analytics, ctx.hist
    out = []
    w = out.append
    w("# Procurement audit risk register (risk indicators for the auditor)\n")
    if draft:
        w("> **DRAFT: THE BUILD HAD FAILURES.** This is not the register. Dropped or failing: %s. "
          "Fix `outputs/risk-ratings.json` and rebuild.\n" % ("; ".join(sorted(F.dropped)) or "see the builder output"))
    w("Prepared for the auditor's approval gate. Every entry is a **risk indicator to investigate**, not a finding "
      "about the council, a department or a supplier. The assessor recommends; the auditor decides.\n")
    if revision_no:
        w("## Revision %d\n" % revision_no)
        w("This revision applies the auditor's decisions recorded in `outputs/auditor-comments.md`. What changed:\n")
        for ch in changes:
            o = next((k for k in kept if k["id"] == ch["id"]), None)
            flag = " ⚑ **auditor override** (%s)" % ", ".join(o["override"]["fields"]) if o and o["override"] else ""
            w("- **%s** %s: %s%s" % (ch["id"], ch["action"], ch["note"], flag))
        unchanged = [k["id"] for k in kept if k["id"] not in {c["id"] for c in changes}]
        if unchanged:
            w("- Unchanged: %s." % ", ".join(unchanged))
        w("")
    w("## How this register was made\n")
    w("- Evidence: `analytics.json` generated %s; `history.json` generated %s; ratings file dated %s." % (
        a.get("generated_at", "unknown"), h.get("generated_on", "unknown"), ratings.get("generated_on", "unknown")))
    w("- Every figure is read from `analytics.json`; every score, matrix label and band is computed by the builder "
      "from the scale below. The assessor chooses levels and cites evidence.")
    if scale.fallback:
        w("- **Scale: FALLBACK, not the council's.** %s" % scale.notes[0].split(": ", 1)[1])
    else:
        w("- Scale: the council's 5x5 matrix (Risk Management Strategy 2024-27, Tables 1, 2 and 4, Figure 1; history ids "
          "%s, %s, %s). Likelihood: %s. Impact: %s." % (
              "%s to %s" % (min(scale.Lid.values()), max(scale.Lid.values())), "%s to %s" % (min(scale.Iid.values()), max(scale.Iid.values())),
              "%s to %s, %s to %s" % (min(c[2] for c in scale.cells.values()), max(c[2] for c in scale.cells.values()), min(b["id"] for _, _, b in scale.bands), max(b["id"] for _, _, b in scale.bands)),
              ", ".join("%d %s" % (k, scale.L[k]) for k in sorted(scale.L)), ", ".join("%d %s" % (k, scale.I[k]) for k in sorted(scale.I))))
        w("- Bands: " + "; ".join("%s = %s" % (bname(b), b["score_range"].strip()) for lo, hi, b in scale.bands) + ".")
    for n in scale.notes[(0 if not scale.fallback else 1):]:
        w("- **%s**" % n)
    skipped = a.get("skipped", [])
    nulls = [k for k, v in a.get("null_parameters", {}).items()]
    if skipped:
        w("- Skipped analysis tiers: %d, because %s have no value in the Contract Rules (a threshold the PDF only names). "
          "Risks that depend on them are rated on what did run." % (len(skipped), ", ".join(nulls) or "a parameter"))
    cav = a.get("contracts", {}).get("caveat")
    if cav:
        w("- Notices caveat: %s" % cav)
    w("")
    counts = {}
    for k in kept:
        key = k["band"]["level"] if k["band"] else "n/a"
        counts[key] = counts.get(key, 0) + 1
    w("## Summary\n")
    w("%d risk%s rated%s.\n" % (len(kept), "" if len(kept) == 1 else "s", (": " + ", ".join("%d %s" % (v, k) for k, v in counts.items())) if kept else ""))
    if kept:
        w("| ID | Theme | Risk | Rating | Likelihood | Impact |" + (" CRR |" if scale.conflict else ""))
        w("|---|---|---|---|---|---|" + ("---|" if scale.conflict else ""))
        for k in kept:
            row = "| %s | %s | %s | %s | %d %s | %d %s |" % (
                k["id"], THEMES[k["theme"]], risk_title(k).replace("|", "/"), rating_cell(k, scale),
                k["L"], scale.L[k["L"]], k["I"], scale.I[k["I"]])
            if scale.conflict:
                row += " %s |" % (k["crr"] or "")
            w(row)
        w("")
    for k in kept:
        w("### %s · %s\n" % (k["id"], risk_title(k)))
        w("**Rating:** %s%s\n" % (rating_cell(k, scale), "  ⚑ auditor override" if k["override"] else ""))
        if scale.conflict and k["crr"]:
            w("**Corporate Risk Register:** %s\n" % k["crr"])
        lk = "%d %s" % (k["L"], scale.L[k["L"]])
        if k["uplift"]:
            lk += " (rubric %d + 1 repeat-finding uplift)" % k["base"]
        elif k["override"] and "likelihood" in k["override"]["fields"]:
            lk += " (auditor-set)"
        w("- **Likelihood %s.** %s" % (lk, k["l_text"]))
        if k["repeat"]:
            w("- **Repeat finding:** %s (%s)" % (k["repeat_text"], ", ".join(k["repeat"]["history_ids"])))
        w("- **Impact %d %s.** %s" % (k["I"], scale.I[k["I"]], k["i_text"]))
        if k["override"]:
            ar = k["override"].get("agent_rating")
            w("- **Auditor override (%s):** %s%s" % (", ".join(k["override"]["fields"]), k["override"]["note"],
                                                       " The assessor's own rating was %s." % ", ".join("%s %s" % (a_, b_) for a_, b_ in ar.items()) if ar else ""))
        w("- **Evidence:**")
        for line in k["evidence"]:
            w("  - %s" % line)
        if k["sample_source"]:
            w("  - sample pointer: %s" % k["sample_source"])
        w("- **Proposed focus (recommendation, for the auditor to decide):** %s\n" % k["focus"])
    if excluded:
        w("## Not rated\n")
        for e in excluded:
            w("- %s%s: %s" % (e.get("id", "") + " " if e.get("id") else "", THEMES.get(e.get("theme"), e.get("theme", "")), e.get("reason", "")))
        w("")
    w("## Auditor decisions\n")
    if not decisions:
        w("No auditor decisions are recorded yet. Record **Approve**, **Amend** or **Reject** with a Comment for each risk in "
          "`outputs/auditor-comments.md`, then re-run the risk-assessor, which applies exactly those decisions as a revision.")
    else:
        w("| Risk | Decision | Comment | Applied in revision | Effect |")
        w("|---|---|---|---|---|")
        for rid, d in sorted(decisions.items()):
            ap = applied.get(rid, {})
            ch = next((c for c in changes if c["id"] == rid), None)
            effect = ("%s: %s" % (ch["action"], ch["note"])) if ch else ("unchanged" if rid in {k["id"] for k in kept} else "no longer rated")
            w("| %s | %s | %s | %s | %s |" % (rid, d[0].capitalize(), d[1].replace("|", "/"), ap.get("revision", "pending"), effect.replace("|", "/")))
        w("\nDecisions are the auditor's; the assessor only applies them.")
    w("")
    w("<!-- build_register:state %s -->" % state_blob)
    return "\n".join(out) + "\n"


def render_comments(kept, scale, existing, removed_rows):
    out = ["# Auditor comments: risk decisions\n",
           "Record one decision per risk: **Approve**, **Amend** (say in the Comment what to change) or **Reject** (give the "
           "reason). Leave Decision blank if you have not decided. Do not edit the other columns. Save, then re-run the "
           "risk-assessor, which applies exactly these decisions as a revision. Decisions already here are kept when the file "
           "is rewritten.\n",
           "| Risk | Statement | Rating | Decision | Comment |", "|---|---|---|---|---|"]
    for k in kept:
        d, c = existing.get(k["id"], ("", ""))
        st = re.sub(r"\s+", " ", risk_title(k)).replace("|", "/")
        out.append("| %s | %s | %s | %s | %s |" % (k["id"], st[:110], rating_cell(k, scale).replace("|", "/"), d.replace("|", "\\|"), c.replace("|", "\\|")))
    keep_ids = {k["id"] for k in kept}
    gone = {i: v for i, v in {**removed_rows, **{i: v for i, v in existing.items() if i not in keep_ids and v[0].strip()}}.items()}
    if gone:
        out += ["", "## Decisions on risks no longer in the register\n", "| Risk | Decision | Comment |", "|---|---|---|"]
        for i, (d, c) in sorted(gone.items()):
            out.append("| %s | %s | %s |" % (i, d.replace("|", "\\|"), c.replace("|", "\\|")))
    return "\n".join(out) + "\n"


# -------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ratings", default="outputs/risk-ratings.json")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--history", default="outputs/history.json")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args(argv)
    ratings, rules = load_json(a.ratings), load_json(a.rules)
    analytics, hist = load_json(a.analytics), load_json(a.history)
    out_dir = Path(a.out_dir)
    F = Findings()
    if not isinstance(ratings, dict) or not set(ratings) <= TOP_KEYS or not {"risks", "excluded", "revision"} <= set(ratings):
        print("cannot run: risk-ratings.json needs risks, excluded and revision (and may hold schema, generated_on)")
        return 2
    scale = Scale(hist, F)
    ctx = Ctx(rules, analytics, hist, scale, F)
    register_path, comments_path = out_dir / "risk-register.md", out_dir / "auditor-comments.md"
    state = load_state(register_path)
    comments, removed_rows = parse_comments(comments_path)
    excluded = ratings.get("excluded") or []
    if not isinstance(ratings["risks"], list) or not isinstance(excluded, list):
        print("cannot run: risks and excluded must be lists")
        return 2
    rev_obj = ratings.get("revision")
    revision_open = bool(state) and (isinstance(rev_obj, dict) and rev_obj.get("number", 0) > 0)
    seen, kept = set(), []
    for r in ratings["risks"]:
        rid = r.get("id") if isinstance(r, dict) else None
        if rid in seen:
            F.fail("E-SCHEMA", "duplicate risk id", rid, drop=True)
            continue
        seen.add(rid)
        o = validate_risk(ctx, scale, r, revision_open)
        if o and rid not in F.dropped:
            kept.append(o)
    risks_raw = [r for r in ratings["risks"] if isinstance(r, dict)]
    revision_no, applied, changes, new = check_revision(F, ratings, risks_raw, excluded, state, comments)
    decisions = {i: (decision_word(d) or d, c) for i, (d, c) in comments.items() if d.strip()}
    blob = json.dumps({"revision": revision_no, "applied": applied,
                       "risks": {r["id"]: r for r in risks_raw if r.get("id") not in F.dropped}},
                      ensure_ascii=False, separators=(",", ":")).replace("-", "\\u002d")
    draft = bool(F.fails)
    text = render_register(ctx, scale, ratings, kept, excluded, revision_no, changes, decisions, applied, blob, F, draft)
    out_dir.mkdir(parents=True, exist_ok=True)
    if draft:
        (out_dir / "risk-register.draft.md").write_text(text, encoding="utf-8")
    else:
        register_path.write_text(text, encoding="utf-8")
        comments_path.write_text(render_comments(kept, scale, comments, removed_rows), encoding="utf-8")
        d = out_dir / "risk-register.draft.md"
        if d.exists():
            d.unlink()
    for rid, codes in sorted(F.dropped.items()):
        print("DROPPED %s (%s)" % (rid, ", ".join(sorted(set(codes)))))
    for f in F.fails:
        print("FAIL  " + f)
    for w in F.warns:
        print("WARN  " + w)
    kinds = ", ".join("%d %s" % (sum(1 for k in kept if k["band"] and k["band"]["level"] == lv), lv)
                      for lv in sorted({k["band"]["level"] for k in kept if k["band"]}))
    print("%s: %d risks kept%s, %d dropped, %d failures, %d warnings%s" % (
        "FAIL" if F.fails else ("WARN" if F.warns else "PASS"), len(kept), " (%s)" % kinds if kinds else "", len(F.dropped),
        len(F.fails), len(F.warns), "; wrote risk-register.draft.md only" if draft else "; wrote risk-register.md and auditor-comments.md"))
    return 1 if F.fails else (3 if F.warns else 0)


if __name__ == "__main__":
    sys.exit(main())
