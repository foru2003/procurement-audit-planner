"""The workflow: stages, the two human gates, the agent team, Live and Replay.

Run holds everything for one session and has no Streamlit dependency, so it is
testable with a fake model. Live stages call an LLM; Replay stages copy the Part A
outputs and walk the same stages and gates with no model calls.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from . import agents
from .caps import CapReached
from .config import ROOT
from .llm import LLMError
from .tools import Toolbox
from .workspace import Workspace

STAGES = [
    ("rules", "1. Extract rules", "extract-rules", "skill, run by the human in Part A"),
    ("spend", "2. Spend analysis", "spend-analyst", "sub-agent"),
    ("findings", "3. Audit history", "findings-analyst", "sub-agent"),
    ("risks", "4. Risk register", "risk-assessor", "sub-agent + risk-assessment skill"),
    ("gate1", "5. Human Gate 1", "", "auditor decisions per risk"),
    ("team", "6. Agent team", "planner, challenger, qa-reviewer", "audit-program skill"),
    ("gate2", "7. Human Gate 2", "", "auditor sign-off"),
]
STAGE_IDS = [s[0] for s in STAGES]

REPLAY_FILES = {
    "rules": ["rules.json"],
    "spend": ["analytics.json", "analytics-full/*"],
    "findings": ["history.json"],
    "risks": ["risk-ratings.json", "risk-register.md", "auditor-comments.md"],
    "team": ["audit-plan.json", "planning-memo.md", "risk-control-matrix.md", "audit-program.md",
             "pack-figures.json", "challenges.md", "review.md", "samples/*"],
}
STAGE_OUTPUTS = {
    "rules": ["outputs/rules.json"],
    "spend": ["outputs/analytics.json"],
    "findings": ["outputs/history.json"],
    "risks": ["outputs/risk-register.md", "outputs/auditor-comments.md", "outputs/risk-ratings.json"],
    "team": ["outputs/planning-memo.md", "outputs/risk-control-matrix.md", "outputs/audit-program.md",
             "outputs/challenges.md", "outputs/review.md"],
}
BLANK_SIGNOFF = "Reviewer: ______________________    Date: ______________\n\nDecision:   [ ] Signed off      [ ] Returned for rework"
SIGNOFF_BLOCK = re.compile(r"(Reviewer:)[^\n]*?(\s+Date:)[^\n]*\n(\s*\n)?(Decision:)[^\n]*", re.M)


class StageError(Exception):
    """A live stage finished without producing what it must."""


class Run:
    def __init__(self, mode, llm=None, budget=None, pause=0.0, on_event=None, sleep=time.sleep):
        self.mode, self.llm, self.budget = mode, llm, budget
        self.pause_seconds, self.on_event, self.sleep = pause, on_event, sleep
        self.ws = Workspace()
        self.toolbox = Toolbox(self.ws)
        self.events, self.messages = [], []
        self.status = {sid: "todo" for sid in STAGE_IDS}
        self.reports = {}
        self.turns = 0
        self.turn_log = []
        self.fallback_reason = ""

    # ---- plumbing ----------------------------------------------------
    def emit(self, kind, text, agent=""):
        ev = {"t": datetime.datetime.now().strftime("%H:%M:%S"), "agent": agent, "kind": kind, "text": text}
        self.events.append(ev)
        if self.on_event:
            self.on_event(ev)

    def close(self):
        self.ws.cleanup()

    def _agent_turn(self, name, task, inbox_agent=None):
        """One agent turn = one run_agent call (several model requests). Pauses between turns."""
        if self.turns and self.pause_seconds:
            self.emit("wait", "pausing %ds between agent turns (free-tier rate limits)" % self.pause_seconds, name)
            self.sleep(self.pause_seconds)
        self.turns += 1
        spec = agents.SPECS[name]
        tb = self.toolbox
        tools = tb.tools_for(spec.tools, write_paths=spec.writes, sender=name, members=agents.MEMBERS)
        self.emit("agent", "%s starts" % name, name)
        self.llm.emit = lambda kind, text, _n=name: self.emit(kind, text, _n)
        t0, used0 = time.time(), self.budget.used if self.budget else 0
        res = self.llm.run_agent(agents.system_prompt(name), task, tools, max_steps=spec.max_steps, label=name)
        self.emit("agent", "%s done after %d model request(s)%s" % (name, res.steps, " (step limit reached)" if res.truncated else ""), name)
        self.turn_log.append({"agent": name, "seconds": round(time.time() - t0, 1), "steps": res.steps, "truncated": res.truncated,
                              "calls": (self.budget.used - used0) if self.budget else None,
                              "model": getattr(self.llm, "model", ""), "final_text": (res.text or "")[:400]})
        return res

    def _run_script(self, args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        p = subprocess.run([sys.executable] + args, cwd=self.ws.root, capture_output=True, env=env, timeout=150)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()

    def _builder(self, name, args=None):
        r = self.toolbox.run_builder(name, args)
        return r.get("exit_code"), r.get("output", r.get("error", ""))

    # ---- stages ------------------------------------------------------
    def run_stage(self, sid):
        self.status[sid] = "running"
        try:
            if self.mode == "replay":
                self._replay_stage(sid)
            else:
                self._live_stage(sid)
        except BaseException:
            self.status[sid] = "failed"
            raise
        self.status[sid] = "done"

    def _live_stage(self, sid):
        name = {"rules": "extract-rules", "spend": "spend-analyst",
                "findings": "findings-analyst", "risks": "risk-assessor"}[sid]
        res = self._agent_turn(name, agents.STAGE_TASKS[name])
        self.reports[sid] = res.text
        missing = [f for f in STAGE_OUTPUTS[sid] if not self.ws.exists(f)]
        if missing:
            raise StageError("%s did not produce %s" % (name, ", ".join(missing)))
        if sid == "rules":
            code, out = self._builder("verify_quotes", ["outputs/rules.json"])
            self.emit("check", "verify_quotes: " + out.splitlines()[-1] if out else "verify_quotes: no output")
            if code != 0:
                raise StageError("rules.json fails quote verification: " + out[-400:])
        if sid == "findings":
            code, out = self._builder("verify_history", ["outputs/history.json"])
            self.emit("check", "verify_history: " + (out.splitlines()[-1] if out else "no output"))
            if code != 0:
                raise StageError("history.json fails verification: " + out[-400:])
        if sid == "spend":
            sp = self.toolbox.spend
            if sp["path"] is None:
                raise StageError("spend-analyst never ran the analysis scripts")
            self.emit("check", self.spend_label())

    def spend_label(self):
        sp = self.toolbox.spend
        if self.mode == "replay" or sp["path"] == "replay":
            return "Spend analysis: precomputed Part A analytics (Replay)."
        if sp["path"] == "live":
            peak = ("%d MB peak memory, " % sp["peak_mb"]) if sp["peak_mb"] else ""
            return "Spend analysis: re-run live from the raw workbooks (%s%.1fs)." % (peak, sp["secs"])
        if sp["path"] == "precomputed":
            return "Spend analysis: precomputed Part A analytics, because the live run %s." % sp["reason"]
        return "Spend analysis: not run yet."

    def _replay_stage(self, sid):
        copied = []
        for pattern in REPLAY_FILES.get(sid, []):
            for src in sorted((ROOT / "outputs").glob(pattern)):
                if src.is_file():
                    rel = src.relative_to(ROOT / "outputs")
                    dst = self.ws.outputs / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    data = src.read_bytes()
                    if src.suffix in (".md", ".json", ".csv"):
                        data = data.replace(b"\r\n", b"\n")
                    if src.name == "review.md":
                        data = self._reset_signoff(data.decode("utf-8")).encode("utf-8")
                    dst.write_bytes(data)
                    copied.append(str(rel))
        if sid == "spend":
            self.toolbox.spend["path"] = "replay"
        self.emit("replay", "Replay: loaded %d Part A file(s) for this stage (no model calls)" % len(copied))
        self.sleep(0.3)
        if sid == "team":
            for m in replay_team_messages(self.ws):
                self.messages.append(m)
        if sid == "rules":
            pass

    @staticmethod
    def _reset_signoff(text):
        return SIGNOFF_BLOCK.sub(lambda m: BLANK_SIGNOFF, text, count=1)

    # ---- Gate 1 ------------------------------------------------------
    def risks_for_gate(self):
        """[{id, statement, rating, decision, comment}] from auditor-comments.md."""
        rows = []
        for line in self.ws.read_text("outputs/auditor-comments.md").splitlines():
            cells = _cells(line)
            if len(cells) >= 5 and re.fullmatch(r"R-\d+", cells[0]):
                rows.append({"id": cells[0], "statement": cells[1], "rating": cells[2],
                             "decision": cells[3], "comment": cells[4]})
        return rows

    def record_gate1(self, decisions, reviewer=""):
        """decisions: {risk_id: (decision, comment)}. Writes auditor-comments.md."""
        if self.mode == "replay":
            recorded = {r["id"]: (r["decision"].lower(), "") for r in self.risks_for_gate()}
            changed = [rid for rid, (d, _) in decisions.items() if recorded.get(rid, ("",))[0] != d.lower()]
            if changed:
                self.emit("replay", "Replay keeps the recorded Part A decisions; your changed decisions for %s apply in Live mode only" % ", ".join(changed))
            self.emit("gate", "Gate 1 closed in Replay with the recorded decisions")
            self.status["gate1"] = "done"
            return
        path = self.ws.root / "outputs" / "auditor-comments.md"
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = _cells(line)
            if len(cells) >= 5 and cells[0] in decisions:
                d, c = decisions[cells[0]]
                cells[3], cells[4] = d, c.replace("|", "\\|").replace("\n", " ")
                line = "| " + " | ".join(x.replace("|", "\\|") if i not in (3, 4) else x for i, x in enumerate(cells)) + " |"
            out.append(line)
        text = "\n".join(out) + "\n"
        text = re.sub(r"^(Reviewer|Date):.*\n", "", text, flags=re.M)
        if reviewer:
            text = text.replace("\n\n|", "\n\nReviewer: %s\nDate: %s\n\n|" % (reviewer, datetime.date.today().isoformat()), 1)
        path.write_text(text, encoding="utf-8")
        self.emit("gate", "Gate 1: %d decision(s) written to auditor-comments.md" % len(decisions))
        self._apply_decisions(decisions)
        self.status["gate1"] = "done"

    def _apply_decisions(self, decisions):
        """Make the register a revision that applies the decisions: the builder alone if all Approve."""
        if all(d.lower() == "approve" for d, _ in decisions.values()):
            # Approve changes no rating, so the revision block is mechanical: next number, no changes.
            m = re.search(r"^## Revision (\d+)\s*$", self.ws.read_text("outputs/risk-register.md"), re.M)
            ratings = json.loads(self.ws.read_text("outputs/risk-ratings.json"))
            ratings["revision"] = {"number": (int(m.group(1)) if m else 0) + 1, "changes": []}
            (self.ws.outputs / "risk-ratings.json").write_text(json.dumps(ratings, indent=1), encoding="utf-8")
            code, out = self._builder("build_register")
            self.emit("check", "build_register (all approved, no model call): " + (out.splitlines()[-1] if out else ""))
            if code != 0:
                raise StageError("build_register failed: " + out[-400:])
        else:
            res = self._agent_turn("risk-assessor",
                                   "The auditor has recorded decisions in outputs/auditor-comments.md. Apply exactly those decisions as a revision "
                                   "(Amend: change what the comment says; Reject: exclude the risk with the reason), then run build_register until it "
                                   "reports no failures and no warnings. Do not approve or change anything the auditor did not.")
            self.reports["risks-revision"] = res.text
        code, out = self._builder("build_pack", ["--gate"])
        self.emit("check", "build_pack --gate: " + (out.splitlines()[-1] if out else ""))
        if code != 0:
            raise StageError("the gate is not closed: " + out[-500:])

    # ---- agent team --------------------------------------------------
    def run_team(self):
        self.status["team"] = "running"
        try:
            if self.mode == "replay":
                self._replay_stage("team")
            else:
                self._live_team()
        except BaseException:
            self.status["team"] = "failed"
            raise
        self.status["team"] = "done"

    def _gate_check(self):
        code, out = self._builder("build_pack", ["--gate"])
        if code != 0:
            raise StageError("gate check failed, the team is not started: " + out[-500:])
        return out

    def _send(self, sender, to, text):
        self.toolbox.send_message(sender, to, text, set(agents.MEMBERS))

    def _inbox(self, name, cursor):
        new = [m for m in self.messages[cursor[name]:] if m["to"] == name]
        cursor[name] = len(self.messages)
        return "\n".join("[from %s] %s" % (m["from"], m["text"]) for m in new) or "(no new messages)"

    def _team_turn(self, name, instruction, cursor):
        before = len(self.messages)
        task = "%s\n\nTeam: planner, challenger, qa-reviewer; the lead is team-lead. Your inbox:\n%s\n\nEnd your turn when you have done this turn's work." % (
            instruction, self._inbox(name, cursor))
        res = self._agent_turn(name, task)
        for m in self.messages[before:]:
            self.emit("message", "%s -> %s: %s" % (m["from"], m["to"], m["text"][:300]), m["from"])
        return res

    def _live_team(self):
        self.toolbox.team_log = self.messages
        self._gate_check()
        cur = {n: 0 for n in agents.MEMBERS}

        def sent(sender, to, needle):
            return [m for m in self.messages if m["from"] == sender and m["to"] == to and needle in m["text"]]

        self._team_turn("planner", "The auditor gate is closed (checked). Build the pack as the audit-program skill says; when the builder reports no failures "
                        "send `PACK READY v1` plus its summary line to challenger and qa-reviewer.", cur)
        if not sent("planner", "challenger", "PACK READY"):
            raise StageError("planner never sent PACK READY v1")
        for rnd in (1, 2):
            n0 = len(sent("challenger", "planner", "CHALLENGE"))
            self._team_turn("challenger", "Challenge round %d of 2. Read the current pack, keep outputs/challenges.md, and send CHALLENGE messages to planner for real weak spots "
                            "(none if there are none; then send CHALLENGER DONE)." % rnd, cur)
            if len(sent("challenger", "planner", "CHALLENGE")) == n0:
                break
            self._team_turn("planner", "Answer each CHALLENGE with RESPONSE #n, rebuild if you accept any, and send the next PACK READY.", cur)
        if not sent("challenger", "team-lead", "CHALLENGER DONE"):
            self._team_turn("challenger", "Closing turn. Verify the responses against the latest pack, finish outputs/challenges.md (status resolved / declined / for the auditor) "
                            "and send CHALLENGER DONE to team-lead, planner and qa-reviewer.", cur)
        qa_ok = False
        for attempt in range(3):
            n0 = len(self.messages)
            self._team_turn("qa-reviewer", "Run the checks on the current pack version and send QA vN: PASS or one QA vN: FAIL per failing check, as your instructions say. "
                            "Do not write review.md yet.", cur)
            fails = [m for m in self.messages[n0:] if m["from"] == "qa-reviewer" and "FAIL" in m["text"]]
            if not fails:
                qa_ok = True
                break
            if attempt < 2:
                self._team_turn("planner", "Fix every QA failure in your inbox (or explain why you cannot), rebuild and send the next PACK READY.", cur)
        if qa_ok:
            self._team_turn("planner", "QA passed. Send PLANNER DONE vN with the five-line summary to team-lead and qa-reviewer.", cur)
        self._team_turn("qa-reviewer", "Final step: write outputs/review.md (results as printed, verdict, points for the auditor, blank sign-off block) and send QA DONE to team-lead.", cur)
        if not self.ws.exists("outputs/review.md"):
            raise StageError("qa-reviewer did not write review.md")

    def team_report(self):
        code, out = self._builder("signoff_report")
        return code, out

    def checks_table(self):
        code, out = self._builder("run_checks")
        return code, out

    # ---- Gate 2 ------------------------------------------------------
    def record_signoff(self, name, decision, comment=""):
        args = [str(ROOT / "scripts" / "signoff.py"), "record", "--name", name,
                "--decision", "sign-off" if decision == "sign-off" else "return",
                "--outputs", str(self.ws.outputs), "--data", str(self.ws.data), "--full", str(self.ws.outputs / "analytics-full")]
        if comment:
            args += ["--comment", comment]
        code, out = self._run_script(args)
        if code == 0:
            self.status["gate2"] = "done"
            self.emit("gate", out)
        return code, out


def _cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return []
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", s)[1:-1]]


def replay_team_messages(ws):
    """Rebuild the team conversation from Part A's challenges.md and review.md (no model)."""
    msgs = [{"from": "planner", "to": "challenger", "text": "PACK READY v1 (replayed from the Part A run)"}]
    try:
        for line in ws.read_text("outputs/challenges.md").splitlines():
            c = _cells(line)
            if len(c) >= 8 and c[0].isdigit():
                msgs.append({"from": "challenger", "to": "planner", "text": "CHALLENGE #%s [%s] %s: %s Ask: %s" % (c[0], c[1], c[2], c[3], c[5])})
                msgs.append({"from": "planner", "to": "challenger", "text": "RESPONSE #%s: %s" % (c[0], c[6])})
        msgs.append({"from": "challenger", "to": "team-lead", "text": "CHALLENGER DONE"})
        for line in ws.read_text("outputs/review.md").splitlines():
            if re.match(r"- v\d+", line):
                msgs.append({"from": "qa-reviewer", "to": "planner", "text": "QA " + line[2:]})
        msgs.append({"from": "planner", "to": "team-lead", "text": "PLANNER DONE (replayed)"})
        msgs.append({"from": "qa-reviewer", "to": "team-lead", "text": "QA DONE"})
    except FileNotFoundError:
        pass
    return msgs


LIVE_ERRORS = (LLMError, CapReached, StageError)
