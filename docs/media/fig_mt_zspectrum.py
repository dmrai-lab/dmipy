#!/usr/bin/env python3
"""Regenerates ``mt_zspectrum.png`` — the emergent MT Z-spectrum vs the analytic oracle.

Sweeps an off-resonance CW saturation pulse across offsets on ONE myelin-like substrate and
reads the free-pool longitudinal magnetization. The narrow free-water line is spared far
off-resonance while the broad, short-T2 bound pool keeps saturating — the MT dip. The emergent
Monte-Carlo points (``dmipy_sim.emergent_z_spectrum``) sit on the analytic two-pool
Bloch--McConnell oracle (``dmipy_sim.mt.mt_z_spectrum``); no lineshape is imposed on either side.

Needs ``dmipy_sim`` on the path (GPU strongly recommended):
    LD_LIBRARY_PATH=<venv nvidia/*/lib> PYTHONPATH=<dmipy-sim worktree> \
        python docs/media/fig_mt_zspectrum.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "8")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_sim import Sphere, emergent_z_spectrum
from dmipy_sim import mt

# dmipy.org dark palette
BG, PANEL, TEXT, MUTED, TEAL, BLUE = "#0d1120", "#111827", "#e8edf5", "#7a8499", "#4af0c4", "#7b9cff"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.edgecolor": "#2a3550", "font.size": 12,
})

# well-mixed sphere, broad bound pool (T2b ~ 10 us) — same physics as the MT tests
R, D = 2e-6, 2e-9
K_F, K_R = 40.0, 80.0
T2A, T1A, T2B, T1B = 80e-3, 1.0, 1e-5, 1.0
W1_HZ, T_SAT, DT = 200.0, 0.025, 2e-5
S_OVER_V = 3.0 / R
KAPPA_MT, DWELL = mt.kappa_MT_from_forward_rate(K_F, S_OVER_V), 1.0 / K_R
F_B = mt.bound_fraction(KAPPA_MT, DWELL, S_OVER_V)

MC_OFFSETS = np.array([0., 250., 500., 1000., 2000., 4000., 8000., 12000., 16000.])
DENSE = np.linspace(0.0, 16000.0, 80)          # smooth analytic curve


def _oracle_total(offsets):
    kw = dict(w1_hz=W1_HZ, t_sat=T_SAT, T1a=T1A, T2a=T2A, T1b=T1B, T2b=T2B, k_f=K_F, k_r=K_R)
    za = np.atleast_1d(mt.mt_z_spectrum(offsets, read_pool="a", **kw))
    zb = np.atleast_1d(mt.mt_z_spectrum(offsets, read_pool="b", **kw))
    m0b = K_F / K_R
    return (za + m0b * zb) / (1.0 + m0b)


def _free_only(offsets):
    """Reference: free water with NO bound pool (k_f=0).  The narrow water line is directly
    saturated only near resonance and recovers to ~1 off-resonance -- there is no broad
    off-resonance absorber, so all the wide depression in the MT curve is the bound pool."""
    return np.atleast_1d(mt.mt_z_spectrum(offsets, w1_hz=W1_HZ, t_sat=T_SAT, T1a=T1A, T2a=T2A,
                                          T1b=T1B, T2b=T2B, k_f=0.0, k_r=K_R, read_pool="a"))


def main():
    print("running emergent Z-spectrum sweep (GPU-recommended)...")
    mc = emergent_z_spectrum(MC_OFFSETS, Sphere(radius=R), n_walkers=6000, diffusivity=D,
                             w1_hz=W1_HZ, t_sat=T_SAT, dt=DT, T2=T2A, T1=T1A,
                             kappa_MT=KAPPA_MT, dwell_time=DWELL, T2_bound=T2B, T1_bound=T1B,
                             equilibrate_binding="auto", seed=3)
    an_dense = _oracle_total(DENSE)
    ref_dense = _free_only(DENSE)                  # no-bound-pool reference (analytic)

    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    fig.subplots_adjust(left=0.11, right=0.96, top=0.87, bottom=0.14)
    # the MT effect = the gap between the two curves
    ax.fill_between(DENSE / 1e3, an_dense, ref_dense, color=TEAL, alpha=0.11, lw=0)
    ax.plot(DENSE / 1e3, ref_dense, "--", color=BLUE, lw=1.8,
            label="no bound pool (reference)")
    ax.plot(DENSE / 1e3, an_dense, "-", color=MUTED, lw=2.2,
            label="with MT — analytic oracle")
    ax.plot(MC_OFFSETS / 1e3, mc, "o", color=TEAL, ms=8, zorder=5,
            markeredgecolor=BG, markeredgewidth=0.8, label="with MT — emergent Monte-Carlo")
    ax.set_xlim(-0.4, 16.4)
    ax.set_ylim(min(mc.min(), an_dense.min()) - 0.05, 1.03)
    ax.set_xlabel("saturation offset from water  (kHz)")
    ax.set_ylabel(r"free-pool  $M_z / M_0$")
    ax.set_title("The MT Z-spectrum: the off-resonance gap is the bound pool",
                 color=TEXT, fontsize=13, pad=10)
    # reference recovers to full signal off-resonance (the anchor)
    ax.annotate("no bound pool → the narrow water line\nrecovers to full signal off-resonance",
                xy=(5.0, ref_dense[np.argmin(np.abs(DENSE - 5000))]),
                xytext=(4.6, 0.60), color=BLUE, fontsize=9, va="center",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.1))
    # the shaded gap = magnetization transfer (only the bound pool absorbs off-resonance)
    i10 = np.argmin(np.abs(DENSE - 10000))
    ax.annotate("this gap is magnetization transfer:\nonly the broad bound pool absorbs\nfar off-resonance",
                xy=(10.0, 0.5 * (an_dense[i10] + ref_dense[i10])),
                xytext=(5.0, 0.40), color=TEAL, fontsize=9,
                arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.1))
    ax.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=9.5)
    for s in ax.spines.values():
        s.set_color("#2a3550")
    ax.grid(True, color="#1c2338", lw=0.8)
    ax.set_axisbelow(True)

    out = os.path.join(os.path.dirname(__file__), "mt_zspectrum.png")
    fig.savefig(out, dpi=140)
    plt.close(fig)
    rel = np.abs(mc - _oracle_total(MC_OFFSETS))
    print(f"wrote {out}")
    print(f"  f_b={F_B:.3f}  max |emergent-oracle| = {rel.max():.4f}")


if __name__ == "__main__":
    main()
