#!/usr/bin/env python3
"""Regenerates ``rf_bir4_movie.gif`` — HS vs BIR-4 trajectory on the Bloch sphere.

Both pulses invert (+z → −z) B1-insensitively, but by very different routes:

  * Adiabatic HS  — the magnetisation follows the swept effective field in one smooth spiral.
  * BIR-4         — four adiabatic half-passages with two phase jumps: the magnetisation sweeps
                    out toward the transverse plane, is abruptly reoriented at each phase jump,
                    and only then lands at −z. You can see the four-segment structure in the path.

Single spin at B1⁺ = 1 (on resonance), traced in the rotating frame, with |B1(t)| playing below.

    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_bir4_movie.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.animation import FuncAnimation, PillowWriter

from dmipy_sim.rf import B1Pulse, bloch_simulate
GAMMA = 2.675e8
dt, T, A0 = 2e-5, 4e-3, 19e-6      # dt=20us keeps the GIF light


def hs(mu=2.0, beta=5.3):
    n = int(round(T / dt)); tau = np.linspace(-1, 1, n); sech = 1 / np.cosh(beta * tau)
    return B1Pulse.from_samples(A0 * sech * np.exp(1j * mu * np.log(sech + 1e-300)), dt)


def bir4(phi_deg=90.0, beta=6.0, kappa=np.arctan(20.0), dmax=10000.0):
    n = int(round(T / dt)); q = n // 4; tau = np.linspace(0, 1, q)
    a0 = np.tanh(beta * tau); f0 = dmax * np.tan(kappa * (1 - tau)) / np.tan(kappa)
    fm = [1, -1, 1, -1]; pj = [0, phi_deg, phi_deg, 0]; A = []; F = []; J = []
    for k in range(4):
        r = (k % 2 == 1)
        A.append(a0[::-1] if r else a0); F.append((f0[::-1] if r else f0) * fm[k])
        J.append(np.full(q, np.deg2rad(pj[k])))
    amp = np.concatenate(A); fr = np.concatenate(F); j = np.concatenate(J)
    g = np.cumsum(2 * np.pi * fr * dt); m = min(len(amp), len(g), len(j))
    return B1Pulse.from_samples(A0 * amp[:m] * np.exp(1j * (g[:m] + j[:m])), dt)


def traj(p):
    _, _, h = bloch_simulate(p, df_hz=0.0, b1_scale=1.0, return_history=True)
    return h[:, :, 0]


P_HS, P_BIR = hs(), bir4()
H_HS, H_BIR = traj(P_HS), traj(P_BIR)
n = min(len(H_HS), len(H_BIR))
mag_hs = np.abs(P_HS.b1) * 1e6
mag_bir = np.abs(P_BIR.b1) * 1e6
t_env = np.arange(len(mag_hs)) * dt * 1e3


def _sphere(ax, title, c):
    u, v = np.mgrid[0:2 * np.pi:24j, 0:np.pi:14j]
    ax.plot_wireframe(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v), color="0.9", lw=0.3)
    ax.plot([0, 0], [0, 0], [-1, 1], color="0.6", lw=0.7)
    ax.text(0, 0, 1.3, "+z", color="0.4", ha="center", fontsize=9)
    ax.text(0, 0, -1.45, "−z", color="0.4", ha="center", fontsize=9)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev=14, azim=-65)
    ax.set_title(title, color=c, fontsize=11)


plt.rcParams.update({"font.size": 10})
fig = plt.figure(figsize=(8.0, 5.0), dpi=100)           # 800×500 (both %4==0)
gs = gridspec.GridSpec(2, 2, height_ratios=[3.4, 1.0], hspace=0.35, wspace=0.05,
                       left=0.03, right=0.97, top=0.9, bottom=0.12)
axH = fig.add_subplot(gs[0, 0], projection="3d")
axB = fig.add_subplot(gs[0, 1], projection="3d")
axE = fig.add_subplot(gs[1, :])
_sphere(axH, "Adiabatic HS — one smooth spiral", "#1b6ca8")
_sphere(axB, "BIR-4 — sweep, reorient, sweep", "#2ca02c")
fig.suptitle("Both invert +z → −z, by very different routes", fontsize=11, y=0.97)

paths = [axH.plot([], [], [], color="#1b6ca8", lw=1.4, alpha=0.55)[0],
         axB.plot([], [], [], color="#2ca02c", lw=1.4, alpha=0.55)[0]]
tips = [axH.plot([], [], [], color="#1b6ca8", lw=3)[0],
        axB.plot([], [], [], color="#2ca02c", lw=3)[0]]

axE.plot(t_env, mag_hs, color="#1b6ca8", lw=1.5, label="HS |B1|")
axE.plot(t_env[:len(mag_bir)], mag_bir, color="#2ca02c", lw=1.5, label="BIR-4 |B1|")
axE.set_xlim(t_env[0], t_env[-1]); axE.set_ylim(0, 21)
axE.set_xlabel("time (ms) — RF waveform"); axE.set_ylabel("|B1| (µT)", fontsize=9)
axE.legend(loc="upper right", fontsize=8, ncol=2)
vcur = axE.axvline(t_env[0], color="0.4", lw=1)


def frame(i):
    for H, path, tip in ((H_HS, paths[0], tips[0]), (H_BIR, paths[1], tips[1])):
        P = H[:i + 1]
        path.set_data(P[:, 0], P[:, 1]); path.set_3d_properties(P[:, 2])
        tip.set_data([0, H[i, 0]], [0, H[i, 1]]); tip.set_3d_properties([0, H[i, 2]])
    vcur.set_xdata([t_env[min(i, len(t_env) - 1)]] * 2)
    return ()


anim = FuncAnimation(fig, frame, frames=range(0, n, 2), interval=80, blit=False)
out = os.path.join(os.path.dirname(__file__), "rf_bir4_movie.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("figure ->", out)
