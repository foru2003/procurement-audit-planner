---
name: risk-assessment
description: Method for rating procurement audit risk indicators from outputs/rules.json, analytics.json and history.json on the council's own 5x5 scale. The agent writes cited judgments to outputs/risk-ratings.json; build_register.py resolves every citation and figure, computes scores, matrix labels and bands, and renders outputs/risk-register.md and the auditor-comments.md decision template. Use when building or revising the risk register.
---

# risk-assessment

The agent **judges**; `build_register.py` (next to this file) **computes and
checks**. You decide which risks the evidence supports, set a likelihood
signal and an impact level, write short justifications and cite the evidence.
You never type a figure, a score, a matrix label or a band: the builder fills
every number from `analytics.json` and works out every score from the
council's matrix in `history.json`. Everything you write describes a **risk
indicator to investigate**, never wrongdoing by the council, a department or
a supplier. You recommend scope; the auditor decides it.

## Inputs and outputs

| | Path |
| --- | --- |
| Rules | `outputs/rules.json` (cite as `[rule:CPR-14]`) |
| Analytics | `outputs/analytics.json` (cite as `[metric:$.tests.x.y]`, fill figures as `{{$.tests.x.y}}`) |
| History | `outputs/history.json` (cite as `[history:AO-12]`) |
| Auditor decisions | `outputs/auditor-comments.md` (read on a re-run only) |
| **You write** | `outputs/risk-ratings.json` |
| Builder writes | `outputs/risk-register.md`, `outputs/auditor-comments.md` (and `risk-register.draft.md` when a build fails) |

Run Python with the project venv: `.venv/Scripts/python.exe` (Windows) or
`.venv/bin/python`.

## Step 1: Read the evidence and learn the IDs

Stop and report if any input is missing or does not parse. Otherwise, with
small queries (never print a whole file):

- `analytics.json`: which tests ran (`$.tests`), which tiers were skipped
  (`$.skipped`), which threshold parameters are null (`$.null_parameters`),
  `$.contracts.caveat`, and the `top20` / `headline_general_procurement`
  shapes of the tests you will cite. List the exact paths you will use and
  check each resolves before you rely on it.
- `rules.json["rules"]`: find rule IDs by `clause` (for example clause 6.16,
  `Appendix B row B1`, `Appendix C row D`). Rule IDs can change if the rules
  are re-extracted: always look them up, never reuse an ID from memory.
- `history.json`: audit items (`AO-nn`, `FU-nn`) with their opinions, the
  scale items (`LS-nn` likelihood, `IS-nn` impact, `MX-nn`, `BD-nn`), the
  `discrepancies` and `gaps`. `scoring_method.status` says whether the council's
  method was found; if it was not, the builder uses the 1-5 Very low to Very
  high fallback and says so in the register header. You do not substitute one.

## Step 2: Choose the risks

Work through the theme table. Propose a risk only when the evidence supports
it; a theme with no rule, no metric and no history item is listed under
`excluded` with a one-line reason, not rated. Fewer risks with clean
citations beat many with thin ones. At most one risk per theme unless the
evidence splits clearly (say why).

| Theme | Rules to look for (by clause) | Analytics to look at | Caveats |
| --- | --- | --- | --- |
| `T01` Splitting and threshold avoidance | 6.16 (anti-avoidance); Appendix B bands | `threshold_clustering`, `split_purchases` | Report the general_procurement tag as the headline; periodic placement fees legitimately recur; a window is an indicator, not a split |
| `T02` Competition not evidenced for high-value suppliers | Appendix B rows B1, B2, C, D | `off_contract` (the unmatched group is the indicator); `high_value_suppliers` is the population list, context only | "No active notice" is a lead for the council's contract register, never evidence of off-contract spend; only suppliers at or above the quote threshold; near-matches are candidates, not matches; `high_value_suppliers` never counts as a second test |
| `T03` Spend after, or beyond, a contract notice | Appendix C rows D and E | `expired_notice_spend`, `spend_vs_award` | A newer contract may exist with no notice; award values may be estimates or maxima |
| `T04` Duplicate payments | the 30-day payment clause in section 10.7.9 | `duplicates` | The `different_time` tier is the higher signal; repeated rows identical in all columns are the `same_timestamp` tier |
| `T05` Exceptions and waivers not observable in the data | 7.2 to 7.5 | none: the payments data cannot show waivers | Rate on the rule and the gap; signal `unobservable` |
| `T06` Contract register and publication completeness | 5.2, 5.2.1, 10.4 | `contracts` and `matching` as **context only**: cite them in the justification, never in `signal_metrics` | notices are not a register; the thin year of notices is a context fact; signal `unobservable` |
| `T07` Care placements and direct payments | Appendix C row F | placement tag in `population.tags` and `high_value_suppliers.by_tag` | individually chosen placements are exempt from competition by row F; the control to look for is the record of reasons in the case notes, not a tender |
| `T08` Grants treated as contracts | none citable (clause 1.6.2 is in an excluded definition) | grant tag in `population.tags` and `high_value_suppliers.by_tag` | cite metrics; say the Rules treat a grant as a contract |
| `T09` Delegated approval and Key Decisions | Appendix A rows; the Key Decision paragraph (clause 4.3) | none for approvals | Appendix A and the Key Decision paragraph disagree: that is recorded in `rules.json["notes"]`, which cannot be cited by tag, so cite the rules themselves (the Appendix A rows and the Key Decision rule) and describe the disagreement in words; rate on the gap, signal `unobservable` |

