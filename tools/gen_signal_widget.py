"""Build the landing page's live-signal widget data -- docs/studio/signal_data.json.

One walk per substrate (cylinders of a few radii, plus free water), replayed offline over a grid
of acquisitions: a PGSE b-sweep and an OGSE frequency sweep, gradient across the axon. The replay
invariant makes this exact and cheap: the walk never depends on the acquisition, so the page shows
real dmipy-sim signals for every knob without simulating anything in the browser.

Run: python tools/gen_signal_widget.py   (needs dmipy-sim importable; a few minutes on a CPU)
"""
from __future__ import annotations

import json
import os
import subprocess

import numpy as np

import dmipy_sim as ds

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "studio", "signal_data.json")

D = 1.7e-9
RADII_UM = [1.0, 2.0, 4.0, 8.0]
B_SMM2 = [0, 250, 500, 1000, 1500, 2000, 3000, 4000]
F_HZ = [25, 50, 100, 200]
N_WALK, T_MAX, DT = 6_000, 0.10, 2e-4


def pack_for(geom, name):
    walk = ds.simulate_trajectories(N_WALK, D, geom, T_max=T_MAX, dt_save=DT, seed=0, require_gpu=False)
    return ds.build_replay_pack(walk, id=f"docs/{name}", license="CC-BY-4.0", citation="dmipy.org", K=48)


def main():
    seqs = dict(
        pgse=ds.pgse([[1, 0, 0]] * len(B_SMM2), 0.010, 0.030, bvalues=[b * 1e6 for b in B_SMM2], slew_rate=np.inf),
        ogse=ds.ogse([[1, 0, 0]] * len(F_HZ), F_HZ, 0.040, shape="cosine", bvalues=[1e9] * len(F_HZ), slew_rate=np.inf),
    )
    substrates = {f"cylinder_{r:g}um": ds.Cylinder(radius=r * 1e-6, orientation=(0, 0, 1)) for r in RADII_UM}
    substrates["free"] = ds.FreeDiffusion()
    out = dict(D=D, b_smm2=B_SMM2, f_hz=F_HZ, pgse=dict(delta_ms=10, Delta_ms=30), ogse=dict(sigma_ms=40, b_smm2=1000),
               substrates={}, dmipy_sim="installed")
    try:
        out["dmipy_sim"] = subprocess.check_output(["git", "-C", os.path.dirname(ds.__file__), "rev-parse", "--short", "HEAD"],
                                                   text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        pass
    for name, geom in substrates.items():
        pack = pack_for(geom, name)
        E = {k: np.abs(np.asarray(pack.replay(s, tissue=False))).round(4).tolist() for k, s in seqs.items()}
        out["substrates"][name] = dict(label=("free water" if name == "free" else f"axon, radius {name.split('_')[1][:-2]} µm"), **E)
        print(name, "pgse", E["pgse"][:3], "... ogse", E["ogse"])
    out["stejskal_tanner"] = np.exp(-np.array(B_SMM2) * 1e6 * D).round(4).tolist()
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", os.path.relpath(OUT), os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
