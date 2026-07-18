#!/usr/bin/env python3
"""Regenerates ``ogse_vanilla_vs_optimized.gif``.

OGSE version of the min-TE / asymmetric-window story: a vanilla **symmetric** OGSE vs the
**asymmetric-window** optimized OGSE, both proper trapezoidal OGSE at the SAME b and the SAME
RMS encoding frequency on real Siemens Prisma limits (cited), brain defaults (no motion nulling).
Both play at the same wall-clock speed, so the asymmetric design echoes first; their encoding
power spectra |q~(f)|^2 are shown side by side (the asymmetric one packs more oscillation periods
into the long pre-180 window, so it is the cleaner, shorter-TE OGSE).

Needs the (private) ``dmipy-design`` package on the path:
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design python fig_ogse_vanilla_vs_optimized.py
"""
import os, dataclasses
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dmipy_design import min_te_for_b, SequenceTiming

GAMMA = 267.513e6
G_MAX, SLEW = 0.080, 200.0                        # Siemens Prisma (cited spec sheet)
rf_dead, ring = 100e-6, 60e-6
TL = rf_dead + 2.56e-3 + ring
TRF = rf_dead + 5.12e-3 + ring + 2 * 1.5e-3
TRO = 10e-6 + 128 * 0.53e-3 * (0.75 - 0.5) / 0.75
t_asym = SequenceTiming(t_excite=TL, t_refocus=TRF, t_readout_pre_echo=TRO)
t_sym = dataclasses.replace(t_asym, symmetric=True)
B, F = 3e8, 40.0                                   # 300 s/mm², 40 Hz OGSE

kw = dict(G_max=G_MAX, slew_rate_max=SLEW, n_t=130, n_restarts=4, tol_te=1.5e-3,
          null_M1=False, null_M2=False, spectral_freq=F)
d_o, TEo = min_te_for_b(B, 1.0, timing=t_asym, **kw)
d_v, TEv = min_te_for_b(B, 1.0, timing=t_sym, **kw)
print(f"vanilla(sym) TE={TEv*1e3:.1f}ms | optim(asym) TE={TEo*1e3:.1f}ms | saved {(TEv-TEo)*1e3:.1f}ms")

def series(d):
    g = np.asarray(d.effective_G())[:, 0]; t = np.arange(len(g)) * d.dt
    q = GAMMA * np.cumsum(g) * d.dt
    f, P = np.fft.rfftfreq(len(q), d.dt), np.abs(np.fft.rfft(q)) ** 2
    frms = float(GAMMA * np.sqrt(np.sum(g ** 2) / (np.sum(q ** 2) + 1e-30)) / (2 * np.pi))
    return dict(t=t, g=g, q=q, f=f, P=P, frms=frms, TE=len(g) * d.dt - d.dt)
V, O = series(d_v), series(d_o)
V["TE"], O["TE"] = TEv, TEo
SNR_GAIN = float(np.exp((TEv - TEo) / 0.08))
gmax_mt = G_MAX * 1e3
panels = [dict(name="Vanilla OGSE  (symmetric)", S=V, TE=TEv, c="#7a8499", vanilla=True),
          dict(name="Optimized OGSE  (asymmetric windows)", S=O, TE=TEo, c="#4af0c4", vanilla=False)]

plt.rcParams.update({"font.family": "monospace", "text.color": "#e8edf5"})
fig = plt.figure(figsize=(9.0, 5.2), facecolor="#07090f")   # 900 px wide (÷4) — avoids row-stride shear
gs = fig.add_gridspec(2, 2, width_ratios=[3.5, 1.9], hspace=0.42, wspace=0.26,
                      left=0.075, right=0.965, top=0.80, bottom=0.14)
T_END = TEv
arts = []
for r, p in enumerate(panels):
    axw = fig.add_subplot(gs[r, 0]); axw.set_facecolor("#0d1120")
    for s in axw.spines.values():
        s.set_color("#2a3350")
    TE, echo = p["TE"], p["TE"] / 2
    for a0, a1, lab in [(0, TL, "90°"), (echo - TRF/2, echo + TRF/2, "180°"), (TE - TRO, TE, "EPI readout")]:
        axw.axvspan(a0*1e3, a1*1e3, color="#28304a", alpha=0.85, lw=0)
        axw.text((a0+a1)*500, gmax_mt*1.16, lab, color="#8a94a8", fontsize=6.3, ha="center", va="bottom")
    if p["vanilla"]:
        pre = (echo - TRF/2) - TL; post = (TE - TRO) - (echo + TRF/2); W = min(pre, post)
        ambers = ([(TL, echo - TRF/2 - W)] if pre > W + 1e-6 else []) + \
                 ([(echo + TRF/2 + W, TE - TRO)] if post > W + 1e-6 else [])
        for a0, a1 in ambers:
            axw.axvspan(a0*1e3, a1*1e3, color="#e0a44a", alpha=0.30, lw=0)
        if ambers:
            a0, a1 = ambers[0]
            axw.text((a0+a1)*500, gmax_mt*0.5, "dead time\n(symmetry)", color="#e6b45a",
                     fontsize=6.6, ha="center", va="center")
    axw.plot(p["S"]["t"]*1e3, p["S"]["g"]*1e3, color=p["c"], lw=0.8, alpha=0.28)
    reveal, = axw.plot([], [], color=p["c"], lw=1.5)
    playhead = axw.axvline(0, color="#e8edf5", lw=1.1)
    echo_txt = axw.text(TE*1e3, -gmax_mt*1.42, "", color=p["c"], fontsize=8, ha="center", va="top", fontweight="bold")
    axw.set_xlim(-1, T_END*1e3+1); axw.set_ylim(-gmax_mt*1.55, gmax_mt*1.5)
    axw.set_ylabel("G (mT/m)", fontsize=8, color="#b8c0d0"); axw.tick_params(labelsize=7, colors="#7a8499")
    axw.set_title(f"{p['name']}   ·   f_rms={p['S']['frms']:.0f} Hz   ·   TE={TE*1e3:.0f} ms",
                  fontsize=8.8, color=p["c"], loc="left", pad=13)
    axw.tick_params(labelbottom=(r == 1))
    if r == 1:
        axw.set_xlabel("time  (ms)  —  both panels play at the same wall-clock speed", fontsize=8, color="#b8c0d0")
    arts.append(dict(reveal=reveal, playhead=playhead, echo_txt=echo_txt, **p))

