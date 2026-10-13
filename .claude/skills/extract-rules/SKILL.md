---
name: extract-rules
description: Extract the testable rules from data/contract-rules.pdf (West Berkshire Council Contract Rules, Part 8) into outputs/rules.json with clause, page, thresholds, approver and a verbatim quote, then verify every quote against the PDF. Use when the user runs /extract-rules or asks to build or refresh the rules file for the procurement audit.
---

# extract-rules

Turn `data/contract-rules.pdf` into `outputs/rules.json`, then prove it with
`verify_quotes.py`. You read and judge; the script checks. Do not run any
arithmetic or look anything up from memory: every figure must be printed in the
PDF.

If the PDF is missing, unreadable, or has a different page count or appendix
layout from the map below, stop and report. Do not guess.

## 1. Read the document first

Use the project venv's Python for scripts (`.venv/Scripts/python.exe` on
Windows, `.venv/bin/python` elsewhere). Extract text page by page, because
quotes are verified per page:

```
pdftotext -enc UTF-8 -f N -l N data/contract-rules.pdf -          # reading order
pdftotext -enc UTF-8 -layout -f N -l N data/contract-rules.pdf -  # table columns
```

`-enc UTF-8` is mandatory: the default encoding turns every `£` into a
replacement character. Read all 15 pages with both modes before writing
anything. Write intermediate text to the scratchpad, not the project.

### Structure (15 pages, page numbers = PDF pages)

| Page | Content |
| --- | --- |
| 1-3 | 1 Introduction, 2 Purpose, 3 Application, 4 Authority, 5 Transparency |
| 3-6 | 6 Buying: preliminaries, thresholds, advertising, value and aggregation (6.15-6.17), principles, tenders (6.19-6.26) |
| 6-7 | 7 Exclusions and exceptions (7.1-7.7) |
| 7-8 | 8 Purchasing schemes, 9 Reporting |
| 8-10 | 10 Entering into a contract, 11 Legal (indemnity, bond 11.2, insurance, sealing 11.11, signature) |
| 11 | Appendix A: delegated authority by contract value (4 rows) |
| 12-13 | Appendix B: thresholds and mandatory processes (rows A, B1, B2, C, D) and footnotes |
| 14-15 | Appendix C: exclusions from competition (rows A-F) and a closing paragraph |

Clause numbers are not reliable layout anchors. The footer on each page
(`$3inav0bz.docx` and a page number) is template residue; ignore it.

### Extraction traps

- **Tables fragment.** In reading-order text, Appendix A/B/C cells interleave
  (row letters, amounts and actions land on separate lines). A quote must be a
  contiguous run of text. For a table row, quote one or more contiguous cell
  fragments as a **list** of strings; every fragment is verified separately
  and must be at least 12 characters. Check each fragment exists in the
  plain or the `-layout` text of its page.
- **Garbled order.** Page 3 prints `4.1.3.3 4.2` / `4.3 4.4` as headings
  before the text of 4.2-4.4. Page 7 prints `7.5.3 7.5.4` together, with the
  text of 7.5.3 and 7.5.4 swapped or merged. Work out which text belongs to
  which clause and record the problem as a gap note.
- **Placeholders.** `Part []` in the title and `Parts [] (Call-In) and []
  (Forward Plan)` in Appendix A are unfilled template text.
- **Hyphenation.** `Call-In` is printed `CallIn` in reading order. Quote what
  the extraction shows, not what you expect.

## 2. Output: `outputs/rules.json`

One JSON object, UTF-8, exactly these top-level keys:

```json
{
  "source": "data/contract-rules.pdf",
  "parameters": { "threshold_goods_services": null },
  "rules": [ ],
  "excluded": [ ],
  "notes": [ ]
}
```

(This replaces the bare array in CLAUDE.md's rule spec: `excluded` and `notes`
now sit beside `rules` rather than trailing it. Downstream agents read
`rules.json["rules"]`.)

### rules

One entry per testable rule: a clause that sets a threshold, a required
action, or an approver that an auditor could check against evidence. Background,
definitions, aspirations ("should consider") with no checkable outcome and
descriptive text are not rules; they go to `excluded`.

