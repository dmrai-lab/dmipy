#!/usr/bin/env python3
"""Regenerates ``mintte_vs_vanilla.gif``.

Vanilla bang-bang PGSE (symmetric) vs the optimized min-TE asymmetric design, encoding the SAME
b on real Siemens Prisma limits (cited), brain defaults (no motion nulling). Both play at the same
wall-clock speed, so the optimized design visibly echoes first. Off-regions are shaded: grey =
scanner-fixed off-time (90° / 180°+crushers / EPI readout); amber = the extra dead time the
vanilla adds purely to stay symmetric.

Needs the (private) ``dmipy-design`` package on the path:
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design python fig_mintte_vs_vanilla.py
"""
import os, dataclasses
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")   # NOW is tiny SciPy SLSQP solves — single-thread BLAS is far faster

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dmipy_design import min_te_for_b, SequenceTiming

GAMMA = 267.513e6
G_MAX, SLEW = 0.080, 200.0                        # Siemens Prisma (cited spec sheet)
rf_dead, ring = 100e-6, 60e-6                     # representative Siemens-class RF timing
TL = rf_dead + 2.56e-3 + ring                     # 90° lead-in
TRF = rf_dead + 5.12e-3 + ring + 2 * 1.5e-3       # 180° + crushers
TRO = 10e-6 + 128 * 0.53e-3 * (0.75 - 0.5) / 0.75  # single-shot EPI readout -> k-centre
t_asym = SequenceTiming(t_excite=TL, t_refocus=TRF, t_readout_pre_echo=TRO)
t_sym = dataclasses.replace(t_asym, symmetric=True)

kw = dict(G_max=G_MAX, slew_rate_max=SLEW, n_t=120, n_restarts=3, tol_te=1e-3,
          null_M1=False, null_M2=False)           # brain: no motion nulling -> bang-bang
d_o, TEo = min_te_for_b(1e9, 1.0, timing=t_asym, **kw)
d_v, TEv = min_te_for_b(1e9, 1.0, timing=t_sym, **kw)
print(f"vanilla(sym) TE={TEv*1e3:.1f}ms b={d_v.b_value:.2e} | optim(asym) TE={TEo*1e3:.1f}ms b={d_o.b_value:.2e}")

B = 1e9
def prep(d, b0):
    G = np.asarray(d.effective_G()) * np.sqrt(B / b0); g = G[:, 0]
    t = np.arange(len(g)) * d.dt
    return t, g, GAMMA * np.cumsum(g) * d.dt
tv, gv, qv = prep(d_v, d_v.b_value); to, go, qo = prep(d_o, d_o.b_value)
SNR_GAIN = float(np.exp((TEv - TEo) / 0.08))
panels = [dict(name="Vanilla bang-bang PGSE  (symmetric)", t=tv, g=gv, q=qv, TE=TEv, c="#7a8499", vanilla=True),
          dict(name="Optimized min-TE  (asymmetric windows)", t=to, g=go, q=qo, TE=TEo, c="#4af0c4", vanilla=False)]
gmax_mt = max(np.abs(gv).max(), np.abs(go).max()) * 1e3
qmax = max(np.abs(qv).max(), np.abs(qo).max())
XPOS = np.linspace(-1, 1, 11) * (2.2 * np.pi / qmax)

plt.rcParams.update({"font.family": "monospace", "text.color": "#e8edf5"})
fig = plt.figure(figsize=(8.6, 5.2), facecolor="#07090f")
gs = fig.add_gridspec(2, 2, width_ratios=[4.4, 1.0], hspace=0.42, wspace=0.18,
                      left=0.08, right=0.97, top=0.82, bottom=0.14)
