# Audit program

*Generated 2026-10-13 by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision 2), `auditor-comments.md`, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review and auditor sign-off.*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

9 risks in scope, 17 controls, 19 tests, 289 sampled transactions. Samples are drawn by the builder from `analytics-full/` by the recipe stated under each test, and every transaction is listed with its workbook row.


## R-01: Payments to one supplier inside a 30-day window that together reach £25,000, each below it, and payments just… [12 (High; Medium High (Amber))]

**Audit objective.** Conclude whether requirements are treated as one purchase and quotes obtained at the right level, or whether repeated payments just under a threshold indicate avoidance of the quote steps.

**C-01.1. Expected control.** Contracts are not artificially split or disaggregated to avoid the Rules, and total value is estimated over the full potential duration. [CPR-14, CPR-13] Owner: Service Director.

**T-01.1. Test.** For each sampled window, obtain the orders, quotes and requisitions and confirm whether the payments belong to one requirement; compare dates and scope. A pass is a documented reason the orders are separate. [CPR-14, metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.count]  
**Evidence to inspect:** Purchase orders, requisitions, quotations, any contract register entry  
**Sample:** 10 items from `split-purchases.csv`, where dominant_tag = general_procurement, threshold = 25000, largest window_total first, largest 5 payments per item; 48 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2185` | 2026-05-20 | VolkerHighways Ltd | £19,420.72 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:723` | 2026-05-05 | VolkerHighways Ltd | £18,033.36 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:701` | 2026-05-12 | VolkerHighways Ltd | £17,896.87 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2179` | 2026-05-19 | VolkerHighways Ltd | £17,882.35 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2178` | 2026-05-05 | VolkerHighways Ltd | £16,916.01 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3184` | 2026-07-13 | VolkerHighways Ltd | £17,882.35 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3185` | 2026-07-16 | VolkerHighways Ltd | £17,882.35 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:822` | 2026-07-15 | VolkerHighways Ltd | £14,660.85 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3211` | 2026-07-15 | VolkerHighways Ltd | £14,141.01 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:621` | 2026-07-13 | VolkerHighways Ltd | £13,855.87 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:13` | 2026-06-01 | The Better Group Ltd | £24,088.98 | Children's Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:2397` | 2026-06-01 | The Better Group Ltd | £22,361.26 | Adult Social Care |
| 3 | `Over500_2026_P02_-_published.xlsx:9` | 2026-05-28 | The Better Group Ltd | £20,457.43 | Adult Social Care |
| 3 | `Over500_2026_P02_-_published.xlsx:10` | 2026-05-28 | The Better Group Ltd | £19,605.14 | Children's Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:2396` | 2026-06-01 | The Better Group Ltd | £18,039.18 | Adult Social Care |
| 4 | `Over500_2026_P03_-_published.xlsx:269` | 2026-06-12 | Newbury & District Ltd | £14,852.00 | Environment |
| 4 | `Over500_2026_P03_-_published.xlsx:268` | 2026-06-01 | Newbury & District Ltd | £13,826.61 | Environment |
| 4 | `Over500_2026_P03_-_published.xlsx:274` | 2026-06-30 | Newbury & District Ltd | £13,663.85 | Environment |
| 4 | `Over500_2026_P03_-_published.xlsx:171` | 2026-06-02 | Newbury & District Ltd | £10,529.33 | Education & SEND |
| 4 | `Over500_2026_P03_-_published.xlsx:336` | 2026-06-02 | Newbury & District Ltd | £9,861.00 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:450` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,615.23 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:452` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,483.38 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:183` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £8,226.54 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:456` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £8,097.04 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:305` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £7,986.00 | Education & SEND |
| 6 | `Over500_2026_P04_-_published.xlsx:735` | 2026-07-13 | Roadside Technologies Ltd | £21,000.00 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:733` | 2026-07-13 | Roadside Technologies Ltd | £11,188.22 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:1287` | 2026-07-13 | Roadside Technologies Ltd | £10,298.22 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:601` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:740` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 7 | `Over500_2026_P02_-_published.xlsx:284` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £3,120.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:424` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,940.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:427` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,925.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:265` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,912.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:422` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,910.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:321` | 2026-07-14 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £4,074.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:467` | 2026-07-09 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £4,018.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:266` | 2026-07-14 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £4,018.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:261` | 2026-07-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £3,956.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:267` | 2026-07-14 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £3,792.50 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:530` | 2026-05-27 | Elior UK PLC | £23,694.03 | Adult Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:440` | 2026-06-16 | Elior UK PLC | £23,516.69 | Adult Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:433` | 2026-06-17 | Elior UK PLC | £18,592.30 | Adult Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:434` | 2026-06-11 | Elior UK PLC | £11,935.93 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:1281` | 2026-07-29 | The Better Group Ltd | £24,476.02 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:911` | 2026-07-08 | The Better Group Ltd | £21,500.00 | Adult Social Care - Transformation Projects |
| 10 | `Over500_2026_P04_-_published.xlsx:490` | 2026-07-06 | The Better Group Ltd | £18,062.50 | Adult Social Care - Transformation Projects |
| 10 | `Over500_2026_P04_-_published.xlsx:495` | 2026-07-07 | The Better Group Ltd | £13,106.88 | Adult Social Care - Transformation Projects |

**C-01.2. Expected control.** Where the combined value reaches the quote threshold, invitations to quote go to at least three sources through the Procurement Portal (goods and services band; the works bands apply only where the purchase is works). [CPR-54, CPR-55]

