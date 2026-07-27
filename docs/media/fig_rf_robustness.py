#!/usr/bin/env python3
"""Regenerates ``rf_robustness.png`` — a taxonomy of ways to make a robust 180°.

Inversion fidelity (M_z from +z; −1 = perfect) vs transmit scale B1⁺, for four strategies:

  * Hard 180°           — a single fixed pulse: perfect only at B1⁺=1, collapses either side.
  * Composite 90ₓ-180_y-90ₓ — robustness from a designed SEQUENCE of simple rotations.
  * Adiabatic HS        — robustness from a continuous frequency SWEEP (the magnetisation follows
                          the effective field). What ``design_refocusing_rf`` produces.
  * BIR-4               — an adiabatic pulse built from four half-passages with phase jumps: a
                          B1-insensitive rotation by ANY angle (shown at 180°).

Built entirely on dmipy-sim's B1Pulse forward.

    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_robustness.py
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


def hard(flip, dur, phase=0.0):
    n = int(round(dur / dt)); amp = np.deg2rad(flip) / (GAMMA * n * dt)
    return np.full(n, amp) * np.exp(1j * np.deg2rad(phase))


def composite():
    seg = lambda f, p: hard(f, max(1, abs(f) / 180) * 0.6e-3, p)
    return B1Pulse.from_samples(np.concatenate([seg(90, 0), seg(180, 90), seg(90, 0)]), dt)


def hs(A0=A0, mu=2.0, beta=5.3):
    n = int(round(T / dt)); tau = np.linspace(-1, 1, n); sech = 1 / np.cosh(beta * tau)
    return B1Pulse.from_samples(A0 * sech * np.exp(1j * mu * np.log(sech + 1e-300)), dt)


def bir4(phi_deg=90.0, A0=A0, beta=6.0, kappa=np.arctan(20.0), dmax=10000.0):
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
    return B1Pulse.from_samples(A0 * amp[:m] * np.exp(1j * (gph[:m] + j[:m])), dt)


b1_ax = np.linspace(0.4, 1.6, 121)
z = np.zeros_like(b1_ax)


def mz(p):
    return bloch_simulate(p, df_hz=z, b1_scale=b1_ax)[1]


series = [("Hard 180°", B1Pulse.from_samples(hard(180, T), dt), "#c1440e", "-"),
          (r"Composite $90_x$-$180_y$-$90_x$", composite(), "#e6ab02", "-"),
          ("Adiabatic HS (design)", hs(), "#1b6ca8", "-"),
          (r"BIR-4 ($\theta$=180°)", bir4(), "#2ca02c", "-")]

plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=100)   # 760×420 (width %4==0)
ax.axvspan(0.7, 1.3, color="0.93", label=r"±30 % $B_1^+$")
for name, p, c, ls in series:
    ax.plot(b1_ax, mz(p), ls, color=c, lw=2, label=name)
ax.axhline(-1, color="0.6", lw=0.8, ls=":")
ax.set_xlabel(r"$B_1^+$ transmit scale"); ax.set_ylabel(r"inversion  $M_z$   (-1 = perfect)")
ax.set_title("Four ways to build a B1-robust 180°")
ax.set_ylim(-1.05, 1.05); ax.legend(loc="lower center", fontsize=9, ncol=1)
ax.grid(alpha=0.2)
fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_robustness.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
