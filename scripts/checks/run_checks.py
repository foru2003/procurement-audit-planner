#!/usr/bin/env python3
"""Run the four QA checks and print one table and a verdict.

Usage: run_checks.py [--outputs DIR] [--data DIR] [--full DIR]

Prints, in this order: the table (check, result, detail), every failure item
under the table, and the verdict line READY FOR SIGN-OFF (all four pass) or
BLOCKED. Exit 0 when ready, 1 when blocked. Nothing is softened: a check that
cannot run counts as FAIL. The checks never change a file.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKS = [("quotes", "check_quotes.py"), ("numbers", "check_numbers.py"),
          ("trace", "check_trace.py"), ("samples", "check_samples.py")]


def load(fname):
    spec = importlib.util.spec_from_file_location(fname[:-3], HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_all(outputs, data, full=None):
    """Run the four checks; return [(name, failures, summary)]. A check that cannot run is a failure."""
    results = []
    for name, fname in CHECKS:
        try:
            mod = load(fname)
            if name == "quotes":
                fails, summary = mod.run(outputs, data)
            elif name == "numbers" or name == "trace":
                fails, summary = mod.run(outputs)
            else:
                fails, summary = mod.run(outputs, data, full)
        except Exception as exc:  # a check that cannot run is a failure, not a pass
            fails, summary = ["the check could not run: %s: %s" % (type(exc).__name__, exc)], "could not run"
        results.append((name, fails, summary))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--full")
    a = ap.parse_args(argv)
    results = run_all(a.outputs, a.data, a.full)
    w = max(len(s) for _, _, s in results)
    print("| Check   | Result | Detail |")
    print("|---------|--------|--------|")
    for name, fails, summary in results:
        print("| %-7s | %-6s | %s |" % (name, "FAIL" if fails else "PASS", ("%d failure%s: " % (len(fails), "" if len(fails) == 1 else "s") if fails else "") + summary))
    bad = [(n, f) for n, f, _ in results if f]
    if bad:
        print("\nFailures")
        for name, fails in bad:
            for item in fails[:25]:
                print("  %s: %s" % (name, item))
            if len(fails) > 25:
                print("  %s: ... and %d more" % (name, len(fails) - 25))
    ready = not bad
    print("\nVERDICT: %s" % ("READY FOR SIGN-OFF" if ready else "BLOCKED"))
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
