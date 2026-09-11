"""Draw the one acquisition object -- docs/media/acquisition_object.png.

A PGSE built to a real timing budget, drawn as the object holds it: the physical gradient
per axis, the RF events as ticks in their finite windows, the readout, and underneath the
derived effective gradient and q(t). Nothing is drawn by hand; every curve is a field or a
derived property of the same ``ScannerSequence``.

Run: python tools/gen_acquisition_figure.py   (needs dmipy-sim importable)
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dmipy_sim as ds

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "media", "acquisition_object.png")


def main():
    timing = ds.SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3)
    seq = ds.pgse([[1, 0, 0]], 0.012, 0.030, bvalues=[1.5e9], timing=timing, slew_rate=150.0)
    t = np.arange(seq.n_t) * seq.dt * 1e3                       # ms
    G = np.asarray(seq.G)[0] * 1e3                              # mT/m, physical
    Geff = np.asarray(seq.G_eff)[0] * 1e3                       # mT/m, as the spins see it
    q = ds.GAMMA * np.cumsum(np.asarray(seq.G_eff)[0], 0) * seq.dt / 1e3   # rad/mm

    bg, ink, mut, acc, acc2 = "#07090f", "#e8edf5", "#7a8499", "#4af0c4", "#7b9cff"
    fig, ax = plt.subplots(3, 1, figsize=(8.4, 5.6), sharex=True, facecolor=bg,
                           gridspec_kw=dict(height_ratios=[1.4, 1, 1], hspace=0.12))
    for a in ax:
        a.set_facecolor(bg)
        for s in a.spines.values():
            s.set_color("#262b36")
        a.tick_params(colors=mut, labelsize=8)
        a.yaxis.label.set_color(ink)
    # the RF windows and the readout, from the schedule
    for a in ax:
        for e in seq.rf:
            t0, t1 = (e.t_s - e.duration_s / 2) * 1e3, (e.t_s + e.duration_s / 2) * 1e3
            a.axvspan(t0, t1, color="#1b2233", zorder=0)
            if a is ax[0]:
                a.text((t0 + t1) / 2, 0.86, f"{e.flip_deg:.0f}°\n{e.label}", ha="center", va="top",
                       fontsize=7.5, color=acc2, transform=a.get_xaxis_transform())
        a.axvline(seq.echo_idx * seq.dt * 1e3, color=acc, lw=1, ls="--", zorder=0)
    ax[0].plot(t, G[:, 0], color=ink, lw=1.6)
    ax[0].set_ylabel("G  [mT/m]\nphysical, stored", fontsize=8.5)
    ax[0].text(seq.echo_idx * seq.dt * 1e3, 0.96, " readout", color=acc, fontsize=7.5,
               va="top", transform=ax[0].get_xaxis_transform())
    ax[1].plot(t, Geff[:, 0], color=acc2, lw=1.6)
    ax[1].set_ylabel("G_eff  [mT/m]\nderived", fontsize=8.5)
    ax[2].plot(t, q[:, 0], color=acc, lw=1.6)
    ax[2].set_ylabel("q(t)  [rad/mm]\nderived", fontsize=8.5)
    ax[2].set_xlabel("time [ms]", color=mut, fontsize=8.5)
    b = float(seq.b()[0]) * 1e-6
    ax[2].text(0.99, 0.08, f"b = {b:.0f} s/mm²   |q(TE)|/max|q| = {seq.refocusing_residual:.0e}",
               ha="right", va="bottom", fontsize=8, color=mut, transform=ax[2].transAxes)
    ax[0].set_title("pgse([[1, 0, 0]], delta=12 ms, Delta=30 ms, bvalues=[1.5e9], timing=…)  →  one ScannerSequence",
                    color=ink, fontsize=9.5, loc="left")
    fig.savefig(OUT, dpi=140, bbox_inches="tight", facecolor=bg)
    print("wrote", os.path.relpath(OUT), "TE = %.1f ms" % (seq.T * 1e3))


if __name__ == "__main__":
    main()
