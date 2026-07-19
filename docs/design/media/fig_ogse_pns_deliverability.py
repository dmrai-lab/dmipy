#!/usr/bin/env python3
"""Regenerates ``ogse_pns_deliverability.gif``.

Deliverability, not spectrum: the same 60 Hz OGSE on real Siemens Prisma limits (cited), designed
two ways. A max-b design rides the slew limit at every edge and peaks at 123% of the peripheral
nerve stimulation (PNS) limit (SAFE model) — the scanner rejects it. Turning the PNS constraint on
holds it at 80% for only ~4% less b — deliverable. Shows why PNS is a hard constraint, not an
afterthought.

Needs the (private) ``dmipy-design`` package on the path:
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design python fig_ogse_pns_deliverability.py
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
from dmipy_design.optimizers.now import _pns_pct, _safe_kernels

G_MAX, SLEW = 0.080, 200.0                        # Siemens Prisma (cited spec sheet)
rf_dead, ring = 100e-6, 60e-6
TL = rf_dead + 2.56e-3 + ring
TRF = rf_dead + 5.12e-3 + ring + 2 * 1.5e-3
TRO = 8e-3
timing = SequenceTiming(t_excite=TL, t_refocus=TRF, t_readout_pre_echo=TRO)
TE, n_t, F = 0.180, 320, 60.0

def build(pns):
    d = design_waveform_now(1.0, G_max=G_MAX, slew_rate_max=SLEW, TE=TE, n_t=n_t, timing=timing,
                            spectral_freq=F, null_M1=False, null_M2=False,
                            pns=pns, pns_target=80.0, n_restarts=8 if pns else 6, seed=0)
    g = np.asarray(d.effective_G()); dt = d.dt
    G3 = np.zeros((g.shape[0], 3)); G3[:, :g.shape[1]] = g
    pns_tr = _pns_pct(G3, dt, _safe_kernels(dt * 1e3, g.shape[0] - 1))     # (n_t-1,) %
    return dict(g=g[:, 0], dt=dt, t=np.arange(g.shape[0]) * dt,
                tp=(np.arange(len(pns_tr)) + 0.5) * dt, pns=pns_tr, b=d.b_value, pk=float(pns_tr.max()))

d0 = build(False)   # max-b, PNS ignored
d1 = build(True)    # PNS-constrained
print(f"max-b: b={d0['b']/1e6:.0f} PNS={d0['pk']:.0f}% | constrained: b={d1['b']/1e6:.0f} PNS={d1['pk']:.0f}%")

gmax_mt = G_MAX * 1e3
panels = [dict(name="Max-b OGSE  (PNS ignored)", d=d0, c="#f0787a",
               verdict=f"✗ PNS peaks {d0['pk']:.0f}% — scanner rejects it"),
          dict(name="PNS-constrained OGSE", d=d1, c="#4af0c4",
               verdict=f"✓ PNS {d1['pk']:.0f}% — deliverable")]

plt.rcParams.update({"font.family": "monospace", "text.color": "#e8edf5"})
fig = plt.figure(figsize=(9.0, 5.0), facecolor="#07090f")   # 900 px wide (÷4)
gs = fig.add_gridspec(2, 1, hspace=0.5, left=0.085, right=0.90, top=0.80, bottom=0.12)
arts = []
for r, p in enumerate(panels):
    d = p["d"]
    axg = fig.add_subplot(gs[r, 0]); axg.set_facecolor("#0d1120")
    for s in axg.spines.values():
        s.set_color("#2a3350")
    for a0, a1 in [(0, TL), (TE/2 - TRF/2, TE/2 + TRF/2), (TE - TRO, TE)]:
        axg.axvspan(a0*1e3, a1*1e3, color="#28304a", alpha=0.85, lw=0)
    axg.plot(d["t"]*1e3, d["g"]*1e3, color="#5a637a", lw=0.8, alpha=0.55)      # gradient (context)
    axg.set_xlim(-1, TE*1e3+1); axg.set_ylim(-gmax_mt*1.25, gmax_mt*1.25)
    axg.set_ylabel("G (mT/m)", fontsize=7.5, color="#6b7488"); axg.tick_params(labelsize=6.5, colors="#6b7488")
    axg.tick_params(labelbottom=(r == 1))
    if r == 1:
        axg.set_xlabel("time  (ms)  —  both play at the same wall-clock speed", fontsize=8, color="#b8c0d0")
    axp = axg.twinx(); axp.set_ylim(0, 145)
    for s in axp.spines.values():
        s.set_color("#2a3350")
    axp.axhline(100, color="#f0787a", ls="--", lw=1.1)                        # PNS limit
    axp.text(TE*1e3, 103, "PNS limit (100%)", color="#f0787a", fontsize=6.5, ha="right", va="bottom")
    over = axp.fill_between([], [], color="#f0787a", alpha=0.25)               # placeholder
    pns_line, = axp.plot([], [], color=p["c"], lw=1.9)
    axp.set_ylabel("PNS  (% of limit)", fontsize=8, color=p["c"]); axp.tick_params(labelsize=7, colors="#8a94a8")
    playhead = axg.axvline(0, color="#e8edf5", lw=1.0)
    axg.set_title(f"{p['name']}   ·   b={d['b']/1e6:.0f} s/mm²", fontsize=9, color=p["c"], loc="left", pad=3)
    verdict_txt = axp.text(TE*500, 128, "", color=p["c"], fontsize=9, ha="center", va="center", fontweight="bold")
    arts.append(dict(pns_line=pns_line, playhead=playhead, verdict_txt=verdict_txt, axp=axp, **p))

fig.text(0.5, 0.94, "Peripheral nerve stimulation — why a max-b OGSE isn't always runnable",
         color="#e8edf5", fontsize=11, ha="center", fontweight="bold")
fig.text(0.5, 0.89, "same 60 Hz OGSE on a Siemens Prisma (SAFE model) — respecting PNS costs only ~4% of b",
         color="#8a94a8", fontsize=8.3, ha="center")

NF = 130
def update(i):
    t = i / (NF - 1) * TE; ch = []
    for a in arts:
        d = a["d"]; k = min(int(t / d["dt"]), len(d["tp"]) - 1)
        a["pns_line"].set_data(d["tp"][:k+1]*1e3, d["pns"][:k+1])
        a["playhead"].set_xdata([t*1e3, t*1e3])
        for coll in list(a["axp"].collections):
            coll.remove()
        seg = d["pns"][:k+1]
        a["axp"].fill_between(d["tp"][:k+1]*1e3, 100, np.maximum(seg, 100), where=seg > 100,
                              color="#f0787a", alpha=0.30)
        a["verdict_txt"].set_text(a["verdict"] if t >= TE - 1e-9 else "")
        ch += [a["pns_line"], a["playhead"], a["verdict_txt"]]
    return ch

anim = FuncAnimation(fig, update, frames=list(range(NF)) + [NF-1]*20, blit=False, interval=55)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ogse_pns_deliverability.gif")
anim.save(out, writer=PillowWriter(fps=18))
print("wrote", out)
