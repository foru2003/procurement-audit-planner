# Procurement audit risk register (risk indicators for the auditor)

Prepared for the auditor's approval gate. Every entry is a **risk indicator to investigate**, not a finding about the council, a department or a supplier. The assessor recommends; the auditor decides.

## Revision 2

This revision applies the auditor's decisions recorded in `outputs/auditor-comments.md`. What changed:

- Unchanged: R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-08, R-09.

## How this register was made

- Evidence: `analytics.json` generated 2026-10-13T00:18:03; `history.json` generated 2026-10-13; ratings file dated 2026-10-13.
- Every figure is read from `analytics.json`; every score, matrix label and band is computed by the builder from the scale below. The assessor chooses levels and cites evidence.
- Scale: the council's 5x5 matrix (Risk Management Strategy 2024-27, Tables 1, 2 and 4, Figure 1; history ids LS-01 to LS-05, IS-01 to IS-05, MX-01 to MX-05, BD-01 to BD-04). Likelihood: 1 Rare, 2 Unlikely, 3 Likely, 4 Almost Certain, 5 Certain. Impact: 1 Negligible, 2 Minor, 3 Medium, 4 Major, 5 Critical.
- Bands: Extreme (Red) = 15 -25; Medium High (Amber) = 8-12; Moderate = 4 - 6; Low (Green) = Up to 3.
- **CONFLICT IN THE COUNCIL'S SCORING METHOD: Table 4 (BD-01) sends scores 15 and above to the Corporate Risk Register; the escalation figure (OR-05) lists risks that score 9 or above. This register USES the Table 4 band (15 and above) for bands and escalation, and MARKS (‡) any risk that meets only the other criterion (score 9 to 14). It is not resolved here; the papers' own discrepancy record is DI-04.**
- **NAMING: the matrix labels some cells 'High' where the bands table names the band 'Medium High'. Both are shown; the band name comes from the bands table.**
- Skipped analysis tiers: 10, because threshold_goods_services, threshold_works_concession, threshold_light_touch have no value in the Contract Rules (a threshold the PDF only names). Risks that depend on them are rated on what did run.
- Notices caveat: contracts.csv holds published notices, not a contract register. It holds awards published on Contracts Finder in roughly the last five years. A contract awarded earlier (e.g. long-running waste or highways contracts), one advertised only on Find a Tender, a framework call-off recorded under another buyer, or an exempt placement will have no notice here. "No notice found" is therefore an indicator to check against the council's contract register, never evidence of off-contract spend.

## Summary

9 risks rated: 5 Medium High, 4 Moderate.

| ID | Theme | Risk | Rating | Likelihood | Impact | CRR |
|---|---|---|---|---|---|---|
| R-01 | Splitting and threshold avoidance | Payments to one supplier inside a 30-day window that together reach £25,000, each below it, and payments just under that threshold are indicators to test for splitting: 62 windows and 10 near-threshold payments in general procurement. | L4 × I3 = 12 · High · Medium High (Amber) | 4 Almost Certain | 3 Medium | ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above) |
| R-02 | Competition not evidenced for high-value suppliers | 181 general procurement suppliers at or above the £25,000 quote threshold show no active notice found in the published-notice export; this is a lead to check against the council's contract register. | L3 × I3 = 9 · High · Medium High (Amber) | 3 Likely | 3 Medium | ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above) |
| R-03 | Spend after, or beyond, a contract notice | 8 general procurement suppliers were paid in the window with every matching notice ended before it, and 8 show annualised spend at or above the flagged multiple of the notice award rate; a newer contract may exist with no notice. | L4 × I3 = 12 · High · Medium High (Amber) | 4 Almost Certain | 3 Medium | ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above) |
| R-04 | Duplicate payments | 37 groups of general procurement payments with the same supplier and amount at different times are an indicator to test for duplicate payment. | L3 × I3 = 9 · High · Medium High (Amber) | 3 Likely | 3 Medium | ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above) |
| R-05 | Exceptions and waivers not observable in the data | Exceptions to and waivers of competition cannot be observed in the payments data, so the control is not tested by any analytic. | L2 × I2 = 4 · Moderate · Moderate | 2 Unlikely | 2 Minor |  |
| R-06 | Contract register and publication completeness | Completeness of the contract register and of tender and award publication cannot be confirmed from the data: only a notice export is held, with no register present. | L2 × I2 = 4 · Moderate · Moderate | 2 Unlikely | 2 Minor |  |
| R-07 | Care placements and direct payments | Care and education placement payments show repeated payments to one supplier in a window and same-amount groups at different times, outside the general procurement headline: 180 windows and 211 groups. | L3 × I3 = 9 · High · Medium High (Amber) | 3 Likely | 3 Medium | ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above) |
| R-08 | Grants treated as contracts | Grant-tagged payments sit outside the general procurement headline: 123 grant suppliers at or above the quote threshold show no active notice found; the Rules treat a grant as a contract. | L2 × I2 = 4 · Moderate · Moderate | 2 Unlikely | 2 Minor |  |
| R-09 | Delegated approval and Key Decisions | Delegated approvals and Key Decision treatment cannot be observed in the payments data, and the printed clauses do not align on where the Key Decision applies. | L3 × I2 = 6 · Moderate · Moderate | 3 Likely | 2 Minor |  |

