"""The only module that imports the Gemini SDK (google-genai).

Everything else uses LLM.run_agent(system, task, tools, ...) and LLM.ping(), so
swapping provider means rewriting this file only.
"""
import random
import re
import time
from dataclasses import dataclass
from typing import Callable

from google import genai
from google.genai import types

from .caps import CallBudget


class LLMError(Exception):
    """kind: auth | quota | rate | model | server | blocked | other"""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind, self.message = kind, message


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema
    fn: Callable


@dataclass
class AgentResult:
    text: str
    steps: int
    truncated: bool = False


def classify(exc):
    code = getattr(exc, "code", None)
    msg = (getattr(exc, "message", None) or str(exc)).lower()
    if code in (401, 403) or (code == 400 and ("api key" in msg or "api_key" in msg)):
        return "auth"
    if code == 429:
        if "limit: 0" in msg or "perday" in msg.replace(" ", "") or "per day" in msg:
            return "quota"
        return "rate"
    if code == 404:
        return "model"
    if isinstance(code, int) and code >= 500:
        return "server"
    return "other"


def retry_delay(exc, attempt):
    """Seconds to wait: the server's hint if it gave one, else exponential with jitter."""
    m = re.search(r"retry in ([\d.]+)s|retrydelay\W+(\d+)s", str(exc).lower())
    if m:
        return min(90.0, float(m.group(1) or m.group(2)) + 1)
    return min(60.0, 2 ** (attempt + 1)) + random.uniform(0, 1.5)


class LLM:
    def __init__(self, api_key, models, budget: CallBudget, emit=None, sleep=time.sleep, max_retries=5):
        if not api_key:
            raise LLMError("auth", "no API key configured (GOOGLE_API_KEY)")
        self.client = genai.Client(api_key=api_key)
        self.models, self.i = list(models), 0
        self.budget, self.emit, self.sleep, self.max_retries = budget, emit or (lambda *a: None), sleep, max_retries

    @property
    def model(self):
        return self.models[self.i]

    def _generate(self, contents, config):
        attempt = 0
        while True:
            self.budget.take()
            try:
                return self.client.models.generate_content(model=self.model, contents=contents, config=config)
            except Exception as exc:  # SDK raises APIError subclasses
                kind = classify(exc)
                detail = (getattr(exc, "message", None) or str(exc))[:300]
                if kind == "auth":
                    raise LLMError("auth", detail)
                if kind in ("quota", "model"):
                    if self.i + 1 < len(self.models):
                        self.emit("wait", "%s unavailable (%s); switching to %s" % (self.model, kind, self.models[self.i + 1]))
                        self.i += 1
                        attempt = 0
                        continue
                    raise LLMError(kind, detail)
                if kind in ("rate", "server") and attempt < self.max_retries:
                    delay = retry_delay(exc, attempt)
                    self.emit("wait", "%s from the model; retrying in %.0fs (%d/%d)" % (
                        "rate limit (429)" if kind == "rate" else "server error", delay, attempt + 1, self.max_retries))
                    self.sleep(delay)
                    attempt += 1
                    continue
                raise LLMError(kind, detail)

    def run_agent(self, system, task, tools, max_steps=12, label=""):
        decls = [types.FunctionDeclaration(name=t.name, description=t.description,
                                           parameters_json_schema=t.parameters) for t in tools]
        by_name = {t.name: t for t in tools}
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=[types.Tool(function_declarations=decls)] if decls else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.2,
        )
        contents = [types.Content(role="user", parts=[types.Part(text=task)])]
        text = ""
        for step in range(1, max_steps + 1):
            self.emit("request", "model request %d (%s)" % (step, self.model))
            resp = self._generate(contents, config)
            cand = resp.candidates[0] if resp.candidates else None
            if cand is None or cand.content is None or not cand.content.parts:
                reason = getattr(cand, "finish_reason", None) if cand else "no candidates"
                raise LLMError("blocked", "the model returned no content (%s)" % reason)
            contents.append(cand.content)
            text = "".join(p.text for p in cand.content.parts if getattr(p, "text", None) and not getattr(p, "thought", False))
            calls = [p.function_call for p in cand.content.parts if p.function_call]
            if not calls:
                return AgentResult(text, step)
            replies = []
            for c in calls:
                args = dict(c.args or {})
                self.emit("tool", "%s(%s)" % (c.name, ", ".join("%s=%s" % (k, str(v)[:40]) for k, v in args.items())))
                tool = by_name.get(c.name)
                try:
                    out = tool.fn(**args) if tool else "error: unknown tool %s" % c.name
                    reply = {"result": out}
                except Exception as exc:  # tool errors go back to the model
                    reply = {"error": "%s: %s" % (type(exc).__name__, exc)}
                replies.append(types.Part.from_function_response(name=c.name, response=reply))
            contents.append(types.Content(role="user", parts=replies))
        return AgentResult(text, max_steps, truncated=True)

    def ping(self):
        """One tiny request. Returns (model that answered, its reply)."""
        config = types.GenerateContentConfig(max_output_tokens=64, temperature=0)
        resp = self._generate("Reply with the single word: ok", config)
        return self.model, (getattr(resp, "text", "") or "").strip()[:40]
