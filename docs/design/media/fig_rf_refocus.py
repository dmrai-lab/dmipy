#!/usr/bin/env python3
"""Regenerates ``rf_refocus.gif`` — the hard-180 vs B1-robust-180 spin echo.

The pedagogy hero for the design/rf page. After a 90 excitation the transverse spins of a
(B1+ transmit scale × off-resonance) ensemble fan out (dephase); a 180 conjugates their phase;
symmetric free precession then refocuses them into an echo. A *hard* 180 is exactly π only at
the nominal operating point, so off-nominal isochromats refocus incompletely and the echo
(the ensemble-mean transverse magnetisation, the measured signal) is small. The B1-robust 180
designed by ``dmipy_design.design_refocusing_rf`` refocuses across the whole ensemble, so a
much larger echo forms — same echo time, more signal.

The designed pulse is bridged into dmipy-sim as a ``B1Pulse`` (``to_b1pulse``) and run through
the SAME ``dmipy_sim.rf.bloch_simulate`` forward as the hard pulse — design proposes, sim scores.

Needs the working-tree dmipy-design + dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/design:/path/sim \
        python fig_rf_refocus.py
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

from dmipy_design import design_refocusing_rf
from dmipy_sim.rf import B1Pulse, bloch_simulate
from dmipy_sim.constants import GAMMA

DT = 1e-4
RF_DUR = 6e-3
B1_MAX = 19e-6                                  # GE SIGNA Premier body coil ≈ 19 µT

# ── design the robust 180 (and take the flat hard 180 as the baseline) ─────────
d = design_refocusing_rf(rf_duration=RF_DUR, dt=DT, B1_max=B1_MAX, sar_headroom=1.30,
                         b1_range=(0.7, 1.3), n_b1=7, off_resonance_hz=250.0,
                         n_off_resonance=7, n_basis=8, n_restarts=6, seed=0)
n_rf = d.B1.shape[0]
guard = np.zeros(n_rf)                          # symmetric free-precession each side

des_env = d.to_b1pulse().b1.real                # designed envelope (T), via the sim bridge
hard_env = B1Pulse.hard(180, RF_DUR, DT).b1.real    # flat hard 180 over the same window

def _composite(env):
    return B1Pulse.from_samples(np.concatenate([guard, env, guard]), DT)

pulse_hard, pulse_des = _composite(hard_env), _composite(des_env)

# ── ensemble (B1+ scale × off-resonance) and the post-90 transverse state ──────
b1s = np.linspace(0.7, 1.3, 7)
dfs = np.linspace(-250.0, 250.0, 7)
B1 = np.repeat(b1s, dfs.size)
DF = np.tile(dfs, b1s.size)
E = B1.size
# instantaneous B1-scaled 90ₓ: +z -> (0, -sin, cos); keeps the echo symmetric about the 180
ang = (np.pi / 2) * B1
M0 = np.stack([np.zeros(E), -np.sin(ang), np.cos(ang)])

_, _, hist_hard = bloch_simulate(pulse_hard, df_hz=DF, b1_scale=B1, M0=M0, return_history=True)
_, _, hist_des = bloch_simulate(pulse_des, df_hz=DF, b1_scale=B1, M0=M0, return_history=True)
n_frames = hist_hard.shape[0]

def echo_frac(hist):
    Mxy = hist[:, 0, :] + 1j * hist[:, 1, :]
    return np.abs(np.mean(Mxy, axis=1))          # coherence over time

coh_hard, coh_des = echo_frac(hist_hard), echo_frac(hist_des)
print("hard   refocused fraction (echo): %.3f" % coh_hard[-1])
print("design refocused fraction (echo): %.3f" % coh_des[-1])

# ── animation: transverse fan + mean (signal) vector, hard vs designed ─────────
plt.rcParams.update({"font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.2), dpi=100)   # 800×420 px (width %4==0)
titles = ("Hard 180°", "B1-robust 180° (designed)")
cols = ("#c1440e", "#1b6ca8")
scts, means, txts = [], [], []
for ax, title, c in zip(axes, titles, cols):
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal")
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.8", lw=1))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("$M_x$"); ax.set_ylabel("$M_y$")
    ax.set_title(title, color=c)
    scts.append(ax.scatter([], [], s=14, color=c, alpha=0.55))
    means.append(ax.annotate("", xy=(0, 0), xytext=(0, 0),
                 arrowprops=dict(arrowstyle="-|>", color=c, lw=2.4)))
    txts.append(ax.text(-1.08, 1.0, "", fontsize=10, color=c))
sup = fig.suptitle("", fontsize=11)

def frame(i):
    for hist, coh, sct, mean, txt in zip((hist_hard, hist_des), (coh_hard, coh_des),
                                         scts, means, txts):
        mx, my = hist[i, 0, :], hist[i, 1, :]
        sct.set_offsets(np.column_stack([mx, my]))
        mean.xy = (mx.mean(), my.mean())
        txt.set_text("signal = %.2f" % coh[i])
    phase = ("① dephasing" if i < n_rf else
             "② 180° refocusing" if i < 2 * n_rf else
             "③ rephasing → echo")
    sup.set_text("Spin echo across a ±30%% B1⁺ × ±250 Hz ensemble    —    %s" % phase)
    return (*scts, *means, *txts, sup)

anim = FuncAnimation(fig, frame, frames=range(0, n_frames, 2), interval=60, blit=False)
out = os.path.join(os.path.dirname(__file__), "rf_refocus.gif")
anim.save(out, writer=PillowWriter(fps=20))
print("figure ->", out)