```json
{
  "rule_id": "CPR-01",
  "clause": "Appendix B row B1",
  "page": 12,
  "type": "procedure",
  "scope": { "contract_types": ["goods", "services"],
             "condition": "value from 25,000 up to the Threshold" },
  "threshold_low":  { "value": 25000, "parameter": null, "inclusive": true },
  "threshold_high": { "value": null, "parameter": "threshold_goods_services", "inclusive": false },
  "required_action": "invitations to quote to at least three sources via the Procurement Portal",
  "approver": null,
  "evidence_source": "appendix-table",
  "quote": ["£25,000 or more and less than the", "least three appropriate sources"]
}
```

- `rule_id`: `CPR-01`, `CPR-02`, ... in document order, no gaps.
- `clause`: the dotted number as printed (`6.16`, `7.4.2`), or for appendices
  `Appendix A row 1`..`4` (top to bottom), `Appendix B row A|B1|B2|C|D`,
  `Appendix B notes`, `Appendix C row A`..`F`, `Appendix C closing paragraph`.
- `page`: the PDF page where the quoted text is printed.
- `type`: `procedure` (quotes, tenders, evaluation), `approval` (who decides),
  `exception` (waivers and exclusions from competition), `advertising`,
  `anti-avoidance` (the no-splitting rule and its aggregation companions),
  `documentation` (records, reports, retention), `legal-form` (writing, seal,
  bond, insurance).
- `scope.contract_types`: any of `goods`, `services`, `works`, `concession`,
  `light_touch`, or `["all"]`. `condition` is a short plain restatement.
- `threshold_low` / `threshold_high`: always objects.
  - `value`: GBP integer exactly as printed, or null.
  - `parameter`: the name of a declared parameter when the PDF only names the
    threshold ("the Threshold", "the relevant Threshold"), else null. Never set
    both `value` and `parameter`.
  - `inclusive`: true for "or more", "up to and including"; false for "above",
    "over", "more than", "less than", "below"; null only when there is no bound
    (all three null).
  - "Above £2.5million" is `value: 2500000`. Amounts are checked against the
    quote, so the figure must appear in it (`£2.5million` is recognised).
  - A printed amount that is not an integer ("more than £24,999.99" in 7.2):
    record `value: 25000, inclusive: true` (the same boundary) and add a note
    saying the PDF prints 24,999.99. The verifier accepts the 24,999.99 form
    for a 25000 bound.
- `required_action`: the obligation, short, in the PDF's words where possible.
- `approver`: the role as printed (e.g. `S.151 Officer`), or null. Do not infer
  an approver the clause does not name. Where two roles are named, join them
  as printed ("Monitoring Officer and S151 Officer").
- `evidence_source`: `clause` (numbered clause text), `appendix-table`,
  or `appendix-note`.
- `quote`: verbatim text from the stated page, a string or a list of
  contiguous fragments. Copy it from the extraction, never retype from memory.
  No ellipses; use separate fragments instead.

### parameters

The PDF names thresholds it never prints: Appendix B footnote *** says there
are three (works and concession; goods and services; light touch) and that the
values are on the Procurement intranet page. Declare exactly:

```json
"parameters": {
  "threshold_goods_services": null,
  "threshold_works_concession": null,
  "threshold_light_touch": null
}
```

Every value stays `null`. Never fill one from memory or from the legislation,
even though they are public: the audit must use the value the auditor supplies
and records. Rules point at a parameter through `threshold_low.parameter` /
`threshold_high.parameter`. Declare a further parameter only when the PDF names
another unprinted quantity; do not declare one nobody uses.

### excluded

Every clause that is not a rule, each with a one-line reason (a single line,
200 characters at most):

```json
{ "clause": "1.5", "page": 1, "reason": "definition of procuring; no threshold, action or approver" }
```

A parent clause covers its children: excluding `10.7` covers `10.7.1` to
`10.7.10`. Use that for lists of the same kind, and for sections excluded
wholesale list each numbered clause (`2.1`, `2.2`, `2.3`); a bare section
number such as `2` is not accepted. Do not list a clause in both `rules`
and `excluded`.

Coverage is enforced: every dotted clause number found in pages 1-10 and every
appendix row (A: rows 1-4; B: rows A, B1, B2, C, D and notes; C: rows A-F and
the closing paragraph) must appear in `rules` or `excluded`. A clause that
holds both a testable part and untestable text becomes a rule.