**T-01.2. Test.** For each sampled payment just under the quote threshold, obtain the quote record and confirm the approach matched the value band and the full requirement. Payments already drawn for T-01.1 are excluded, so each is tested once. [CPR-54, metric:$.tests.threshold_clustering.per_threshold[2].by_tag.general_procurement.count]  
**Evidence to inspect:** Quote invitations and responses, order and invoice  
**Sample:** 4 items from `threshold-clustering.csv`, where tag = general_procurement, threshold = 25000, largest amount first, excluding suppliers and rows already drawn in T-01.1, (only 4 available); 4 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2201` | 2026-05-15 | WOKINGHAM BOROUGH COUNCIL | £24,416.73 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:649` | 2026-06-18 | Triple Value Impact | £24,244.00 | Chief Executive |
| 3 | `Over500_2026_P02_-_published.xlsx:560` | 2026-05-12 | DevComms South East Ltd | £24,227.07 | Development & Housing |
| 4 | `Over500_2026_P03_-_published.xlsx:396` | 2026-06-10 | BookingLab Limited | £24,000.00 | Transformation, Customer & ICT |


## R-02: 181 general procurement suppliers at or above the £25,000 quote threshold show no active notice found in the… [9 (High; Medium High (Amber))]

**Audit objective.** Conclude whether competition or a published award can be evidenced for high-value general procurement suppliers with no active notice found.

**C-02.1. Expected control.** Above the quote threshold, competition follows the band for the contract type: for goods and services, invitations to quote go to at least three sources through the Procurement Portal; for works, concessions and light-touch contracts, the works bands apply, with full tender above the stated value; the opportunity is advertised on the CDP. The Threshold value is not stated in the Rules, so the applicable band is confirmed in fieldwork. [CPR-54, CPR-55, CPR-56, CPR-11]

**T-02.1. Test.** For each sampled supplier, first establish the contract type and so the band that applies, then check the contract register and obtain the quote or tender file and any notice. A pass is a documented competitive route for that band, a framework call-off or a recorded exception. [CPR-54, CPR-55, CPR-56, metric:$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count]  
**Evidence to inspect:** Contract register entry, quote or tender file, framework agreement, notice  
**Sample:** 10 items from `off-contract.csv`, where dominant_tag = general_procurement, match_class = none, largest total first, 5 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2; 34 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 1 | `Over500_2026_P03_-_published.xlsx:2146` | 2026-06-29 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,180,425.32 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:3194` | 2026-07-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £1,803,783.32 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:2216` | 2026-06-03 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P04_-_published.xlsx:3789` | 2026-07-29 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P04_-_published.xlsx:3311` | 2026-07-29 | Millbrook Healthcare Limited | £33,611.35 | Finance, Property & Procurement |
| 3 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 3 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |
| 3 | `Over500_2026_P02_-_published.xlsx:653` | 2026-05-27 | SoftwareONE UK Ltd | £59,650.56 | Transformation, Customer & ICT |
| 3 | `Over500_2026_P02_-_published.xlsx:654` | 2026-05-27 | SoftwareONE UK Ltd | £1,759.34 | Transformation, Customer & ICT |
| 4 | `Over500_2026_P02_-_published.xlsx:2200` | 2026-05-13 | Livity Life Ltd | £135,591.03 | Finance, Property & Procurement |
| 4 | `Over500_2026_P03_-_published.xlsx:3087` | 2026-06-17 | Livity Life Ltd | £127,886.78 | Finance, Property & Procurement |
| 4 | `Over500_2026_P04_-_published.xlsx:3310` | 2026-07-13 | Livity Life Ltd | £50,961.45 | Finance, Property & Procurement |
| 4 | `Over500_2026_P04_-_published.xlsx:3197` | 2026-07-13 | Livity Life Ltd | £46,409.47 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:2199` | 2026-05-13 | Livity Life Ltd | £42,882.27 | Finance, Property & Procurement |
| 5 | `Over500_2026_P04_-_published.xlsx:784` | 2026-07-10 | E W BEARD LTD | £64,202.50 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:674` | 2026-05-20 | E W BEARD LTD | £60,039.70 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:675` | 2026-05-20 | E W BEARD LTD | £55,594.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:664` | 2026-06-10 | E W BEARD LTD | £38,672.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:672` | 2026-05-20 | E W BEARD LTD | £36,170.52 | Education & SEND |
| 6 | `Over500_2026_P02_-_published.xlsx:2198` | 2026-05-13 | SLOUGH BOROUGH COUNCIL | £296,177.15 | Finance, Property & Procurement |
| 7 | `Over500_2026_P03_-_published.xlsx:183` | 2026-06-03 | Sikandar Hayat t/a Prompt Cars | £73,296.50 | Education & SEND |
| 7 | `Over500_2026_P03_-_published.xlsx:203` | 2026-06-03 | Sikandar Hayat t/a Prompt Cars | £26,085.00 | Education & SEND |
| 7 | `Over500_2026_P03_-_published.xlsx:208` | 2026-06-03 | Sikandar Hayat t/a Prompt Cars | £17,607.50 | Education & SEND |
| 7 | `Over500_2026_P03_-_published.xlsx:162` | 2026-06-03 | Sikandar Hayat t/a Prompt Cars | £9,944.00 | Education & SEND |
| 7 | `Over500_2026_P04_-_published.xlsx:220` | 2026-07-21 | Sikandar Hayat t/a Prompt Cars | £3,743.00 | Education & SEND |
| 8 | `Over500_2026_P03_-_published.xlsx:661` | 2026-06-08 | ANDY AND ES LIMITED | £59,335.72 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:1283` | 2026-07-15 | ANDY AND ES LIMITED | £56,941.82 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:670` | 2026-05-13 | ANDY AND ES LIMITED | £54,881.31 | Education & SEND |
| 9 | `Over500_2026_P04_-_published.xlsx:589` | 2026-07-16 | BBOWT | £118,027.50 | Environment |
| 9 | `Over500_2026_P04_-_published.xlsx:623` | 2026-07-16 | BBOWT | £25,000.00 | Environment |
| 9 | `Over500_2026_P02_-_published.xlsx:641` | 2026-05-21 | BBOWT | £1,289.93 | Environment |
| 10 | `Over500_2026_P03_-_published.xlsx:2217` | 2026-06-10 | BRACKNELL FOREST BOROUGH CNCL | £130,310.57 | Finance, Property & Procurement |

**T-02.3. Test.** Lower-value stratum: same test as T-02.1 on suppliers nearest the quote threshold, to show whether the quote step is followed lower down the list. Establish the band first. [CPR-54, CPR-55, CPR-56, metric:$.tests.off_contract.groups.unmatched.by_tag.general_procurement.count]  
**Evidence to inspect:** Contract register entry, quote or tender file, framework agreement, notice  
**Sample:** 10 items from `off-contract.csv`, where dominant_tag = general_procurement, match_class = none, smallest total first, 5 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1; 22 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:2127` | 2026-06-16 | Reading Refugee Support Group | £1,198.35 | Development & Housing |
| 1 | `Over500_2026_P03_-_published.xlsx:3077` | 2026-06-16 | Reading Refugee Support Group | £1,198.35 | Development & Housing |
| 1 | `Over500_2026_P03_-_published.xlsx:2114` | 2026-06-12 | Reading Refugee Support Group | £743.09 | Development & Housing |
| 1 | `Over500_2026_P03_-_published.xlsx:3078` | 2026-06-17 | Reading Refugee Support Group | £743.09 | Development & Housing |
| 1 | `Over500_2026_P03_-_published.xlsx:2128` | 2026-06-16 | Reading Refugee Support Group | £599.18 | Development & Housing |
| 2 | `Over500_2026_P02_-_published.xlsx:764` | 2026-05-27 | EDINGTON SPINK & HYNE LIMITED | £4,870.00 | Education & SEND |
| 2 | `Over500_2026_P03_-_published.xlsx:748` | 2026-06-18 | EDINGTON SPINK & HYNE LIMITED | £1,500.00 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:3082` | 2026-06-09 | Nagels (UK) Ltd | £6,385.00 | Environment |
| 4 | `Over500_2026_P04_-_published.xlsx:1562` | 2026-07-30 | DOWNLAND VOLUNTEER GROUP | £6,387.20 | Environment |
| 5 | `Over500_2026_P02_-_published.xlsx:737` | 2026-05-01 | SSE POWER DISTRIBUTION LIMITED | £6,441.47 | Environment |
| 6 | `Over500_2026_P03_-_published.xlsx:153` | 2026-06-11 | Rygor Commercials Ltd | £2,486.72 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:415` | 2026-07-31 | Rygor Commercials Ltd | £1,785.06 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:242` | 2026-07-15 | Rygor Commercials Ltd | £990.06 | Environment |
| 6 | `Over500_2026_P03_-_published.xlsx:150` | 2026-06-11 | Rygor Commercials Ltd | £648.94 | Environment |
| 6 | `Over500_2026_P03_-_published.xlsx:149` | 2026-06-11 | Rygor Commercials Ltd | £634.36 | Environment |
| 7 | `Over500_2026_P03_-_published.xlsx:39` | 2026-06-05 | R & G SMITH (SOUTHERN) LTD | £4,000.00 | Community Services |
| 7 | `Over500_2026_P02_-_published.xlsx:29` | 2026-05-26 | R & G SMITH (SOUTHERN) LTD | £2,565.00 | Community Services |
| 8 | `Over500_2026_P02_-_published.xlsx:461` | 2026-05-07 | Intellident Ltd t/a Bibliotheca | £6,571.00 | Community Services |
| 9 | `Over500_2026_P04_-_published.xlsx:351` | 2026-07-21 | Rail Settlement | £3,437.00 | Children's Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:272` | 2026-06-23 | Rail Settlement | £3,170.00 | Children's Social Care |
| 10 | `Over500_2026_P03_-_published.xlsx:400` | 2026-06-30 | ACCESS UK LIMITED | £5,700.00 | Adult Social Care - Transformation Projects |
| 10 | `Over500_2026_P04_-_published.xlsx:1016` | 2026-07-31 | ACCESS UK LIMITED | £950.00 | Adult Social Care - Transformation Projects |