# shared spectrum panel
axS = fig.add_subplot(gs[:, 1]); axS.set_facecolor("#0d1120")
for s in axS.spines.values():
    s.set_color("#2a3350")
fmax = 130; sel = V["f"] <= fmax
# normalise to the peak in the OSCILLATORY band (f>15 Hz) — the DC/envelope bin is common
# to both (bulk diffusion weighting) and would otherwise dwarf the OGSE peak.
osc = (V["f"] > 15) & (V["f"] <= fmax)
nv, no = V["P"][osc].max(), O["P"][osc].max()
axS.fill_between(V["f"][sel], np.minimum(V["P"][sel]/nv, 1.1), color="#7a8499", alpha=0.30)
axS.plot(V["f"][sel], np.minimum(V["P"][sel]/nv, 1.1), color="#7a8499", lw=1.4, label=f"vanilla ({V['frms']:.0f} Hz)")
axS.plot(O["f"][sel], np.minimum(O["P"][sel]/no, 1.1), color="#4af0c4", lw=1.6, label=f"optimized ({O['frms']:.0f} Hz)")
axS.axvline(V["frms"], color="#7a8499", ls=":", lw=1.0); axS.axvline(O["frms"], color="#4af0c4", ls=":", lw=1.0)
axS.set_xlim(0, fmax); axS.set_ylim(0, 1.12); axS.set_yticks([])
axS.set_xlabel("encoding frequency  (Hz)", fontsize=8, color="#b8c0d0")
axS.set_title("encoding power spectrum  |q̃(f)|²", fontsize=9, color="#e8edf5", loc="left", pad=6)
axS.tick_params(labelsize=7, colors="#7a8499")
axS.legend(fontsize=7.5, facecolor="#0d1120", edgecolor="#2a3350", labelcolor="#e8edf5", loc="upper right")

fig.text(0.5, 0.945, "OGSE  ·  same b = 300 s/mm², same 40 Hz encoding  ·  Siemens Prisma (brain)",
         color="#e8edf5", fontsize=10.5, ha="center", fontweight="bold")
sub = fig.text(0.5, 0.895, "", color="#4af0c4", fontsize=9.5, ha="center")
fig.text(0.5, 0.028, "grey = scanner off-time (fixed)     amber = dead time the vanilla adds for symmetry     "
         "white = usable encoding", color="#8a94a8", fontsize=7.4, ha="center")

NF = 150
def update(i):
    t = i / (NF - 1) * T_END; changed = [sub]; both = True
    for a in arts:
        S = a["S"]; tp = min(t, a["TE"]); k = min(int(tp / (S["t"][1] - S["t"][0])), len(S["t"]) - 1)
        a["reveal"].set_data(S["t"][:k+1]*1e3, S["g"][:k+1]*1e3); a["playhead"].set_xdata([tp*1e3, tp*1e3])
        done = t >= a["TE"]; both &= done
        a["echo_txt"].set_text(f"◆ ECHO  TE={a['TE']*1e3:.0f} ms" if done else "")
        changed += [a["reveal"], a["playhead"], a["echo_txt"]]
    if TEo <= t < TEv:
        sub.set_text(f"↑ vanilla still encoding   ·   ↓ optimized already echoed  ({(TEv-TEo)*1e3:.0f} ms sooner)"); sub.set_color("#4af0c4")
    elif both:
        sub.set_text(f"same b & frequency — optimized echoes {(TEv-TEo)*1e3:.0f} ms sooner  →  {SNR_GAIN:.2f}× SNR"); sub.set_color("#4af0c4")
    else:
        sub.set_text("encoding diffusion (OGSE) …"); sub.set_color("#7a8499")
    return changed

anim = FuncAnimation(fig, update, frames=list(range(NF)) + [NF-1]*18, blit=False, interval=55)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ogse_vanilla_vs_optimized.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("wrote", out)