Add nothing outside the table without saying why in `excluded`.

## Step 3: Rate

### 3a. Likelihood: the rubric

Likelihood is chosen by **evidence signal**, not by feel, so two runs on the
same evidence rate the same way. It is an evidence-based mapping onto the
council's 1-5 scale for audit planning, not a probability estimate. Choose
the **highest row whose conditions are all met**; the builder rejects a base
score that does not match the signal.

Definitions: the **headline** is the `general_procurement` tag. A **test** is
a key under `$.tests`. The **indicator is present** when an **indicator metric**
is above zero. Near-match **candidates** never count as an indicator.

An **indicator metric** is a count or £ of *flagged items* from one of six
tests: `threshold_clustering` (`band_count`, `by_tag.*`), `split_purchases`
(`windows`, `headline_general_procurement.*`, `by_tag.*`), `duplicates`
(a tier's `groups`, `rows`, `headline_general_procurement.*`, `by_tag.*`),
`off_contract` (the **unmatched** group only), `expired_notice_spend` and
`spend_vs_award` (their counts and `headline_general_procurement.*`). These
are **not** indicator metrics and never count toward a signal, even though you
may cite them as context in the text: `high_value_suppliers` (it is the
population list, not a flagged set), `off_contract` matched or candidate groups,
`suppliers_compared`, and the `population`, `contracts` and `matching`
sections. The builder rejects any `signal_metrics` path that is not an
indicator metric.

| Signal | Base | All conditions |
| --- | --- | --- |
| `none` | 1 | The relevant test ran and a cited headline indicator metric is zero; no gap in the data |
| `unobservable` | 2 | The control cannot be seen in the data (approvals, waivers, register completeness) **or** the relevant test was skipped; you cite the rule, `signal_metrics` stays empty, and context metrics may be cited in the text only |
| `outside_headline` | 2 | The indicator is present only in tags other than general_procurement (placement, grant, agency, premises); cite that metric |
| `headline_single` | 3 | The indicator is present in the headline in exactly one test |
| `headline_corroborated` | 4 | Present in the headline in two or more distinct tests |
| `headline_broad` | 5 | Present in the headline in three or more distinct tests |

Fields: `likelihood.signal` is the row name; `likelihood.score` is **always the
base for the signal** (never the figure after the uplift, which the builder adds
and shows as "rubric n + 1");
`likelihood.signal_metrics` lists the `$.paths` that prove it. Every path in
`signal_metrics` must also be cited as `[metric:...]` in the justification. For
a headline signal at least one path must contain `general_procurement`, and
the count of distinct `$.tests.<name>` with a value above zero must meet the
row. State the signal in words in the justification (for example "signal
headline_corroborated"); do not type numbers.

**Repeat-finding uplift.** If a prior audit in `history.json` gave an adverse
opinion on the same theme, likelihood goes up by one point (capped at 5), and
you say so explicitly. The council's papers do not rank opinions, so this
skill fixes the convention: **adverse** means the printed opinion or
implementation progress is `Limited Assurance`, `Weak`, `Unsatisfactory` or
`No Assurance`. Judge "same theme" from the audit title (for example an
accounts-payable audit for duplicate payments, a direct-payments audit for
T07). Cite the `AO-` or `FU-` item with `[history:ID]` in the likelihood
justification, put the same IDs in `repeat_finding.history_ids`, and include
the word "repeat" in the justification. An audit with `Reasonable Assurance`
or `Substantial Assurance` never triggers the uplift, and nothing ever
lowers a rating: favourable opinions are recorded, not scored.

### 3b. Impact

Use the council's impact table (`IS-01` to `IS-05`, Critical to Negligible),
the numbering in the table, not the prose sentence that numbers it
differently. Pick the **highest** of the financial, people, assets,
reputation and compliance descriptions that the cited evidence actually
demonstrates; if you cannot tell between two levels, take the lower and say
so. For the financial dimension, read the cited £ metric and the band in the
impact item side by side and do not compute anything. Your impact
justification **must cite its own scale item**, for example `[history:IS-03]`
for a score of 3; the builder fails an impact whose scale item is not cited.

### 3c. Writing

- **Statement**: one sentence naming the indicator, in indicator language
  ("payments ... together reach", "no active notice found"). No supplier,
  officer or department is named; no word such as fraud, illegal, breach.
- **Justifications**: one or two sentences each, with at least one
  resolvable citation each. A justification with no resolvable citation drops
  the whole risk.
- **Figures**: only `{{$.path}}` placeholders. Formats: `{{$.path|gbp0}}`
  for £ with no pence, `|gbp`, `|int`, `|dp1`, `|dp2`; by default a value
  under a key naming gbp, estimate, rate, value or amount shows as £. A
  placeholder must resolve to a single value.
- **Proposed focus**: begin "Recommend ...". It is a suggestion for the
  auditor, never a decision.

## Step 4: Write `outputs/risk-ratings.json`

```json
{
  "schema": 1,
  "generated_on": "YYYY-MM-DD",
  "risks": [
    {
      "id": "R-01",
      "theme": "T01",
      "statement": "Payments to one supplier inside a {{$.tests.split_purchases.parameters.window_days}}-day window that together reach {{$.quote_threshold|gbp0}}, each below it, are an indicator to test for splitting: {{$.tests.split_purchases.per_threshold[0].headline_general_procurement.count}} windows in general procurement.",
      "likelihood": {
        "score": 4,
        "signal": "headline_corroborated",
        "signal_metrics": ["$.tests.split_purchases.per_threshold[0].headline_general_procurement.count",
                           "$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count"],
        "justification": "Two independent tests show the indicator in the general procurement headline: [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.count] windows and [metric:$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count] payments just under the threshold; rule [rule:CPR-14] bars artificial splitting."
      },
      "impact": {
        "score": 3,
        "justification": "Medium on the council's scale [history:IS-03] (compliance); the Appendix B competition steps [rule:CPR-54] could be bypassed."
      },
      "repeat_finding": null,
      "proposed_focus": "Recommend testing the flagged windows against the written quotes held for each supplier, largest window first.",
      "sample_source": "outputs/analytics-full/split-purchases.csv"
    }
  ],
  "excluded": [ { "theme": "T05", "reason": "no metric and no history item; recorded as a gap, not rated" } ],
  "revision": null
}
```

A second example, with a repeat-finding uplift. The score stays at the base for
the signal (2, outside the headline); the builder adds the uplift and the
register shows 3:

```json
{
  "id": "R-07",
  "theme": "T07",
  "statement": "Care and education placement payments show repeated payments to one supplier in a window: {{$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count}} windows outside the general procurement headline.",
  "likelihood": {
    "score": 2,
    "signal": "outside_headline",
    "signal_metrics": ["$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count"],
    "justification": "The indicator is present only in the placement tag, signal outside_headline: [metric:$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count] windows. Repeat finding: a prior direct-payments audit gave an adverse opinion [history:AO-12], so the likelihood is raised one point."
  },
  "impact": {
    "score": 3,
    "justification": "Medium on the council's scale [history:IS-03]; the Rules require a record of the reasons for each placement choice [rule:CPR-63]."
  },
  "repeat_finding": {"applies": true, "history_ids": ["AO-12"], "note": "The direct-payments audit covers the same theme."},
  "proposed_focus": "Recommend testing a sample of placement payments for the case-note record of reasons for the choice of provider."
}
```

(The paths and IDs above are examples: look every one up in the current
inputs.) Rules for the file:

- `id` is `R-01`, `R-02`, ... and never reused for a different risk.
- `repeat_finding` is `null` or `{"applies": true, "history_ids": ["AO-12"],
  "note": "..."}`.
- `sample_source` (optional) points at a file under `outputs/analytics-full/`;
  it is the only place a supplier-level pointer belongs.
- `excluded` entries name a `theme` and a `reason`; after a rejection they also
  carry the risk's `id`.
- `revision` is `null` on a first run.

### Re-running after the auditor's gate

When `outputs/auditor-comments.md` holds decisions (Approve, Amend, Reject
with a Comment):

1. If every Decision cell is blank, this is a first run: build as usual.
2. **Approve**: leave the risk exactly as it is.
3. **Amend**: apply the change the Comment asks for and nothing else. If the
   auditor sets a level the evidence would not give, keep the auditor's level
   and add `"auditor_override": {"fields": ["likelihood"|"impact"], "note":
   "<the Comment, quoted>", "agent_rating": {"likelihood": n, "impact": n}}`
   to the risk. An overridden field is exempt from the rubric and the impact
   anchor, but its justification still needs a real citation (the comments
   file is not a citable source). An overridden likelihood is the final value:
   no uplift is added.
4. **Reject**: remove the risk from `risks` and add it to `excluded` with its
   `id`, its `theme` and the auditor's reason.
5. Add no new risk unless a Comment asks for one; if it does, list it as
   `added` and name the risk id of that Comment in the note.
6. Add the `revision` block: `{"number": N, "changes": [{"id": "R-03",
   "action": "amended" | "rejected" | "added", "note": "what changed and why"}]}`
   with `N` one more than the last revision, listing **every** risk that
   changed and no other. The builder fails if a decision is left unapplied, if
   a risk changed without a decision, or if the list does not match the
   difference. Never change a rating the auditor did not ask about, even if
   you would now rate it differently.

## Step 5: Build and validate

```
.venv/Scripts/python.exe .claude/skills/risk-assessment/build_register.py
```

Exit codes: `0` clean; `3` warnings only (files written); `1` failures
(only `outputs/risk-register.draft.md` is written, and the last clean
register and comments are left alone); `2` could not run. Run it until it
prints `PASS` with no failures and no warnings. Never edit the builder, the
register or the comments file to make it pass.

| Code | Means | Fix |
| --- | --- | --- |
| `E-SCHEMA` | missing or wrong field, bad id, unknown theme | correct the JSON |
| `E-NOCITE` | a justification has no resolvable citation; **the risk is dropped** | add a real citation or remove the risk |
| `E-CITE` | a tag points at a rule, path or history id that does not exist | look the reference up |
| `E-PLACEHOLDER` | a `{{...}}` does not resolve to one value; **the risk is dropped** | use a real scalar path |
| `E-RUBRIC` | base score does not match the signal, a `signal_metrics` path is not an indicator metric, or the metrics do not prove the signal | re-classify the signal honestly; use flagged-item metrics only |
| `E-REPEAT` | uplift without an adverse audit, or not cited and stated | cite the adverse audit or drop the uplift |
| `E-IMPACT` | the impact justification does not cite its own scale item | cite `[history:IS-n]` |
| `E-OVERRIDE`, `E-DECISION`, `E-REVISION`, `E-UNASKED`, `E-UNAPPLIED` | the revision does not match the auditor's decisions | make the JSON match the decisions |
| `E-SCALE` | the council's method in history.json is incomplete | stop and report |
| `W-FIGURE` | a figure is typed in prose | replace it with a placeholder |
| `W-LANGUAGE`, `W-NAME` | accusing wording or a supplier name | reword |

Fix a finding by correcting the citation, placeholder or wording to match the
evidence. Never clear one by weakening a claim, typing the figure, or deleting
a risk the evidence supports. If the evidence is not in the inputs, remove the
risk and list it as not rated.

What the builder does: resolves every citation and placeholder; computes the
score and matrix label from `MX-` items and the band from `BD-` items;
applies the uplift; marks overrides; checks the revision against the
decisions and the last register (kept inside the register as a comment); and
writes the "Auditor decisions" section and the decision template, keeping
decisions already recorded. **Conflicts in the council's method** are never
resolved silently: where the bands table and the escalation figure give
different scores for the Corporate Risk Register, the builder uses the bands
table, marks risks that meet only the other criterion with a double dagger (‡), and says so in the register header. Naming differences between the
matrix and the bands table are noted the same way.

## Step 6: Report

Under 400 words, from the builder's own output: how many risks and by band;
each risk dropped or not rated, with the reason; every note the builder put in
the header (conflicting threshold, naming difference, fallback scale, skipped
tiers); on a re-run, the revision's changes and any override. State
recommendations as recommendations. End with this request: **the auditor
should record a decision for each risk in `outputs/auditor-comments.md`
(Approve, Amend or Reject, with a Comment), then the risk-assessor will be
re-run to apply them.** Do not paste the register; point to the files.
