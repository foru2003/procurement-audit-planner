"""Live-mode orchestration with a scripted model: stages, Gate 1 paths, team protocol,
caps and error classification. No network.

    python tests/test_live_flow.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fakes import FakeLLM  # noqa: E402
from harness import agents  # noqa: E402
from harness.caps import CallBudget, CapReached, reset_daily_for_tests  # noqa: E402
from harness.llm import classify, retry_delay  # noqa: E402
from harness.stages import Run  # noqa: E402


def make(fail_on=None, challenge=True, cap=130):
    reset_daily_for_tests()
    b = CallBudget(cap, 300)
    return Run("live", llm=FakeLLM(b, fail_on, challenge), budget=b, pause=0, sleep=lambda s: None), b


def first_four(r):
    for sid in ("rules", "spend", "findings", "risks"):
        r.run_stage(sid)


def test_prompts_load():
    for name, text in agents.load_all().items():
        assert len(text) > 500 and "Harness note" in text, name


def test_full_live_flow_all_approved():
    r, b = make()
    first_four(r)
    assert r.toolbox.spend["path"] == "live", r.toolbox.spend
    rows = r.risks_for_gate()
    assert rows and all(x["decision"] == "" for x in rows), "template should be undecided"
    r.record_gate1({x["id"]: ("Approve", "") for x in rows}, reviewer="T")
    assert r.llm.turns == ["extract-rules", "spend-analyst", "findings-analyst", "risk-assessor"], "all-approve must not call the model"
    r.run_team()
    order = r.llm.turns
    assert order[4:] == ["planner", "challenger", "planner", "challenger", "qa-reviewer", "planner", "qa-reviewer"], order
    code, out = r.team_report()
    assert code == 0 and "READY FOR SIGN-OFF" in out, out
    sc = r.record_signoff("Test Auditor", "sign-off")
    assert sc[0] == 0, sc
    assert b.used == 2 * len(order)
    r.close()


def test_gate1_amend_calls_risk_assessor():
    r, _ = make()
    first_four(r)
    rows = r.risks_for_gate()
    recorded = {}
    for line in (ROOT / "outputs" / "auditor-comments.md").read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 5 and c[0].startswith("R-"):
            recorded[c[0]] = (c[3], c[4])
    r.record_gate1({x["id"]: recorded[x["id"]] for x in rows})
    assert r.llm.turns.count("risk-assessor") == 2
    r.close()


def test_write_scope_and_paths():
    r, _ = make()
    tools = {t.name: t.fn for t in r.toolbox.tools_for(("write_output", "read_file", "run_builder"), write_paths=("outputs/rules.json",))}
    refusals = [lambda: tools["write_output"]("outputs/other.json", "{}"), lambda: tools["read_file"]("../x"),
                lambda: tools["read_file"]("/etc/passwd"), lambda: tools["run_builder"]("bash", []),
                lambda: tools["run_builder"]("clean", ["--evil"]), lambda: tools["run_builder"]("verify_quotes", ["../../x"])]
    for bad in refusals:
        try:
            bad()
        except (PermissionError, ValueError):
            continue
        raise AssertionError("expected a refusal")
    r.close()


def test_caps():
    r, b = make(cap=3)
    try:
        r.run_stage("rules")
        r.run_stage("spend")
    except CapReached:
        pass
    else:
        raise AssertionError("cap not enforced")
    assert b.used == 3
    r.close()


def test_error_classification():
    class E(Exception):
        def __init__(self, code, message):
            self.code, self.message = code, message
    assert classify(E(429, "RESOURCE_EXHAUSTED quota exceeded, limit: 0")) == "quota"
    assert classify(E(429, "Quota exceeded for metric GenerateRequestsPerDayPerProjectPerModel")) == "quota"
    assert classify(E(429, "Resource exhausted. Please try again later. retry in 12.3s")) == "rate"
    assert classify(E(400, "API key not valid. Please pass a valid API key.")) == "auth"
    assert classify(E(404, "models/x is not found")) == "model"
    assert classify(E(503, "overloaded")) == "server"
    assert 13 <= retry_delay(E(429, "retry in 12.3s"), 0) <= 14
    assert 2 <= retry_delay(E(429, "slow down"), 0) <= 4


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
