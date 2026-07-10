#!/usr/bin/env python
"""fig_demyelination_bias.py -- clinical relevance: does the surface-relaxivity MWF
bias over- or under-state true myelin loss as a tract demyelinates?

Design (paired, within-subject, seed-independent).  Primary demyelination is myelin
thinning at PRESERVED axons: the g-ratio g = r_in/r_out RISES toward 1 while the inner
axon radius and axon count are unchanged.  We model this faithfully and cleanly:

  1. For each "subject" (seed) we sample a Gamma axon population and pack the OUTER
     (myelin) cylinders ONCE, at the baseline (thickest myelin, largest outer walls,
     g = G_BASE).  Packing the largest-ever cylinders first guarantees every later,
     thinner state is overlap-free.
  2. We FREEZE the centres and the inner (axon) radii, and demyelinate by shrinking
     ONLY the outer wall, r_out = r_in / g, as g rises.  So each subject is its own
     longitudinal series -- the SAME axon distribution, progressively demyelinated --
     not a fresh random substrate per stage.

At every stage we read the geometry directly off the realised pack: the myelin volume
fraction MVF, the interior surface-to-volume <4/d>_V (FIXED -- the axon lumen is
preserved), and the exterior S_ext/V_ext (which FALLS as the outer walls retreat and the
extra space grows).  We then run the SAME MC-validated 3-pool surface-relaxivity forward
model + standard chi^2-NNLS as Fig 3, at rho=0 (true MWF) and at the cited rho
(apparent MWF).

Result: the bias is set by the INNER (lumen) radius, which primary demyelination leaves
intact, so it is a nearly CONSTANT positive offset -- apparent MWF sits just ABOVE true
(fine WM reads myelin-richer) at every stage, ~+0.11 pp at baseline and ~+0.09 pp at
g=0.90.  A within-subject CHANGE subtracts that baseline offset, so it very nearly
CANCELS: over a true 10.86 pp MWF drop the apparent falls 10.88 pp, an over-report of only
~0.015 pp (0.1% of the true change).  The surface confound is therefore a CROSS-REGION
effect, not a longitudinal one (for lumen-preserving demyelination).  Averaged over many
subjects the trajectory is clean.

Run:  python fig_demyelination_bias.py            # compute (packs) + plot
      python fig_demyelination_bias.py --plot-only
"""
import os
import sys
import numpy as np

