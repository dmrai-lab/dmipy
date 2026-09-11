"""Regenerate the spin studio's data -- the ``GEOM`` literal in docs/studio/bloch_pedagogy.html.

The studio shows a few dozen water spins from each compartment of the canonical white matter
(extra-axonal, intra-axonal, myelin water) evolving under a pulse sequence. Their positions are a
real dmipy-sim walk on the canonical substrate (``Substrate.canonical().request(...)`` walked by
``walk_spec``), taken raw from the walk (a pack decode is band-limited, not a path); the compartments' T2/T1 come from the
substrate; the cross-section is the realised packing. The page's script integrates the Bloch
equation on those positions in the browser -- the one place on the site where physics runs in
JavaScript -- and ``tools/check_spin_studio.{js,py}`` check that integration against
``dmipy_sim.replay_bloch`` on the same positions and the same sequence.

Run: python tools/gen_spin_studio.py   (needs dmipy-sim importable; the walk takes a while on a CPU)
"""
from __future__ import annotations

import json
import os
import subprocess

import numpy as np

import dmipy_sim as ds
from dmipy_sim.spec import walk_spec
from dmipy_sim.substrate import Substrate

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "docs", "studio", "bloch_pedagogy.html")
N_FIBRES, N_WALKERS, T_MAX, DT_SAVE, PER_COMP, SEED = 12, 600, 0.10, 3.5e-4, 24, 0


def main():
    sub = Substrate.canonical(field_T=3.0)
    spec = sub.request(n_fibres=N_FIBRES, seed=SEED)
    cache = os.environ.get("SPIN_STUDIO_WALK", "")                  # the walk is the expensive part: keep it raw
    if cache and os.path.exists(cache):
        z = np.load(cache)
        r, comp0, dt_save, T_stored = z["r"], z["comp0"], float(z["dt"]), float(z["T"])
    else:
        walk = walk_spec(spec, N_WALKERS, T_MAX, dt_save=DT_SAVE, seed=SEED, require_gpu=False, field=False)
        bank = walk._bank_dict()
        key = next(k for k in ("traj", "positions", "r") if k in bank)
        r = np.asarray(bank[key], np.float64)                        # (n_w, n_t, 3) metres, the RAW walk:
        #                                                             a pack decode is band-limited, not a path
        comp = np.asarray(walk.compartment)
        comp0 = comp[:, 0] if comp.ndim == 2 else comp
        dt_save, T_stored = DT_SAVE, walk.T_max
        if cache:
            np.savez(cache, r=r, comp0=comp0, dt=dt_save, T=T_stored)
    n_t = r.shape[1]
    # pool ids -> the studio's order (extra, intra, myelin), by name from the spec
    names = [p.name for p in spec.pools]
    order = [names.index(n) for n in ("extra", "intra", "myelin")]
    T2 = [float(getattr(spec.pools[i], "T2")) for i in order]
    T1 = [float(getattr(spec.pools[i], "T1")) for i in order]
    rng = np.random.default_rng(SEED)
    spins = []
    for c_out, c_in in enumerate(order):
        idx = np.flatnonzero(comp0 == c_in)
        pick = rng.choice(idx, size=min(PER_COMP, idx.size), replace=False)
        for i in pick:
            spins.append(dict(comp=c_out, r=np.round(r[i] * 1e6, 4).tolist()))
    from dmipy_sim.spec import geometry_from_spec
    geom = geometry_from_spec(spec)
    def field(*names):
        for n in names:
            if hasattr(geom, n):
                return np.asarray(getattr(geom, n))
        raise AttributeError(names)
    cell = float(field("cell_size", "_cell_size", "L").ravel()[0])
    centers = field("centers", "_centers_np", "_centers")
    r_in = field("inner_radii", "_inner_radii_np", "_inner_radii")
    r_out = field("outer_radii", "_outer_radii_np", "_outer_radii")
    cyl = [[float(c[0]) * 1e6, float(c[1]) * 1e6, float(ri) * 1e6, float(ro) * 1e6]
           for c, ri, ro in zip(centers, r_in, r_out)]
    try:
        rev = subprocess.check_output(["git", "-C", os.path.dirname(ds.__file__), "rev-parse", "--short", "HEAD"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        rev = "installed"
    GEOM = dict(dt=float(dt_save), n_t=int(n_t), TE=T_MAX, fibre=[0, 0, 1], comps=["extra", "intra", "myelin"],
                T2=T2, T1=T1, spins=spins, substrate=dict(cell=cell * 1e6, cyl=cyl),
                provenance=dict(dmipy_sim=rev, walk="walk_spec on Substrate.canonical(3 T).request(n_fibres=%d)" % N_FIBRES,
                                n_walkers=N_WALKERS, seed=SEED, dt_save=dt_save))
    html = open(PAGE, encoding="utf-8").read()
    i = html.index("const GEOM =")
    j = html.index(";\n", i)
    html = html[:i] + "const GEOM = " + json.dumps(GEOM, separators=(",", ":")) + html[j:]
    open(PAGE, "w", encoding="utf-8").write(html)
    print(f"wrote GEOM: {len(spins)} spins, n_t={n_t}, dt={dt_save:.2e}, T2={T2}, T1={T1}, sim {rev}")


if __name__ == "__main__":
    main()
