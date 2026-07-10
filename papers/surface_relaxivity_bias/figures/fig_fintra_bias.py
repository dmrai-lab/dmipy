"""fig_fintra_bias.py -- the diffusion-side companion to the MWF bias.

Same surface-relaxivity physics, read by a diffusion microstructure model instead of a
relaxometry one. Intra- and extra-axonal water relax at different surface rates
(interior S/V = 4/d per axon; exterior S/V set by packing), so their T2 differ, so the
TE-weighted b=0 that every fraction estimator normalises by mis-weights them --- biasing
the recovered intra-axonal signal fraction f_intra (NODDI / SMT / standard model).

Closed form (mean-rate; the distributed intra pool is the small correction plotted):
  interior  (S/V)_a = 2<r>/<r^2>  (area/spin-weighted, calibre only)
  exterior  (S/V)_e = (S/V)_a * g*VF/(1-VF)          [total outer perimeter / extra area]
  ratio     (S/V)_a/(S/V)_e = (1-VF)/(g*VF),   crossover  VF* = 1/(1+g)
  odds      f_app/(1-f_app) = [f/(1-f)] * exp(-TE * rho * [(S/V)_a - (S/V)_e])

so f_intra is UNDER-estimated in loosely packed WM (interior wins) and OVER-estimated in
densely packed WM (exterior wins, extra water squeezed into high-S/V crevices), crossing
zero at VF*=1/(1+g). Physiological WM (fibre VF ~0.65-0.8) sits ABOVE the crossover, where
the intra-axonal signal WEIGHT (the leading-order recovered-f_intra bias) is over-estimated
by ~8-10% over the robust band VF 0.65-0.70 at clinical TE and the cited rho (larger values
at VF>=0.72 are a mean-field upper edge, not a central estimate). Scales ~linearly with the
order-of-magnitude-uncertain rho; TE-testable via a packing-dependent drift, unlike the
sub-noise MWF bias.

Run: python fig_fintra_bias.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                            "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                            "legend.fontsize": 10.5})
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("m", os.path.join(HERE, "fig_mwf_sv_bias.py"))
mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm)
RHO, A = mm.RHO_REF, mm.ALPHA                       # cited surface relaxivity; Gamma shape
_d = np.linspace(0.02e-6, 8e-6, 4000)
G_REF = 0.70                                        # canonical g-ratio
WM_VF = (0.65, 0.80)                                # physiological fibre volume fraction band


# d_mean here is the OUTER (fibre) diameter -- the histology convention (Aboitiz).
# The interior wall is the INNER (axon) diameter d_in = g * d_out; the exterior wall is
# the fibre boundary. This matches the dmipy-sim Substrate / biophysical-constants catalogue.
def sv_int(d_out_mean, g=G_REF):                    # area/spin-weighted interior S/V (m^-1)
    th = d_out_mean / A; w = _d ** (A - 1) * np.exp(-_d / th)
    r_in = g * _d / 2                                # inner radius = g * outer radius
    r1 = np.sum(w * r_in) / np.sum(w); r2 = np.sum(w * r_in ** 2) / np.sum(w)
    return 2 * r1 / r2


def sv_ext(d_out_mean, g, VF):                       # exterior S/V (ratio law, convention-free)
    return sv_int(d_out_mean, g) * g * VF / (1.0 - VF)


def f_bias(d_out_mean, g, VF, TE_ms):                # exact distributed f_intra bias (rel, %)
    TE = TE_ms * 1e-3; th = d_out_mean / A
    w = _d ** (A - 1) * np.exp(-_d / th) * _d ** 2; w /= w.sum()
    GI = np.sum(w * np.exp(-TE * RHO * (4.0 / (g * _d))))  # intra relaxes on INNER wall g*d_out
    GE = np.exp(-TE * RHO * sv_ext(d_out_mean, g, VF))
    AI = VF * g ** 2; AE = 1.0 - VF                  # lumen vs extra water (myelin gone at dMRI TE)
    ft = AI / (AI + AE)
    fa = AI * GI / (AI * GI + AE * GE)
    return 100 * (fa - ft) / ft


def f_bias_closed(d_out_mean, g, VF, TE_ms):         # mean-rate closed form (rel, %)
    TE = TE_ms * 1e-3
    dSV = sv_int(d_out_mean, g) - sv_ext(d_out_mean, g, VF)
    AI = VF * g ** 2; AE = 1.0 - VF; ft = AI / (AI + AE)
    odds = ft / (1 - ft) * np.exp(-TE * RHO * dSV)
    fa = odds / (1 + odds)
    return 100 * (fa - ft) / ft


def plot():
    fig, ax = plt.subplots(1, 3, figsize=(15.0, 4.3))
    VFg = np.linspace(0.30, 0.85, 120)
    vfstar = 1.0 / (1.0 + G_REF)

    # A: interior vs exterior S/V vs fibre VF -> crossover
    ax[0].axhline(sv_int(0.6e-6) / 1e6, color='#1f77b4', lw=2, label=r'interior $S/V=4/d$ (calibre)')
    ax[0].plot(VFg, [sv_ext(0.6e-6, G_REF, v) / 1e6 for v in VFg], '-', color='#d95f0e', lw=2,
               label=r'exterior $S/V$ (packing)')
    ax[0].axvspan(*WM_VF, color='0.88', zorder=0)
    ax[0].axvline(vfstar, color='0.5', ls=':', lw=1.2)
    ax[0].text(vfstar + 0.005, 12, r'$VF^\ast\!=\!\frac{1}{1+g}$', fontsize=8, color='0.4')
    ax[0].text(np.mean(WM_VF), 13.3, 'WM', ha='center', fontsize=8, color='0.4')
    ax[0].set_xlabel('fibre volume fraction'); ax[0].set_ylabel(r'$S/V$  ($\mu$m$^{-1}$)')
    ax[0].set_ylim(0, 14); ax[0].set_title(r'A  interior vs exterior $S/V$ ($d=0.6\,\mu$m, $g=0.7$)')
    ax[0].legend(fontsize=8, loc='upper left'); ax[0].grid(alpha=0.25)

    # B: f_intra bias vs fibre VF (two calibres) at clinical TE, + closed-form check
    ax[1].axhline(0, color='0.6', lw=1)
    ax[1].axvspan(*WM_VF, color='0.88', zorder=0)
    ax[1].axvline(vfstar, color='0.5', ls=':', lw=1.2)
    for dm, c, lab in [(0.6e-6, '#d95f0e', r'$d=0.6\,\mu$m'), (1.5e-6, '#1f77b4', r'$d=1.5\,\mu$m')]:
        ax[1].plot(VFg, [f_bias(dm, G_REF, v, 80) for v in VFg], '-', color=c, lw=2, label=lab)
        ax[1].plot(VFg[::10], [f_bias_closed(dm, G_REF, v, 80) for v in VFg[::10]], 'o', color=c,
                   ms=3, alpha=0.6)
    ax[1].text(0.31, 4, 'closed form (o)', fontsize=7.5, color='0.4')
    ax[1].set_xlabel('fibre volume fraction'); ax[1].set_ylabel(r'$f_{\rm intra}$ rel. bias  (%)')
    ax[1].set_title('B  fine WM: under-est loose, over-est dense (TE 80 ms)')
    ax[1].legend(fontsize=8, loc='upper left'); ax[1].grid(alpha=0.25)

    # C: TE dependence at three packings -> the testable signature
    TEg = np.linspace(20, 130, 60)
    for VF, c, lab in [(0.45, '#2ca02c', 'VF 0.45 (loose)'), (0.588, '0.4', r'VF$^\ast$ 0.59'),
                       (0.72, '#d95f0e', 'VF 0.72 (dense WM)')]:
        ax[2].plot(TEg, [f_bias(0.6e-6, G_REF, VF, t) for t in TEg], '-', color=c, lw=2, label=lab)
    ax[2].axhline(0, color='0.6', lw=1)
    ax[2].set_xlabel('TE  (ms)'); ax[2].set_ylabel(r'$f_{\rm intra}$ rel. bias  (%)')
    ax[2].set_title('C  TE-dependent (testable), $d=0.6\\,\\mu$m')
    ax[2].legend(fontsize=8, loc='upper left'); ax[2].grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(HERE, "fig_fintra_bias.pdf")
    fig.savefig(out, bbox_inches='tight'); fig.savefig(out.replace('.pdf', '.png'), dpi=140, bbox_inches='tight')
    print("saved", out)
    print(f"VF* = 1/(1+g) = {vfstar:.3f}")
    for VF in [0.45, 0.55, 0.65, 0.72, 0.80]:
        print(f"  VF={VF:.2f} d=0.6um TE=80: exact {f_bias(0.6e-6,G_REF,VF,80):+.1f}%  "
              f"closed {f_bias_closed(0.6e-6,G_REF,VF,80):+.1f}%  "
              f"(SVin {sv_int(0.6e-6)/1e6:.1f}, SVext {sv_ext(0.6e-6,G_REF,VF)/1e6:.1f} /um)")


if __name__ == '__main__':
    plot()