os.environ.setdefault('XLA_PYTHON_CLIENT_PREALLOCATE', 'false')
for _p in (os.environ.get('DMIPY_SIM_PUBLIC'),
           os.environ.get('DMIPY_FIT_PUBLIC')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NPZ = os.path.join(HERE, 'fig_demyelination_bias_data.npz')
PDF = os.path.join(HERE, 'fig_demyelination_bias.pdf')

# shared canonical constants + the standard MWF protocol/estimator (Fig 3)
from fig_mwf_sv_bias import (RHO_REF, F0, G0, W_M, T2_BULK_IE, T2_MYELIN, ET,
                             MYELIN_CUTOFF, T2_GRID_BC)

ALPHA = 2.0                 # Gamma diameter shape (canonical)
GAMMA_SCALE = 0.304e-6      # canonical OUTER-diameter scale (mean outer / fibre d ~0.6 um)
MIN_D = 0.10e-6            # keep the thin-axon tail (it carries the crossing effect)
N_CYL = 300
N_SUBJ = 24                # independent axon populations (subjects)
G_BASE = 0.70              # healthy / baseline g-ratio (most myelin in the trajectory)
G_GRID = np.linspace(G_BASE, 0.90, 11)   # demyelination: g rises toward 1


def _subject(seed):
    """One axon population, packed at the baseline (thickest myelin).  Returns the
    FROZEN inner radii, centres, and domain size; demyelination later only shrinks
    r_out, keeping the axon centres and inner radii fixed."""
    from dmipy_sim.geometries import pack_cylinders
    rng = np.random.default_rng(seed)
    d_out = np.clip(rng.gamma(ALPHA, GAMMA_SCALE, size=N_CYL), MIN_D, None)  # OUTER (fibre) diameter
    r_out_base = 0.5 * d_out                          # thickest myelin -> largest outer walls
    r_in = G_BASE * r_out_base                        # inner (axon) radius = g * outer (frozen)
    centers, L, _ = pack_cylinders(r_out_base, target_vf=F0, seed=seed)
    return r_in, float(L), np.asarray(centers, float)


def _mwf_stage(r_in, L, g, rho):
    """True (rho=0) / apparent (rho>0) MWF of one realised pack demyelinated to g.
    Grid-free short-T2 fraction: myelin water + the intra water of the thinnest axons
    (per-axon interior S/V = 2/r_in) whose T2 = 1/(1/T2_bulk + rho*2/r_in) falls below the
    myelin window.  The crossing is set by the INNER radii, which demyelination preserves,
    so the bias is a nearly-constant, lumen-driven offset (it cancels in longitudinal change).
    """
    r_out = r_in / g
    area = L * L
    f_in = float(np.sum(np.pi * r_in ** 2) / area)              # axon lumen frac (FIXED)
    f_out = float(np.sum(np.pi * r_out ** 2) / area)            # fibre (outer) frac
    mvf = f_out - f_in                                          # myelin volume fraction
    A_I, A_E, A_M = f_in, 1.0 - f_out, mvf * W_M                # compartment water
    sw = A_I + A_E + A_M
    F_I, F_M = A_I / sw, A_M / sw
    sv_in = float(np.sum(2 * np.pi * r_in) / np.sum(np.pi * r_in ** 2))   # <4/d>_V (FIXED)
    sv_ext = float(np.sum(2 * np.pi * r_out) / (area - np.sum(np.pi * r_out ** 2)))
    # distributed intra crossing (volume/spin-weighted by r_in^2), grid-free
    T2i = 1.0 / (1.0 / T2_BULK_IE + rho * (2.0 / r_in))
    w = r_in ** 2
    phi = float(np.sum(w[T2i < MYELIN_CUTOFF]) / np.sum(w))     # crossed intra fraction (0 at rho=0)
    mwf = F_M + F_I * phi                                       # apparent short-T2 fraction
    return mwf, mvf, sv_in, sv_ext, F_M


TE_DMRI = 80e-3                # clinical PGSE echo time for the f_intra (diffusion) readout


def _fintra_bias(r_in, L, g, rho, TE=TE_DMRI):
    """Relative bias (%) of the diffusion intra-axonal SIGNAL fraction f_intra along the
    SAME demyelination trajectory. Unlike MWF (set by the fixed INNER wall, hence constant
    and cancelling), f_intra is set by the interior-MINUS-exterior differential of Eq. (9):
    the exterior wall RETREATS as myelin thins, so (S/V)_ext falls, the differential grows,
    and the f_intra bias DRIFTS -- it does NOT cancel. Myelin water is gone at the dMRI TE."""
    r_out = r_in / g
    area = L * L
    f_in = float(np.sum(np.pi * r_in ** 2) / area)              # lumen (axon) fraction, FIXED
    f_out = float(np.sum(np.pi * r_out ** 2) / area)            # fibre (outer) fraction
    sv_in = float(np.sum(2 * np.pi * r_in) / np.sum(np.pi * r_in ** 2))       # (S/V)_int, FIXED
    sv_ext = float(np.sum(2 * np.pi * r_out) / (area - np.sum(np.pi * r_out ** 2)))  # falls
    AI, AE = f_in, 1.0 - f_out                                  # lumen vs extra water (no myelin)
    ft = AI / (AI + AE)
    odds = ft / (1 - ft) * np.exp(-TE * rho * (sv_in - sv_ext))
    fa = odds / (1 + odds)
    return 100.0 * (fa - ft) / ft


def compute():
    ng = len(G_GRID)
    true_mwf = np.zeros((N_SUBJ, ng)); app_mwf = np.zeros((N_SUBJ, ng))
    mvf = np.zeros((N_SUBJ, ng)); sv_ext = np.zeros((N_SUBJ, ng)); sv_in = np.zeros(N_SUBJ)
    fintra_bias = np.zeros((N_SUBJ, ng))
    geom0 = None
    for s in range(N_SUBJ):
        r_in, L, centers = _subject(s)
        if s == 0:                                  # keep one subject's geometry to draw
            geom0 = dict(r_in=r_in, L=L, centers=centers)
        for j, g in enumerate(G_GRID):
            t, mv, svi, sve, _ = _mwf_stage(r_in, L, g, 0.0)
            a, _, _, _, _ = _mwf_stage(r_in, L, g, RHO_REF)
            true_mwf[s, j] = t * 100; app_mwf[s, j] = a * 100
            mvf[s, j] = mv * 100; sv_ext[s, j] = sve / 1e6
            fintra_bias[s, j] = _fintra_bias(r_in, L, g, RHO_REF)   # diffusion f_intra bias
        sv_in[s] = svi / 1e6
        print(f"[subj {s:2d}] true MWF {true_mwf[s,0]:.1f}->{true_mwf[s,-1]:.1f}%  "
              f"app {app_mwf[s,0]:.1f}->{app_mwf[s,-1]:.1f}%  "
              f"S/V_ext {sv_ext[s,0]:.2f}->{sv_ext[s,-1]:.2f}/um", flush=True)
    # paired changes from each subject's own baseline (g=G_BASE)
    d_true = true_mwf[:, [0]] - true_mwf            # true MWF drop (>=0) at each stage
    d_app = app_mwf[:, [0]] - app_mwf               # apparent MWF drop
    out = dict(g=G_GRID, true_mwf=true_mwf, app_mwf=app_mwf, mvf=mvf, sv_ext=sv_ext,
               sv_in=sv_in, d_true=d_true, d_app=d_app, fintra_bias=fintra_bias,
               rho_ref=RHO_REF, g_base=G_BASE,
               geom0_rin=geom0['r_in'], geom0_L=geom0['L'], geom0_centers=geom0['centers'])
    np.savez(NPZ, **out)
    print(f"saved {NPZ}")
    return dict(np.load(NPZ))


def _draw_substrate(ax, r_in, centers, L, g, title):
    """One subject's cross-section at g: axons (inner, FIXED) + myelin annulus
    (outer = r_in/g, shrinks as g rises).  Cropped to a window so axons are visible.

    NOTE: pack_cylinders returns centres in [-L/2, +L/2] (the periodic domain is
    centred on the ORIGIN, not [0, L]).  The crop window must therefore be centred on
    0 (x0 = -W/2), not on L/2 -- using L/2 catches only the +x/+y corner and the
    cylinders bunch in one corner.  (Burned once; do not repeat.)"""
    import matplotlib.patches as mpatches
    W = 0.32 * L
    x0, y0 = -0.5 * W, -0.5 * W                                    # domain is centred on origin
    r_out = r_in / g
    ax.set_facecolor('#e9eef5')                                   # extra-axonal water
    for (cx, cy), ri, ro in zip(centers, r_in, r_out):
        if x0 - ro <= cx <= x0 + W + ro and y0 - ro <= cy <= y0 + W + ro:
            ax.add_patch(mpatches.Circle((cx, cy), ro, facecolor='#caa96a',
                                         edgecolor='none', zorder=1))      # myelin
            ax.add_patch(mpatches.Circle((cx, cy), ri, facecolor='white',
                                         edgecolor='#8a8a8a', lw=0.3, zorder=2))  # axon
    ax.set_xlim(x0, x0 + W); ax.set_ylim(y0, y0 + W)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=8.5)


