"""Loads the Part A prompts (.claude/agents/*.md, .claude/skills/*/SKILL.md) and defines
how each one runs in the harness: its tools, the one file it may write, its turn limit.

The prompts are used as written. A short harness note is appended that maps the
Claude Code tools they mention onto the harness tools.
"""
import re
from dataclasses import dataclass, field

from .config import ROOT

TEAM = ("planner", "challenger", "qa-reviewer")
MEMBERS = TEAM + ("team-lead",)

HARNESS_NOTE = """

---
# Harness note (overrides any conflicting instruction above)

You are running inside a web harness, not Claude Code. You have no shell and no file
system beyond the tools below. Paths are relative to the workspace: `data/...` (inputs,
read-only) and `outputs/...`.

| Instruction above says | Do this instead |
| --- | --- |
| Bash / run a Python script / `.venv/...python` | `run_builder(name, args)`. Names: `clean`, `analyse`, `verify_quotes`, `verify_history`, `build_register`, `build_pack` (`--gate` to check the gate), `run_checks`, `signoff_report`. Pass only the flags and paths the instruction shows, workspace-relative, e.g. `run_builder("verify_quotes", ["outputs/rules.json"])`. |
| Read / Glob / Grep a file | `read_file(path, offset)` for text files, `query_csv(path, ...)` for CSVs (aggregates and small heads only) |
| `pdftotext -f N -l N file` | `read_pdf_page(file, page, layout)` |
| Write / Edit a file | `write_output(path, content)`: always the whole file; only the path(s) listed in the tool description |
| SendMessage | `send_message(to, text)` |
| Writing your own analysis scripts | Not available. The existing scripts run through `run_builder`. |
| Agent memory, CLAUDE.md, `.claude/` paths | Not available; ignore them. |

Work in as few model turns as you can: call several tools in one turn when they are
independent, never page through large files, and finish with a short plain-text report.
Outputs are risk indicators to investigate, never accusations.
"""


@dataclass
class AgentSpec:
    name: str
    prompt_file: str                 # under .claude/
    skill: str = ""                  # SKILL.md folder appended to the prompt, if any
    tools: tuple = ()
    writes: tuple = ()
    max_steps: int = 12
    note: str = ""


SPECS = {
    "extract-rules": AgentSpec("extract-rules", "", skill="extract-rules",
                               tools=("read_pdf_page", "read_file", "write_output", "run_builder"),
                               writes=("outputs/rules.json",), max_steps=14),
    "spend-analyst": AgentSpec("spend-analyst", "agents/spend-analyst.md",
                               tools=("read_file", "query_csv", "run_builder"), writes=(), max_steps=10),
    "findings-analyst": AgentSpec("findings-analyst", "agents/findings-analyst.md",
                                  tools=("read_pdf_page", "read_file", "write_output", "run_builder"),
                                  writes=("outputs/history.json",), max_steps=16),
    "risk-assessor": AgentSpec("risk-assessor", "agents/risk-assessor.md", skill="risk-assessment",
                               tools=("read_file", "query_csv", "write_output", "run_builder"),
                               writes=("outputs/risk-ratings.json",), max_steps=14),
    "planner": AgentSpec("planner", "agents/planner.md", skill="audit-program",
                         tools=("read_file", "query_csv", "write_output", "run_builder", "send_message"),
                         writes=("outputs/audit-plan.json",), max_steps=14),
    "challenger": AgentSpec("challenger", "agents/challenger.md",
                            tools=("read_file", "query_csv", "write_output", "send_message"),
                            writes=("outputs/challenges.md",), max_steps=10),
    "qa-reviewer": AgentSpec("qa-reviewer", "agents/qa-reviewer.md",
                             tools=("read_file", "write_output", "run_builder", "send_message"),
                             writes=("outputs/review.md",), max_steps=8),
}

STAGE_TASKS = {
    "extract-rules": "Run the extract-rules skill on data/contract-rules.pdf and write outputs/rules.json. Verify it with the verify_quotes builder and fix every error. Finish with a short report.",
    "spend-analyst": "Run the analysis: call run_builder clean, then analyse, then read outputs/analytics.json (headline fields only) and report the findings per test as risk indicators. Do not try to write analytics.json yourself.",
    "findings-analyst": "Read the committee papers in data/committee/ and write outputs/history.json as your instructions describe. Verify it with the verify_history builder and fix every error. Finish with a short report.",
    "risk-assessor": "Build the first risk register: read outputs/rules.json, analytics.json and history.json, write outputs/risk-ratings.json, and run build_register until it reports no failures and no warnings. Recommend scope; do not approve it. Finish with a short report.",
}


def _read(rel):
    return (ROOT / ".claude" / rel).read_text(encoding="utf-8")


def _strip_frontmatter(text):
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def system_prompt(name):
    spec = SPECS[name]
    parts = []
    if spec.prompt_file:
        parts.append(_strip_frontmatter(_read(spec.prompt_file)))
    if spec.skill:
        parts.append("# Skill: %s\n\n%s" % (spec.skill, _strip_frontmatter(_read("skills/%s/SKILL.md" % spec.skill))))
    return "\n\n".join(parts) + HARNESS_NOTE


def load_all():
    """Used by tests: every prompt must load."""
    return {n: system_prompt(n) for n in SPECS}
