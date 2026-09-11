"""Parity of the spin studio's in-browser Bloch integration with dmipy_sim.replay_bloch.

``tools/check_spin_studio.js`` runs the page's script at a knob setting and dumps the sequence it
built and the magnetisation it computed for every spin. This replays the SAME positions (the
``GEOM`` walk embedded in the page) under the SAME physical gradient and RF events with the
engine's vector-Bloch replay, and compares the per-compartment mean transverse magnetisation at
the echo. The page interpolates the walk onto its fine grid and the engine integrates the walk
piecewise-exactly, so the two agree to interpolation error, not to rounding.

Run: python tools/check_spin_studio.py   (needs node and dmipy-sim importable)
Exit status is the number of settings that disagree.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np

import dmipy_sim as ds

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "docs", "studio", "bloch_pedagogy.html")
SETTINGS = [
    dict(fam="pgse", te=60, pgse_b=1000, pgse_del=8, pgse_Dd=30, gang=90, relax=False),
    dict(fam="pgse", te=60, pgse_b=2000, pgse_del=8, pgse_Dd=30, gang=0, relax=True),
    dict(fam="cpmg", te=60, cpmg_ne=4, relax=True),
]
TOL = 0.03


def geom():
    html = open(PAGE, encoding="utf-8").read()
    i = html.index("const GEOM =")
    return json.loads(html[i + len("const GEOM ="):html.index(";\n", i)])


def run_js(setting, out):
    subprocess.check_call(["node", os.path.join(HERE, "check_spin_studio.js"), json.dumps(setting), out],
                          stdout=subprocess.DEVNULL)
    return json.load(open(out))


def engine(G, run, r, dt_traj, T2, T1, comps, relax):
    n, dt = run["n"], run["dt"]
    r = r[:, : int(np.ceil(run["TE"] / dt_traj)) + 1]                # the walk up to the readout: the engine
    #                                                                  relaxes to the end of what it is given
    rf = []
    for k, e in enumerate(run["rf"]):                                # the page's finite pulses, as events
        t0 = max(0, e["i0"] - (e["nsub"] >> 1)) * dt
        rf.append(dict(t_s=t0 + e["nsub"] * dt / 2, flip_deg=float(np.degrees(e["flip_rad"])),
                       axis_deg=float(np.degrees(e["axis_rad"])), duration_s=e["nsub"] * dt, offset_hz=0.0,
                       label="Mz→Mxy" if k == 0 else "refocus"))
    rf = ds.RFSchedule.from_dicts(rf)
    kw = dict(comp_traj=np.broadcast_to(comps[:, None], r.shape[:2]).copy(),
              T2_per_comp=np.array(T2), T1_per_comp=np.array(T1)) if relax else {}
    walkers, _ = ds.replay_bloch(r, dt_traj, G[None], dt, rf, return_walker_signals=True, **kw)
    return np.asarray(walkers)                                       # (3, n_w): Mx, My, Mz per walker at the end


def main():
    g = geom()
    r = np.array([s["r"] for s in g["spins"]], np.float64) * 1e-6      # (n_w, n_t, 3) metres
    comps = np.array([s["comp"] for s in g["spins"]])
    bad = 0
    for k, setting in enumerate(SETTINGS):
        run = run_js(setting, f"/tmp/spin_studio_{k}.json")
        G = np.asarray(run["G"], np.float64)                           # (n, 3) physical, fine grid
        M = np.asarray(run["M"])                                       # (n, n_w, 3)
        echo = run["echoes"][-1] if run["echoes"] else run["n"] - 1
        js = np.array([np.abs((M[echo, comps == c, 0] + 1j * M[echo, comps == c, 1]).mean()) for c in range(3)])
        try:
            W = engine(G, run, r, g["dt"], g["T2"], g["T1"], comps, setting.get("relax", True))
            en = np.array([np.abs((W[0, comps == c] + 1j * W[1, comps == c]).mean()) for c in range(3)])
        except Exception as e:                                         # the engine refused: report, count
            print(f"[{k}] {setting}: engine replay failed: {e}")
            bad += 1
            continue
        gap = float(np.abs(js - en).max())
        ok = gap < TOL
        bad += not ok
        print(f"[{k}] {run['label']}: page |Mxy| per comp {js.round(3)}  engine {en.round(3)}  max gap {gap:.3f} {'ok' if ok else 'MISMATCH'}")
    print(f"{bad} setting(s) disagree (tolerance {TOL})")
    return bad


if __name__ == "__main__":
    sys.exit(main())
