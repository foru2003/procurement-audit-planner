"""Procurement Audit Planner: Streamlit harness for the Part A agents and scripts.

Run locally:  streamlit run app.py
Replay mode needs no secrets. Live mode needs .streamlit/secrets.toml (see the .example).
"""
import hmac
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from harness import config
from harness.caps import CallBudget, daily_used
from harness.llm import LLM, LLMError
from harness.stages import LIVE_ERRORS, STAGES, Run

st.set_page_config(page_title="Procurement Audit Planner", page_icon=None, layout="wide")

SESSION_CAP = config.int_setting("SESSION_CALL_CAP", 130)
DAILY_CAP = config.int_setting("DAILY_CALL_CAP", 300)
PAUSE = config.int_setting("TURN_PAUSE_SECONDS", 4)
ICON = {"todo": "[ ]", "running": "[..]", "done": "[x]", "failed": "[!]"}
KIND_LABEL = {"request": "request", "tool": "tool", "wait": "wait", "agent": "agent", "check": "check",
              "replay": "replay", "message": "message", "gate": "gate"}

ss = st.session_state
ss.setdefault("run", None)
ss.setdefault("budget", CallBudget(SESSION_CAP, DAILY_CAP))
ss.setdefault("unlocked", False)
ss.setdefault("error", "")
ss.setdefault("ping", "")
ss.setdefault("zip", None)


def scrub(text):
    key = config.api_key()
    return str(text).replace(key, "***") if key else str(text)


def new_run(mode):
    llm = None
    if mode == "live":
        llm = LLM(config.api_key(), config.model_chain(), ss.budget)
    return Run(mode, llm=llm, budget=ss.budget, pause=PAUSE if mode == "live" else 0)


def reset():
    if ss.run:
        ss.run.close()
    ss.run, ss.error, ss.zip = None, "", None


def show_event(container, ev):
    container.write("`%s` **%s** %s" % (ev["t"], KIND_LABEL.get(ev["kind"], ev["kind"]), scrub(ev["text"])))


def replay_upto(sid):
    """Switch the session to a fresh Replay run and bring it to the stage that failed."""
    old = ss.run
    run = new_run("replay")
    run.events = old.events if old else []
    order = ["rules", "spend", "findings", "risks", "gate1", "team"]
    for s in order[:order.index(sid) + 1]:
        if s == "gate1":
            run.record_gate1({r["id"]: (r["decision"], r["comment"]) for r in run.risks_for_gate()})
        elif s == "team":
            run.run_team()
        else:
            run.run_stage(s)
    if old:
        old.close()
    ss.run = run


def on_live_failure(exc, sid):
    msg = scrub(exc)
    st.session_state.error = "Live mode failed at '%s': %s" % (sid, msg)
    if ss.get("auto_fallback", True):
        try:
            replay_upto(sid)
            ss.run.fallback_reason = ss.error
            ss.error = ""
        except Exception as inner:  # replay should never fail; say so if it does
            ss.error += "  Replay fallback also failed: %s" % scrub(inner)


def run_with_ui(label, fn, sid):
    run = ss.run
    with st.status(label, expanded=True) as status:
        run.on_event = lambda ev: show_event(status, ev)
        try:
            fn()
            status.update(label=label + ": done", state="complete", expanded=False)
        except Exception as exc:
            status.update(label=label + ": failed", state="error")
            if run.mode == "live" and True:
                on_live_failure(exc, sid)
            else:
                ss.error = scrub(exc)
        finally:
            run.on_event = None
    st.rerun()


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Mode")
    mode_label = st.radio("Run mode", ["Replay (no model calls)", "Live (Gemini)"], key="mode_label",
                          disabled=bool(ss.run and any(s != "todo" for s in ss.run.status.values())),
                          help="Reset the run to change mode.")
    live_selected = mode_label.startswith("Live")
    if live_selected:
        if not config.passcode():
            st.warning("Live mode is disabled: no APP_PASSCODE is configured.")
        code = st.text_input("Passcode", type="password", key="passcode")
        ss.unlocked = bool(config.passcode()) and hmac.compare_digest(code.encode(), config.passcode().encode())
        if code and not ss.unlocked:
            st.error("Wrong passcode.")
        if ss.unlocked and not config.api_key():
            st.error("Unlocked, but no GOOGLE_API_KEY is configured.")
    else:
        ss.unlocked = False
    st.checkbox("Fall back to Replay automatically if Live fails", value=True, key="auto_fallback")
    st.caption("Live model: `%s` (from MODEL_NAME). Free-tier Gemini; answers can vary between runs." % config.model_name())

    st.header("Model calls")
    b = ss.budget
    st.metric("This session", "%d used / %d remaining" % (b.used, b.session_remaining), help="Cap %d. One call = one model request." % b.session_cap)
    st.metric("Today, all visitors", "%d used / %d remaining" % (daily_used(), b.daily_remaining), help="Cap %d; shared by every session until the app restarts." % b.daily_cap)

    st.header("Connection")
    if st.button("Test model connection", disabled=not (live_selected and ss.unlocked and bool(config.api_key()))):
        try:
            model, reply = LLM(config.api_key(), config.model_chain(), ss.budget).ping()
            ss.ping = "OK: **%s** answered (%r)." % (model, reply)
        except LLMError as exc:
            hint = {"auth": "bad or missing API key", "quota": "no free quota for the model(s) tried",
                    "rate": "rate limit (429) persisted after retries", "model": "model name not found"}.get(exc.kind, exc.kind)
            ss.ping = "FAILED (%s): %s" % (hint, scrub(exc.message))
        except Exception as exc:
            ss.ping = "FAILED: %s" % scrub(exc)
        st.rerun()
    if ss.ping:
        (st.success if ss.ping.startswith("OK") else st.error)(ss.ping)
    st.button("Reset run", on_click=reset)

