"""A per-session scratch folder: a copy of data/ plus an empty outputs/.

The Part A scripts use paths relative to the working directory, so each is run with
this folder as cwd. The disk is not persistent on Streamlit Community Cloud, so
nothing here outlives the session; old folders are purged on the next start.
"""
import shutil
import tempfile
import time
from pathlib import Path

from .config import ROOT

PREFIX = "audit-ws-"
MAX_AGE_SECONDS = 6 * 3600


class Workspace:
    def __init__(self):
        self.purge_old()
        self.root = Path(tempfile.mkdtemp(prefix=PREFIX))
        shutil.copytree(ROOT / "data", self.root / "data")
        (self.root / "outputs" / "analytics-full").mkdir(parents=True)

    @property
    def outputs(self):
        return self.root / "outputs"

    @property
    def data(self):
        return self.root / "data"

    def resolve(self, rel, area=("data", "outputs")):
        """Absolute path for a workspace-relative path, or ValueError."""
        rel = str(rel).replace("\\", "/").strip()
        p = (self.root / rel).resolve()
        if not p.is_relative_to(self.root.resolve()):
            raise ValueError("path outside the workspace: %s" % rel)
        top = p.relative_to(self.root.resolve()).parts[:1]
        if not top or top[0] not in area:
            raise ValueError("path must start with %s: %s" % (" or ".join(a + "/" for a in area), rel))
        return p

    def exists(self, rel):
        return (self.root / rel).exists()

    def read_text(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def purge_old():
        tmp = Path(tempfile.gettempdir())
        now = time.time()
        for d in tmp.glob(PREFIX + "*"):
            try:
                if now - d.stat().st_mtime > MAX_AGE_SECONDS:
                    shutil.rmtree(d, ignore_errors=True)
            except OSError:
                pass
