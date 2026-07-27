#!/usr/bin/env python3
"""Regenerates ``rf_refocus.gif`` — the hard-180 vs B1-robust-180 spin echo, with context.

The pedagogy hero for the design/rf page. The figure is built to be self-explanatory:

  * header states the scenario (a 180 refocusing pulse across a real head) and the objective;
  * each spin is a DOT in the transverse (Mx,My) plane, COLOURED by the transmit strength B1+
    it feels — so the viewer sees the ensemble is "the same tissue seen under many B1+/off-res
    conditions", and which spins misbehave;
  * the bold black arrow is the VECTOR SUM = the echo the scanner actually measures;
  * an inset shows the B1(t) waveform being played, with a time cursor;
  * a bottom trace plots the measured signal over time for both pulses, so "better" is explicit.

A hard 180 is exactly π only at B1+=1; off-nominal spins under/over-flip, fail to refocus, and
fan out — their vector sum (signal) stays small. The designed pulse refocuses across the whole
ensemble, so the sum is large. Same echo time, more signal.

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
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation, PillowWriter

from dmipy_design import design_refocusing_rf
from dmipy_sim.rf import B1Pulse, bloch_simulate

DT, RF_DUR, B1_MAX = 1e-4, 6e-3, 19e-6

# ── design the robust 180; the flat hard 180 is the baseline ───────────────────
d = design_refocusing_rf(rf_duration=RF_DUR, dt=DT, B1_max=B1_MAX, sar_headroom=1.30,
                         b1_range=(0.7, 1.3), n_b1=7, off_resonance_hz=250.0,
                         n_off_resonance=7, n_basis=8, n_restarts=6, seed=0)
n_rf = d.B1.shape[0]
guard = np.zeros(n_rf)
des_env = d.to_b1pulse().b1.real
hard_env = B1Pulse.hard(180, RF_DUR, DT).b1.real
_composite = lambda env: B1Pulse.from_samples(np.concatenate([guard, env, guard]), DT)

# ── ensemble (B1+ scale × off-resonance) and the post-90 transverse state ──────
b1s = np.linspace(0.7, 1.3, 7)
dfs = np.linspace(-250.0, 250.0, 7)
B1 = np.repeat(b1s, dfs.size)
DF = np.tile(dfs, b1s.size)
E = B1.size
ang = (np.pi / 2) * B1                       # instantaneous B1-scaled 90ₓ: +z -> (0,-sin,cos)
M0 = np.stack([np.zeros(E), -np.sin(ang), np.cos(ang)])

_, _, hh = bloch_simulate(_composite(hard_env), df_hz=DF, b1_scale=B1, M0=M0, return_history=True)
_, _, hd = bloch_simulate(_composite(des_env), df_hz=DF, b1_scale=B1, M0=M0, return_history=True)
n_t = hh.shape[0]
t_ms = np.arange(n_t) * DT * 1e3

def coherence(h):     # measured signal over time = |vector sum of the ensemble| (the echo)
    return np.abs(np.mean(h[:, 0, :] + 1j * h[:, 1, :], axis=1))
coh_h, coh_d = coherence(hh), coherence(hd)
print("hard echo=%.3f   design echo=%.3f" % (coh_h[-1], coh_d[-1]))

# full-timeline B1 magnitude (µT) for the inset: zeros in the guards, shape in the middle
env_full_h = np.concatenate([guard, hard_env, guard]) * 1e6
env_full_d = np.concatenate([guard, des_env, guard]) * 1e6
env_max = max(env_full_h.max(), env_full_d.max()) * 1.15
t_env = np.arange(env_full_h.size) * DT * 1e3      # pulse has n_t-1 samples (history has n_t)

# ── figure ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({"font.size": 10})
cmap = plt.cm.viridis
norm = Normalize(0.7, 1.3)
colors = cmap(norm(B1))

fig = plt.figure(figsize=(9.0, 6.0), dpi=100)                 # 900×600 (both %4==0)
gs = gridspec.GridSpec(2, 2, height_ratios=[3.1, 1.0], hspace=0.5, wspace=0.16,
                       left=0.08, right=0.86, top=0.76, bottom=0.10)
axH = fig.add_subplot(gs[0, 0]); axD = fig.add_subplot(gs[0, 1])
axS = fig.add_subplot(gs[1, :])

fig.suptitle("A 180° refocusing pulse must flip EVERY spin by 180°. Across a head each spin (a dot)\n"
             "feels a different transmit strength B1⁺ (its colour) and off-resonance — the scanner\n"
             "measures their vector SUM (black arrow).",
             fontsize=9.5, y=0.995)
fig.text(0.5, 0.80,
         "The designed pulse maximises that summed echo over the whole ensemble.",
         ha="center", fontsize=9.5, style="italic", color="#1b6ca8")

specs = [(axH, hh, coh_h, env_full_h, "Hard 180°", "#c1440e"),
         (axD, hd, coh_d, env_full_d, "B1-robust 180° (designed)", "#1b6ca8")]
scatts, arrows, insets, cursors, sigtxt = [], [], [], [], []
for ax, hist, coh, envf, title, c in specs:
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal")
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="0.8", lw=1))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel("$M_x$"); ax.set_ylabel("$M_y$")
    ax.set_title(title, color=c, fontsize=11)
    scatts.append(ax.scatter(hist[0, 0], hist[0, 1], s=26, c=colors, edgecolors="none",
                             alpha=0.9, zorder=3))
    arrows.append(ax.annotate("", xy=(0, 0), xytext=(0, 0),
                  arrowprops=dict(arrowstyle="-|>", color="k", lw=3), zorder=4))
    sigtxt.append(ax.text(0.0, -1.07, "", ha="center", fontsize=10, color="k",
                          fontweight="bold"))
    # inset: the B1(t) waveform this panel plays, with a time cursor
    ins = ax.inset_axes([0.02, 0.79, 0.34, 0.19])
    ins.plot(t_env, envf, color=c, lw=1.3)
    ins.set_ylim(0, env_max); ins.set_xlim(t_ms[0], t_ms[-1])
    ins.set_xticks([]); ins.set_yticks([]); ins.set_facecolor("none")
    ins.set_title("B1(t) played", fontsize=7.5, color="0.35", pad=1)
    for sp in ins.spines.values():
        sp.set_color("0.8")
    cursors.append(ins.axvline(t_ms[0], color="0.35", lw=1))
    insets.append(ins)

# signal METER: two horizontal bars (current measured signal), the payoff made explicit and
# unambiguous — longer bar = more signal. Both collapse as spins dephase; at the echo the
# designed bar recovers far more. Tied to the same dots shown above.
axS.set_xlim(0, 1.0); axS.set_ylim(-0.6, 1.6)
axS.set_yticks([0, 1]); axS.set_yticklabels(["hard 180°", "designed"])
axS.set_xlabel("measured signal  =  |vector sum of all spins|  (0 = fully dephased, 1 = perfect echo)")
axS.tick_params(axis="y", length=0)
for x in (0.2, 0.4, 0.6, 0.8):
    axS.axvline(x, color="0.9", lw=0.8, zorder=0)
barH = axS.barh(0, 0, height=0.55, color="#c1440e")[0]
barD = axS.barh(1, 0, height=0.55, color="#1b6ca8")[0]
barval = [axS.text(0, 0, "", va="center", fontsize=10, fontweight="bold", color="#c1440e"),
          axS.text(0, 1, "", va="center", fontsize=10, fontweight="bold", color="#1b6ca8")]
phase_txt = axS.text(0.5, 1.45, "", ha="center", fontsize=10, color="0.25")

cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=[axH, axD],
                    fraction=0.03, pad=0.02)
cbar.set_label("local B1⁺ scale", fontsize=8.5)
cbar.set_ticks([0.7, 1.0, 1.3]); cbar.ax.set_yticklabels(["0.7×", "1.0×", "1.3×"])

def frame(i):
    for (ax, hist, coh, envf, title, c), sct, arr, cur, stx in zip(
            specs, scatts, arrows, cursors, sigtxt):
        sct.set_offsets(np.column_stack([hist[i, 0, :], hist[i, 1, :]]))
        mx, my = hist[i, 0, :].mean(), hist[i, 1, :].mean()
        arr.xy = (mx, my)
        stx.set_text("measured signal = %.2f" % np.hypot(mx, my))   # matches the arrow (dots' sum)
        cur.set_xdata([t_ms[i], t_ms[i]])
    sh, sd = np.hypot(*hh[i, :2, :].mean(axis=1)), np.hypot(*hd[i, :2, :].mean(axis=1))
    barH.set_width(sh); barD.set_width(sd)
    barval[0].set_text("  %.2f" % sh); barval[0].set_x(sh)
    barval[1].set_text("  %.2f" % sd); barval[1].set_x(sd)
    phase = ("just excited — all spins aligned" if i == 0 else
             "① dephasing (spins fan out by off-resonance)" if i < n_rf else
             "② the 180° pulse plays (flips every spin)" if i < 2 * n_rf else
             "③ rephasing → echo (aligned spins add up = signal)")
    phase_txt.set_text(phase)
    return ()

anim = FuncAnimation(fig, frame, frames=range(0, n_t, 2), interval=90, blit=False)
out = os.path.join(os.path.dirname(__file__), "rf_refocus.gif")
anim.save(out, writer=PillowWriter(fps=16))
print("figure ->", out)