**C-02.2. Expected control.** Awards are made on the most advantageous quote or tender against criteria notified in advance, with a written award report kept. [CPR-19, CPR-18, CPR-30, CPR-31] Owner: Service Director.

**T-02.2. Test.** For the same suppliers, obtain the award report and evaluation record and confirm criteria were set before evaluation and the report is retained. [CPR-30, CPR-19]  
**Evidence to inspect:** Award reports, evaluation criteria, evaluation scores  
**Sample:** Document test on the suppliers drawn for T-02.1 and T-02.3; no further transactions.


## R-03: 8 general procurement suppliers were paid in the window with every matching notice ended before it, and 8 sho… [12 (High; Medium High (Amber))]

**Audit objective.** Conclude whether payments after a notice ended, or above the notice award rate, were covered by an approved extension or variation.

**C-03.1. Expected control.** An extension of a contract beyond its term is approved by the S151 Officer. [CPR-61] Owner: S151 Officer.

**T-03.1. Test.** For each sampled supplier, obtain the contract file and extension approval, and any newer contract that explains payments after the notice end. [CPR-61, metric:$.tests.expired_notice_spend.headline_general_procurement.count]  
**Evidence to inspect:** Contract file, extension approval, newer contract  
**Sample:** 8 items from `expired-notice-spend.csv`, where dominant_tag = general_procurement, largest total_gbp first, 5 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, (only 8 available); 17 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:704` | 2026-06-16 | Hope & Clay (Construction) Ltd | £91,306.75 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:58` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £8,250.00 | Development & Housing |
| 2 | `Over500_2026_P03_-_published.xlsx:42` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £6,250.00 | Development & Housing |
| 2 | `Over500_2026_P03_-_published.xlsx:279` | 2026-06-09 | BERKSHIRE MECHANICAL SERVICES | £5,585.00 | Development & Housing |
| 2 | `Over500_2026_P03_-_published.xlsx:52` | 2026-06-09 | BERKSHIRE MECHANICAL SERVICES | £4,000.00 | Development & Housing |
| 2 | `Over500_2026_P04_-_published.xlsx:374` | 2026-07-03 | BERKSHIRE MECHANICAL SERVICES | £3,400.00 | Development & Housing |
| 3 | `Over500_2026_P04_-_published.xlsx:856` | 2026-07-14 | Berkshire Womens Aid | £39,569.75 | Public Health & Wellbeing |
| 3 | `Over500_2026_P04_-_published.xlsx:721` | 2026-07-14 | Berkshire Womens Aid | £13,427.75 | Public Health & Wellbeing |
| 4 | `Over500_2026_P02_-_published.xlsx:467` | 2026-05-08 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 4 | `Over500_2026_P03_-_published.xlsx:531` | 2026-06-10 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 4 | `Over500_2026_P03_-_published.xlsx:721` | 2026-06-10 | G7 BUSINESS SOLUTIONS LIMITED | £1,365.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P04_-_published.xlsx:1309` | 2026-07-15 | G7 BUSINESS SOLUTIONS LIMITED | £1,365.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:762` | 2026-05-19 | G7 BUSINESS SOLUTIONS LIMITED | £910.00 | Finance, Property & Procurement |
| 5 | `Over500_2026_P02_-_published.xlsx:459` | 2026-05-15 | CACI Limited | £12,071.67 | Children's Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:686` | 2026-06-22 | Morton Pattison Ltd | £1,102.00 | Environment |
| 7 | `Over500_2026_P03_-_published.xlsx:821` | 2026-06-03 | Davis and Associates Consultancy Limited | £800.00 | Chief Executive |
| 8 | `Over500_2026_P04_-_published.xlsx:58` | 2026-07-20 | Tactical Facilities Management Ltd | £681.94 | Development & Housing |

