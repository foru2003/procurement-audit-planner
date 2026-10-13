# Procurement audit: planning memo

*Generated 2026-10-13 by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision 2), `auditor-comments.md`, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review and auditor sign-off.*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

## Purpose

This plan sets out how the audit will test the nine procurement risk indicators the auditor approved, so that fieldwork can start from the Rules and from patterns in the payments data rather than from a random sample.

## Background

8,527 payments across 3 months were tested against the Contract Procedure Rules [metric:$.population.rows_after_exclusions].
The analysis flags indicators to investigate. None of them is a finding, and none characterises an officer, a department or a supplier.

## Scope

The register lists 9 rated risks. The auditor recorded 9 decisions: 9 risks are approved and in scope, and 0 are not.

| ID | Risk | Score | Band | Decision | Auditor comment |
|---|---|---|---|---|---|
| R-01 | Payments to one supplier inside a 30-day window that together reach £25,000, each below it, and payments just under tha… | 12 | Medium High (Amber) | approve | Recorded 2026-10-13. |
| R-02 | 181 general procurement suppliers at or above the £25,000 quote threshold show no active notice found in the published-… | 9 | Medium High (Amber) | approve | Recorded 2026-10-13. |
| R-03 | 8 general procurement suppliers were paid in the window with every matching notice ended before it, and 8 show annualis… | 12 | Medium High (Amber) | approve | Recorded 2026-10-13. |
| R-04 | 37 groups of general procurement payments with the same supplier and amount at different times are an indicator to test… | 9 | Medium High (Amber) | approve | Recorded 2026-10-13. |
| R-05 | Exceptions to and waivers of competition cannot be observed in the payments data, so the control is not tested by any a… | 4 | Moderate | approve | Recorded 2026-10-13. |
| R-06 | Completeness of the contract register and of tender and award publication cannot be confirmed from the data: only a not… | 4 | Moderate | approve | Recorded 2026-10-13. |
| R-07 | Care and education placement payments show repeated payments to one supplier in a window and same-amount groups at diff… | 9 | Medium High (Amber) | approve | Recorded 2026-10-13. |
| R-08 | Grant-tagged payments sit outside the general procurement headline: 123 grant suppliers at or above the quote threshold… | 4 | Moderate | approve | Recorded 2026-10-13. |
| R-09 | Delegated approvals and Key Decision treatment cannot be observed in the payments data, and the printed clauses do not… | 6 | Moderate | amend | Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes. Recorded 2026-10-13. (auditor override applied) |

## Approach

Risks were identified from the Rules and the payments analysis, rated on the council's own 5x5 scale, and approved by the auditor, who set the likelihood of one risk.
For each approved risk the plan names the control the Rules require, a test step, the evidence to inspect and a targeted sample. Samples are drawn by code from the flagged lists, with larger samples for higher scores.
Risks that cannot be seen in the payments data (exceptions, register completeness, approvals) are tested by document request, with no transaction sample.

The programme holds 17 expected controls and 19 test steps, with 289 sampled transactions worth £16,742,264.39, each traceable to its row in the council's published workbooks (see `audit-program.md` and `outputs/samples/`).

## Rules coverage

42 of 64 rules in `rules.json` are cited by a risk, a control or a test. The remaining 22 are not tested in this audit, for these reasons:

- tender-process steps (suitability, tender receipt and opening, late tenders) sit in procurement files, not the payments data, and no approved risk covers formal tenders: CPR-10, CPR-15, CPR-16, CPR-17
- definition, scope or advice clause, not a control that can be tested here: CPR-01, CPR-29, CPR-57
- documentation of procedure progress kept after award, outside the approved risks and not observable in the spend data: CPR-32
- contract form, standard clauses, bonds, insurance, sealing and Counsel instruction: legal formalities not visible in payments and not tied to an approved risk; candidates for a later audit: CPR-34, CPR-36, CPR-37, CPR-38, CPR-40, CPR-41, CPR-42, CPR-43, CPR-44, CPR-45, CPR-46, CPR-47, CPR-48, CPR-49

## Limitations

- Contracts.csv holds published notices, not a contract register, so no notice found is a lead to check against the register and never evidence of off-contract spend.
- Some tiers could not be run because the Rules name a threshold without giving its value. Tests therefore use the thresholds the Rules do state.
- Recurring charges, care placements and grants can be legitimate; fieldwork must establish the facts before any conclusion is drawn.

## Review and sign-off

The challenger's points and their status are in `challenges.md`; points marked *for the auditor* need a decision at sign-off. The QA reviewer's checks and verdict are in `review.md`, which ends with the sign-off block.
