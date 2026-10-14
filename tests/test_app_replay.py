"""Headless run of app.py in Replay mode: every stage, both gates, downloads. No model calls."""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(timeout=120)
            return
    raise AssertionError("no button %r; have %s" % (label, [b.label for b in at.button]))


def test_replay_end_to_end():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception, at.exception
    click(at, "Start run")
    for title in ("1. Extract rules", "2. Spend analysis", "3. Audit history", "4. Risk register"):
        click(at, "Run: " + title)
        assert not at.exception, at.exception
        assert not at.error, [e.value for e in at.error]
    click(at, "Record decisions")
    assert not at.exception and not at.error, (at.exception, [e.value for e in at.error])
    click(at, "Run: agent team (planner, challenger, qa-reviewer)")
    assert any("READY FOR SIGN-OFF" in s.value for s in at.success), [s.value for s in at.success]
    [t for t in at.text_input if t.label == "Your full name"][0].input("Test Auditor")
    click(at, "Record decision")
    assert any("Signed off" in s.value for s in at.success), ([s.value for s in at.success], [e.value for e in at.error], at.exception)
    print("replay end-to-end ok")


if __name__ == "__main__":
    test_replay_end_to_end()
