"""One full Live run against the real model, headless: every stage, Gate 1 (approve all),
the agent team and Gate 2. Writes a JSON summary and an event log; never prints settings.

    python tests/live_run.py <summary.json> <events.log>

Stops at the first model error (quota, auth, rate limit after retries) and reports it.
Uses only the primary model (no fallback chain) so a quota problem stops the run
instead of silently moving to a different model. The run's temp workspace is deleted
at the end; the summary has the facts.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness import config  # noqa: E402
from harness.caps import CallBudget  # noqa: E402
from harness.llm import LLM, LLMError  # noqa: E402
from harness.stages import Run  # noqa: E402

summary_path, log_path = Path(sys.argv[1]), Path(sys.argv[2])
KEY = config.api_key()


def scrub(text):
    text = str(text)
    return text.replace(KEY, "***") if KEY else text


log = log_path.open("w", encoding="utf-8")
events = []


def on_event(ev):
    events.append(ev)
    line = "%s %-14s %-10s %s" % (ev["t"], ev["agent"], ev["kind"], scrub(ev["text"]))
    log.write(line + "\n")
    log.flush()
    if ev["kind"] in ("agent", "wait", "tool_error", "check", "gate"):
        print(line, flush=True)


budget = CallBudget(config.int_setting("SESSION_CALL_CAP", 130), config.int_setting("DAILY_CALL_CAP", 300))
llm = LLM(KEY, [config.model_name()], budget, max_retries=3)
run = Run("live", llm=llm, budget=budget, pause=config.int_setting("TURN_PAUSE_SECONDS", 4), on_event=on_event)

result = {"model": config.model_name(), "stages": {}, "error": None, "finished": False}
t_start = time.time()


def stage(label, fn):
    t0, c0 = time.time(), budget.used
    try:
        fn()
        ok = True
    finally:
        result["stages"][label] = {"seconds": round(time.time() - t0, 1), "calls": budget.used - c0}
    return ok


try:
    for sid in ("rules", "spend", "findings", "risks"):
        stage(sid, lambda sid=sid: run.run_stage(sid))
    rows = run.risks_for_gate()
    result["risks"] = [r["id"] for r in rows]
    stage("gate1", lambda: run.record_gate1({r["id"]: ("Approve", "") for r in rows}, reviewer=""))
    stage("team", run.run_team)
    code, report = run.team_report()
    result["team_report"] = scrub(report)
    result["team_report_exit"] = code
    ccode, table = run.checks_table()
    result["checks"] = scrub(table)
    stage("gate2", lambda: result.update(signoff=run.record_signoff("Automated test run (not a real sign-off)", "sign-off")[1]))
    result["finished"] = True
except LLMError as exc:
    result["error"] = "LLMError(%s): %s" % (exc.kind, scrub(exc.message))
except Exception as exc:  # report whatever stopped the run
    result["error"] = "%s: %s" % (type(exc).__name__, scrub(exc))

result["total_seconds"] = round(time.time() - t_start, 1)
result["calls_total"] = budget.used
result["turns"] = [{k: (scrub(v) if isinstance(v, str) else v) for k, v in t.items()} for t in run.turn_log]
result["stage_status"] = run.status
result["retries_or_waits"] = [scrub(e["text"]) for e in events if e["kind"] == "wait"]
result["tool_errors"] = [scrub("%s: %s" % (e["agent"], e["text"])) for e in events if e["kind"] == "tool_error"]
result["builder_failures"] = [{k: scrub(v) if isinstance(v, str) else v for k, v in f.items()} for f in run.toolbox.failures]
result["spend"] = {"label": run.spend_label(), **{k: v for k, v in run.toolbox.spend.items()}}
result["messages"] = [{"from": m["from"], "to": m["to"], "text": scrub(m["text"])[:300]} for m in run.messages]
summary_path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
run.close()
print("DONE finished=%s calls=%d error=%s" % (result["finished"], budget.used, result["error"]), flush=True)
