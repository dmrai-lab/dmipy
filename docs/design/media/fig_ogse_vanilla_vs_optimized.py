#!/usr/bin/env python3
"""Regenerates ``ogse_vanilla_vs_optimized.gif``.

Textbook cosine-OGSE (vanilla) vs the NOW-optimized OGSE at the same TE / hardware and a
matched RMS encoding frequency — showing that the encoding power spectra are NOT the same and
that the optimized design packs more b. Real Siemens Prisma limits (cited), brain defaults
(no motion nulling).

Needs the (private) ``dmipy-design`` package on the path:
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design python fig_ogse_vanilla_vs_optimized.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")   # NOW is tiny SciPy SLSQP solves — single-thread BLAS is far faster

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dmipy_design import design_waveform_now, SequenceTiming

GAMMA = 267.513e6
G_MAX, SLEW = 0.080, 200.0                        # Siemens Prisma (cited spec sheet)
rf_dead, ring = 100e-6, 60e-6                     # representative Siemens-class RF timing
t_lead = rf_dead + 2.56e-3 + ring
t_refocus = rf_dead + 5.12e-3 + ring + 2 * 1.5e-3
t_ro = 10e-6 + 40 * 0.30e-3                        # short readout -> long OGSE windows
timing = SequenceTiming(t_excite=t_lead, t_refocus=t_refocus, t_readout_pre_echo=t_ro, symmetric=True)
TE, n_t, F = 0.140, 220, 50.0
dt = TE / (n_t - 1)
on, echo = timing.masks(TE, n_t); on = on[:, 0] > 0.5

q_of = lambda g: GAMMA * np.cumsum(g) * dt
frms_of = lambda g: float(GAMMA * np.sqrt(np.sum(g**2) / (np.sum(q_of(g)**2) + 1e-30)) / (2 * np.pi))
b_of = lambda g: float(np.sum(q_of(g)**2) * dt)
def spec(g):
    q = q_of(g); return np.fft.rfftfreq(len(q), dt), np.abs(np.fft.rfft(q))**2

def lobes(mask):
    idx = np.where(mask)[0]; out, start = [], idx[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if b != a + 1:
            out.append((start, a)); start = b
    out.append((start, idx[-1])); return out
def cosine_ogse(freq):
    g = np.zeros(n_t)
    for a, b in lobes(on):
        n = max(1, round(freq * (b - a) * dt))
        u = (np.arange(a, b + 1) - a) / max(1, (b - a))
        g[a:b + 1] = G_MAX * np.sin(2 * np.pi * n * u)     # 0 at both ends -> refocuses per lobe
    return g

# optimized first -> realized f_rms, then match the vanilla cosine's f_rms to it
d = design_waveform_now(1.0, G_max=G_MAX, slew_rate_max=SLEW, TE=TE, n_t=n_t, timing=timing,
                        spectral_freq=F, null_M1=False, null_M2=False, n_restarts=10, seed=0)
g_opt = np.asarray(d.effective_G())[:, 0]; frms_o = frms_of(g_opt)
g_van = min((cosine_ogse(ff) for ff in np.linspace(0.6 * frms_o, 1.6 * frms_o, 40)),
            key=lambda g: abs(frms_of(g) - frms_o))
fv, Pv = spec(g_van); fo, Po = spec(g_opt)
bv, bo, rmsv = b_of(g_van), d.b_value, frms_of(g_van)
print(f"vanilla cosine-OGSE b={bv:.2e} f_rms={rmsv:.0f}Hz | optimized b={bo:.2e} f_rms={frms_o:.0f}Hz")

# ---------------- animation ----------------
gmax_mt = G_MAX * 1e3
tt = np.arange(n_t) * dt
panels = [dict(name="Vanilla cosine-OGSE", g=g_van, f_rms=rmsv, b=bv, c="#7a8499"),
          dict(name="Optimized NOW-OGSE", g=g_opt, f_rms=frms_o, b=bo, c="#4af0c4")]

plt.rcParams.update({"font.family": "monospace", "text.color": "#e8edf5"})
fig = plt.figure(figsize=(9.0, 5.0), facecolor="#07090f")
gs = fig.add_gridspec(2, 2, width_ratios=[3.1, 2.0], hspace=0.42, wspace=0.26,
                      left=0.075, right=0.965, top=0.82, bottom=0.12)
axs, playheads, reveals = [], [], []
for r, p in enumerate(panels):
    ax = fig.add_subplot(gs[r, 0]); ax.set_facecolor("#0d1120")
    for s in ax.spines.values():
        s.set_color("#2a3350")
    for a0, a1, lab in [(0, t_lead, "90°"), (TE/2 - t_refocus/2, TE/2 + t_refocus/2, "180°"),
                        (TE - t_ro, TE, "readout")]:
        ax.axvspan(a0*1e3, a1*1e3, color="#28304a", alpha=0.85, lw=0)
        ax.text((a0+a1)*500, gmax_mt*1.12, lab, color="#8a94a8", fontsize=6.3, ha="center", va="bottom")
    ax.plot(tt*1e3, p["g"]*1e3, color=p["c"], lw=0.8, alpha=0.30)
    rev, = ax.plot([], [], color=p["c"], lw=1.6); reveals.append(rev)
    playheads.append(ax.axvline(0, color="#e8edf5", lw=1.1))
    ax.set_xlim(-1, TE*1e3+1); ax.set_ylim(-gmax_mt*1.45, gmax_mt*1.45)
    ax.set_ylabel("G (mT/m)", fontsize=8, color="#b8c0d0"); ax.tick_params(labelsize=7, colors="#7a8499")
    ax.set_title(f"{p['name']}   ·   f_rms={p['f_rms']:.0f} Hz   ·   b={p['b']/1e6:.0f} s/mm²",
                 fontsize=8.8, color=p["c"], loc="left", pad=12)
    ax.tick_params(labelbottom=(r == 1))
    if r == 1:
        ax.set_xlabel("time  (ms)", fontsize=8, color="#b8c0d0")
    axs.append(ax)

# shared spectrum panel — the two are NOT the same
axS = fig.add_subplot(gs[:, 1]); axS.set_facecolor("#0d1120")
for s in axS.spines.values():
    s.set_color("#2a3350")
fmax = 160
sel = fv <= fmax
axS.fill_between(fv[sel], Pv[sel]/Pv.max(), color="#7a8499", alpha=0.30)
axS.plot(fv[sel], Pv[sel]/Pv.max(), color="#7a8499", lw=1.4, label=f"vanilla ({rmsv:.0f} Hz)")
axS.plot(fo[sel], Po[sel]/Po.max(), color="#4af0c4", lw=1.6, label=f"optimized ({frms_o:.0f} Hz)")
axS.axvline(rmsv, color="#7a8499", ls=":", lw=1.0); axS.axvline(frms_o, color="#4af0c4", ls=":", lw=1.0)
axS.set_xlim(0, fmax); axS.set_ylim(0, 1.12)
axS.set_xlabel("encoding frequency  (Hz)", fontsize=8, color="#b8c0d0")
axS.set_title("encoding power spectrum  |q̃(f)|²", fontsize=9, color="#e8edf5", loc="left", pad=6)
axS.tick_params(labelsize=7, colors="#7a8499"); axS.set_yticks([])
axS.legend(fontsize=7.5, facecolor="#0d1120", edgecolor="#2a3350", labelcolor="#e8edf5", loc="upper right")

fig.text(0.5, 0.945, "OGSE  ·  same TE = 140 ms, same hardware (Prisma)  ·  the spectra are NOT the same",
         color="#e8edf5", fontsize=10.5, ha="center", fontweight="bold")
fig.text(0.5, 0.895, "same b-tensor, different temporal/spectral content — what OGSE actually probes",
         color="#8a94a8", fontsize=8.5, ha="center")

NF = 130
def update(i):
    t = i / (NF - 1) * TE
    k = min(int(t/dt), n_t-1)
    ch = []
    for p, rev, ph in zip(panels, reveals, playheads):
        rev.set_data(tt[:k+1]*1e3, p["g"][:k+1]*1e3); ph.set_xdata([t*1e3, t*1e3])
        ch += [rev, ph]
    return ch

anim = FuncAnimation(fig, update, frames=list(range(NF)) + [NF-1]*16, blit=False, interval=55)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ogse_vanilla_vs_optimized.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("wrote", out)