### R-01 · Payments to one supplier inside a 30-day window that together reach £25,000, each below it, and payments just under that threshold are indicators to test for splitting: 62 windows and 10 near-threshold payments in general procurement.

**Rating:** L4 × I3 = 12 · High · Medium High (Amber)

**Corporate Risk Register:** ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above)

- **Likelihood 4 Almost Certain.** Signal headline_corroborated: two tests show the indicator in the general procurement headline, [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.count] windows and [metric:$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count] payments just under the threshold; rule [rule:CPR-14] bars artificial splitting.
- **Impact 3 Medium.** Medium on the council's scale [history:IS-03] (compliance): the quote steps of [rule:CPR-54] could be bypassed for the flagged windows, which together reach [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.gbp]; the windows total payments, not a loss, so the lower level is taken.
- **Evidence:**
  - metric $.tests.split_purchases.per_threshold[0].headline_general_procurement.count = 62
  - metric $.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count = 10
  - rule CPR-14 · clause 6.16 · no artificial splitting or disaggregation of a contract to avoid Procurement Legislation or these Rules
  - history IS-03 · Medium
  - rule CPR-54 · clause Appendix B row B1 · invitations to quote via the Procurement Portal to at least three sources incl. an SME/VCSE and a local supplier; contract notice on the CDP
  - metric $.tests.split_purchases.per_threshold[0].headline_general_procurement.gbp = £3,333,218.21
  - sample pointer: outputs/analytics-full/split-purchases.csv
- **Proposed focus (recommendation, for the auditor to decide):** Recommend testing the flagged windows against the written quotes held for each supplier, largest window first.

### R-02 · 181 general procurement suppliers at or above the £25,000 quote threshold show no active notice found in the published-notice export; this is a lead to check against the council's contract register.

**Rating:** L3 × I3 = 9 · High · Medium High (Amber)

**Corporate Risk Register:** ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above)

- **Likelihood 3 Likely.** Signal headline_single: one test, off_contract, shows the indicator in the headline, [metric:$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count] suppliers with no active notice found; the population list [metric:$.tests.high_value_suppliers.headline_general_procurement.count] is context only, and the notice export is not a register so this is a lead, rule [rule:CPR-54].
- **Impact 3 Medium.** Medium on the council's scale [history:IS-03] (compliance): the Appendix B competition steps [rule:CPR-54] are not evidenced in the data for these suppliers; the notice export is incomplete by design (see [metric:$.contracts.register_present]), so the lower level is taken.
- **Evidence:**
  - metric $.tests.off_contract.groups.unmatched.by_tag.general_procurement.count = 181
  - metric $.tests.high_value_suppliers.headline_general_procurement.count = 223
  - rule CPR-54 · clause Appendix B row B1 · invitations to quote via the Procurement Portal to at least three sources incl. an SME/VCSE and a local supplier; contract notice on the CDP
  - history IS-03 · Medium
  - metric $.contracts.register_present = no
  - sample pointer: outputs/analytics-full/off-contract.csv
