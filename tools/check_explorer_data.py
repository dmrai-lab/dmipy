"""The committed explorer grid is what the installed dmipy-sim builds.

Regenerates the grid into a temporary directory and compares it with docs/studio/explorer_data:
the knobs, the calls and the refusals must match exactly, the stored curves and scalars to a
relative 2e-3 (the grid is rounded to four significant figures and platforms differ in the last
one). The dmipy-sim revision stamp is provenance, not content, and is ignored.

Run: python tools/check_explorer_data.py      (exit status 1 when the committed grid is stale)
"""
import json
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_explorer_data as gen  # noqa: E402

COMMITTED = os.path.join(HERE, "..", "docs", "studio", "explorer_data")
RTOL = 2e-3


def close(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        if a and all(isinstance(x, (int, float)) for x in a) and len(a) == len(b):
            return np.allclose(a, b, rtol=RTOL, atol=1e-9)
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return np.isclose(a, b, rtol=RTOL, atol=1e-9)
    return a == b


def main():
    with tempfile.TemporaryDirectory() as tmp:
        gen.main(tmp)
        stale = []
        for name in list(gen.FAMILIES) + ["index"]:
            fresh = json.load(open(os.path.join(tmp, f"{name}.json")))
            try:
                old = json.load(open(os.path.join(COMMITTED, f"{name}.json")))
            except FileNotFoundError:
                stale.append(f"{name}: missing"); continue
            fresh.pop("dmipy_sim", None); old.pop("dmipy_sim", None)
            if not close(fresh, old):
                stale.append(name)
    if stale:
        print("explorer_data is stale for:", ", ".join(stale), "-- run tools/gen_explorer_data.py and commit")
        return 1
    print("explorer_data matches what the installed dmipy-sim builds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
