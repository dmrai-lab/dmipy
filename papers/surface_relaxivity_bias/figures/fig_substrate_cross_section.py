#!/usr/bin/env python
"""fig_substrate_cross_section.py --- the three white-matter substrates this paper
acts on, and the myelin water fraction each yields at FIXED myelin volume.

Three packs at identical fibre fraction f=0.55, g-ratio 0.70, and identical myelin
volume: a small-calibre and a large-calibre Gamma pack (synthetic, drawn from the
canonical inner-diameter distributions), and a real rat spinal-cord cross-section
(AxonDeepSeg manual segmentation, 0.13 um/px; Zaimi 2018 -- the paper's only real
data). All drawn at the same physical scale.

The point: the three have the SAME myelin volume but different surface-to-volume
ratio S/V (small axons pack more wall per unit volume), so the surface-relaxivity
rate rho*(S/V) absorbed into the multi-echo T2 differs -- and the standard NNLS
myelin water fraction (MWF), read off the SAME forward model as Fig 2, drifts
between them even though the myelin content is identical. The recovered MWF and its
offset from truth are annotated on each panel (interpolated from the Fig-2 sweep at
each pack's mean inner diameter).

No GPU; CPU RSA packing + the real image + the committed Fig-2 data. Run:
  python fig_substrate_cross_section.py
"""
import os
import sys
for _p in (os.environ.get('DMIPY_SIM_PUBLIC'),
           os.environ.get('DMIPY_FIT_PUBLIC')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import to_rgb
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'fig_substrate_cross_section.pdf')
MWF_DATA = os.path.join(HERE, 'fig_mwf_sv_bias_data.npz')

G_RATIO = 0.70
VF_TARGET = 0.55
BOX = 36.0

# mean_d / outer_scale are the OUTER (fibre) diameter Gamma (histology convention);
# the inner (axon) diameter is g * outer, and interior S/V uses that inner diameter.
FINE = dict(alpha=2.0, outer_scale=0.304, color='#2c7fb8', label='SMALL-CALIBRE',
            tract='CC genu / general WM', mean_d=0.61)
LARGE = dict(alpha=2.0, outer_scale=1.00, color='#b8420f', label='LARGE-CALIBRE',
             tract='corticospinal / CC midbody', mean_d=2.0)
RAT = dict(color='#2ca02c', label='REAL', tract='rat spinal cord (AxonDeepSeg)',
           crop=os.path.join(HERE, 'rat_sem_crop.png'),
           meta=os.path.join(HERE, 'rat_sem_crop_meta.npz'))


def _mwf_at(mean_d_um):
    """Recovered MWF (%) and offset-from-true (pp) at this mean OUTER (fibre) diameter,
    interpolated from the committed Fig-2 sweep (the 3-pool NNLS forward model, whose
    d_um axis is the OUTER diameter)."""
    d = dict(np.load(MWF_DATA))
    mwf = float(np.interp(mean_d_um, d['d_um'], d['mwf_nnls']))
    true = float(d['true_mwf']) * 100
    return mwf, mwf - true


def rsa_packing(seed, alpha, outer_scale, box=BOX, vf=VF_TARGET, n_pos=80):
    rng = np.random.default_rng(seed)
    target = vf * box * box
    radii, area = [], 0.0
    while area < target:
        r = 0.5 * rng.gamma(alpha, outer_scale)
        radii.append(r); area += np.pi * r * r
    radii = np.sort(radii)[::-1]
    xs, ys, rs = [], [], []
    for r in radii:
        for _ in range(n_pos):
            x, y = rng.uniform(0, box), rng.uniform(0, box)
            if rs:
                ax_, ay, ar = np.asarray(xs), np.asarray(ys), np.asarray(rs)
                dx = np.abs(x - ax_); dx = np.minimum(dx, box - dx)
                dy = np.abs(y - ay); dy = np.minimum(dy, box - dy)
                if np.any(dx * dx + dy * dy < (r + ar) ** 2):
                    continue
            xs.append(x); ys.append(y); rs.append(r); break
    return np.asarray(xs), np.asarray(ys), np.asarray(rs)


def draw_pack(ax, xs, ys, rs, spec):
    for x, y, r in zip(xs, ys, rs):
        for ox in (0, -BOX, BOX):
            for oy in (0, -BOX, BOX):
                ax.add_patch(Circle((x + ox, y + oy), r, facecolor='0.78',
                                    edgecolor='0.45', lw=0.4, zorder=1))
                ax.add_patch(Circle((x + ox, y + oy), G_RATIO * r,
                                    facecolor=spec['color'], edgecolor='none',
                                    alpha=0.85, zorder=2))
    ax.set_xlim(0, BOX); ax.set_ylim(0, BOX); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(spec['color']); s.set_linewidth(1.6)


def add_scalebar(ax, um=10):
    bar = AnchoredSizeBar(ax.transData, um, rf'${um}\,\mu$m', 'lower left',
                          pad=0.25, borderpad=0.35, sep=3, color='black', frameon=True,
                          size_vertical=BOX * 0.012,
                          fontproperties=fm.FontProperties(size=8))
    bar.patch.set(alpha=0.85, edgecolor='none')
    ax.add_artist(bar)