**C-03.2. Expected control.** A variation is approved in writing by the Monitoring Officer and S151 Officer below the Threshold, or by the relevant board above it. [CPR-62] Owner: Monitoring Officer and S151 Officer.

**T-03.2. Test.** For each sampled supplier, compare payments to the award and obtain any variation approval; note that award values may be estimates or maxima. [CPR-62, metric:$.tests.spend_vs_award.headline_general_procurement.count]  
**Evidence to inspect:** Award notice, variation record and approval  
**Sample:** 7 items from `spend-vs-award.csv`, where dominant_tag = general_procurement, ratio ≥ 1.25, largest annualised_estimate first, 5 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, (only 7 available); 21 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:905` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £129,125.00 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:492` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £91,629.15 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:487` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £52,054.00 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:494` | 2026-07-24 | NEC SOFTWARE SOLUTIONS UK LIMITED | £15,094.00 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:488` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £13,063.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:2130` | 2026-06-09 | TWO SAINTS LTD | £38,775.00 | Development & Housing |
| 2 | `Over500_2026_P04_-_published.xlsx:3181` | 2026-07-22 | TWO SAINTS LTD | £38,775.00 | Development & Housing |
| 2 | `Over500_2026_P02_-_published.xlsx:2160` | 2026-05-12 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 2 | `Over500_2026_P02_-_published.xlsx:2161` | 2026-05-13 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 2 | `Over500_2026_P02_-_published.xlsx:2162` | 2026-05-27 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 3 | `Over500_2026_P04_-_published.xlsx:1276` | 2026-07-22 | WCL UK Ltd (Trading as Everything ICT) | £102,882.78 | Education & SEND |
| 4 | `Over500_2026_P03_-_published.xlsx:371` | 2026-06-08 | IDOX SOFTWARE LTD | £48,579.20 | Community Services |
| 4 | `Over500_2026_P02_-_published.xlsx:462` | 2026-05-20 | IDOX SOFTWARE LTD | £2,647.21 | Development & Housing |
| 5 | `Over500_2026_P03_-_published.xlsx:384` | 2026-06-04 | Exacom Systems Ltd | £12,105.85 | Development & Housing |
| 6 | `Over500_2026_P02_-_published.xlsx:460` | 2026-05-20 | Softcat Ltd | £8,979.02 | Education & SEND |
| 6 | `Over500_2026_P03_-_published.xlsx:375` | 2026-06-17 | Softcat Ltd | £2,025.98 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P03_-_published.xlsx:276` | 2026-06-30 | SMS-Environmental Ltd | £2,070.00 | Adult Social Care |
| 7 | `Over500_2026_P04_-_published.xlsx:365` | 2026-07-09 | SMS-Environmental Ltd | £1,335.60 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:29` | 2026-06-22 | SMS-Environmental Ltd | £1,175.00 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:17` | 2026-05-28 | SMS-Environmental Ltd | £1,129.15 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:19` | 2026-05-27 | SMS-Environmental Ltd | £759.16 | Adult Social Care |


## R-04: 37 groups of general procurement payments with the same supplier and amount at different times are an indicat… [9 (High; Medium High (Amber))]

**Audit objective.** Conclude whether repeated same-supplier same-amount payments are legitimate recurring charges or duplicate payments, and whether payments follow valid invoices.

**C-04.1. Expected control.** Payments are made against a valid, undisputed invoice within the contractual payment term, with written evidence of the purchase held. [CPR-39, CPR-33]

