#!/usr/bin/env python3
"""Regenerates ``rf_pushit.png`` — the optimal-control designer on a deliberately hard spec.

Push ``design_refocusing_rf`` to a demanding target: invert across ±50 % B1⁺ AND ±500 Hz
off-resonance on a 19 µT / 5 ms budget. A plain hard 180° is hopeless there; the adiabatic HS
warm start already does well; and the GRAPE refinement squeezes out extra efficiency and
peak-B1 headroom. This is dmipy-design's own optimiser working at the edge.

    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/design:/path/sim python fig_rf_pushit.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_design import design_refocusing_rf
from dmipy_design.optimizers.rf_pulse import _inversion_mz, GAMMA

kw = dict(rf_duration=5e-3, dt=1e-4, B1_max=19e-6, b1_range=(0.5, 1.5), n_b1=9,
          off_resonance_hz=500.0, n_off_resonance=9)
hs = design_refocusing_rf(refine=False, **kw)
gr = design_refocusing_rf(refine=True, n_refine_basis=10, refine_maxiter=300, **kw)
n = hs.B1.shape[0]
A0 = np.pi / (GAMMA * n * hs.dt)
hard = np.full(n, A0, dtype=np.complex128)

b1 = np.repeat(np.linspace(0.5, 1.5, 9), 9)
dw = np.tile(np.linspace(-500, 500, 9) * 2 * np.pi, 9)
eta = lambda b: float(np.mean((1 - _inversion_mz(b, b1, dw, hs.dt)) / 2))
eta_hard, eta_hs, eta_gr = eta(hard), hs.refocusing_efficiency, gr.refocusing_efficiency

plt.rcParams.update({"font.size": 10})
fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.6), dpi=100)   # 920×360 (width %4==0)
C = {"hard": "#c1440e", "hs": "#e6ab02", "gr": "#1b6ca8"}

b1_ax = np.linspace(0.5, 1.5, 101); z = np.zeros_like(b1_ax)
axL.axvspan(0.5, 1.5, color="0.96")
axL.plot(b1_ax, _inversion_mz(hard, b1_ax, z, hs.dt), color=C["hard"], lw=2, label="hard 180°")
axL.plot(b1_ax, _inversion_mz(hs.B1, b1_ax, z, hs.dt), color=C["hs"], lw=2, label="HS warm start")
axL.plot(b1_ax, _inversion_mz(gr.B1, b1_ax, z, hs.dt), color=C["gr"], lw=2, label="HS + GRAPE")
axL.axhline(-1, color="0.6", lw=0.8, ls=":")
axL.set_xlabel(r"$B_1^+$ transmit scale"); axL.set_ylabel(r"inversion $M_z$")
axL.set_title("Invert across ±50 % B1⁺  (±500 Hz)"); axL.set_ylim(-1.05, 1.05)
axL.legend(fontsize=8, loc="lower center")

bars = axR.bar(["hard\n180°", "HS\nwarm start", "HS +\nGRAPE"], [eta_hard, eta_hs, eta_gr],
               color=[C["hard"], C["hs"], C["gr"]])
for b, v in zip(bars, [eta_hard, eta_hs, eta_gr]):
    axR.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", fontsize=10, fontweight="bold")
axR.set_ylabel(r"refocusing efficiency  $\eta$"); axR.set_ylim(0, 1.05)
axR.set_title("Ensemble η on the hard spec")
axR.text(0.5, 0.5, "GRAPE trims peak-B1\n%.1f → %.1f µT" % (hs.peak_B1 * 1e6, gr.peak_B1 * 1e6),
         transform=axR.transAxes, ha="center", fontsize=8, color=C["gr"])

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_pushit.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