T_END = TEv
arts = []
for r, p in enumerate(panels):
    axw = fig.add_subplot(gs[r, 0]); axp = fig.add_subplot(gs[r, 1])
    for ax in (axw, axp):
        ax.set_facecolor("#0d1120")
        for s in ax.spines.values():
            s.set_color("#2a3350")
    TE, echo = p["TE"], p["TE"] / 2
    for a0, a1, lab in [(0, TL, "90°"), (echo - TRF/2, echo + TRF/2, "180°"), (TE - TRO, TE, "EPI readout")]:
        axw.axvspan(a0*1e3, a1*1e3, color="#28304a", alpha=0.85, lw=0)
        axw.text((a0+a1)*500, gmax_mt*1.16, lab, color="#8a94a8", fontsize=6.5, ha="center", va="bottom")
    if p["vanilla"]:
        pre = (echo - TRF/2) - TL; post = (TE - TRO) - (echo + TRF/2); W = min(pre, post)
        ambers = ([(TL, echo - TRF/2 - W)] if pre > W + 1e-6 else []) + \
                 ([(echo + TRF/2 + W, TE - TRO)] if post > W + 1e-6 else [])
        for a0, a1 in ambers:
            axw.axvspan(a0*1e3, a1*1e3, color="#e0a44a", alpha=0.30, lw=0)
        if ambers:
            a0, a1 = ambers[0]
            axw.text((a0+a1)*500, gmax_mt*0.45, "dead time\n(symmetry)", color="#e6b45a",
                     fontsize=6.8, ha="center", va="center")
    axw.plot(p["t"]*1e3, p["g"]*1e3, color=p["c"], lw=0.8, alpha=0.28)
    reveal, = axw.plot([], [], color=p["c"], lw=1.8)
    playhead = axw.axvline(0, color="#e8edf5", lw=1.2)
    echo_txt = axw.text(p["TE"]*1e3, -gmax_mt*1.42, "", color=p["c"], fontsize=8, ha="center", va="top", fontweight="bold")
    axw.set_xlim(-1, T_END*1e3+1); axw.set_ylim(-gmax_mt*1.55, gmax_mt*1.5)
    axw.set_ylabel("G  (mT/m)", fontsize=8, color="#b8c0d0"); axw.tick_params(labelsize=7, colors="#7a8499")
    axw.set_title(p["name"], fontsize=9.5, color=p["c"], loc="left", pad=14)
    axw.tick_params(labelbottom=(r == 1))
    if r == 1:
        axw.set_xlabel("time  (ms)  —  both panels play at the same wall-clock speed", fontsize=8, color="#b8c0d0")
    axp.set_xlim(-1.25, 1.25); axp.set_ylim(-1.25, 1.25); axp.set_aspect("equal"); axp.axis("off")
    axp.add_artist(plt.Circle((0, 0), 1.0, fill=False, ec="#2a3350", lw=1.0))
    quiv = axp.quiver(np.zeros_like(XPOS), np.zeros_like(XPOS), np.ones_like(XPOS), np.zeros_like(XPOS),
                      color=p["c"], scale=1.0, scale_units="xy", angles="xy", width=0.02, alpha=0.9)
    sig_txt = axp.text(0, -1.5, "", color=p["c"], fontsize=8, ha="center", va="top")
    axp.text(0, 1.42, "spins", color="#7a8499", fontsize=7, ha="center")
    arts.append(dict(reveal=reveal, playhead=playhead, echo_txt=echo_txt, quiv=quiv, sig_txt=sig_txt, **p))

fig.text(0.5, 0.955, "Same b = 1000 s/mm²  ·  Siemens Prisma (80 mT/m, 200 T/m/s)  ·  brain (no motion nulling)",
         color="#e8edf5", fontsize=10.5, ha="center", fontweight="bold")
sub = fig.text(0.5, 0.905, "", color="#4af0c4", fontsize=9.5, ha="center")
fig.text(0.5, 0.028, "grey = scanner off-time (fixed: 90° / 180°+crushers / readout)     "
         "amber = dead time the vanilla adds for symmetry     white = usable encoding",
         color="#8a94a8", fontsize=7.4, ha="center")

NF = 150
def update(i):
    t = i / (NF - 1) * T_END; changed = [sub]; both = True
    for a in arts:
        tp = min(t, a["TE"]); k = min(int(tp / (a["t"][1] - a["t"][0])), len(a["t"]) - 1)
        a["reveal"].set_data(a["t"][:k+1]*1e3, a["g"][:k+1]*1e3); a["playhead"].set_xdata([tp*1e3, tp*1e3])
        ang = a["q"][k] * XPOS; a["quiv"].set_UVC(np.cos(ang), np.sin(ang))
        a["sig_txt"].set_text(f"echo {np.abs(np.mean(np.exp(1j*ang)))*100:3.0f}%")
        done = t >= a["TE"]; both &= done
        a["echo_txt"].set_text(f"◆ ECHO  TE={a['TE']*1e3:.0f} ms" if done else "")
        changed += [a["reveal"], a["playhead"], a["quiv"], a["sig_txt"], a["echo_txt"]]
    if TEo <= t < TEv:
        sub.set_text(f"↑ vanilla still encoding   ·   ↓ optimized already echoed  ({(TEv-TEo)*1e3:.0f} ms sooner)"); sub.set_color("#4af0c4")
    elif both:
        sub.set_text(f"optimized echoes {(TEv-TEo)*1e3:.0f} ms sooner  →  {SNR_GAIN:.2f}× SNR (less T2 decay)"); sub.set_color("#4af0c4")
    else:
        sub.set_text("encoding diffusion …"); sub.set_color("#7a8499")
    return changed

anim = FuncAnimation(fig, update, frames=list(range(NF)) + [NF-1]*18, blit=False, interval=55)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mintte_vs_vanilla.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("wrote", out)