- **Proposed focus (recommendation, for the auditor to decide):** Recommend checking the largest unmatched suppliers against the council's contract register and the quote or tender file before any further testing.

### R-03 · 8 general procurement suppliers were paid in the window with every matching notice ended before it, and 8 show annualised spend at or above the flagged multiple of the notice award rate; a newer contract may exist with no notice.

**Rating:** L4 × I3 = 12 · High · Medium High (Amber)

**Corporate Risk Register:** ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above)

- **Likelihood 4 Almost Certain.** Signal headline_corroborated: two tests show the indicator in the headline, [metric:$.tests.expired_notice_spend.headline_general_procurement.count] suppliers after notice end and [metric:$.tests.spend_vs_award.headline_general_procurement.count] above the award rate; rules [rule:CPR-61] and [rule:CPR-62] set the approvals for extensions and variations.
- **Impact 3 Medium.** Medium on the council's scale [history:IS-03] (compliance): extension and variation approvals [rule:CPR-61] [rule:CPR-62] are not observable here; the annualised estimate of [metric:$.tests.spend_vs_award.headline_general_procurement.annualised_estimate_gbp] is an estimate and award values may be maxima, so the lower level is taken.
- **Evidence:**
  - metric $.tests.expired_notice_spend.headline_general_procurement.count = 8
  - metric $.tests.spend_vs_award.headline_general_procurement.count = 8
  - rule CPR-61 · clause Appendix C row D · approval of the S151 Officer
  - rule CPR-62 · clause Appendix C row E · below the Threshold prior written approval of Monitoring Officer and S151 Officer; above it approval of the relevant board
  - history IS-03 · Medium
  - metric $.tests.spend_vs_award.headline_general_procurement.annualised_estimate_gbp = £2,946,603.88
- **Proposed focus (recommendation, for the auditor to decide):** Recommend asking for the contract file, extension approval and variation record for the flagged suppliers, largest first.

### R-04 · 37 groups of general procurement payments with the same supplier and amount at different times are an indicator to test for duplicate payment.

**Rating:** L3 × I3 = 9 · High · Medium High (Amber)

**Corporate Risk Register:** ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above)

- **Likelihood 3 Likely.** Signal headline_single: one test, duplicates, shows the indicator in the headline; the higher-signal different-time tier has [metric:$.tests.duplicates.tiers.different_time.headline_general_procurement.groups] groups, set against the payment-timing clause [rule:CPR-39]. The prior accounts payable audit [history:AO-11] has a Reasonable Assurance opinion, so no repeat uplift applies.
- **Impact 3 Medium.** Medium on the council's scale [history:IS-03] (financial): the amount beyond the first payment in these groups is [metric:$.tests.duplicates.tiers.different_time.headline_general_procurement.gbp_beyond_first]; repeated rows can be legitimate recurring charges.
- **Evidence:**
  - metric $.tests.duplicates.tiers.different_time.headline_general_procurement.groups = 37
  - rule CPR-39 · clause 10.7.9.1 · payment due from the Council made within 30 days of a valid, undisputed invoice
  - history AO-11 · Accounts Payable · Reasonable Assurance
  - history IS-03 · Medium
  - metric $.tests.duplicates.tiers.different_time.headline_general_procurement.gbp_beyond_first = £297,355.44
- **Proposed focus (recommendation, for the auditor to decide):** Recommend testing the different-time groups against invoices and remittances, largest value first.

### R-05 · Exceptions to and waivers of competition cannot be observed in the payments data, so the control is not tested by any analytic.

**Rating:** L2 × I2 = 4 · Moderate · Moderate

- **Likelihood 2 Unlikely.** Signal unobservable: the payments data cannot show waivers; rules [rule:CPR-20] and [rule:CPR-26] require them to be limited to listed circumstances and fully documented.
- **Impact 2 Minor.** Minor on the council's scale [history:IS-04] (compliance): no flagged amount ties to waivers, so the impact cannot be shown above the lower level; see [rule:CPR-26].
- **Evidence:**
  - rule CPR-20 · clause 7.2 · competitive process may be excepted or waived only in the circumstances listed in 7.2.1 and 7.2.2, subject to 7.4
  - rule CPR-26 · clause 7.5 · fully document it
  - history IS-04 · Minor