# ------------------------------------------------------------------ header
st.title("Procurement Audit Planner")
st.caption("West Berkshire Council: plans an internal audit of procurement from public data. Outputs are risk indicators to investigate, not findings against anyone.")

with st.container(border=True):
    st.markdown("**How to use this app**")
    st.markdown(
        "- **Replay** (default) walks every stage and both human gates using the saved results of the original Part A run. No model is called and no passcode is needed.\n"
        "- **Live** runs the agents for real. It needs the passcode and calls a **free-tier Gemini model** (`%s`), so answers can differ from the Part A run and the free quota is shared by all visitors. If Live fails, the app can fall back to Replay.\n"
        "- Work down the stages, make your decisions at **Gate 1** (Approve / Amend / Reject each risk) and sign off at **Gate 2**, then download the pack." % config.model_name())

run: Run | None = ss.run
if run and run.mode == "replay" and run.fallback_reason:
    st.warning("Fell back to Replay. " + scrub(run.fallback_reason))
if ss.error:
    st.error(ss.error)
    if run and run.mode == "live" and st.button("Continue this stage in Replay"):
        sid = next((s for s, v in run.status.items() if v == "failed"), "rules")
        replay_upto(sid)
        ss.error = ""
        st.rerun()

# ------------------------------------------------------------------ stages
st.subheader("Workflow")
status = run.status if run else {s[0]: "todo" for s in STAGES}
for sid, title, agent, kind in STAGES:
    st.write("%s **%s**  ·  %s%s" % (ICON[status[sid]], title, agent or "human", (" (%s)" % kind) if kind else ""))

if run is None:
    can_start = (not live_selected) or (ss.unlocked and bool(config.api_key()))
    if st.button("Start run", type="primary", disabled=not can_start):
        try:
            ss.run = new_run("live" if live_selected else "replay")
        except LLMError as exc:
            ss.error = scrub(exc.message)
        st.rerun()
    if live_selected and not can_start:
        st.info("Enter the passcode in the sidebar to unlock Live mode.")
    st.stop()

st.caption("Mode: **%s**%s" % (run.mode.upper(), " · " + run.spend_label() if status["spend"] == "done" else ""))

NEXT = [s for s in ("rules", "spend", "findings", "risks") if status[s] != "done"]
if NEXT:
    sid = NEXT[0]
    title = next(t for i, t, *_ in STAGES if i == sid)
    if st.button("Run: " + title, type="primary"):
        run_with_ui(title, lambda: run.run_stage(sid), sid)


def preview(rel, label, kind="md"):
    p = run.ws.root / rel
    if not p.exists():
        return
    with st.expander(label):
        text = p.read_text(encoding="utf-8")
        st.markdown(text) if kind == "md" else st.code(text[:20000], language="json")
        st.download_button("Download " + p.name, p.read_bytes(), file_name=p.name, key="dl-" + rel)


