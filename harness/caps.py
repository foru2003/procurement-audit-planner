"""Call caps. A "call" is one request sent to the model.

The session counter lives in the user's session; the daily counter is module-level,
so every session in this process shares it. It resets on a restart and at UTC midnight.
"""
import datetime
import threading

_lock = threading.Lock()
_daily = {"day": None, "n": 0}


class CapReached(Exception):
    """Raised before a request that would exceed a cap."""


def _today():
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def daily_used():
    with _lock:
        if _daily["day"] != _today():
            _daily.update(day=_today(), n=0)
        return _daily["n"]


def reset_daily_for_tests():
    with _lock:
        _daily.update(day=None, n=0)


class CallBudget:
    def __init__(self, session_cap, daily_cap):
        self.session_cap, self.daily_cap, self.used = session_cap, daily_cap, 0

    @property
    def session_remaining(self):
        return max(0, self.session_cap - self.used)

    @property
    def daily_remaining(self):
        return max(0, self.daily_cap - daily_used())

    def take(self):
        with _lock:
            if _daily["day"] != _today():
                _daily.update(day=_today(), n=0)
            if self.used >= self.session_cap:
                raise CapReached("session cap of %d model calls reached" % self.session_cap)
            if _daily["n"] >= self.daily_cap:
                raise CapReached("daily cap of %d model calls (all visitors) reached" % self.daily_cap)
            self.used += 1
            _daily["n"] += 1
