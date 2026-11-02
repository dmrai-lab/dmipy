"""Regenerate the spin studio's data -- the ``GEOM`` literal in docs/studio/bloch_pedagogy.html.

The studio shows a few dozen water spins from each compartment of the canonical white matter
(extra-axonal, intra-axonal, myelin water) evolving under a pulse sequence. Their positions are a
real dmipy-sim walk on the canonical substrate (``Substrate.canonical().request(...)`` walked by
``walk`` with ``raw_subset``), the walk's own block ends (a pack decode is band-limited, not a path); the
compartments' T2/T1 come from the substrate; the cross-section is the realised packing. The page's script
integrates the Bloch equation on those positions in the browser -- the one place on the site where physics runs in
JavaScript -- and ``tools/check_spin_studio.{js,py}`` check that integration against dmipy-replay's vector-Bloch
propagator on the same positions and the same sequence.

Run: python tools/gen_spin_studio.py   (needs dmipy-sim importable; the walk takes a while on a CPU)
"""
from __future__ import annotations

import json
import os
from importlib.metadata import version

import numpy as np

from dmipy_replay import Envelope
from dmipy_sim import walk
from dmipy_sim.spec import geometry_from_spec
from dmipy_sim.substrate import Substrate

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "docs", "studio", "bloch_pedagogy.html")
N_FIBRES, N_WALKERS, T_MAX, PER_COMP, SEED = 12, 600, 0.10, 24, 0
BAND_HZ = 400.0                      # 80 bands over the 100 ms walk: blocks of 0.32 ms, the positions the page reads


def envelope_of_spec(spec):
    """The envelope the walk is certified for: the page's band, the catalogue's field, and the susceptibility the
    spec's magnetic pools state (the myelin's), which the walk reads its field at."""
    chi = max(abs(p.susceptibility.chi_iso or 0.0) + abs(p.susceptibility.chi_aniso or 0.0)
              for p in spec.pools if p.susceptibility is not None)
    return Envelope(name="dmipy.org spin studio", band_hz=BAND_HZ, G_max=0.08, B0_list=(3.0,), chi_max=chi,
                    rho2_max=None, max_refocusing_pulses=None)


def main():
    # the canonical substrate has permeable membranes (kappa = 1e-5 m/s) and immobile myelin water, so an
    # intra-axonal walker that crosses into the sheath stops until it crosses back; for a page that shows
    # each compartment's own spins, the walls are closed (kappa = 0) and every spin stays in its pool
    sub = Substrate.canonical(field_T=3.0, kappa=0.0)
    spec = sub.request(n_fibres=N_FIBRES, seed=SEED)
    cache = os.environ.get("SPIN_STUDIO_WALK", "")                  # the walk is the expensive part: keep it raw
    if cache and os.path.exists(cache):
        z = np.load(cache)
        r, comp0, dt_save = z["r"], z["comp0"], float(z["dt"])
    else:
        w = walk(spec, N_WALKERS, T_max=T_MAX, envelope=envelope_of_spec(spec), seed=SEED, require_gpu=False,
                 raw_subset=N_WALKERS)
        r = np.asarray(w.raw_positions, np.float64)                  # (n_w, n_blocks + 1, 3) metres: the walk's own
        comp0 = np.asarray(w.raw_compartment)[:, 0]                  # block ends, and the pool each starts in
        dt_save = float(w.block["h"])
        if cache:
            np.savez(cache, r=r, comp0=comp0, dt=dt_save)
    n_t = r.shape[1]
    # pool ids -> the studio's order (extra, intra, myelin), by name from the spec
    names = [p.name for p in spec.pools]
    order = [names.index(n) for n in ("extra", "intra", "myelin")]
    T2 = [float(getattr(spec.pools[i], "T2")) for i in order]
    T1 = [float(getattr(spec.pools[i], "T1")) for i in order]
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
    rng = np.random.default_rng(SEED)
    spins = []
    for c_out, c_in in enumerate(order):
        idx = np.flatnonzero(comp0 == c_in)
        pick = rng.choice(idx, size=min(PER_COMP, idx.size), replace=False)
        for i in pick:
            spins.append(dict(comp=c_out, r=np.round(r[i] * 1e6, 4).tolist()))
    rev = version("dmipy-sim")
    GEOM = dict(dt=float(dt_save), n_t=int(n_t), TE=T_MAX, fibre=[0, 0, 1], comps=["extra", "intra", "myelin"],
                T2=T2, T1=T1, spins=spins, substrate=dict(cell=cell * 1e6, cyl=cyl),
                provenance=dict(dmipy_sim=rev, walk="walk on Substrate.canonical(3 T, kappa=0).request(n_fibres=%d)" % N_FIBRES,
                                n_walkers=N_WALKERS, seed=SEED, block_h=dt_save))
    html = open(PAGE, encoding="utf-8").read()
    i = html.index("const GEOM =")
    j = html.index(";\n", i)
    html = html[:i] + "const GEOM = " + json.dumps(GEOM, separators=(",", ":")) + html[j:]
    open(PAGE, "w", encoding="utf-8").write(html)
    print(f"wrote GEOM: {len(spins)} spins, n_t={n_t}, dt={dt_save:.2e}, T2={T2}, T1={T1}, sim {rev}")


if __name__ == "__main__":
    main()
