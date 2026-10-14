"""Read the precomputed page text from data/pdf-text/ (see precompute_pdf_text.py).

Used by the verifiers when pdftotext is not installed (Vercel functions) or when
PDF_TEXT_CACHE=1. The text is the raw pdftotext output; callers normalise it.
"""
import json
import os
import shutil
from pathlib import Path


def wanted():
    return os.environ.get("PDF_TEXT_CACHE") == "1" or not (shutil.which("pdftotext") and shutil.which("pdfinfo"))


def load(pdf_path):
    pdf = Path(pdf_path)
    for base in (pdf.parent, *pdf.parents):
        f = base / "pdf-text" / (pdf.stem + ".json")
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parent.parent / "data" / "pdf-text" / (pdf.stem + ".json")
    if root.exists():
        return json.loads(root.read_text(encoding="utf-8"))
    raise RuntimeError("pdftotext not found and no cached text for %s (run scripts/precompute_pdf_text.py)" % pdf.name)
