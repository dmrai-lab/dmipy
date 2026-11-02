"""Execute every ``python`` code block in ``docs/`` against the installed engines.

The site's examples are the contract: a block that no longer runs is a page that lies. Blocks
on one page run in order in one namespace (later blocks may use earlier names). A block opts
out with a first line ``# docs: skip`` (pseudo-code, or something that needs a scanner, a GPU
or a file that is not in the repo); its dmipy names are still checked: every import from a
``dmipy_*`` package and every attribute it reads off an imported ``dmipy_*`` module must resolve,
so a name a package refuses cannot hide in a block that does not run. ``# docs: cwd`` runs the
page's blocks with the page's directory as the working directory (for examples that read a
cached artefact next to them).

Run:  python tools/run_snippets.py [docs/page.md ...]      (default: every page)
Exit status is the number of pages that failed.
"""
from __future__ import annotations

import ast
import importlib
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


def dmipy_names(src: str) -> list[str]:
    """The dmipy names a block spells, as dotted paths: what it imports from a ``dmipy_*`` package, and the
    attributes it reads off a ``dmipy_*`` module it imported (``ds.walk`` after ``import dmipy_sim as ds``). A block
    that is not Python (pseudo-code) is read for its import lines alone."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        lines = [ln.strip() for ln in src.splitlines() if ln.strip().startswith(("import ", "from "))]
        tree = ast.parse("\n".join(ln.split("#")[0].rstrip() for ln in lines))
    names, modules = [], {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("dmipy_"):
                    names.append(a.name)
                    modules[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("dmipy_"):
            for a in node.names:
                names.append(f"{node.module}.{a.name}")
                modules[a.asname or a.name] = f"{node.module}.{a.name}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in modules:
            names.append(f"{modules[node.value.id]}.{node.attr}")
    return names


def unresolved(name: str) -> str | None:
    """Why the dotted ``name`` does not resolve against the installed packages, or None when it does."""
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:i]))
        except ImportError:
            continue
        try:
            for attr in parts[i:]:
                obj = getattr(obj, attr)
        except AttributeError as e:
            return str(e)
        return None
    return f"no module {parts[0]!r}"


def run_page(page: Path) -> tuple[bool, float]:
    ns = {"__name__": "__docs__", "__file__": str(page)}
    cwd = os.getcwd()
    t0 = time.time()
    try:
        for line, src in blocks(page):
            first = src.lstrip().splitlines()[0] if src.strip() else ""
            if first.startswith("# docs: skip"):
                bad = [(n, why) for n in dict.fromkeys(dmipy_names(src)) if (why := unresolved(n))]
                if bad:
                    print(f"\n--- {page.relative_to(ROOT)} skipped block at line {line} names what does not resolve:")
                    for n, why in bad:
                        print(f"    {n}: {why}")
                    return False, time.time() - t0
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
