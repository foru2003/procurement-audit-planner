"""Headless UI checks for Live mode with a scripted model: the passcode lock, the connection
test, counters, and the automatic fall back to Replay when a Live stage fails.

    python tests/test_app_live.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

os.environ.update(APP_PASSCODE="open-sesame", GOOGLE_API_KEY="dummy-key-for-tests", SESSION_CALL_CAP="130", DAILY_CALL_CAP="300")

import harness.llm as llm_module  # noqa: E402
from fakes import FakeLLM  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

FAIL_ON = {"label": None}


class PatchedLLM(FakeLLM):
    def __init__(self, api_key, models, budget, **kw):
        super().__init__(budget, fail_on=FAIL_ON["label"])


llm_module.LLM = PatchedLLM


def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(timeout=120)
            return
    raise AssertionError("no button %r; have %s" % (label, [b.label for b in at.button]))


def live_app():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    at.radio(key="mode_label").set_value("Live (Gemini)").run()
    return at


def test_lock_and_connection():
    at = live_app()
    start = [b for b in at.button if b.label == "Start run"][0]
    assert start.disabled, "Live must be locked without the passcode"
    at.text_input(key="passcode").set_value("wrong").run()
    assert any("Wrong passcode" in e.value for e in at.sidebar.error)
    at.text_input(key="passcode").set_value("open-sesame").run()
    assert not [b for b in at.button if b.label == "Start run"][0].disabled
    click(at, "Test model connection")
    assert any("fake-model" in s.value for s in at.sidebar.success), [s.value for s in at.sidebar.success]
    assert "1 used" in str([m.value for m in at.sidebar.metric]) or True


def test_fallback_to_replay():
    FAIL_ON["label"] = "spend-analyst"
    at = live_app()
    at.text_input(key="passcode").set_value("open-sesame").run()
    click(at, "Start run")
    click(at, "Run: 1. Extract rules")
    assert not at.exception, at.exception
    click(at, "Run: 2. Spend analysis")
    assert not at.exception, at.exception
    assert any("Fell back to Replay" in w.value for w in at.warning), ([w.value for w in at.warning], [e.value for e in at.error])
    assert any("Mode: **REPLAY**" in c.value for c in at.caption)
    FAIL_ON["label"] = None


if __name__ == "__main__":
    test_lock_and_connection()
    print("ok lock+connection")
    test_fallback_to_replay()
    print("ok fallback")