**T-04.1. Test.** For each sampled group, obtain invoices and remittances and confirm each payment matches a separate invoice and goods or services received. [CPR-39, metric:$.tests.duplicates.tiers.different_time.headline_general_procurement.groups]  
**Evidence to inspect:** Invoices, remittance advice, orders, receipt records  
**Sample:** 10 items from `duplicates.csv`, where tier = different_time, dominant_tag = general_procurement, largest gbp_beyond_first first, largest 5 payments per item, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2; 24 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:259` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 1 | `Over500_2026_P04_-_published.xlsx:264` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 1 | `Over500_2026_P04_-_published.xlsx:474` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 2 | `Over500_2026_P02_-_published.xlsx:8` | 2026-05-13 | Pavillion Publishing and Media Ltd | £9,084.60 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:643` | 2026-05-14 | Pavillion Publishing and Media Ltd | £9,084.60 | Executive Director People - Children's Services |
| 3 | `Over500_2026_P02_-_published.xlsx:412` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 3 | `Over500_2026_P02_-_published.xlsx:416` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 3 | `Over500_2026_P02_-_published.xlsx:418` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 4 | `Over500_2026_P02_-_published.xlsx:369` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 4 | `Over500_2026_P02_-_published.xlsx:372` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 4 | `Over500_2026_P02_-_published.xlsx:395` | 2026-05-13 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:459` | 2026-06-25 | LOCAL GOVERNMENT PROPERTY CONSULTANTS (LGPC) | £4,925.00 | Finance, Property & Procurement |
| 5 | `Over500_2026_P03_-_published.xlsx:467` | 2026-06-25 | LOCAL GOVERNMENT PROPERTY CONSULTANTS (LGPC) | £4,925.00 | Finance, Property & Procurement |
| 6 | `Over500_2026_P03_-_published.xlsx:427` | 2026-06-17 | BRITISH TELECOM | £4,364.06 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P03_-_published.xlsx:431` | 2026-06-17 | BRITISH TELECOM | £4,364.06 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P04_-_published.xlsx:635` | 2026-07-14 | AMR CONSULT LTD | £2,665.27 | Education & SEND |
| 7 | `Over500_2026_P04_-_published.xlsx:838` | 2026-07-14 | AMR CONSULT LTD | £2,665.27 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:202` | 2026-05-06 | CRESCENT SIGNS LTD | £2,300.00 | Environment |
| 8 | `Over500_2026_P02_-_published.xlsx:203` | 2026-05-13 | CRESCENT SIGNS LTD | £2,300.00 | Environment |
| 9 | `Over500_2026_P02_-_published.xlsx:233` | 2026-05-05 | Valley Cars | £2,004.00 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:234` | 2026-05-06 | Valley Cars | £2,004.00 | Education & SEND |
| 10 | `Over500_2026_P04_-_published.xlsx:126` | 2026-07-30 | Glen Cleaning Company Ltd | £901.77 | Community Services |
| 10 | `Over500_2026_P04_-_published.xlsx:141` | 2026-07-30 | Glen Cleaning Company Ltd | £901.77 | Community Services |
| 10 | `Over500_2026_P04_-_published.xlsx:142` | 2026-07-30 | Glen Cleaning Company Ltd | £901.77 | Community Services |

**T-04.2. Test.** For each sampled same-timestamp group, confirm from the payment run and invoices whether each row is a distinct invoice. [CPR-33, metric:$.tests.duplicates.tiers.same_timestamp.headline_general_procurement.groups]  
**Evidence to inspect:** Payment run listing, invoices  
**Sample:** 10 items from `duplicates.csv`, where tier = same_timestamp, dominant_tag = general_procurement, largest gbp_beyond_first first, largest 5 payments per item, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2, T-04.1; 25 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:2134` | 2026-06-18 | SEISMIC SEWAGE SYSTEMS LTD | £5,360.00 | Environment |
| 1 | `Over500_2026_P03_-_published.xlsx:2141` | 2026-06-18 | SEISMIC SEWAGE SYSTEMS LTD | £5,360.00 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:162` | 2026-07-21 | COMPASS EXECUTIVE CARS (UK) LTD | £2,178.00 | Education & SEND |
| 2 | `Over500_2026_P04_-_published.xlsx:171` | 2026-07-21 | COMPASS EXECUTIVE CARS (UK) LTD | £2,178.00 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:165` | 2026-06-30 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £2,050.00 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:334` | 2026-06-30 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £2,050.00 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:353` | 2026-07-23 | Go Green Taxis Ltd | £962.60 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:357` | 2026-07-23 | Go Green Taxis Ltd | £962.60 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:484` | 2026-07-23 | Go Green Taxis Ltd | £962.60 | Children's Social Care |
| 5 | `Over500_2026_P03_-_published.xlsx:376` | 2026-06-30 | Perceptive On Line Ltd T/A Amatis Networks | £635.64 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P03_-_published.xlsx:392` | 2026-06-30 | Perceptive On Line Ltd T/A Amatis Networks | £635.64 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P03_-_published.xlsx:533` | 2026-06-30 | Perceptive On Line Ltd T/A Amatis Networks | £635.64 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P03_-_published.xlsx:534` | 2026-06-30 | Perceptive On Line Ltd T/A Amatis Networks | £635.64 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P02_-_published.xlsx:484` | 2026-05-06 | Perceptive On Line Ltd T/A Amatis Networks | £600.72 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P02_-_published.xlsx:485` | 2026-05-06 | Perceptive On Line Ltd T/A Amatis Networks | £600.72 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P02_-_published.xlsx:486` | 2026-05-06 | Perceptive On Line Ltd T/A Amatis Networks | £600.72 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P02_-_published.xlsx:487` | 2026-05-06 | Perceptive On Line Ltd T/A Amatis Networks | £600.72 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P03_-_published.xlsx:324` | 2026-06-02 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £1,500.00 | Education & SEND |
| 7 | `Over500_2026_P03_-_published.xlsx:332` | 2026-06-02 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £1,500.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:163` | 2026-07-22 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £1,500.00 | Education & SEND |
| 8 | `Over500_2026_P04_-_published.xlsx:240` | 2026-07-22 | DANIEL GRIFFITHS T/A BLUEBIRD PASSENGER SERVICES | £1,500.00 | Education & SEND |
| 9 | `Over500_2026_P03_-_published.xlsx:195` | 2026-06-22 | COMPASS EXECUTIVE CARS (UK) LTD | £1,485.00 | Education & SEND |
| 9 | `Over500_2026_P03_-_published.xlsx:331` | 2026-06-22 | COMPASS EXECUTIVE CARS (UK) LTD | £1,485.00 | Education & SEND |
| 10 | `Over500_2026_P03_-_published.xlsx:645` | 2026-06-09 | BPR Ltd trading as We Are Lean and Agile | £1,400.00 | Transformation, Customer & ICT |
| 10 | `Over500_2026_P03_-_published.xlsx:646` | 2026-06-09 | BPR Ltd trading as We Are Lean and Agile | £1,400.00 | Transformation, Customer & ICT |


## R-05: Exceptions to and waivers of competition cannot be observed in the payments data, so the control is not teste… [4 (Moderate; Moderate)]

**Audit objective.** Conclude whether exceptions to and waivers of competition are limited to the listed circumstances, approved at the right level and fully documented.

**C-05.1. Expected control.** A competitive process is excepted or waived only in listed circumstances, and the exception is fully documented. [CPR-20, CPR-26, CPR-22] Owner: Monitoring Officer and/or S151 Officer.

**T-05.1. Test.** Obtain the register of exceptions and waivers and, for a selection, confirm the circumstance relied on and the documentation held. [CPR-20, CPR-26]  
**Evidence to inspect:** Register of exceptions and waivers, exception files  
**Sample:** Exceptions are not observable in the payments data; select from the register once obtained.

**C-05.2. Expected control.** Exceptions are approved at the level the exception value requires: S151 Officer, S151 Officer consulting others, or the Executive. [CPR-23, CPR-24, CPR-25, CPR-21] Owner: S151 Officer.

**T-05.2. Test.** For the same selection, confirm the approver matched the exception value and the Executive approved those above the stated value. [CPR-24, CPR-25]  
**Evidence to inspect:** Approval records, delegation scheme  
**Sample:** Document test on the T-05.1 selection.

**C-05.3. Expected control.** Exception reports go to the relevant board and the S151 Officer records the circumstances; Appendix C exceptions have prior written approval. [CPR-27, CPR-28, CPR-58, CPR-59, CPR-60, CPR-64]

**T-05.3. Test.** Confirm exception reports reached the board and S151 recording exists; for Appendix C placements confirm prior written approval. [CPR-27, CPR-28, CPR-58]  
**Evidence to inspect:** Board papers, S151 records, written approvals  
**Sample:** Document test on the T-05.1 selection.


## R-06: Completeness of the contract register and of tender and award publication cannot be confirmed from the data:… [4 (Moderate; Moderate)]

**Audit objective.** Conclude whether the contract register and the publication of tenders, awards and expenditure are complete.

**C-06.1. Expected control.** A register of contracts is kept and published, and awards are notified so they are recorded on it. [CPR-08, CPR-35] Owner: Service Director.

**T-06.1. Test.** Obtain the contract register and compare it with the published notice export to see which notices have no entry and the reverse. [CPR-08, metric:$.contracts.register_present]  
**Evidence to inspect:** Contract register, notice export  
**Sample:** Whole-register comparison once the register is supplied.

**C-06.2. Expected control.** Invitations to tender, expenditure and contract information are published and reported as the Rules require, with CDP notices approved by the Service Lead. [CPR-06, CPR-07, CPR-09, CPR-12] Owner: Service Lead for Procurement and Commissioning.

**T-06.2. Test.** Confirm that tenders above the stated value were published, monthly board reporting occurred, and CDP notices were approved. [CPR-07, CPR-09, CPR-12]  
**Evidence to inspect:** Published tender list, board reports, CDP approvals  
**Sample:** Document and enquiry test.


## R-07: Care and education placement payments show repeated payments to one supplier in a window and same-amount grou… [9 (High; Medium High (Amber))]

**Audit objective.** Conclude whether care and education placement payments are supported by a recorded reason for the choice of provider and by valid invoices.

**C-07.1. Expected control.** The Service Director keeps a record of the reasons for the choice of provider in the individual's case notes. [CPR-63] Owner: Service Director.

**T-07.1. Test.** For each sampled window, obtain the case-note record of reasons for the choice of provider and the placement agreement, and confirm repeated payments match the agreed placement. [CPR-63, metric:$.tests.split_purchases.per_threshold[0].by_tag.care_or_education_placement.count]  
**Evidence to inspect:** Case notes, placement agreements, invoices  
**Sample:** 10 items from `split-purchases.csv`, where dominant_tag = care_or_education_placement, threshold = 25000, largest window_total first, largest 5 payments per item, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2, T-04.1, T-04.2; 50 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:1850` | 2026-07-08 | BUPA Care Services | £10,400.00 | Adult Social Care |
| 1 | `Over500_2026_P04_-_published.xlsx:1039` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 1 | `Over500_2026_P04_-_published.xlsx:1043` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 1 | `Over500_2026_P04_-_published.xlsx:1073` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 1 | `Over500_2026_P04_-_published.xlsx:1120` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2171` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2172` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2191` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2192` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2193` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P04_-_published.xlsx:2239` | 2026-07-01 | Affinity Trust Support Ltd | £24,926.00 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:1629` | 2026-06-24 | Affinity Trust Support Ltd | £17,444.96 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:1678` | 2026-06-24 | Affinity Trust Support Ltd | £14,080.00 | Adult Social Care |
| 3 | `Over500_2026_P04_-_published.xlsx:2342` | 2026-07-01 | Affinity Trust Support Ltd | £14,080.00 | Adult Social Care |
| 3 | `Over500_2026_P04_-_published.xlsx:2350` | 2026-07-08 | Affinity Trust Support Ltd | £13,237.62 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:1832` | 2026-05-13 | BUPA Care Services | £8,077.32 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:1458` | 2026-05-13 | BUPA Care Services | £7,325.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:1630` | 2026-05-13 | BUPA Care Services | £7,325.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:985` | 2026-05-13 | BUPA Care Services | £7,078.84 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:1465` | 2026-05-13 | BUPA Care Services | £6,811.71 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:2245` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2258` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2262` | 2026-05-21 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2259` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £23,076.67 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P03_-_published.xlsx:2229` | 2026-06-17 | Phoenix Child Care Limited -The Grange School | £22,295.24 | Education (DSG Funded) & Other Education Grants |
| 6 | `Over500_2026_P02_-_published.xlsx:1508` | 2026-05-20 | GCH (Alder) Ltd t/a Hungerford Care Home | £18,144.00 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:1573` | 2026-05-20 | GCH (Alder) Ltd t/a Hungerford Care Home | £6,580.00 | Adult Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:1497` | 2026-06-17 | GCH (Alder) Ltd t/a Hungerford Care Home | £6,580.00 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:1018` | 2026-05-20 | GCH (Alder) Ltd t/a Hungerford Care Home | £6,000.00 | Adult Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:2714` | 2026-06-17 | GCH (Alder) Ltd t/a Hungerford Care Home | £6,000.00 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:1642` | 2026-05-13 | VOYAGE CARE | £14,756.16 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:1465` | 2026-06-10 | VOYAGE CARE | £14,756.16 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:1641` | 2026-05-13 | VOYAGE CARE | £12,820.44 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:1405` | 2026-06-10 | VOYAGE CARE | £12,820.44 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:1836` | 2026-05-13 | VOYAGE CARE | £10,598.40 | Adult Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:772` | 2026-06-10 | PURLEY PARK TRUST LTD | £10,156.00 | Adult Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:649` | 2026-07-08 | PURLEY PARK TRUST LTD | £10,156.00 | Adult Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:773` | 2026-06-10 | PURLEY PARK TRUST LTD | £9,702.44 | Adult Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:847` | 2026-07-08 | PURLEY PARK TRUST LTD | £9,702.44 | Adult Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:753` | 2026-06-10 | PURLEY PARK TRUST LTD | £9,665.00 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:1415` | 2026-07-15 | WEST BERKSHIRE MENCAP | £18,035.64 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:680` | 2026-07-29 | WEST BERKSHIRE MENCAP | £18,035.64 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:869` | 2026-07-15 | WEST BERKSHIRE MENCAP | £12,370.88 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:682` | 2026-07-29 | WEST BERKSHIRE MENCAP | £12,370.88 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:1416` | 2026-07-15 | WEST BERKSHIRE MENCAP | £11,755.56 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:896` | 2026-07-08 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:921` | 2026-07-08 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:956` | 2026-07-29 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:957` | 2026-07-29 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:1374` | 2026-07-08 | We Are The Care Company Ltd | £4,144.16 | Adult Social Care |

