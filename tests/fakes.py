"""A scripted stand-in for harness.llm.LLM. It performs the work through the real tools
(so tool wiring, write scopes and the Part A scripts are exercised) using the Part A
outputs as the model's answers. It checks orchestration, not prompt quality."""
import json
from pathlib import Path

from harness.llm import AgentResult, LLMError
from harness.stages import Run

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def first_build_ratings():
    """Part A's final ratings with the revision removed: what a first-pass assessor writes."""
    d = json.loads(part_a("risk-ratings.json"))
    d["revision"] = None
    for r in d["risks"]:
        ov = r.pop("auditor_override", None)
        if ov:  # back to what the agent rated before the auditor amended it
            r["likelihood"]["score"] = ov["agent_rating"]["likelihood"]
            r["impact"]["score"] = ov["agent_rating"]["impact"]
    return json.dumps(d, indent=1)


def revised_ratings():
    """Part A's final ratings as the first revision (this test run has had no earlier one)."""
    d = json.loads(part_a("risk-ratings.json"))
    d["revision"] = {"number": 1, "changes": [{"id": "R-09", "action": "amended", "note": "Likelihood raised as the auditor commented on R-09."}]}
    return json.dumps(d, indent=1)


def part_a(name):
    return (OUT / name).read_text(encoding="utf-8").replace("\r\n", "\n")


class FakeLLM:
    def __init__(self, budget=None, fail_on=None, challenge=True):
        self.emit = lambda *a: None
        self.budget, self.fail_on, self.challenge = budget, fail_on, challenge
        self.turns = []
        self.model = "fake-model"

    @staticmethod
    def _fn(tools, name):
        return next((t.fn for t in tools if t.name == name), None)

    def run_agent(self, system, task, tools, max_steps=12, label=""):
        self.turns.append(label)
        if self.fail_on == label:
            raise LLMError("quota", "fake: no quota")
        for _ in range(2):  # pretend two model requests per turn
            if self.budget:
                self.budget.take()
        w, run, send = self._fn(tools, "write_output"), self._fn(tools, "run_builder"), self._fn(tools, "send_message")
        if label == "extract-rules":
            w("outputs/rules.json", part_a("rules.json"))
            run("verify_quotes", ["outputs/rules.json"])
        elif label == "spend-analyst":
            run("clean")
            run("analyse")
        elif label == "findings-analyst":
            w("outputs/history.json", part_a("history.json"))
            run("verify_history", ["outputs/history.json"])
        elif label == "risk-assessor":
            revising = "auditor has recorded" in task
            w("outputs/risk-ratings.json", revised_ratings() if revising else first_build_ratings())
            r = run("build_register")
            assert r["exit_code"] == 0, r
        elif label == "planner":
            w("outputs/audit-plan.json", part_a("audit-plan.json"))
            r = run("build_pack")
            assert r["exit_code"] == 0, r
            if "Fix every QA" in task:
                send("qa-reviewer", "PACK READY v3")
            elif "Answer each CHALLENGE" in task:
                send("challenger", "RESPONSE #1: accepted")
                send("qa-reviewer", "PACK READY v2")
            elif "QA passed" in task:
                send("team-lead", "PLANNER DONE v2")
                send("qa-reviewer", "PLANNER DONE v2")
            else:
                send("challenger", "PACK READY v1")
                send("qa-reviewer", "PACK READY v1")
        elif label == "challenger":
            w("outputs/challenges.md", part_a("challenges.md"))
            if "Challenge round 1" in task and self.challenge:
                send("planner", "CHALLENGE #1 [sample] R-01: overlap. Evidence: x. Ask: redraw.")
            else:
                send("team-lead", "CHALLENGER DONE")
        elif label == "qa-reviewer":
            if "Final step" in task:
                w("outputs/review.md", Run._reset_signoff(part_a("review.md")))
                send("team-lead", "QA DONE")
            else:
                r = run("run_checks")
                send("planner", "QA v2: PASS" if r["exit_code"] == 0 else "QA v2: FAIL see output")
        return AgentResult("ok", 2)

    def ping(self):
        return self.model, "ok"
