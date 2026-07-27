#!/usr/bin/env python3
"""Regenerates ``rf_profile.png`` — why the robust 180 wins, in one static figure.

Three panels:
  (left, centre)  the refocusing map — each isochromat's echo projected onto the ensemble
                  refocus axis (+y), over the (off-resonance × B1+ transmit scale) plane, for
                  the hard and the designed 180.  Red = refocuses (adds to the echo), blue =
                  anti-phase (subtracts).  The hard pulse concentrates its refocusing at the
                  nominal point (B1+=1, on-resonance) and loses it off there; the designed pulse
                  spreads red across the ±30% / ±250 Hz design box (dashed), which is what lifts
                  the ensemble refocused fraction.  (The vertical banding is the real
                  finite-bandwidth phase structure of a 6 ms pulse.)
  (right)         the B1 envelopes: flat hard 180 vs the band-limited designed envelope, with
                  peak-B1 and SAR annotated — both inside the deliverability box.

Needs the working-tree dmipy-design + dmipy-sim on the path:
    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/design:/path/sim python fig_rf_profile.py
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
from dmipy_sim.rf import B1Pulse, bloch_simulate

DT, RF_DUR, B1_MAX = 1e-4, 6e-3, 19e-6
HARD, DES = "#c1440e", "#1b6ca8"

d = design_refocusing_rf(rf_duration=RF_DUR, dt=DT, B1_max=B1_MAX, sar_headroom=1.30,
                         b1_range=(0.7, 1.3), n_b1=7, off_resonance_hz=250.0,
                         n_off_resonance=7, n_basis=8, n_restarts=6, seed=0)
n_rf = d.B1.shape[0]
guard = np.zeros(n_rf)
des_env = d.to_b1pulse().b1.real
hard_env = B1Pulse.hard(180, RF_DUR, DT).b1.real


def _refoc_map(env, b1_ax, df_ax):
    """Echo projected onto the +y refocus axis (M_y) over the (df × b1) grid.
    A 90ₓ tips +z→−y and a perfect spin echo returns every isochromat to +y, so M_y is the
    signed contribution to the coherent echo; its mean over the box is the refocused fraction."""
    B1, DF = np.meshgrid(b1_ax, df_ax, indexing="ij")
    B1f, DFf = B1.ravel(), DF.ravel()
    ang = (np.pi / 2) * B1f
    M0 = np.stack([np.zeros(B1f.size), -np.sin(ang), np.cos(ang)])
    pulse = B1Pulse.from_samples(np.concatenate([guard, env, guard]), DT)
    Mxy, _ = bloch_simulate(pulse, df_hz=DFf, b1_scale=B1f, M0=M0)
    return Mxy.imag.reshape(B1.shape)


b1_ax = np.linspace(0.6, 1.4, 81)
df_ax = np.linspace(-300, 300, 81)
map_hard = _refoc_map(hard_env, b1_ax, df_ax)
map_des = _refoc_map(des_env, b1_ax, df_ax)

plt.rcParams.update({"font.size": 10})
fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.4), dpi=100)   # 1080×340 (width %4==0)
ext = [df_ax[0], df_ax[-1], b1_ax[0], b1_ax[-1]]
for ax, M, title, frac in ((axes[0], map_hard, "Hard 180°", d.refocused_fraction_hard),
                           (axes[1], map_des, "B1-robust 180° (designed)", d.refocused_fraction)):
    im = ax.imshow(M, origin="lower", extent=ext, aspect="auto", vmin=-1, vmax=1, cmap="RdBu_r")
    ax.add_patch(plt.Rectangle((-250, 0.7), 500, 0.6, fill=False, ec="k", lw=1.1, ls="--"))
    ax.set_xlabel("off-resonance (Hz)")
    ax.set_title("%s  —  refocused %.2f" % (title, frac))
axes[0].set_ylabel("B1$^+$ transmit scale")
cb = fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
cb.set_label("echo on refocus axis (M$_y$)")

t = d.times() * 1e3
axes[2].plot(t, hard_env * 1e6, color=HARD, lw=1.8, label="hard 180°")
axes[2].plot(t, des_env * 1e6, color=DES, lw=1.8, label="designed")
axes[2].axhline(B1_MAX * 1e6, color="0.4", ls="--", lw=1)
axes[2].text(t[0], B1_MAX * 1e6 * 1.02, "peak-B1 limit", fontsize=8, color="0.4")
axes[2].set_xlabel("time (ms)"); axes[2].set_ylabel("B1 (µT)"); axes[2].set_title("Envelope")
axes[2].set_ylim(-1, 21); axes[2].legend(fontsize=8, loc="upper right")
axes[2].text(0.03, 0.06, "peak %.1f µT   SAR %.2f× hard" % (d.peak_B1 * 1e6, d.sar_ratio),
             transform=axes[2].transAxes, fontsize=8, color=DES)

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_profile.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
