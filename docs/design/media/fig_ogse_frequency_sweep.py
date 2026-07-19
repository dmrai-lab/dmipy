#!/usr/bin/env python3
"""Regenerates ``ogse_frequency_sweep.gif``.

OGSE spectral-targeting sweep: deliverable OGSE designed at three encoding frequencies
(30 / 60 / 90 Hz) on real Siemens Prisma limits (cited), brain defaults (no motion nulling),
with a short readout + long TE so each waveform holds many oscillation periods. The encoding
power spectra |q~(f)|^2 are sharp, well-separated peaks at the target frequencies — and the
b-value (SNR) drops steeply with frequency, the OGSE cost.

Needs the (private) ``dmipy-design`` package on the path:
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design python fig_ogse_vanilla_vs_optimized.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dmipy_design import design_waveform_now, SequenceTiming

GAMMA = 267.513e6
G_MAX, SLEW = 0.080, 200.0                        # Siemens Prisma (cited spec sheet)
rf_dead, ring = 100e-6, 60e-6
TL = rf_dead + 2.56e-3 + ring
TRF = rf_dead + 5.12e-3 + ring + 2 * 1.5e-3
TRO = 8e-3                                         # short readout -> long OGSE windows (many periods)
timing = SequenceTiming(t_excite=TL, t_refocus=TRF, t_readout_pre_echo=TRO)
TE, n_t = 0.180, 320
FREQS = [(30, "#7b9cff"), (60, "#4af0c4"), (90, "#f08fb0")]

def design(F):
    d = design_waveform_now(1.0, G_max=G_MAX, slew_rate_max=SLEW, TE=TE, n_t=n_t, timing=timing,
                            spectral_freq=F, null_M1=False, null_M2=False, n_restarts=6, seed=0)
    g = np.asarray(d.effective_G())[:, 0]; dt = d.dt
    q = GAMMA * np.cumsum(g) * dt
    fq, P = np.fft.rfftfreq(len(q), dt), np.abs(np.fft.rfft(q)) ** 2
    frms = float(GAMMA * np.sqrt(np.sum(g ** 2) / (np.sum(q ** 2) + 1e-30)) / (2 * np.pi))
    return dict(g=g, dt=dt, t=np.arange(len(g)) * dt, fq=fq, P=P, frms=frms, b=d.b_value)

designs = [(F, c, design(F)) for F, c in FREQS]
for F, _, d in designs:
    print(f"OGSE {F:3d} Hz -> f_rms={d['frms']:.0f} Hz  b={d['b']/1e6:.0f} s/mm²")

gmax_mt = G_MAX * 1e3
plt.rcParams.update({"font.family": "monospace", "text.color": "#e8edf5"})
fig = plt.figure(figsize=(9.0, 5.4), facecolor="#07090f")   # 900 px wide (÷4)
gs = fig.add_gridspec(3, 2, width_ratios=[3.2, 2.2], hspace=0.5, wspace=0.24,
                      left=0.08, right=0.965, top=0.80, bottom=0.11)
reveals, playheads = [], []
for r, (F, c, d) in enumerate(designs):
    ax = fig.add_subplot(gs[r, 0]); ax.set_facecolor("#0d1120")
    for s in ax.spines.values():
        s.set_color("#2a3350")
    for a0, a1 in [(0, TL), (TE/2 - TRF/2, TE/2 + TRF/2), (TE - TRO, TE)]:
        ax.axvspan(a0*1e3, a1*1e3, color="#28304a", alpha=0.85, lw=0)
    ax.plot(d["t"]*1e3, d["g"]*1e3, color=c, lw=0.7, alpha=0.30)
    rev, = ax.plot([], [], color=c, lw=1.3); reveals.append(rev)
    playheads.append(ax.axvline(0, color="#e8edf5", lw=1.0))
    ax.set_xlim(-1, TE*1e3+1); ax.set_ylim(-gmax_mt*1.35, gmax_mt*1.35)
    ax.set_ylabel("G (mT/m)", fontsize=7.5, color="#b8c0d0"); ax.tick_params(labelsize=6.5, colors="#7a8499")
    ax.set_title(f"OGSE @ {F} Hz   ·   f_rms={d['frms']:.0f} Hz   ·   b={d['b']/1e6:.0f} s/mm²",
                 fontsize=8.5, color=c, loc="left", pad=3)
    ax.tick_params(labelbottom=(r == 2))
    if r == 2:
        ax.set_xlabel("time  (ms)", fontsize=8, color="#b8c0d0")

axS = fig.add_subplot(gs[:, 1]); axS.set_facecolor("#0d1120")
for s in axS.spines.values():
    s.set_color("#2a3350")
fmax = 130
for F, c, d in designs:
    sel = d["fq"] <= fmax
    osc = (d["fq"] > 12) & (d["fq"] <= fmax)
    P = np.minimum(d["P"] / d["P"][osc].max(), 1.08)
    axS.fill_between(d["fq"][sel], P[sel], color=c, alpha=0.18)
    axS.plot(d["fq"][sel], P[sel], color=c, lw=1.7, label=f"{F} Hz")
    axS.axvline(d["frms"], color=c, ls=":", lw=0.9, alpha=0.7)
axS.set_xlim(0, fmax); axS.set_ylim(0, 1.15); axS.set_yticks([])
axS.set_xlabel("encoding frequency  (Hz)", fontsize=8.5, color="#b8c0d0")
axS.set_title("encoding power spectrum  |q̃(f)|²", fontsize=9.5, color="#e8edf5", loc="left", pad=8)
axS.tick_params(labelsize=7.5, colors="#7a8499")
axS.legend(fontsize=8, facecolor="#0d1120", edgecolor="#2a3350", labelcolor="#e8edf5",
           loc="upper right", title="target", title_fontsize=7.5)

fig.text(0.5, 0.945, "OGSE  ·  placing diffusion sensitivity at a chosen frequency band",
         color="#e8edf5", fontsize=11, ha="center", fontweight="bold")
fig.text(0.5, 0.895, "deliverable on a Siemens Prisma (brain) — sharp, separated peaks; b (SNR) falls steeply with frequency",
         color="#8a94a8", fontsize=8.3, ha="center")

NF = 130
def update(i):
    t = i / (NF - 1) * TE; ch = []
    for (F, c, d), rev, ph in zip(designs, reveals, playheads):
        k = min(int(t / d["dt"]), len(d["t"]) - 1)
        rev.set_data(d["t"][:k+1]*1e3, d["g"][:k+1]*1e3); ph.set_xdata([t*1e3, t*1e3])
        ch += [rev, ph]
    return ch

anim = FuncAnimation(fig, update, frames=list(range(NF)) + [NF-1]*16, blit=False, interval=55)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ogse_frequency_sweep.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("wrote", out)