def draw_rat(ax, spec):
    seg = np.array(Image.open(spec['crop']))
    seg = seg[..., 0] if seg.ndim == 3 else seg
    m = np.load(spec['meta'])
    px = float(m['px']) * 1e-6
    L = seg.shape[0] * float(m['px'])
    rgb = np.ones((*seg.shape, 3))
    rgb[seg == 127] = (0.78, 0.78, 0.78)
    rgb[seg == 255] = to_rgb(spec['color'])
    ax.imshow(rgb, origin='lower', extent=[0, L, 0, L], interpolation='nearest')
    ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(spec['color']); s.set_linewidth(1.6)
    # measured exterior S/V from the real mask (outer-wall length / extra area)
    fibre = (seg == 255) | (seg == 127)
    edge = (fibre[1:] != fibre[:-1]).sum() + (fibre[:, 1:] != fibre[:, :-1]).sum()
    sv = (edge * px) / (float((~fibre).sum()) * px ** 2) / 1e6
    return float(m['mean_d']), sv, float(m['myelin_frac'])


def _annotate(ax, mean_d, spec, color):
    """Synthetic, myelin-volume-matched packs: show S/V and the recovered MWF.
    mean_d is the OUTER (fibre) diameter; interior S/V uses inner = g*outer."""
    sv = 4.0 * 2.0 / (G_RATIO * mean_d * (2.0 + 1.0))  # area-weighted <4/d_in>_V, alpha=2
    mwf, bias = _mwf_at(mean_d)
    ax.set_title(f"{spec['label']}  ({spec['tract']})\n"
                 rf"$\langle d\rangle={mean_d:.2f}\,\mu$m,  $\langle S/V\rangle={sv:.1f}\,\mu$m$^{{-1}}$"
                 "\n" rf"recovered MWF $={mwf:.1f}\%$  (${bias:+.1f}$ pp)",
                 fontsize=8.5, color=color, fontweight='bold')


def draw_fitted(ax, spec):
    """Draw the fitted myelinated-cylinder reconstruction of the real crop:
    each segmented axon as an outer (myelin) circle + inner (lumen) circle at its
    true centroid, per-axon inner radius and g-ratio (real_substrate extraction)."""
    import sys
    sys.path.insert(0, HERE)
    from real_substrate import extract_myelinated_cylinders
    seg = np.array(Image.open(spec['crop']))
    seg = seg[..., 0] if seg.ndim == 3 else seg
    m = np.load(spec['meta']); px = float(m['px']) * 1e-6
    L = seg.shape[0] * px * 1e6                     # micron
    centers, ri, ro = extract_myelinated_cylinders(seg, px)
    for (cx, cy), a, b in zip(centers * 1e6, ri * 1e6, ro * 1e6):
        ax.add_patch(Circle((cx, cy), b, facecolor='0.78', edgecolor='0.45', lw=0.3, zorder=1))
        ax.add_patch(Circle((cx, cy), a, facecolor=spec['color'], edgecolor='none',
                            alpha=0.85, zorder=2))
    ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(spec['color']); s.set_linewidth(1.6); s.set_linestyle('--')
    return float(2 * ri.mean() * 1e6), float(np.mean(ri / ro))


def main():
    fig, ax = plt.subplots(1, 4, figsize=(15.6, 4.7))
    for a, spec, seed in zip(ax[:2], (FINE, LARGE), (3, 7)):
        xs, ys, rs = rsa_packing(seed, spec['alpha'], spec['outer_scale'])
        draw_pack(a, xs, ys, rs, spec)
        _annotate(a, spec['mean_d'], spec, spec['color'])
    # real segmentation (panel 3) and its fitted-cylinder reconstruction (panel 4)
    rat_d, rat_sv, rat_mvf = draw_rat(ax[2], RAT)
    ax[2].set_title(f"{RAT['label']} segmentation ({RAT['tract']})\n"
                    rf"$\langle d\rangle={rat_d:.2f}\,\mu$m,  $S/V={rat_sv:.1f}\,\mu$m$^{{-1}}$"
                    "\n" rf"real EM (MVF $=$ {rat_mvf:.2f})",
                    fontsize=8.5, color=RAT['color'], fontweight='bold')
    fit_d, fit_g = draw_fitted(ax[3], RAT)
    ax[3].set_title(f"{RAT['label']} fitted cylinders\n"
                    rf"$\langle d\rangle={fit_d:.2f}\,\mu$m,  per-axon $g={fit_g:.2f}$"
                    "\n" r"(what the walk sees)",
                    fontsize=8.5, color=RAT['color'], fontweight='bold')
    for a in ax:
        add_scalebar(a, um=10)
    fig.text(0.5, 0.015,
             rf'Panels 1--2: synthetic packs at identical myelin volume (${BOX:.0f}\,\mu$m cell, '
             rf'$f=0.55$, $g=0.70$) $\Rightarrow$ higher $S/V$ (smaller axons) gives larger '
             r'$\rho(S/V)$ in $T_2$ and lower recovered MWF at constant myelin.  '
             r'Panels 3--4: a real rat cross-section and the myelinated cylinders fitted to it '
             r'(real positions, per-axon diameter and g-ratio) that the Monte Carlo walks.',
             ha='center', fontsize=8, color='0.3')
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(PDF, bbox_inches='tight')
    fig.savefig(PDF.replace('.pdf', '.png'), dpi=150, bbox_inches='tight')
    print(f"wrote {PDF}")


if __name__ == '__main__':
    main()