### notes

Contradictions and drafting gaps in the PDF itself. Report what the text says,
without deciding which side is right.

```json
{ "kind": "contradiction", "clauses": ["6.15", "Appendix B"],
  "text": "6.15 counts VAT in contract value; Appendix B thresholds are exclusive of VAT.",
  "quotes": [ { "page": 5, "quote": "Value Added Tax" },
              { "page": 12, "quote": "Total Value exclusive of VAT" } ] }
```

`kind` is `contradiction` (two passages disagree; both quoted) or `gap`
(missing, placeholder, misnumbered, undefined or uncovered; quote where
possible). `quotes` are verified like rule quotes.

Leads to check against the text, not conclusions to copy:

- **Boundaries.** Appendix A rows and 7.4 leave exact values at £500,000 and
  £2.5million in no row or two rows ("less than" against "above"; "or more"
  against "in excess of"). Appendix B's lowest band starts "above £1,000" and
  nothing covers payments up to £1,000.
- **Key Decision.** Compare the over-£500,000 Key Decision paragraph in
  4.2-4.4 (the headings print together, so the clause number is inferred from
  paragraph order) with Appendix A, where Key Decision wording sits with the
  £2.5million-or-more row only.
- **VAT.** 6.15 includes VAT; Appendix B excludes it.
- **SME and local suppliers.** Appendix B asks for at least one SME/VCSE and
  one local supplier; footnote ** says the Council cannot prefer them.
- **Waiver scope.** 7.2 applies above £24,999.99; 7.4.1 reaches "all contracts
  up to the Threshold".
- **Numbering.** 6.23 is a heading numbered as a clause; 7.5.3/7.5.4 text is
  displaced; 7.1 and 7.7 repeat each other; 10.2 cites Appendix B for which
  contracts must be written but Appendix B does not say.
- **Undefined or unprinted.** "the Threshold" (1.4, 6.5, throughout),
  "appropriate source", "local supplier", "relevant board", "annual or total
  value" (Appendix C closing paragraph), the unfilled `Parts []`, and the
  difference between the £5,000 tender-publication figure in 5.2 and the
  £25,000 band in Appendix B.
- **Data fit.** The PDF's thresholds apply to total contract value; the spend
  data holds single payments. That belongs in the spend-analyst's limitations,
  not here, unless a clause says otherwise.

Only keep a lead after you have read both passages and confirmed it.

## 3. Verify, then fix until it passes

```
.venv/Scripts/python.exe -I .claude/skills/extract-rules/verify_quotes.py outputs/rules.json
```

Run it after writing the file, read every `ERROR` line, fix the JSON from the
PDF text and run it again. Repeat until it prints `PASS`. Exit codes: 0 pass,
1 errors, 2 could not run. The checks:

| Code | Meaning |
| --- | --- |
| `E-SCHEMA` | missing or extra field, wrong type or enum, bad threshold object, low above high |
| `E-ID` | rule IDs not `CPR-01`, `CPR-02`, ... in order |
| `E-PARAM` | undeclared parameter, or a parameter value that is not null |
| `E-QUOTE` | a quote fragment is not on the stated page (the message says if it is on another page) |
| `E-FIGURE` | a threshold amount is not printed in that rule's quote |
| `E-COVERAGE` | a clause or appendix row is in neither list, listed twice, or not in the PDF |
| `E-EXCLUDED` | an excluded entry lacks a clause, page, or one-line reason |
| `E-NOTE` | a note is malformed or its quote is not on its page |

`WARN` lines (a clause number that does not start on the stated page, an
unused parameter, no `anti-avoidance` rule) do not fail the run: look at each
and fix or accept it knowingly. A passing run proves the quotes exist and the
structure is complete. It does not prove that you classified a clause correctly
or that a threshold is on the right side of inclusive/exclusive; reread those
against the quote before you finish.

Never edit a quote to make the check pass. If a quote does not match, the
extraction text is the authority. If a figure is not printed, the rule cannot
use it.

## 4. Report back

Give counts (rules, excluded, notes), the parameters that need the auditor to
supply a value, each `contradiction` note in one line, and the verifier's final
line. Do not describe wrongdoing; these notes are drafting issues in the Rules.
