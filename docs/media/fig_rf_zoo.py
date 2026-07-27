#!/usr/bin/env python3
"""Regenerates ``rf_zoo.gif`` — watch the spins under a 90 vs a 180 hard pulse.

The forward model has no idea a pulse is "excitation" or "refocusing" — hand
``dmipy_sim.rf.bloch_simulate`` any B1(t) and it integrates the Bloch equation. Here two hard
pulses of the same duration but different flip: a 90 tips the magnetisation from +z into the
transverse plane; a 180 drives it through to −z (inversion). Same code path, different area.

Needs the working-tree dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_zoo.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from dmipy_sim.rf import B1Pulse, bloch_simulate

DT, DUR = 2e-5, 2e-3
p90 = B1Pulse.hard(90, DUR, DT)
p180 = B1Pulse.hard(180, DUR, DT)
_, _, h90 = bloch_simulate(p90, df_hz=0.0, return_history=True)
_, _, h180 = bloch_simulate(p180, df_hz=0.0, return_history=True)
h90, h180 = h90[:, :, 0], h180[:, :, 0]      # (n+1, 3)
n_frames = h90.shape[0]


def _sphere(ax):
    u, v = np.mgrid[0:2 * np.pi:24j, 0:np.pi:16j]
    ax.plot_wireframe(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v),
                      color="0.85", lw=0.4)
    for a in ("x", "y", "z"):
        e = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[a]
        ax.plot([0, e[0]], [0, e[1]], [0, e[2]], color="0.6", lw=0.8)
        ax.text(1.15 * e[0], 1.15 * e[1], 1.15 * e[2], a, color="0.5", fontsize=9)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.view_init(elev=18, azim=-60)


plt.rcParams.update({"font.size": 11})
fig = plt.figure(figsize=(8.0, 4.2), dpi=100)                 # 800×420 (width %4==0)
specs = [("90° excitation", h90, "#1b6ca8"), ("180° inversion", h180, "#c1440e")]
axes, paths, tips = [], [], []
for k, (title, hist, c) in enumerate(specs):
    ax = fig.add_subplot(1, 2, k + 1, projection="3d")
    _sphere(ax); ax.set_title(title, color=c)
    axes.append(ax)
    paths.append(ax.plot([], [], [], color=c, lw=1.2, alpha=0.6)[0])
    tips.append(ax.plot([], [], [], color=c, lw=3)[0])


def frame(i):
    for hist, path, tip in zip((h90, h180), paths, tips):
        P = hist[:i + 1]
        path.set_data(P[:, 0], P[:, 1]); path.set_3d_properties(P[:, 2])
        tip.set_data([0, hist[i, 0]], [0, hist[i, 1]])
        tip.set_3d_properties([0, hist[i, 2]])
    return (*paths, *tips)


anim = FuncAnimation(fig, frame, frames=range(0, n_frames, 2), interval=70, blit=False)
out = os.path.join(os.path.dirname(__file__), "rf_zoo.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("figure ->", out)