if status["rules"] == "done":
    rp = run.ws.root / "outputs" / "rules.json"
    with st.expander("Rules extracted (rules.json)"):
        data = json.loads(rp.read_text(encoding="utf-8"))
        df = pd.DataFrame(data["rules"])
        cols = [c for c in ("rule_id", "clause", "page", "type", "scope", "threshold_low", "threshold_high", "required_action", "approver") if c in df.columns]
        st.dataframe(df[cols], width="stretch", hide_index=True)
        st.download_button("Download rules.json", rp.read_bytes(), file_name="rules.json", key="dl-rules")
if status["spend"] == "done":
    preview("outputs/analytics.json", "Spend analytics (analytics.json)", "json")
if status["findings"] == "done":
    preview("outputs/history.json", "Audit history (history.json)", "json")
if status["risks"] == "done":
    preview("outputs/risk-register.md", "Risk register")

# ------------------------------------------------------------------ gate 1
if status["risks"] == "done" and status["gate1"] != "done":
    st.subheader("Human Gate 1: decide each risk")
    st.caption("Approve, Amend (say what to change) or Reject (give the reason). " +
               ("In Replay the recorded Part A decisions are used." if run.mode == "replay" else "Live: your decisions are applied as a revision of the register."))
    with st.form("gate1"):
        reviewer = st.text_input("Your name (recorded as reviewer)")
        picks = {}
        for r in run.risks_for_gate():
            c1, c2, c3 = st.columns([5, 2, 4])
            c1.markdown("**%s**  ·  %s  \n`%s`" % (r["id"], r["statement"][:260], r["rating"]))
            opts = ["Approve", "Amend", "Reject"]
            default = r["decision"] if r["decision"] in opts else "Approve"
            d = c2.selectbox("Decision", opts, index=opts.index(default), key="d-" + r["id"], label_visibility="collapsed")
            c = c3.text_input("Comment", value=r["comment"] if r["decision"] in opts else "", key="c-" + r["id"], label_visibility="collapsed")
            picks[r["id"]] = (d, c)
        submitted = st.form_submit_button("Record decisions", type="primary")
    if submitted:
        bad = [k for k, (d, c) in picks.items() if d != "Approve" and not c.strip()]
        if bad:
            st.error("Amend and Reject need a comment: " + ", ".join(bad))
        else:
            run_with_ui("Applying Gate 1 decisions", lambda: run.record_gate1(picks, reviewer.strip()), "gate1")
    st.stop()

# ------------------------------------------------------------------ team
if status["gate1"] == "done" and status["team"] != "done":
    if st.button("Run: agent team (planner, challenger, qa-reviewer)", type="primary"):
        run_with_ui("Agent team", run.run_team, "team")
    st.stop()

if status["team"] == "done":
    with st.expander("Team conversation (%d messages)" % len(run.messages)):
        for m in run.messages:
            with st.chat_message("assistant" if m["from"] != "team-lead" else "user"):
                st.markdown("**%s → %s**  \n%s" % (m["from"], m["to"], scrub(m["text"])))
    for rel, label in [("outputs/planning-memo.md", "Planning memo"), ("outputs/risk-control-matrix.md", "Risk-control matrix"),
                       ("outputs/audit-program.md", "Audit program"), ("outputs/challenges.md", "Challenges"), ("outputs/review.md", "QA review")]:
        preview(rel, label)
    code, rep = run.team_report()
    (st.success if code == 0 else st.error)(rep.replace("\r", ""))

    # -------------------------------------------------------------- gate 2
    if status["gate2"] != "done":
        st.subheader("Human Gate 2: sign-off")
        with st.form("gate2"):
            name = st.text_input("Your full name")
            decision = st.radio("Decision", ["Sign off", "Return for rework"], horizontal=True)
            comment = st.text_input("Comment (optional)")
            go = st.form_submit_button("Record decision", type="primary")
        if go:
            if not name.strip():
                st.error("A real name is required; none is invented.")
            else:
                c, out = run.record_signoff(name.strip(), "sign-off" if decision == "Sign off" else "return", comment.strip())
                (st.success if c == 0 else st.error)(out)
                if c == 0:
                    ss.zip = None
                    st.rerun()
        st.stop()
    st.success("Signed off. The pack is complete.")

    # -------------------------------------------------------------- downloads
    st.subheader("Downloads")
    if ss.zip is None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted((run.ws.root / "outputs").rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(run.ws.root).as_posix())
        ss.zip = buf.getvalue()
    st.download_button("Download everything (zip)", ss.zip, file_name="audit-planning-pack.zip", mime="application/zip", type="primary")
