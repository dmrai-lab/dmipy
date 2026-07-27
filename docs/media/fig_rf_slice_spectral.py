#!/usr/bin/env python3
"""Regenerates ``rf_slice_spectral.png`` — slice selectivity and the frequency dual.

Two panels, both straight from ``dmipy_sim.rf`` forwards:
  (left)  slice profile under a slice-select gradient — a windowed-sinc 90 excites a sharp
          slice (``slice_profile``); a hard 90 of the same duration has no spatial selectivity.
  (right) the small-tip (Pauly) frequency dual — |M_xy| vs off-resonance for low-flip pulses:
          a hard (box) pulse gives a sinc spectral profile; a windowed sinc gives a
          near-rectangular passband. Excitation profile ≈ FT of the B1 envelope.

Needs the working-tree dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_slice_spectral.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_sim.rf import B1Pulse, bloch_simulate, slice_profile

SINC, HARDC = "#1b6ca8", "#c1440e"

plt.rcParams.update({"font.size": 10})
fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.6), dpi=100)   # 920×360 (width %4==0)

# ── (left) slice profile: sinc vs hard 90 under a slice-select gradient ────────
sinc90 = B1Pulse.windowed_sinc(90, 2.56e-3, 1e-5, time_bw=4)
hard90 = B1Pulse.hard(90, 2.56e-3, 1e-5)
Gss = 20e-3                                                   # T/m
z = np.linspace(-15, 15, 601) * 1e-3                          # m
for p, c, lbl in ((sinc90, SINC, "windowed sinc"), (hard90, HARDC, "hard")):
    _, Mxy, _ = slice_profile(p, Gss, z)
    axL.plot(z * 1e3, np.abs(Mxy), color=c, lw=1.8, label=lbl)
axL.set_xlabel("position along slice (mm)"); axL.set_ylabel("|M$_{xy}$| (excited)")
axL.set_title("Slice selectivity (90°)"); axL.legend(fontsize=8); axL.set_ylim(-0.03, 1.05)

# ── (right) small-tip frequency profile: hard (→sinc) vs sinc (→rect) ──────────
df = np.linspace(-4000, 4000, 401)
sinc8 = B1Pulse.windowed_sinc(8, 2.56e-3, 1e-5, time_bw=4)
hard8 = B1Pulse.hard(8, 1e-3, 1e-6)
for p, c, lbl in ((hard8, HARDC, "hard (box → sinc)"), (sinc8, SINC, "sinc → rect")):
    Mxy, _ = bloch_simulate(p, df_hz=df)
    axR.plot(df * 1e-3, np.abs(Mxy) / np.abs(Mxy).max(), color=c, lw=1.8, label=lbl)
axR.set_xlabel("off-resonance (kHz)"); axR.set_ylabel("|M$_{xy}$| (normalised)")
axR.set_title("Small-tip frequency dual"); axR.legend(fontsize=8); axR.set_ylim(-0.03, 1.05)

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_slice_spectral.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