- **Proposed focus (recommendation, for the auditor to decide):** Recommend requesting the register of exceptions and waivers and testing a sample for the documentation the rules require.

### R-06 · Completeness of the contract register and of tender and award publication cannot be confirmed from the data: only a notice export is held, with no register present.

**Rating:** L2 × I2 = 4 · Moderate · Moderate

- **Likelihood 2 Unlikely.** Signal unobservable: register completeness cannot be seen in the payments data; rules [rule:CPR-35] and [rule:CPR-07] require award recording and publication, and context [metric:$.contracts.register_present] shows no register was supplied.
- **Impact 2 Minor.** Minor on the council's scale [history:IS-04] (compliance): an incomplete register weakens other checks but no loss is shown; see [rule:CPR-35].
- **Evidence:**
  - rule CPR-35 · clause 10.4 · Service Director notifies the Service Lead for Commissioning and Procurement so it is recorded on the Council Contract Register
  - rule CPR-07 · clause 5.2 · publish details of every invitation to tender
  - metric $.contracts.register_present = no
  - history IS-04 · Minor
- **Proposed focus (recommendation, for the auditor to decide):** Recommend obtaining the council's contract register and comparing it with the notice export.

### R-07 · Care and education placement payments show repeated payments to one supplier in a window and same-amount groups at different times, outside the general procurement headline: 180 windows and 211 groups.

**Rating:** L3 × I3 = 9 · High · Medium High (Amber)

**Corporate Risk Register:** ‡ meets only the escalation-figure criterion (score 9 or above), not Table 4 (15 or above)

- **Likelihood 3 Likely (rubric 2 + 1 repeat-finding uplift).** Signal outside_headline: the indicator is in the placement tag, [metric:$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count] windows and [metric:$.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups] groups. Repeat finding: the direct payments audit [history:AO-12] gave a Limited Assurance opinion, so the likelihood is raised one point; recurring placement charges can be legitimate.
- **Repeat finding:** The direct payments audit covers the same theme and gave a Limited Assurance opinion. (AO-12)
- **Impact 3 Medium.** Medium on the council's scale [history:IS-03] (compliance): [rule:CPR-63] exempts individual placements from competition but requires a record of the reasons for the choice of provider; the case notes are not in the data.
- **Evidence:**
  - metric $.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count = 180
  - metric $.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups = 211
  - history AO-12 · Personal Budgets (Direct Payments) · Limited Assurance
  - history IS-03 · Medium
  - rule CPR-63 · clause Appendix C row F · Service Director keeps a record of the reasons for the choice of provider in the individual's case notes
- **Proposed focus (recommendation, for the auditor to decide):** Recommend testing a sample of placement payments for the case-note record of reasons for the choice of provider.

### R-08 · Grant-tagged payments sit outside the general procurement headline: 123 grant suppliers at or above the quote threshold show no active notice found; the Rules treat a grant as a contract.

**Rating:** L2 × I2 = 4 · Moderate · Moderate

- **Likelihood 2 Unlikely.** Signal outside_headline: the grant tag shows [metric:$.tests.off_contract.groups.unmatched.by_tag.grant.count] suppliers with no active notice found and [metric:$.tests.split_purchases.per_threshold[0].by_tag.grant.count] repeated-payment windows; a grant may be properly outside competition, so this is a lead only.
- **Impact 2 Minor.** Minor on the council's scale [history:IS-04] (compliance): the exposure of [metric:$.tests.split_purchases.per_threshold[0].by_tag.grant.gbp] in windows is small, and Minor cannot be told from Medium without the grant terms, so the lower level is taken.
- **Evidence:**
  - metric $.tests.off_contract.groups.unmatched.by_tag.grant.count = 123
  - metric $.tests.split_purchases.per_threshold[0].by_tag.grant.count = 6
  - history IS-04 · Minor
  - metric $.tests.split_purchases.per_threshold[0].by_tag.grant.gbp = £184,106.50
- **Proposed focus (recommendation, for the auditor to decide):** Recommend asking how grants are classified and approved, and testing a sample against the grant conditions.

### R-09 · Delegated approvals and Key Decision treatment cannot be observed in the payments data, and the printed clauses do not align on where the Key Decision applies.

