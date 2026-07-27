#!/usr/bin/env python3
"""Regenerates ``rf_bir4.png`` — BIR-4, the exotic: a B1-insensitive rotation by ANY angle.

BIR-4 (B1-Independent Rotation, 4 segments; Garwood & Ke 1991) is built from four adiabatic
half-passages with an alternating frequency sweep and two phase jumps. Unlike an adiabatic full
passage (which only inverts), BIR-4 rotates the magnetisation by an arbitrary angle set purely by
the phase jump — B1-insensitively.

  (left)   the waveform: a double-hump sech amplitude and the alternating tanh frequency sweep;
  (centre) tunability: the achieved flip angle vs the phase jump φ, ≈ 2φ, essentially flat across
           the ±30 % B1⁺ band (shaded spread) — the "arbitrary-angle, B1-insensitive" property;
  (right)  at θ=180° it is a near-perfect inversion (M_z ≈ −1) across the whole B1⁺ range, where a
           hard 180° collapses.

    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_bir4.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_sim.rf import B1Pulse, bloch_simulate
GAMMA = 2.675e8
dt, T, A0 = 1e-5, 4e-3, 19e-6
BIR = "#2ca02c"


def bir4(phi_deg, beta=6.0, kappa=np.arctan(20.0), dmax=10000.0):
    n = int(round(T / dt)); q = n // 4; tau = np.linspace(0, 1, q)
    amp0 = np.tanh(beta * tau); fr0 = dmax * np.tan(kappa * (1 - tau)) / np.tan(kappa)
    fm = [1, -1, 1, -1]; phj = [0, phi_deg, phi_deg, 0]; A = []; F = []; J = []
    for k in range(4):
        rev = (k % 2 == 1)
        A.append(amp0[::-1] if rev else amp0)
        F.append((fr0[::-1] if rev else fr0) * fm[k])
        J.append(np.full(q, np.deg2rad(phj[k])))
    amp = np.concatenate(A); fr = np.concatenate(F); j = np.concatenate(J)
    gph = np.cumsum(2 * np.pi * fr * dt); m = min(len(amp), len(gph), len(j))
    return B1Pulse.from_samples(A0 * amp[:m] * np.exp(1j * (gph[:m] + j[:m])), dt), fr[:m]


plt.rcParams.update({"font.size": 10})
fig, axes = plt.subplots(1, 3, figsize=(11.6, 3.4), dpi=100)   # 1160×340 (width %4==0)

# (A) waveform
p, fr = bir4(90.0)
t = np.arange(p.n) * dt * 1e3
axA = axes[0]; axF = axA.twinx()
axA.plot(t, np.abs(p.b1) * 1e6, color=BIR, lw=1.8, label="|B1|")
axF.plot(t, fr * 1e-3, color="0.5", lw=1.2, ls="--", label="freq sweep")
axA.set_xlabel("time (ms)"); axA.set_ylabel("|B1| (µT)", color=BIR)
axF.set_ylabel("freq sweep (kHz)", color="0.5", fontsize=9)
axA.tick_params(axis="y", labelcolor=BIR); axF.tick_params(axis="y", labelcolor="0.5")
axA.set_title("BIR-4 waveform (4 half-passages)")

# (B) tunability: flip vs phase jump, across B1+
phis = np.arange(0, 91, 10)
probe = np.array([0.7, 1.0, 1.3]); zero = np.zeros_like(probe)
flip_nom, flip_lo, flip_hi = [], [], []
for phi in phis:
    pp, _ = bir4(float(phi))
    mz = bloch_simulate(pp, df_hz=zero, b1_scale=probe)[1]
    fl = np.rad2deg(np.arccos(np.clip(mz, -1, 1)))
    flip_nom.append(fl[1]); flip_lo.append(fl.min()); flip_hi.append(fl.max())
axes[1].fill_between(phis, flip_lo, flip_hi, color=BIR, alpha=0.2, label="spread over ±30 % B1⁺")
axes[1].plot(phis, flip_nom, "o-", color=BIR, lw=2, label="achieved flip")
axes[1].plot(phis, 2 * phis, "k:", lw=1, label=r"$\theta = 2\varphi$")
axes[1].set_xlabel(r"phase jump  $\varphi$ (deg)"); axes[1].set_ylabel("flip angle (deg)")
axes[1].set_title("Tunable, B1-insensitive rotation"); axes[1].legend(fontsize=8, loc="upper left")

# (C) inversion robustness at theta=180 vs hard
b1_ax = np.linspace(0.4, 1.6, 121); z = np.zeros_like(b1_ax)
p180, _ = bir4(90.0)
hard = B1Pulse.from_samples(np.full(int(round(T / dt)), np.deg2rad(180) / (GAMMA * int(round(T / dt)) * dt)), dt)
axes[2].axvspan(0.7, 1.3, color="0.93")
axes[2].plot(b1_ax, bloch_simulate(hard, df_hz=z, b1_scale=b1_ax)[1], color="#c1440e", lw=2, label="hard 180°")
axes[2].plot(b1_ax, bloch_simulate(p180, df_hz=z, b1_scale=b1_ax)[1], color=BIR, lw=2, label="BIR-4 (θ=180°)")
axes[2].axhline(-1, color="0.6", lw=0.8, ls=":")
axes[2].set_xlabel(r"$B_1^+$ transmit scale"); axes[2].set_ylabel(r"inversion $M_z$")
axes[2].set_title("Inversion across B1⁺"); axes[2].set_ylim(-1.05, 1.05); axes[2].legend(fontsize=8)

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_bir4.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
