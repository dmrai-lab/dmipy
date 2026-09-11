"""Build the sequence explorer's data -- docs/studio/explorer_data/<family>.json.

Every point on the explorer's grid is one call to a dmipy-sim builder; what the page draws is
what the object holds: the physical gradient ``G``, the sign the pulses impose, ``q(t)`` and ``b``
from the object, the RF events from its schedule, the readout, and -- when the builder refuses the
point -- the refusal itself. The browser looks up and draws; no physics is re-implemented there.

Run: python tools/gen_explorer_data.py   (needs dmipy-sim importable)
"""
from __future__ import annotations

import itertools
import json
import os
import subprocess

import numpy as np

import dmipy_sim as ds

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "studio", "explorer_data")
N_T = 240                           # the grid the sequences are built on; the page draws EVERY sample
N_DRAW = N_T
INF = "inf"


def _grid(**knobs):
    keys = list(knobs)
    for values in itertools.product(*(knobs[k] for k in keys)):
        yield dict(zip(keys, values))


def _slew(v):
    return np.inf if v == INF else float(v)


FAMILIES = {
    "pgse": dict(
        label="PGSE — spin echo",
        knobs=dict(delta_ms=[5, 10, 15, 20], Delta_ms=[20, 30, 40, 60], b=[0.5e9, 1e9, 2e9, 3e9], slew=[80, 200, INF]),
        build=lambda k: ds.pgse([[1, 0, 0]], k["delta_ms"] * 1e-3, k["Delta_ms"] * 1e-3, bvalues=[k["b"]],
                                n_t=N_T, slew_rate=_slew(k["slew"])),
        call=lambda k: f'pgse([[1, 0, 0]], delta={k["delta_ms"]}e-3, Delta={k["Delta_ms"]}e-3, bvalues=[{k["b"]:.1e}], slew_rate={k["slew"]})',
    ),
    "pgste": dict(
        label="PGSTE — stimulated echo",
        knobs=dict(delta_ms=[4, 6, 10], TM_ms=[20, 50, 100, 200], b=[0.5e9, 1e9, 2e9], slew=[200, INF]),
        build=lambda k: ds.pgste([[1, 0, 0]], k["delta_ms"] * 1e-3, k["TM_ms"] * 1e-3, bvalues=[k["b"]],
                                 n_t=N_T, slew_rate=_slew(k["slew"])),
        call=lambda k: f'pgste([[1, 0, 0]], delta={k["delta_ms"]}e-3, TM={k["TM_ms"]}e-3, bvalues=[{k["b"]:.1e}], slew_rate={k["slew"]})',
    ),
    "ogse": dict(
        label="OGSE — oscillating gradient",
        knobs=dict(f_hz=[25, 50, 100, 200], sigma_ms=[20, 40], shape=["trapezoid", "cosine"], b=[0.5e9, 1e9, 2e9], slew=[200, INF]),
        build=lambda k: ds.ogse([[1, 0, 0]], float(k["f_hz"]), k["sigma_ms"] * 1e-3, shape=k["shape"], bvalues=[k["b"]],
                                n_t=N_T, slew_rate=_slew(k["slew"])),
        call=lambda k: f'ogse([[1, 0, 0]], {k["f_hz"]}.0, {k["sigma_ms"]}e-3, shape="{k["shape"]}", bvalues=[{k["b"]:.1e}], slew_rate={k["slew"]})',
    ),
    "cpmg": dict(
        label="CPMG — refocusing train (no gradient)",
        knobs=dict(n_echoes=[4, 8, 16, 32], TE_ms=[5, 10, 20, 40]),
        build=lambda k: ds.cpmg(k["n_echoes"], k["TE_ms"] * 1e-3, n_t_per_echo=max(15, N_T // k["n_echoes"])),
        call=lambda k: f'cpmg({k["n_echoes"]}, {k["TE_ms"]}e-3)',
    ),
    "gre": dict(
        label="GRE — gradient echo",
        knobs=dict(TE_ms=[20, 40, 80], delta_ms=[5, 10], Delta_ms=[15, 25], b=[0, 5e8, 1e9]),
        build=lambda k: ds.gre(k["TE_ms"] * 1e-3, gradient_directions=[[1, 0, 0]], bvalues=[k["b"]],
                               delta=k["delta_ms"] * 1e-3, Delta=k["Delta_ms"] * 1e-3, n_t=N_T),
        call=lambda k: f'gre({k["TE_ms"]}e-3, gradient_directions=[[1, 0, 0]], bvalues=[{k["b"]:.1e}], delta={k["delta_ms"]}e-3, Delta={k["Delta_ms"]}e-3)',
    ),
    "ste": dict(
        label="STE — spherical b-tensor",
        knobs=dict(sigma_ms=[30, 45, 60], b=[0.5e9, 1e9, 2e9], slew=[200, INF]),
        build=lambda k: ds.ste(k["sigma_ms"] * 1e-3, bvalues=[k["b"]], n_t=N_T, slew_rate=_slew(k["slew"])),
        call=lambda k: f'ste({k["sigma_ms"]}e-3, bvalues=[{k["b"]:.1e}], slew_rate={k["slew"]})',
    ),
    "pte": dict(
        label="PTE — planar b-tensor",
        knobs=dict(sigma_ms=[30, 45, 60], b=[0.5e9, 1e9, 2e9], slew=[200, INF]),
        build=lambda k: ds.pte([0, 0, 1], k["sigma_ms"] * 1e-3, bvalues=[k["b"]], n_t=N_T, slew_rate=_slew(k["slew"])),
        call=lambda k: f'pte([0, 0, 1], {k["sigma_ms"]}e-3, bvalues=[{k["b"]:.1e}], slew_rate={k["slew"]})',
    ),
}


def _draw(a, n):
    """Resample a per-step curve onto n points for drawing (nearest step: the object is a hold)."""
    a = np.asarray(a, np.float64)
    idx = np.minimum((np.arange(n) * a.shape[0] / n).astype(int), a.shape[0] - 1)
    return a[idx]


def _r(a, sig=4):
    """Round to ``sig`` significant figures (compact JSON, drawing precision)."""
    return [0.0 if v == 0 else float(f"{v:.{sig}g}") for v in np.asarray(a, np.float64).ravel()]


def encode(seq):
    n = seq.n_t
    t = np.arange(n) * seq.dt
    G = np.asarray(seq.G)[0]                                   # (n_t, 3) physical
    sign = np.asarray(seq.rf.sign(t)) if len(seq.rf) else np.ones(n)
    q = ds.GAMMA * np.cumsum(np.asarray(seq.G_eff)[0], 0) * seq.dt   # rad/m
    B = np.asarray(seq.btensor())[0]
    lam = np.sort(np.linalg.eigvalsh(B))[::-1]
    tr = float(lam.sum())
    b_delta = float((lam[0] - (tr - lam[0]) / 2) / tr) if tr > 0 else 0.0
    axes = [i for i in range(3) if np.any(G[:, i] != 0)] or [0]  # the axes that play (drawn; the rest is zero)
    return dict(
        T_ms=round(seq.T * 1e3, 3), n_t=int(n), dt_us=round(seq.dt * 1e6, 3),
        axes=axes,                                                  # t for sample k is k * dt
        G_mT=[_r(_draw(G[:, i], N_DRAW) * 1e3, 3) for i in axes],
        sign=_r(_draw(sign, N_DRAW), 1),
        q=[_r(_draw(q[:, i], N_DRAW) / 1e3, 3) for i in axes],       # rad/mm
        b_smm2=round(float(seq.b()[0]) * 1e-6, 1), b_delta=round(b_delta, 3),
        residual=float(f"{seq.refocusing_residual:.2e}"),
        rf=[dict(t_ms=round(e.t_s * 1e3, 3), flip=e.flip_deg, label=e.label, dur_ms=round(e.duration_s * 1e3, 3)) for e in seq.rf],
        readout_ms=[round(i * seq.dt * 1e3, 3) for i in seq.readout],
        echoes=len(seq.echoes), TM_ms=None if seq.TM is None else round(seq.TM * 1e3, 3),
        Gmax_mT=round(float(np.abs(G).max()) * 1e3, 2),
    )


def main(out=OUT):
    os.makedirs(out, exist_ok=True)
    try:
        sim_rev = subprocess.check_output(["git", "-C", os.path.dirname(ds.__file__), "rev-parse", "--short", "HEAD"],
                                          text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        sim_rev = "installed"
    index = dict(families={}, dmipy_sim=sim_rev, n_draw=N_DRAW)
    for name, fam in FAMILIES.items():
        points = []
        n_ok = n_ref = 0
        for k in _grid(**fam["knobs"]):
            entry = dict(knobs=k, call=fam["call"](k))
            try:
                entry["seq"] = encode(fam["build"](k))
                n_ok += 1
            except ValueError as e:
                entry["refused"] = str(e)
                n_ref += 1
            points.append(entry)
        data = dict(family=name, label=fam["label"], knobs=fam["knobs"], points=points, dmipy_sim=sim_rev)
        path = os.path.join(out, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, separators=(",", ":"))
        index["families"][name] = dict(label=fam["label"], knobs=fam["knobs"], n_points=len(points), n_refused=n_ref)
        print(f"{name:6s} {n_ok:3d} built, {n_ref:3d} refused -> {os.path.getsize(path) / 1e3:.0f} kB")
    with open(os.path.join(out, "index.json"), "w") as f:
        json.dump(index, f, separators=(",", ":"))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