**Rating:** L3 × I2 = 6 · Moderate · Moderate  ⚑ auditor override

- **Likelihood 3 Likely (auditor-set).** Signal unobservable: approvals are not in the payments data; the Key Decision paragraph [rule:CPR-04] makes every award over its stated value a Key Decision, while the Appendix A rows [rule:CPR-51] and [rule:CPR-52] attach Key Decision wording to a higher band only.
- **Impact 2 Minor.** Minor on the council's scale [history:IS-04] (compliance): the disagreement between [rule:CPR-04] and [rule:CPR-52] is a clarity gap, and no flagged amount is tied to it.
- **Auditor override (likelihood):** Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes. The assessor's own rating was likelihood 2, impact 2.
- **Evidence:**
  - rule CPR-04 · clause 4.3 · treat the award as a Key Decision of the Council
  - rule CPR-51 · clause Appendix A row 3 · Service Director, after S151 and Monitoring Officer recommendation, with a written report approved by the relevant board
  - rule CPR-52 · clause Appendix A row 4 · Key Decision; Executive approval above 2.5million, with a board-approved written report
  - history IS-04 · Minor
- **Proposed focus (recommendation, for the auditor to decide):** Recommend asking the council which clause it applies and sampling large awards for the approval route used.

## Auditor decisions

| Risk | Decision | Comment | Applied in revision | Effect |
|---|---|---|---|---|
| R-01 | Approve | Recorded 2026-10-13. | 1 | unchanged |
| R-02 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-03 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-04 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-05 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-06 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-07 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-08 | Approve | Recorded 2026-10-13. | 2 | unchanged |
| R-09 | Amend | Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes. Recorded 2026-10-13. | 1 | unchanged |

Decisions are the auditor's; the assessor only applies them.

