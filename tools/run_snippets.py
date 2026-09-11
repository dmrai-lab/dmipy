"""Execute every ``python`` code block in ``docs/`` against the installed engines.

The site's examples are the contract: a block that no longer runs is a page that lies. Blocks
on one page run in order in one namespace (later blocks may use earlier names). A block opts
out with a first line ``# docs: skip`` (pseudo-code, or something that needs a scanner, a GPU
or a file that is not in the repo). ``# docs: cwd`` runs the page's blocks with the page's
directory as the working directory (for examples that read a cached artefact next to them).

Run:  python tools/run_snippets.py [docs/page.md ...]      (default: every page)
Exit status is the number of pages that failed.
"""
from __future__ import annotations

import os
import re
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FENCE = re.compile(r"^```python[^\n]*\n(.*?)^```", re.S | re.M)


def blocks(page: Path):
    text = page.read_text(encoding="utf-8")
    for m in FENCE.finditer(text):
        yield text[: m.start()].count("\n") + 2, m.group(1)


def run_page(page: Path) -> tuple[bool, float]:
    ns = {"__name__": "__docs__", "__file__": str(page)}
    cwd = os.getcwd()
    t0 = time.time()
    try:
        for line, src in blocks(page):
            first = src.lstrip().splitlines()[0] if src.strip() else ""
            if first.startswith("# docs: skip"):
                continue
            if first.startswith("# docs: cwd"):
                os.chdir(page.parent)
            try:
                exec(compile(src, f"{page.relative_to(ROOT)}:{line}", "exec"), ns)
            except Exception:
                print(f"\n--- {page.relative_to(ROOT)} block at line {line} failed:")
                traceback.print_exc(limit=6)
                return False, time.time() - t0
        return True, time.time() - t0
    finally:
        os.chdir(cwd)


def main(argv):
    pages = [Path(a).resolve() for a in argv] if argv else sorted(DOCS.rglob("*.md"))
    failed = 0
    for page in pages:
        n = sum(1 for _ in blocks(page))
        if n == 0:
            continue
        ok, dt = run_page(page)
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {page.relative_to(ROOT)}  ({n} blocks, {dt:.1f}s)")
    print(f"\n{failed} page(s) failed")
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
