"""Settings from st.secrets (Streamlit Cloud / .streamlit/secrets.toml) or the environment.

The key is only ever read here and handed to harness.llm; it is never logged or shown.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _secret(name, default=""):
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no secrets file, or not running under streamlit
        pass
    return os.environ.get(name, default)


def api_key():
    return _secret("GOOGLE_API_KEY") or _secret("GEMINI_API_KEY")


def model_name():
    return _secret("MODEL_NAME", "gemini-3.8-flash")


def model_chain():
    """MODEL_NAME first, then MODEL_FALLBACKS, without repeats."""
    fb = _secret("MODEL_FALLBACKS", "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-2.5-flash")
    out = []
    for m in [model_name()] + [x.strip() for x in fb.split(",")]:
        if m and m not in out:
            out.append(m)
    return out


def passcode():
    return _secret("APP_PASSCODE")


def int_setting(name, default):
    try:
        return int(_secret(name, str(default)))
    except ValueError:
        return default