<!-- build_register:state {"revision":2,"applied":{"R\u002d01":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":1},"R\u002d09":{"decision":"amend","comment":"Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes. Recorded 2026\u002d10\u002d13.","revision":1},"R\u002d02":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d03":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d04":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d05":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d06":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d07":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2},"R\u002d08":{"decision":"approve","comment":"Recorded 2026\u002d10\u002d13.","revision":2}},"risks":{"R\u002d01":{"id":"R\u002d01","theme":"T01","statement":"Payments to one supplier inside a {{$.tests.split_purchases.parameters.window_days}}\u002dday window that together reach {{$.quote_threshold|gbp0}}, each below it, and payments just under that threshold are indicators to test for splitting: {{$.tests.split_purchases.per_threshold[0].headline_general_procurement.count}} windows and {{$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count}} near\u002dthreshold payments in general procurement.","likelihood":{"score":4,"signal":"headline_corroborated","signal_metrics":["$.tests.split_purchases.per_threshold[0].headline_general_procurement.count","$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count"],"justification":"Signal headline_corroborated: two tests show the indicator in the general procurement headline, [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.count] windows and [metric:$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count] payments just under the threshold; rule [rule:CPR\u002d14] bars artificial splitting."},"impact":{"score":3,"justification":"Medium on the council's scale [history:IS\u002d03] (compliance): the quote steps of [rule:CPR\u002d54] could be bypassed for the flagged windows, which together reach [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.gbp]; the windows total payments, not a loss, so the lower level is taken."},"repeat_finding":null,"proposed_focus":"Recommend testing the flagged windows against the written quotes held for each supplier, largest window first.","sample_source":"outputs/analytics\u002dfull/split\u002dpurchases.csv"},"R\u002d02":{"id":"R\u002d02","theme":"T02","statement":"{{$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count}} general procurement suppliers at or above the {{$.quote_threshold|gbp0}} quote threshold show no active notice found in the published\u002dnotice export; this is a lead to check against the council's contract register.","likelihood":{"score":3,"signal":"headline_single","signal_metrics":["$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count"],"justification":"Signal headline_single: one test, off_contract, shows the indicator in the headline, [metric:$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count] suppliers with no active notice found; the population list [metric:$.tests.high_value_suppliers.headline_general_procurement.count] is context only, and the notice export is not a register so this is a lead, rule [rule:CPR\u002d54]."},"impact":{"score":3,"justification":"Medium on the council's scale [history:IS\u002d03] (compliance): the Appendix B competition steps [rule:CPR\u002d54] are not evidenced in the data for these suppliers; the notice export is incomplete by design (see [metric:$.contracts.register_present]), so the lower level is taken."},"repeat_finding":null,"proposed_focus":"Recommend checking the largest unmatched suppliers against the council's contract register and the quote or tender file before any further testing.","sample_source":"outputs/analytics\u002dfull/off\u002dcontract.csv"},"R\u002d03":{"id":"R\u002d03","theme":"T03","statement":"{{$.tests.expired_notice_spend.headline_general_procurement.count}} general procurement suppliers were paid in the window with every matching notice ended before it, and {{$.tests.spend_vs_award.headline_general_procurement.count}} show annualised spend at or above the flagged multiple of the notice award rate; a newer contract may exist with no notice.","likelihood":{"score":4,"signal":"headline_corroborated","signal_metrics":["$.tests.expired_notice_spend.headline_general_procurement.count","$.tests.spend_vs_award.headline_general_procurement.count"],"justification":"Signal headline_corroborated: two tests show the indicator in the headline, [metric:$.tests.expired_notice_spend.headline_general_procurement.count] suppliers after notice end and [metric:$.tests.spend_vs_award.headline_general_procurement.count] above the award rate; rules [rule:CPR\u002d61] and [rule:CPR\u002d62] set the approvals for extensions and variations."},"impact":{"score":3,"justification":"Medium on the council's scale [history:IS\u002d03] (compliance): extension and variation approvals [rule:CPR\u002d61] [rule:CPR\u002d62] are not observable here; the annualised estimate of [metric:$.tests.spend_vs_award.headline_general_procurement.annualised_estimate_gbp] is an estimate and award values may be maxima, so the lower level is taken."},"repeat_finding":null,"proposed_focus":"Recommend asking for the contract file, extension approval and variation record for the flagged suppliers, largest first.","sample_source":null},"R\u002d04":{"id":"R\u002d04","theme":"T04","statement":"{{$.tests.duplicates.tiers.different_time.headline_general_procurement.groups}} groups of general procurement payments with the same supplier and amount at different times are an indicator to test for duplicate payment.","likelihood":{"score":3,"signal":"headline_single","signal_metrics":["$.tests.duplicates.tiers.different_time.headline_general_procurement.groups"],"justification":"Signal headline_single: one test, duplicates, shows the indicator in the headline; the higher\u002dsignal different\u002dtime tier has [metric:$.tests.duplicates.tiers.different_time.headline_general_procurement.groups] groups, set against the payment\u002dtiming clause [rule:CPR\u002d39]. The prior accounts payable audit [history:AO\u002d11] has a Reasonable Assurance opinion, so no repeat uplift applies."},"impact":{"score":3,"justification":"Medium on the council's scale [history:IS\u002d03] (financial): the amount beyond the first payment in these groups is [metric:$.tests.duplicates.tiers.different_time.headline_general_procurement.gbp_beyond_first]; repeated rows can be legitimate recurring charges."},"repeat_finding":null,"proposed_focus":"Recommend testing the different\u002dtime groups against invoices and remittances, largest value first.","sample_source":null},"R\u002d05":{"id":"R\u002d05","theme":"T05","statement":"Exceptions to and waivers of competition cannot be observed in the payments data, so the control is not tested by any analytic.","likelihood":{"score":2,"signal":"unobservable","signal_metrics":[],"justification":"Signal unobservable: the payments data cannot show waivers; rules [rule:CPR\u002d20] and [rule:CPR\u002d26] require them to be limited to listed circumstances and fully documented."},"impact":{"score":2,"justification":"Minor on the council's scale [history:IS\u002d04] (compliance): no flagged amount ties to waivers, so the impact cannot be shown above the lower level; see [rule:CPR\u002d26]."},"repeat_finding":null,"proposed_focus":"Recommend requesting the register of exceptions and waivers and testing a sample for the documentation the rules require.","sample_source":null},"R\u002d06":{"id":"R\u002d06","theme":"T06","statement":"Completeness of the contract register and of tender and award publication cannot be confirmed from the data: only a notice export is held, with no register present.","likelihood":{"score":2,"signal":"unobservable","signal_metrics":[],"justification":"Signal unobservable: register completeness cannot be seen in the payments data; rules [rule:CPR\u002d35] and [rule:CPR\u002d07] require award recording and publication, and context [metric:$.contracts.register_present] shows no register was supplied."},"impact":{"score":2,"justification":"Minor on the council's scale [history:IS\u002d04] (compliance): an incomplete register weakens other checks but no loss is shown; see [rule:CPR\u002d35]."},"repeat_finding":null,"proposed_focus":"Recommend obtaining the council's contract register and comparing it with the notice export.","sample_source":null},"R\u002d07":{"id":"R\u002d07","theme":"T07","statement":"Care and education placement payments show repeated payments to one supplier in a window and same\u002damount groups at different times, outside the general procurement headline: {{$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count}} windows and {{$.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups}} groups.","likelihood":{"score":2,"signal":"outside_headline","signal_metrics":["$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count","$.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups"],"justification":"Signal outside_headline: the indicator is in the placement tag, [metric:$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count] windows and [metric:$.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups] groups. Repeat finding: the direct payments audit [history:AO\u002d12] gave a Limited Assurance opinion, so the likelihood is raised one point; recurring placement charges can be legitimate."},"impact":{"score":3,"justification":"Medium on the council's scale [history:IS\u002d03] (compliance): [rule:CPR\u002d63] exempts individual placements from competition but requires a record of the reasons for the choice of provider; the case notes are not in the data."},"repeat_finding":{"applies":true,"history_ids":["AO\u002d12"],"note":"The direct payments audit covers the same theme and gave a Limited Assurance opinion."},"proposed_focus":"Recommend testing a sample of placement payments for the case\u002dnote record of reasons for the choice of provider.","sample_source":null},"R\u002d08":{"id":"R\u002d08","theme":"T08","statement":"Grant\u002dtagged payments sit outside the general procurement headline: {{$.tests.off_contract.groups.unmatched.by_tag.grant.count}} grant suppliers at or above the quote threshold show no active notice found; the Rules treat a grant as a contract.","likelihood":{"score":2,"signal":"outside_headline","signal_metrics":["$.tests.off_contract.groups.unmatched.by_tag.grant.count","$.tests.split_purchases.per_threshold[0].by_tag.grant.count"],"justification":"Signal outside_headline: the grant tag shows [metric:$.tests.off_contract.groups.unmatched.by_tag.grant.count] suppliers with no active notice found and [metric:$.tests.split_purchases.per_threshold[0].by_tag.grant.count] repeated\u002dpayment windows; a grant may be properly outside competition, so this is a lead only."},"impact":{"score":2,"justification":"Minor on the council's scale [history:IS\u002d04] (compliance): the exposure of [metric:$.tests.split_purchases.per_threshold[0].by_tag.grant.gbp] in windows is small, and Minor cannot be told from Medium without the grant terms, so the lower level is taken."},"repeat_finding":null,"proposed_focus":"Recommend asking how grants are classified and approved, and testing a sample against the grant conditions.","sample_source":null},"R\u002d09":{"id":"R\u002d09","theme":"T09","statement":"Delegated approvals and Key Decision treatment cannot be observed in the payments data, and the printed clauses do not align on where the Key Decision applies.","likelihood":{"score":3,"signal":"unobservable","signal_metrics":[],"justification":"Signal unobservable: approvals are not in the payments data; the Key Decision paragraph [rule:CPR\u002d04] makes every award over its stated value a Key Decision, while the Appendix A rows [rule:CPR\u002d51] and [rule:CPR\u002d52] attach Key Decision wording to a higher band only."},"impact":{"score":2,"justification":"Minor on the council's scale [history:IS\u002d04] (compliance): the disagreement between [rule:CPR\u002d04] and [rule:CPR\u002d52] is a clarity gap, and no flagged amount is tied to it."},"repeat_finding":null,"proposed_focus":"Recommend asking the council which clause it applies and sampling large awards for the approval route used.","sample_source":null,"auditor_override":{"fields":["likelihood"],"note":"Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes.","agent_rating":{"likelihood":2,"impact":2}}}}} -->
