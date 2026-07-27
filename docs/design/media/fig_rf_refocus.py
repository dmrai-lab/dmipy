#!/usr/bin/env python3
"""Regenerates ``rf_refocus.gif`` — hard vs B1-robust 180°, watched spin by spin.

A 180° refocusing pulse must flip magnetisation by 180° — i.e. drive it from +z to −z — for
EVERY spin, whatever transmit strength B1⁺ that spin happens to feel. This animation follows
three spins on the Bloch sphere (rotating frame), one weak-transmit (B1⁺ = 0.7×), one nominal
(1.0×), one strong (1.3×), under the plain hard pulse (left) and the designed pulse (right),
with the B1(t) waveform playing below.

Hard 180°: exactly π only at B1⁺ = 1, so the 0.7× and 1.3× spins under/over-rotate and stall
far from the south pole — they are NOT inverted, and a spin echo built on them loses signal.
Designed 180°: a phase-modulated (composite/adiabatic-like) pulse whose net rotation is ≈180°
across the whole B1⁺ range, so all three spins arrive at −z. That per-spin robustness is what
``design_refocusing_rf`` maximises (crushed-echo refocusing efficiency η = (1−M_z)/2).

The designed pulse is bridged into dmipy-sim as a ``B1Pulse`` (``to_b1pulse``) and run through
the SAME ``dmipy_sim.rf.bloch_simulate`` forward as the hard pulse — design proposes, sim scores.

Needs the working-tree dmipy-design + dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/design:/path/sim python fig_rf_refocus.py
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

from dmipy_design import design_refocusing_rf
from dmipy_sim.rf import B1Pulse, bloch_simulate

DT, RF_DUR, B1_MAX = 1e-4, 6e-3, 19e-6

d = design_refocusing_rf(rf_duration=RF_DUR, dt=DT, B1_max=B1_MAX,      # peak-limited (robust)
                         b1_range=(0.7, 1.3), n_b1=7, off_resonance_hz=250.0,
                         n_off_resonance=7, n_basis=10, n_restarts=8, seed=0)
p_des = d.to_b1pulse()
p_hard = B1Pulse.hard(180, RF_DUR, DT)

B1S = np.array([0.7, 1.0, 1.3])                       # three representative transmit scales
SPIN_C = ["#6a3d9a", "#111111", "#e6ab02"]            # weak / nominal / strong
SPIN_L = ["B1⁺ = 0.7×  (weak)", "B1⁺ = 1.0×  (nominal)", "B1⁺ = 1.3×  (strong)"]
_, _, HH = bloch_simulate(p_hard, df_hz=0.0, b1_scale=B1S, return_history=True)   # (n+1,3,3)
_, _, HD = bloch_simulate(p_des, df_hz=0.0, b1_scale=B1S, return_history=True)
n_frames = HH.shape[0]
mag_h = np.abs(p_hard.b1) * 1e6
mag_d = np.abs(p_des.b1) * 1e6
t_env = np.arange(mag_h.size) * DT * 1e3
t_ms = np.arange(n_frames) * DT * 1e3
env_ymax = max(mag_h.max(), mag_d.max()) * 1.15


def _sphere(ax, title, color):
    u, v = np.mgrid[0:2 * np.pi:24j, 0:np.pi:14j]
    ax.plot_wireframe(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v),
                      color="0.9", lw=0.35)
    ax.plot([0, 0], [0, 0], [-1, 1], color="0.55", lw=0.8)
    ax.text(0, 0, 1.28, "+z", color="0.4", fontsize=9, ha="center")
    ax.text(0, 0, -1.42, "−z", color="0.4", fontsize=9, ha="center")
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev=12, azim=-70)
    ax.set_title(title, color=color, fontsize=12, pad=-2)


plt.rcParams.update({"font.size": 10})
fig = plt.figure(figsize=(9.0, 6.0), dpi=100)          # 900×600 (both %4==0)
gs = gridspec.GridSpec(2, 2, height_ratios=[3.3, 1.0], hspace=0.05, wspace=0.05,
                       left=0.04, right=0.97, top=0.80, bottom=0.13)
axH = fig.add_subplot(gs[0, 0], projection="3d")
axD = fig.add_subplot(gs[0, 1], projection="3d")
axE = fig.add_subplot(gs[1, :])
_sphere(axH, "Hard 180°", "#c1440e")
_sphere(axD, "B1-robust 180° (designed)", "#1b6ca8")

fig.suptitle("A 180° pulse should invert EVERY spin (+z → −z) whatever transmit strength B1⁺ it feels.\n"
             "Three spins are followed on the Bloch sphere (rotating frame); the RF waveform plays below.",
             fontsize=10, y=0.98)

paths, tips = {}, {}
for ax, H in ((axH, HH), (axD, HD)):
    for j, c in enumerate(SPIN_C):
        paths[(id(ax), j)] = ax.plot([], [], [], color=c, lw=0.8, alpha=0.35)[0]
        tips[(id(ax), j)] = ax.plot([], [], [], color=c, lw=3.0)[0]
# legend (shared) via proxy handles
handles = [plt.Line2D([0], [0], color=c, lw=2.6) for c in SPIN_C]
fig.legend(handles, SPIN_L, loc="lower center", ncol=3, fontsize=9, frameon=False,
           bbox_to_anchor=(0.5, 0.005))

axE.plot(t_env, mag_h, color="#c1440e", lw=1.6, label="hard |B1|")
axE.plot(t_env, mag_d, color="#1b6ca8", lw=1.6, label="designed |B1|")
axE.axhline(B1_MAX * 1e6, color="0.5", ls="--", lw=1)
axE.text(t_env[-1], B1_MAX * 1e6 + 0.4, "peak-B1 limit", ha="right", fontsize=8, color="0.5")
axE.set_xlim(t_ms[0], t_ms[-1]); axE.set_ylim(0, env_ymax)
axE.set_xlabel("time (ms)  —  the RF waveform being played"); axE.set_ylabel("|B1| (µT)", fontsize=9)
axE.legend(loc="upper right", fontsize=8, ncol=2)
vcur = axE.axvline(t_ms[0], color="0.4", lw=1)
mz_txt = fig.text(0.5, 0.325, "", ha="center", fontsize=9.5, color="0.2")


def frame(i):
    for ax, H in ((axH, HH), (axD, HD)):
        for j in range(3):
            P = H[:i + 1, :, j]
            pl = paths[(id(ax), j)]; pl.set_data(P[:, 0], P[:, 1]); pl.set_3d_properties(P[:, 2])
            tp = tips[(id(ax), j)]
            tp.set_data([0, H[i, 0, j]], [0, H[i, 1, j]]); tp.set_3d_properties([0, H[i, 2, j]])
    vcur.set_xdata([t_ms[i], t_ms[i]])
    mz_txt.set_text("inversion M$_z$ (−1 = fully flipped)   "
                    "hard: % .2f / % .2f / % .2f    designed: % .2f / % .2f / % .2f"
                    % (HH[i, 2, 0], HH[i, 2, 1], HH[i, 2, 2],
                       HD[i, 2, 0], HD[i, 2, 1], HD[i, 2, 2]))
    return ()


anim = FuncAnimation(fig, frame, frames=range(0, n_frames, 2), interval=90, blit=False)
out = os.path.join(os.path.dirname(__file__), "rf_refocus.gif")
anim.save(out, writer=PillowWriter(fps=16))
print("hard eff=%.3f  designed eff=%.3f" % (d.refocusing_efficiency_hard, d.refocusing_efficiency))
print("figure ->", out)