**C-07.2. Expected control.** Placement payments are made against valid, undisputed invoices. [CPR-39]

**T-07.2. Test.** For each sampled same-amount group, match payments to invoices and the placement rate to establish whether the repeats are recurring charges. [CPR-39, metric:$.tests.duplicates.tiers.different_time.by_tag.care_or_education_placement.groups]  
**Evidence to inspect:** Invoices, placement fee schedule, remittances  
**Sample:** 10 items from `duplicates.csv`, where tier = different_time, dominant_tag = care_or_education_placement, largest gbp_beyond_first first, largest 5 payments per item, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2, T-04.1, T-04.2, T-07.1; 28 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:2157` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2158` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2159` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2306` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3102` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P02_-_published.xlsx:2266` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P02_-_published.xlsx:2267` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P02_-_published.xlsx:2269` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P03_-_published.xlsx:1931` | 2026-06-16 | Care Services To You | £23,989.77 | Children's Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:2008` | 2026-06-16 | Care Services To You | £23,989.77 | Children's Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:3044` | 2026-06-22 | Care Services To You | £23,989.77 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:3750` | 2026-07-17 | Care Services To You | £23,989.77 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:3092` | 2026-07-23 | Care Services To You | £23,989.77 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:3161` | 2026-07-23 | Care Services To You | £23,989.77 | Children's Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:2092` | 2026-05-26 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:2105` | 2026-05-27 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |
| 6 | `Over500_2026_P04_-_published.xlsx:3081` | 2026-07-20 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |
| 6 | `Over500_2026_P04_-_published.xlsx:3752` | 2026-07-20 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:2091` | 2026-05-26 | Amegreen Childrens Services | £33,320.40 | Children's Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:2108` | 2026-05-28 | Amegreen Childrens Services | £33,320.40 | Children's Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:2032` | 2026-06-17 | Amegreen Childrens Services | £33,320.40 | Children's Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:2033` | 2026-06-17 | Amegreen Childrens Services | £33,320.40 | Children's Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:1440` | 2026-06-24 | LIAISE LODDON LTD | £14,721.68 | Adult Social Care |
| 9 | `Over500_2026_P03_-_published.xlsx:1514` | 2026-06-24 | LIAISE LODDON LTD | £14,721.68 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:2179` | 2026-07-01 | LIAISE LODDON LTD | £14,721.68 | Adult Social Care |
| 10 | `Over500_2026_P02_-_published.xlsx:2234` | 2026-05-11 | The Unicorn School | £13,771.00 | Education (DSG Funded) & Other Education Grants |
| 10 | `Over500_2026_P02_-_published.xlsx:2235` | 2026-05-11 | The Unicorn School | £13,771.00 | Education (DSG Funded) & Other Education Grants |
| 10 | `Over500_2026_P02_-_published.xlsx:2236` | 2026-05-11 | The Unicorn School | £13,771.00 | Education (DSG Funded) & Other Education Grants |


## R-08: Grant-tagged payments sit outside the general procurement headline: 123 grant suppliers at or above the quote… [4 (Moderate; Moderate)]

**Audit objective.** Conclude how grant-tagged payments are classified and approved, and whether grants above the quote threshold followed the Rules or a recorded exemption.

**C-08.1. Expected control.** Where a grant is treated as a contract, the quote steps apply at the value bands the Rules set, unless an exception is recorded. [CPR-53, CPR-54, CPR-20]

**T-08.1. Test.** For each sampled grant recipient, obtain the grant award, its conditions and approval, and any quote or exception record; confirm how the grant was classified. [CPR-54, metric:$.tests.off_contract.groups.unmatched.by_tag.grant.count]  
**Evidence to inspect:** Grant agreement, conditions, approval, classification note  
**Sample:** 5 items from `off-contract.csv`, where dominant_tag = grant, match_class = none, largest total first, 5 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2, T-04.1, T-04.2, T-07.1, T-07.2; 12 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:511` | 2026-06-17 | JUBILEE DAY NURSERY | £400,824.68 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:623` | 2026-06-30 | JUBILEE DAY NURSERY | £6,769.87 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P04_-_published.xlsx:703` | 2026-07-03 | JUBILEE DAY NURSERY | £1,000.00 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2075` | 2026-06-17 | ACRES OF FUN DAY NURSERY AND PRE SCHOOL | £323,872.96 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P03_-_published.xlsx:525` | 2026-06-17 | ROCKING HORSE DAY NURSERY - NEWBURY RACECOURSE PLC | £317,171.95 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P03_-_published.xlsx:620` | 2026-06-30 | ROCKING HORSE DAY NURSERY - NEWBURY RACECOURSE PLC | £3,291.55 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:579` | 2026-06-17 | TIGERS DAY NURSERY | £240,841.71 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P04_-_published.xlsx:704` | 2026-07-03 | TIGERS DAY NURSERY | £1,500.00 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P04_-_published.xlsx:578` | 2026-07-03 | TIGERS DAY NURSERY | £1,200.00 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P04_-_published.xlsx:3255` | 2026-07-02 | TIGERS DAY NURSERY | £797.54 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P03_-_published.xlsx:2081` | 2026-06-17 | Tigers at Theale Day Nursery | £240,149.35 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P03_-_published.xlsx:634` | 2026-06-30 | Tigers at Theale Day Nursery | £596.16 | Education (DSG Funded) & Other Education Grants |


## R-09: Delegated approvals and Key Decision treatment cannot be observed in the payments data, and the printed claus… [6 (Moderate; Moderate)]

**Audit objective.** Conclude whether awards above the Key Decision and board bands were approved by the route the Rules require, and which clause the council applies where they differ.

**C-09.1. Expected control.** Contracts are within a decision of the Council or Executive and the budget, and are approved under Appendix A before award. [CPR-02, CPR-03, CPR-05]

**T-09.2. Test.** For the same suppliers, confirm the decision was within a Council or Executive decision and budget provision. [CPR-02, CPR-03, CPR-05]  
**Evidence to inspect:** Council or Executive minutes, budget lines  
**Sample:** Document test on the T-09.1 suppliers.

**C-09.2. Expected control.** Awards above the stated value are treated as Key Decisions, with Service Director delegation below the lower band and board or Executive approval in the higher bands. [CPR-04, CPR-50, CPR-51, CPR-52] Owner: Relevant Service Director.

**T-09.1. Test.** For each sampled supplier whose annualised spend is above the Key Decision value, obtain the award decision and approval and confirm the route used; ask the council which clause it applies. [CPR-04, CPR-52, metric:$.tests.high_value_suppliers.headline_general_procurement.count]  
**Evidence to inspect:** Decision records, written reports, delegation scheme  
**Sample:** 2 items from `high-value-suppliers.csv`, where dominant_tag = general_procurement, annualised_estimate ≥ 500000, largest annualised_estimate first, 3 payments per supplier, excluding suppliers and rows already drawn in T-01.1, T-01.2, T-02.1, T-02.3, T-03.1, T-03.2, T-04.1, T-04.2, T-07.1, T-07.2, T-08.1, (only 2 available); 4 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:669` | 2026-05-26 | ASCIA CONSTRUCTION LIMITED | £332,579.29 | Education & SEND |
| 2 | `Over500_2026_P02_-_published.xlsx:738` | 2026-05-20 | ANCHOR PIPEWORK LIMITED | £33,148.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:2406` | 2026-06-18 | ANCHOR PIPEWORK LIMITED | £33,148.00 | Finance, Property & Procurement |
| 2 | `Over500_2026_P02_-_published.xlsx:23` | 2026-05-29 | ANCHOR PIPEWORK LIMITED | £10,111.05 | Adult Social Care |


## Prepared-by-client (PBC) request list

Derived from the test steps above. Each item names the tests that need it.

| # | Risk | Item requested | For tests |
|---|---|---|---|
| 1 | R-01 | Purchase orders and requisitions for the sampled windows | T-01.1 |
| 2 | R-01 | Quotations or tender records for the sampled windows | T-01.1 |
| 3 | R-01 | Quote records and orders for the sampled payments | T-01.2 |
| 4 | R-02 | Contract register extract | T-02.1 |
| 5 | R-02 | Quote or tender files for the sampled suppliers | T-02.1 |
| 6 | R-02 | Quote or tender files for the lower-value sampled suppliers | T-02.3 |
| 7 | R-02 | Award reports and evaluation records for the T-02.1 suppliers | T-02.2 |
| 8 | R-03 | Contract files and extension approvals for the sampled suppliers | T-03.1 |
| 9 | R-03 | Variation records and approvals for the sampled suppliers | T-03.2 |
| 10 | R-04 | Invoices and remittances for the sampled groups | T-04.1 |
| 11 | R-04 | Payment run listings and invoices for the sampled groups | T-04.2 |
| 12 | R-05 | Register of exceptions and waivers | T-05.1 |
| 13 | R-05 | Exception files for the selection | T-05.1 |
| 14 | R-05 | Approval records for the selected exceptions | T-05.2 |
| 15 | R-05 | Board exception reports and S151 records | T-05.3 |
| 16 | R-06 | Council Contract Register extract | T-06.1 |
| 17 | R-06 | Board contract reports | T-06.2 |
| 18 | R-06 | CDP notice approvals | T-06.2 |
| 19 | R-07 | Case-note extracts (access-controlled) for the sampled placements | T-07.1 |
| 20 | R-07 | Invoices and fee schedules for the sampled groups | T-07.2 |
| 21 | R-08 | Grant agreements and approvals for the sampled recipients | T-08.1 |
| 22 | R-09 | Award decisions and approvals for the sampled suppliers | T-09.1 |
| 23 | R-09 | Minutes and budget evidence for the T-09.1 suppliers | T-09.2 |