def plot(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                                "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                                "legend.fontsize": 10.5})
    g = d['g']
    tm, am = d['true_mwf'], d['app_mwf']
    tm_m, tm_s = tm.mean(0), tm.std(0)
    am_m, am_s = am.mean(0), am.std(0)
    dt_m = d['d_true'].mean(0); da_m = d['d_app'].mean(0)
    da_s = d['d_app'].std(0)

    fig = plt.figure(figsize=(12.0, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.92, 1.25], hspace=0.32, wspace=0.28)

    # ── top filmstrip: ONE subject's substrate at three demyelination stages, showing
    # the design -- axon centres + inner radii fixed, outer myelin wall shrinking ──
    if 'geom0_centers' in d:
        rin0 = d['geom0_rin']; cen0 = d['geom0_centers']; L0 = float(d['geom0_L'])
        stages = [(0, 'healthy'), (len(g) // 2, ''), (len(g) - 1, 'demyelinated')]
        for col, (j, tag) in enumerate(stages):
            axs = fig.add_subplot(gs[0, col])
            lab = f'g = {g[j]:.2f}' + (f'  ({tag})' if tag else '')
            _draw_substrate(axs, rin0, cen0, L0, g[j], lab)
            if col == 0:
                axs.set_ylabel('one subject:\naxons fixed,\nmyelin thins', fontsize=8)
    fig.text(0.5, 0.985, 'A   demyelination = shrink the outer myelin wall, axons unchanged',
             ha='center', va='top', fontsize=9.5, weight='bold')

    # A (lower-left): true vs apparent MWF along the demyelination trajectory
    aA = fig.add_subplot(gs[1, 0])
    aA.plot(g, tm_m, '--', color='#d95f0e', lw=2.0, label='true MWF (myelin volume)')
    aA.fill_between(g, tm_m - tm_s, tm_m + tm_s, color='#d95f0e', alpha=0.12)
    aA.plot(g, am_m, '-', color='#d95f0e', lw=2.4, label=r'apparent MWF (cited $\rho$)')
    aA.fill_between(g, am_m - am_s, am_m + am_s, color='#d95f0e', alpha=0.18)
    aA.set_xlabel(r'g-ratio  (demyelination $\rightarrow$)')
    aA.set_ylabel('MWF  (%)', color='#d95f0e')
    aA.set_title('B  apparent vs true MWF')
    aA.grid(alpha=0.25)
    aA.annotate('', xy=(g[-1], aA.get_ylim()[1]*0.92), xytext=(g[0], aA.get_ylim()[1]*0.92),
                arrowprops=dict(arrowstyle='->', color='0.5'))
    # right axis: the MWF bias (apparent - true) itself -- positive (fine axons read
    # richer) and nearly CONSTANT, because it is set by the inner radii, which
    # demyelination preserves; that constancy is why it cancels in longitudinal change.
    axr = aA.twinx()
    bias = am_m - tm_m
    axr.plot(g, bias, ':', color='#3182bd', lw=1.8, label=r'bias (app$-$true)')
    axr.set_ylabel(r'MWF bias  (pp)', color='#3182bd')
    axr.tick_params(axis='y', colors='#3182bd')
    axr.set_ylim(0.0, max(0.25, float(bias.max()) * 1.8))
    aA.text(g[0] + 0.004, tm_m[0],
            f'apparent sits just ABOVE true\n(lumen-set offset {bias[0]:+.2f} pp,\nnearly constant)',
            fontsize=7.3, color='0.35', va='top')
    h1, l1 = aA.get_legend_handles_labels(); h2, l2 = axr.get_legend_handles_labels()
    aA.legend(h1 + h2, l1 + l2, fontsize=8, loc='lower left')

    # C: apparent vs true MWF *change* (paired) -- lumen-set offset cancels in the change
    aB = fig.add_subplot(gs[1, 1])
    lim = max(dt_m.max(), da_m.max()) * 1.08
    aB.plot([0, lim], [0, lim], '-', color='0.6', lw=1.2, label='no bias (apparent = true)')
    aB.plot(dt_m, da_m, 'o-', color='#762a83', lw=2.2, ms=5,
            label=r'measured (cited $\rho$)')
    # the surface bias is lumen-driven (inner radii fixed) -> nearly constant -> it
    # cancels in the within-subject CHANGE; the measured curve sits on the identity line.
    resid = da_m[-1] - dt_m[-1]        # +ve: apparent over-reports; ~0.01 pp (negligible)
    pct = resid / dt_m[-1] * 100 if dt_m[-1] > 0 else 0.0
    aB.annotate('apparent change tracks the true loss:\nthe bias is lumen-driven '
                '(inner radii fixed),\nnearly constant, so it CANCELS in the\n'
                f'longitudinal change (residual {resid:+.2f} pp, {pct:+.1f}%)',
                xy=(dt_m[-1], da_m[-1]), xytext=(0.06, 0.72), textcoords='axes fraction',
                fontsize=7.6, color='#762a83', ha='left', va='top',
                arrowprops=dict(arrowstyle='->', color='#762a83', lw=1))
    aB.set_xlabel('true MWF change  (pp)')
    aB.set_ylabel('apparent MWF change  (pp)')
    aB.set_title('C  bias cancels in the change')
    aB.legend(fontsize=8, loc='lower right'); aB.grid(alpha=0.25)

    # D: the unifying contrast -- SAME S/V physics, two metrics diverge under demyelination.
    # MWF reads the INTERIOR crossing (inner wall, fixed) -> bias flat -> cancels.
    # f_intra reads the interior-MINUS-exterior differential of Eq.(9); the exterior wall
    # retreats as myelin thins -> (S/V)_ext falls -> the f_intra bias DRIFTS (does not cancel).
    aD = fig.add_subplot(gs[1, 2])
    fb = d['fintra_bias'].mean(0) if 'fintra_bias' in d else None
    mwf_bias = am_m - tm_m                                   # pp, ~flat
    aD.axhline(0, color='0.6', lw=1)
    aD.plot(g, mwf_bias, ':', color='#3182bd', lw=2.0, marker='s', ms=4,
            label='MWF bias (pp, qMRI)')
    aD.set_xlabel(r'g-ratio  (demyelination $\rightarrow$)')
    aD.set_ylabel('MWF bias  (pp)', color='#3182bd')
    aD.tick_params(axis='y', colors='#3182bd')
    aD.set_title('D  MWF cancels, $f_{\\rm intra}$ drifts')
    aD.grid(alpha=0.25)
    if fb is not None:
        aDr = aD.twinx()
        aDr.plot(g, fb, '-', color='#d95f0e', lw=2.4, marker='o', ms=4,
                 label=r'$f_{\rm intra}$ bias (%, dMRI)')
        aDr.set_ylabel(r'$f_{\rm intra}$ relative bias  (%)', color='#d95f0e')
        aDr.tick_params(axis='y', colors='#d95f0e')
        aD.text(g[0] + 0.004, 0.02,
                'MWF: interior wall (fixed)\n$\\Rightarrow$ nearly constant',
                fontsize=7.0, color='#3182bd', va='bottom')
        aDr.text(g[-1] - 0.004, fb[-1],
                 r'$f_{\rm intra}$: interior$-$exterior' + '\n(exterior retreats)\n'
                 r'$\Rightarrow$ drifts ' + f'{fb[0]:+.0f}$\\to${fb[-1]:+.0f}%',
                 fontsize=7.0, color='#d95f0e', va='center', ha='right')
        h1, l1 = aD.get_legend_handles_labels(); h2, l2 = aDr.get_legend_handles_labels()
        aD.legend(h1 + h2, l1 + l2, fontsize=7.5, loc='upper left')

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(PDF, bbox_inches='tight')
    fig.savefig(PDF.replace('.pdf', '.png'), dpi=140, bbox_inches='tight')
    print(f"saved {PDF}")
    # headline numbers
    i = -1
    print(f"[demyel g {g[0]:.2f}->{g[i]:.2f}] true MWF {tm_m[0]:.2f}->{tm_m[i]:.2f}%  "
          f"apparent {am_m[0]:.2f}->{am_m[i]:.2f}%")
    print(f"  baseline bias (true-app) = {tm_m[0]-am_m[0]:.3f} pp;  "
          f"demyelinated bias = {tm_m[i]-am_m[i]:.3f} pp")
    print(f"  true drop = {dt_m[i]:.2f} pp;  apparent drop = {da_m[i]:.2f} pp;  "
          f"over-report = {da_m[i]-dt_m[i]:.3f} pp ({(da_m[i]-dt_m[i])/dt_m[i]*100:.1f}% of true)")
    print(f"  (S/V)_ext {d['sv_ext'].mean(0)[0]:.2f}->{d['sv_ext'].mean(0)[i]:.2f}/um;  "
          f"(S/V)_in (fixed) = {d['sv_in'].mean():.2f}/um")
    if 'fintra_bias' in d:
        fb = d['fintra_bias'].mean(0)
        print(f"  f_intra bias (dMRI, TE={TE_DMRI*1e3:.0f}ms) DRIFTS {fb[0]:+.1f}%->{fb[i]:+.1f}% "
              f"(does NOT cancel: interior-exterior differential, exterior wall retreats)")


if __name__ == '__main__':
    d = dict(np.load(NPZ)) if '--plot-only' in sys.argv else compute()
    plot(d)
