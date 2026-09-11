"""Regenerate the spin studio's data -- the ``GEOM`` literal in docs/studio/bloch_pedagogy.html.

The studio shows a few dozen water spins from each compartment of the canonical white matter
(extra-axonal, intra-axonal, myelin water) evolving under a pulse sequence. Their positions are a
real dmipy-sim walk on the canonical substrate (``Substrate.canonical().request(...)`` walked by
``walk_spec``), stored as a replay pack and decoded here; the compartments' T2/T1 come from the
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
    walk = walk_spec(spec, N_WALKERS, T_MAX, dt_save=DT_SAVE, seed=SEED, require_gpu=False, field=False)
    pack = ds.build_replay_pack(walk, id="dmipy.org/spin-studio", license="CC-BY-4.0",
                                citation="dmipy.org spin studio", K=64)
    r = np.asarray(pack.positions(), np.float64)                      # (n_w, n_t, 3) metres
    comp = np.asarray(walk.compartment)
    comp0 = comp[:, 0] if comp.ndim == 2 else comp                    # the compartment a walker starts in
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
    geom = walk.geometry
    cell = float(np.asarray(geom.cell_size).ravel()[0])
    cyl = [[float(c[0]) * 1e6, float(c[1]) * 1e6, float(ri) * 1e6, float(ri / g) * 1e6]
           for c, ri, g in zip(np.asarray(geom.centers), np.asarray(geom.inner_radii), np.asarray(geom.g_ratios))]
    try:
        rev = subprocess.check_output(["git", "-C", os.path.dirname(ds.__file__), "rev-parse", "--short", "HEAD"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        rev = "installed"
    GEOM = dict(dt=float(pack.dt), n_t=int(pack.n_t), TE=T_MAX, fibre=[0, 0, 1], comps=["extra", "intra", "myelin"],
                T2=T2, T1=T1, spins=spins, substrate=dict(cell=cell * 1e6, cyl=cyl),
                provenance=dict(dmipy_sim=rev, pack=pack.id if hasattr(pack, "id") else "dmipy.org/spin-studio",
                                n_fibres=N_FIBRES, n_walkers=N_WALKERS, seed=SEED, substrate="Substrate.canonical(3 T)"))
    html = open(PAGE, encoding="utf-8").read()
    i = html.index("const GEOM =")
    j = html.index(";\n", i)
    html = html[:i] + "const GEOM = " + json.dumps(GEOM, separators=(",", ":")) + html[j:]
    open(PAGE, "w", encoding="utf-8").write(html)
    print(f"wrote GEOM: {len(spins)} spins, n_t={pack.n_t}, dt={pack.dt:.2e}, T2={T2}, T1={T1}, sim {rev}")


if __name__ == "__main__":
    main()
