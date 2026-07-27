#!/usr/bin/env python3
"""Regenerates ``rf_profile.png`` — why the robust 180 wins, in one static figure.

Three panels:
  (left)   refocusing efficiency η = (1−M_z)/2 vs B1+ transmit scale (on resonance). The hard
           180 is a sharp peak at B1+=1 and collapses either side; the designed pulse holds
           η≈1 flat across the ±30% transmit spread — every spin genuinely inverts.
  (centre) η vs off-resonance (at B1+=1) — the designed pulse also holds its passband across
           the ±250 Hz design band.
  (right)  the designed waveform: |B1(t)| (amplitude modulation) and its phase (phase
           modulation) — the composite/adiabatic-like structure that buys the robustness,
           against the flat hard 180. Peak-B1 and the SAR cost are annotated.

Needs the working-tree dmipy-design + dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/design:/path/sim python fig_rf_profile.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_design import design_refocusing_rf
from dmipy_design.optimizers.rf_pulse import _inversion_mz, GAMMA

DT, RF_DUR, B1_MAX = 1e-4, 6e-3, 19e-6
HARD, DES = "#c1440e", "#1b6ca8"

d = design_refocusing_rf(rf_duration=RF_DUR, dt=DT, B1_max=B1_MAX,
                         b1_range=(0.7, 1.3), n_b1=7, off_resonance_hz=250.0,
                         n_off_resonance=7, n_basis=10, n_restarts=8, seed=0)
n_rf = d.B1.shape[0]
A0 = np.pi / (GAMMA * n_rf * DT)
hard = np.full(n_rf, A0, dtype=np.complex128)


def eta(b1c, b1_scale, df_hz):
    b1 = np.broadcast_to(b1_scale, np.broadcast(b1_scale, df_hz).shape).ravel().astype(float)
    dw = np.broadcast_to(df_hz, np.broadcast(b1_scale, df_hz).shape).ravel().astype(float) * 2 * np.pi
    return (1.0 - _inversion_mz(b1c, b1, dw, DT)) / 2.0


plt.rcParams.update({"font.size": 10})
fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.4), dpi=100)   # 1120×340 (width %4==0)

# (A) efficiency vs B1+ transmit scale, on resonance
b1_ax = np.linspace(0.5, 1.5, 121)
axes[0].axvspan(0.7, 1.3, color="0.92", label="design range")
axes[0].plot(b1_ax, eta(hard, b1_ax, 0.0), color=HARD, lw=2, label="hard 180°")
axes[0].plot(b1_ax, eta(d.B1, b1_ax, 0.0), color=DES, lw=2, label="designed")
axes[0].set_xlabel("B1$^+$ transmit scale"); axes[0].set_ylabel("refocusing efficiency  η")
axes[0].set_title("Transmit-field robustness"); axes[0].set_ylim(0, 1.05)
axes[0].legend(fontsize=8, loc="lower center")

# (B) efficiency vs off-resonance, at B1+ = 1
df_ax = np.linspace(-600, 600, 241)
axes[1].axvspan(-250, 250, color="0.92", label="design band")
axes[1].plot(df_ax, eta(hard, 1.0, df_ax), color=HARD, lw=2, label="hard 180°")
axes[1].plot(df_ax, eta(d.B1, 1.0, df_ax), color=DES, lw=2, label="designed")
axes[1].set_xlabel("off-resonance (Hz)"); axes[1].set_title("Off-resonance robustness")
axes[1].set_ylim(0, 1.05); axes[1].legend(fontsize=8, loc="lower center")

# (C) the designed waveform: amplitude + phase modulation
t = d.times() * 1e3
axC = axes[2]; axP = axC.twinx()
axC.plot(t, np.abs(hard) * 1e6, color=HARD, lw=1.6, label="hard |B1|")
axC.plot(t, np.abs(d.B1) * 1e6, color=DES, lw=1.8, label="designed |B1|")
axC.axhline(B1_MAX * 1e6, color="0.5", ls="--", lw=1)
axP.plot(t, np.unwrap(np.angle(d.B1)) * 180 / np.pi, color=DES, lw=1.0, ls=":", alpha=0.8)
axC.set_xlabel("time (ms)"); axC.set_ylabel("|B1| (µT)")
axP.set_ylabel("designed phase (°)", color=DES, fontsize=9)
axP.tick_params(axis="y", labelcolor=DES)
axC.set_title("Designed waveform (amp + phase)")
axC.set_ylim(0, B1_MAX * 1e6 * 1.15)
axC.legend(fontsize=8, loc="upper right")
axC.text(0.03, 0.06, "peak %.1f µT   SAR %.0f× hard" % (d.peak_B1 * 1e6, d.sar_ratio),
         transform=axC.transAxes, fontsize=8, color=DES)

fig.suptitle("Refocusing efficiency across the ensemble:  hard %.2f  →  designed %.2f   "
             "(η = 1 means every spin is genuinely inverted)"
             % (d.refocusing_efficiency_hard, d.refocusing_efficiency), fontsize=10.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
out = os.path.join(os.path.dirname(__file__), "rf_profile.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
