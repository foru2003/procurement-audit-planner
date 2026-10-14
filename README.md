# Procurement Audit Planner

An agent system, built with Claude Code skills, sub-agents, a human gate and an agent team, that plans an internal audit of procurement for **West Berkshire Council** from its public data.

## 1. Overview

The system turns the council's Contract Procedure Rules (Part 8) into 64 testable rules, analyses every payment in three monthly "Expenditure over £500" workbooks against them, folds in the council's past audit opinions and its own risk-scoring method, and rates nine risks on the council's 5x5 matrix. A human auditor approves, amends or rejects each risk; an agent team then turns the approved risks into a planning memo, a risk-control matrix and an audit program with a targeted sample, and the auditor signs the pack off. Python computes every number and checks every citation; the language model reads, judges and writes.

> **The outputs are risk indicators for audit planning, not findings of wrongdoing.** A pattern in public data (for example a payment run just under a threshold, or a supplier with no contract notice) is a lead to test during fieldwork. Nothing here says the council, a department, an officer or a supplier did anything wrong.

## 2. Skills

| Skill | How it is triggered | What it produces | Script that computes or verifies it |
| --- | --- | --- | --- |
| `extract-rules` | **Run by me** (`/extract-rules`) | `outputs/rules.json`: 64 rules (each with clause, page, thresholds, approver and a verbatim quote), 45 excluded clauses with reasons, 20 notes on contradictions and gaps in the Rules | `.claude/skills/extract-rules/verify_quotes.py` checks every quote is on its stated PDF page, the schema, sequential rule IDs, and that every clause is in `rules` or `excluded` |
| `risk-assessment` | **Loaded by an agent** (`risk-assessor`) | `outputs/risk-ratings.json` (the agent's cited judgments), then `outputs/risk-register.md` and the `outputs/auditor-comments.md` decision template | `.claude/skills/risk-assessment/build_register.py` resolves every `[rule:]`, `[metric:]` and `[history:]` citation, fills every `{{$.path}}` figure from `analytics.json`, computes score, matrix label and band from the council's matrix, drops any risk without a resolvable citation, and checks revisions against the auditor's decisions |
| `audit-program` | **Loaded by an agent** (`planner`) | `outputs/audit-plan.json` (the planner's judgments), then `planning-memo.md`, `risk-control-matrix.md`, `audit-program.md`, `outputs/samples/T-*.csv` and `pack-figures.json` | `.claude/skills/audit-program/build_pack.py` checks the auditor gate (`--gate`), resolves citations, draws every sample deterministically (10 items for scores of 9 and above, 5 below), verifies each transaction exists, and checks that every rule is cited or listed as not tested; `scripts/checks/*.py` then re-check the finished pack |

## 3. Agents

All six agents are in `.claude/agents/` and use project memory (`memory: project`).

| Agent | Role | Tools | Inputs | Outputs |
| --- | --- | --- | --- | --- |
| `spend-analyst` | Sub-agent. Cleans and analyses the full spend population; runs seven tests (threshold clustering, split purchases, high-value suppliers, off-contract, duplicates, expired-notice spend, spend vs award). Python computes every number | Bash, Read, Write, Edit, Glob, Grep | `rules.json`, `data/spend/*.xlsx`, `data/contracts.csv` | `outputs/analytics.json`, `outputs/analytics-full/`, and `scripts/clean.py`, `analyse.py`, `common.py`, `selfcheck.py` |
| `findings-analyst` | Sub-agent. Records audit opinions, follow-ups, risk themes and the council's scoring method from the committee papers; records, never scores | Bash, Read, Write, Edit, Glob, Grep | `data/committee/*.pdf` (4 papers) | `outputs/history.json`, verified by `scripts/verify_history.py` |
| `risk-assessor` | Sub-agent. Merges rules, analytics and history into rated risks following the `risk-assessment` skill; recommends scope, never approves it | Bash, Read, Write, Edit, Glob, Grep | `rules.json`, `analytics.json`, `history.json` (and `auditor-comments.md` on a re-run) | `outputs/risk-ratings.json`; the builder writes the register and the comments template |
| `planner` | Team member. Writes the audit plan for the approved risks only and runs the builder | Bash, Read, Write, Edit, Glob, Grep, SendMessage | register, auditor comments, ratings, `rules.json`, `analytics.json` | `outputs/audit-plan.json`; the builder writes the pack |
| `challenger` | Team member. Sends up to eight challenges, then up to four more, and records each with the planner's response and a status | Bash, Read, Write, Edit, Glob, Grep, SendMessage | register, comments, ratings, `rules.json`, `analytics.json`, `history.json`, the planner's pack | `outputs/challenges.md` |
| `qa-reviewer` | Team member. Runs the four QA checks and blocks sign-off until all pass; fixes nothing | Bash, Read, Write, Glob, Grep, SendMessage | the pack and `scripts/checks/run_checks.py` | `outputs/review.md` (results, verdict, sign-off block) |

## 4. How they work together

```mermaid
flowchart TD
    PDF["data/contract-rules.pdf"] --> ER["/extract-rules skill<br/>run by the auditor<br/>verify_quotes.py"]
    ER --> RULES["outputs/rules.json"]
    SPEND["data/spend/*.xlsx<br/>data/contracts.csv"] --> SA["spend-analyst agent<br/>clean.py, analyse.py, selfcheck.py"]
    RULES --> SA
    SA --> ANA["outputs/analytics.json<br/>outputs/analytics-full/"]
    COMM["data/committee/*.pdf"] --> FA["findings-analyst agent<br/>verify_history.py"]
    FA --> HIST["outputs/history.json"]
    RULES --> RA
    ANA --> RA
    HIST --> RA["risk-assessor agent<br/>loads the risk-assessment skill<br/>build_register.py"]
    RA --> REG["outputs/risk-register.md<br/>outputs/auditor-comments.md"]
    REG --> G1{{"HUMAN GATE 1<br/>auditor records Approve, Amend or Reject"}}
    G1 -- "Amend or Reject: revision" --> RA
    G1 -- "all decided and applied" --> GATE["build_pack.py --gate"]
    GATE --> TEAM
    subgraph TEAM["Agent team (Phase 3)"]
        PL["planner<br/>audit-program skill<br/>audit-plan.json, build_pack.py"]
        CH["challenger<br/>challenges.md"]
        QA["qa-reviewer<br/>scripts/checks/run_checks.py<br/>review.md"]
        PL -- "PACK READY vN" --> CH
        PL -- "PACK READY vN" --> QA
        CH -- "CHALLENGE #n" --> PL
        QA -- "QA vN: FAIL" --> PL
    end
    TEAM --> PACK["planning-memo.md<br/>risk-control-matrix.md<br/>audit-program.md<br/>samples/"]
    PACK --> G2{{"HUMAN GATE 2<br/>auditor signs off in review.md<br/>signoff.py record"}}
    G2 --> DONE["Signed-off audit planning pack"]
```

**Design.** The model reads and judges; Python computes every figure, so no agent does arithmetic over the data. Each judgment is written to a JSON file (`risk-ratings.json`, `audit-plan.json`) that a builder script validates before any document is rendered, and a risk or plan entry that cannot be traced to a rule, a named metric or a history item is dropped or rejected. The first human gate sits between the register and the pack: the register is a revision only once the auditor's decisions are applied, and `build_pack.py --gate` refuses to start otherwise. Inside the agent team the planner owns the plan, the challenger owns `challenges.md`, and the qa-reviewer owns `review.md`; each owns exactly one file and talks to the others by message. The second human gate is the sign-off block, which `scripts/signoff.py` records only when all four checks pass and a real name is given.

## 5. Human gate decisions

**Gate 1: risk decisions** (`outputs/auditor-comments.md`, applied in the register as Revision 2):

| Risk | Decision | Applied in |
| --- | --- | --- |
| R-01 Splitting and threshold avoidance | Approve | revision 1 |
| R-02 to R-08 | Approve (each recorded 2026-10-13) | revision 2 |
| R-09 Delegated approval and Key Decisions | **Amend**: "Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes." Applied as an auditor override (likelihood 2 to 3, score 4 to 6, still Moderate; the assessor's own rating stays visible in the register) | revision 1 |

No risk was rejected; all nine are in scope.

**Gate 2: sign-off** (`outputs/review.md`): Reviewer **Forum Sanjanwala**, date **2026-10-13**, decision **Signed off**. The Comments line is blank. The review lists three points marked *for the auditor* that were not actioned: **#6** (whether R-08 should stay at 4), **#7** (whether the 308 unmatched care and education placement suppliers should be in scope) and **#9** (whether T-09.1's sample of two suppliers is enough for the Key Decision test).

## 6. Results

| Stage | Result |
| --- | --- |
| Rules | 64 rules, 45 excluded clauses, 20 notes (15 gaps, 5 contradictions); 3 threshold parameters left `null` because the PDF never prints them |
| Spend data | 10,607 rows (1 May to 31 July 2026) reduced to 8,527 after exclusions (2,015 redacted-supplier, 12 pension and statutory, 46 inter-authority, 7 non-procurement accounting); £66,764,299.64 in total |
| Contract notices | 150 rows in `contracts.csv`, 141 for the council, 210 notice-supplier pairs, 130 active in the spend window |
| Supplier matching | 674 suppliers at or above the £25,000 quote threshold (annualised): 40 exact matches to a live notice, 6 candidates for the auditor to confirm, 628 with no active notice found (a lead to check against the contract register, not evidence) |
| Audit history | 16 audit opinions, 3 follow-ups, 1 advisory review, 0 agreed actions, 12 discrepancies and 7 gaps recorded; the council's scoring method was found |
| Risk register | 9 risks: 5 Medium High, 4 Moderate, none Extreme (Revision 2) |
| Audit pack | 9 risks in scope, 17 controls, 19 tests, 289 sampled transactions worth £16,742,264.39, 23 PBC items; 42 of 64 rules cited, 22 listed as not tested with reasons |
| Challenges | 9: 6 resolved, 3 for the auditor |
| QA | 4 of 4 checks pass (quotes; 313 figures traced; 64 rules traced; 289 transactions found at their workbook rows). Verdict: **READY FOR SIGN-OFF**, pack v3 |

**Limitations.** Contract notices are published notices, not the council's contract register. Spend covers payments over £500 for three months only. Ten analysis tiers were skipped because the Threshold values the Rules refer to are not printed in the PDF. In the recorded run the planner, challenger and qa-reviewer were started as general-purpose agents that each read their own agent file, with messages addressed by agent ID, because the agent files were created after the Claude Code session began.

## 7. Steps completed

The guide at <https://procurement-audit-planner.vercel.app> has 5 lessons and 27 steps. The progress tracker below shows all of them complete:

| Lesson | Steps |
| --- | --- |
| Setup | 7/7 |
| Skills | 2/2 |
| Sub-agents | 7/7 |
| Human gate | 3/3 |
| Agent teams | 8/8 |
| **Overall** | **27/27** |

![Progress tracker showing 27/27 steps complete](docs/progress.png)

**How each component was made.**

*Generated from prompts*

- Skills: `extract-rules` and its `verify_quotes.py`; `risk-assessment` and its `build_register.py`
- Agents: `findings-analyst`, `risk-assessor`, `challenger`, `qa-reviewer`
- Scripts: `scripts/verify_history.py`, `scripts/signoff.py`, and the five QA scripts in `scripts/checks/`; `scripts/clean.py`, `analyse.py`, `common.py` and `selfcheck.py` were written by the `spend-analyst` agent when it ran
- Configuration and outputs: `.claude/settings.json`, `requirements-analytics.txt`, and everything in `outputs/`

*Copied as finished files (then adapted to this project)*

- `CLAUDE.md` (pasted whole; edited since by prompts)
- The `audit-program` skill: `SKILL.md` and `build_pack.py` (pasted; adapted to this project's file formats, then extended by prompt with sample sizing by score, a language check and the one-line gate output)
- The `spend-analyst` agent (pasted; paths and rule-reading adapted to this project, then updated from the data study)
- The `planner` agent: the pasted `planner.md` is the version in the repo. It replaced an earlier planner that had been written from a prompt. Three changes were made to the pasted file: `SendMessage` was added to its tools (without it the planner could not message its teammates); `PLANNER DONE` now waits for the qa-reviewer's `QA vN: PASS` on the latest version; and `PLANNER DONE` is sent to the qa-reviewer as well as the lead
- The public data in `data/` and the screenshot `docs/progress.png`

*Guide versions pasted but not used.* Finished guide versions of the `extract-rules` skill (with its verifier), the `findings-analyst`, `risk-assessor`, `challenger` and `qa-reviewer` agents, and the check scripts `run_checks.py`, `check_quotes.py`, `check_numbers.py` and `check_trace.py` were also pasted during the build. The repository holds the generated versions of all of these, not the pasted ones.

## 8. How to run it on Windows

You need Windows, Python 3.9, Claude Code, and the poppler-style tools `pdftotext` and `pdfinfo` on your PATH (they came with MiKTeX on the machine this was built on).

```
:: 1. Create the environment and install the two packages
py -3.9 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-analytics.txt

:: 2. Put the public data in place (names as used here)
::    data\contract-rules.pdf   data\contracts.csv
::    data\spend\Over500_2026_P02_-_published.xlsx (and P03, P04)
::    data\committee\*.pdf      (the 4 Governance Committee papers)
```

Open the project folder in Claude Code, then work through the flow in `CLAUDE.md`:

1. Run `/extract-rules`. It writes `outputs/rules.json` and checks it with `verify_quotes.py`.
2. Ask Claude to run the `spend-analyst`, then the `findings-analyst`. They write `outputs/analytics.json` and `outputs/history.json`.
3. Ask Claude to run the `risk-assessor`. It writes `outputs/risk-register.md` and `outputs/auditor-comments.md`.
4. Gate 1: fill the Decision (Approve, Amend or Reject) and Comment columns in `outputs/auditor-comments.md`, then run the `risk-assessor` again to apply them as a revision.
5. Check the gate: `.venv\Scripts\python.exe .claude\skills\audit-program\build_pack.py --gate`
6. Run the agent team (planner, challenger, qa-reviewer). Agent teams are switched on by `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in `.claude/settings.json`; restart Claude Code after changing it or adding agent files.
7. Print the team report: `.venv\Scripts\python.exe scripts\signoff.py report`
8. Gate 2: record the sign-off with your own name: `.venv\Scripts\python.exe scripts\signoff.py record --name "Your Name"`. It refuses unless the QA checks pass. To run the checks yourself: `.venv\Scripts\python.exe scripts\checks\run_checks.py`

## 9. Repository structure

```
procurement-audit-planner/
  CLAUDE.md                  # full system spec and the lead procedure for the agent team
  README.md                  # this file
  requirements-analytics.txt         # pandas, openpyxl
  .gitignore
  data/                      # public inputs, read-only
    contract-rules.pdf       #   Contract Procedure Rules (Part 8)
    contracts.csv            #   Contracts Finder export
    spend/*.xlsx             #   3 monthly "Expenditure over £500" workbooks
    committee/*.pdf          #   4 Governance Committee papers
  docs/progress.png          # guide progress tracker (27/27)
  .claude/
    settings.json            # turns on agent teams
    agents/                  # spend-analyst, findings-analyst, risk-assessor,
                             #   planner, challenger, qa-reviewer
    skills/
      extract-rules/         #   SKILL.md, verify_quotes.py
      risk-assessment/       #   SKILL.md, build_register.py
      audit-program/         #   SKILL.md, build_pack.py
  scripts/
    clean.py, analyse.py,    # written by the spend-analyst agent
      common.py, selfcheck.py
    verify_history.py        # checks history.json quotes against the committee PDFs
    signoff.py               # team-done report and the auditor's sign-off recorder
    checks/                  # QA scripts: run_checks.py, check_quotes.py,
                             #   check_numbers.py, check_trace.py, check_samples.py
  outputs/
    rules.json, analytics.json, analytics-full/, history.json
    risk-ratings.json, risk-register.md, auditor-comments.md
    audit-plan.json, planning-memo.md, risk-control-matrix.md, audit-program.md
    samples/, pack-figures.json, challenges.md, review.md
```
