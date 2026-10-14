"""Write per-page pdftotext output for every PDF in data/ to data/pdf-text/<name>.json.

Run locally (needs poppler's pdftotext and pdfinfo). The JSON is bundled read-only
with the deployed app, because Vercel functions have no pdftotext. Each file holds
the same two views the verifiers use: plain reading order and -layout.

    python scripts/precompute_pdf_text.py
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "pdf-text"


def run(args):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise SystemExit("%s failed: %s" % (args[0], r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace")


def main():
    OUT.mkdir(exist_ok=True)
    pdfs = sorted((ROOT / "data").rglob("*.pdf"))
    for pdf in pdfs:
        n = int(re.search(r"^Pages:\s+(\d+)", run(["pdfinfo", str(pdf)]), re.M).group(1))
        views = {"plain": [], "layout": []}
        for p in range(1, n + 1):
            for name, extra in (("plain", []), ("layout", ["-layout"])):
                cmd = ["pdftotext", "-enc", "UTF-8", "-f", str(p), "-l", str(p)] + extra
                views[name].append(run(cmd + [str(pdf), "-"]))
        dest = OUT / (pdf.stem + ".json")
        dest.write_text(json.dumps({"file": pdf.name, "pages": n, **views}, ensure_ascii=False),
                        encoding="utf-8")
        print("%s: %d pages -> %s (%d KB)" % (pdf.name, n, dest.relative_to(ROOT), dest.stat().st_size // 1024))


if __name__ == "__main__":
    main()
