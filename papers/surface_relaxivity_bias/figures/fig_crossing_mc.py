"""fig_crossing_mc.py -- direct Monte-Carlo demonstration of the myelin-window crossing.

The MWF bias is carried by axons whose INNER diameter falls below d* = 4rho/(1/T2_cut - 1/T2_bulk)
~ 0.17um: their intra-axonal water T2 = 1/(1/T2_bulk + rho*4/d) drops below the 25ms myelin
window and NNLS counts it as myelin. A dense packed MC floors this sub-micron tail (step ~ 1/R^2
cost), so the pack cannot show the crossing -- but the crossing is an INTERIOR (confined-walker)
effect, and the wall-counting estimator is accurate for confined interiors (single-cylinder rate
validated to <1% vs the exact Robin eigenvalue, App. A). So we show it directly on ISOLATED
axons: a gradient-free wall-counting walk in a single reflecting cylinder at a range of inner
diameters recovers the apparent intra T2, which crosses below 25ms at d ~ 0.17um -- confirming
the mechanism the forward model integrates over the calibre distribution.

Cost note: the finest disks need ~1/R^2 scan steps; the full run wants a GPU (seconds) or a few
minutes on CPU. Use --quick for a CPU-tractable (coarser, fewer-walker) version in ~seconds.

Run:
  python fig_crossing_mc.py                 # full, GPU recommended
  python fig_crossing_mc.py --quick         # fast CPU demo
  python fig_crossing_mc.py --outdir /tmp   # write the figure elsewhere (don't dirty the repo)
"""
import os
import sys
import time
import argparse
import numpy as np
import jax
import jax.numpy as jnp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                            "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                            "legend.fontsize": 10.5})

jax.config.update("jax_enable_x64", True)
HERE = os.path.dirname(os.path.abspath(__file__))
from dmipy_sim.substrate.biophysical_constants import canonical_white_matter
_C = canonical_white_matter(3.0)
RHO, D = _C['rho2'], _C['D_intra']          # 1.16e-6 m/s, 1.7e-9 m^2/s
T2_BULK = 0.075                              # surface-free intra bulk T2 (s)
CUT = 0.025                                  # myelin-water window cutoff (s)
D_STAR = 4.0 * RHO / (1.0 / CUT - 1.0 / T2_BULK)     # critical INNER diameter (m)


def surface_rate(R, N=12000, step_frac=0.25, n_decay=5.0, seed=0, tag=''):
    """rho*<S/V> for a single reflecting disk (2D cross-section, confined intra walkers),
    by wall counting (realised-overshoot estimator; accurate for confined interiors).
    Returns the surface relaxation rate (1/s) from the tail slope of -log<weight>."""
    rate_guess = RHO * 4.0 / (2.0 * R)       # rho*(4/d), d=2R
    T = n_decay / rate_guess
    step_l = step_frac * R
    dt = step_l ** 2 / (4.0 * D)             # 2D
    n_steps = int(np.ceil(T / dt))
    sig = np.sqrt(2.0 * D * dt)              # per-component std
    # progress: this loop is the cost; announce n_steps BEFORE running so it never looks hung
    print(f"    {tag} R={R*1e6:.3f}um  n_steps={n_steps:,}  N={N} ...", end='', flush=True)
    t0 = time.perf_counter()
    key = jax.random.PRNGKey(seed)
    key, k0 = jax.random.split(key)
    u = jax.random.uniform(k0, (N, 2))
    rr = R * jnp.sqrt(u[:, 0]); th = 2 * jnp.pi * u[:, 1]
    r0 = jnp.stack([rr * jnp.cos(th), rr * jnp.sin(th)], axis=1)

    def step(carry, _):
        r, lw, key = carry
        key, kk = jax.random.split(key)
        rp = r + jax.random.normal(kk, (N, 2)) * sig
        rn = jnp.linalg.norm(rp, axis=1)
        crossed = rn > R
        overshoot = jnp.where(crossed, rn - R, 0.0)
        scale = jnp.where(crossed, (2.0 * R - rn) / rn, 1.0)
        r_new = rp * scale[:, None]
        lw = lw - 2.0 * (RHO / D) * overshoot          # boundary local time -> weight
        return (r_new, lw, key), jnp.mean(jnp.exp(lw))

    (_, _, _), W = jax.lax.scan(step, (r0, jnp.zeros(N), key), None, length=n_steps)
    W = np.asarray(W); t = np.arange(1, n_steps + 1) * dt
    m = t > 0.5 * T
    A = np.vstack([t[m], np.ones(m.sum())]).T
    rate = float(np.linalg.lstsq(A, -np.log(W[m]), rcond=None)[0][0])
    print(f" done in {time.perf_counter()-t0:5.1f}s  rate={rate:.1f}/s")
    return rate


def compute(quick=False):
    if quick:                                # CPU-tractable: coarser step, fewer walkers, skip finest
        d_in = np.array([0.15, 0.20, 0.30, 0.50]) * 1e-6
        kw = dict(N=1500, step_frac=0.5, n_decay=2.5)
        print(f"[quick] coarse CPU demo ({len(d_in)} diameters, N={kw['N']})")
    else:
        d_in = np.array([0.12, 0.15, 0.20, 0.30, 0.45, 0.70]) * 1e-6      # inner diameters (m)
        kw = dict(N=12000, step_frac=0.25, n_decay=5.0)
    rate_mc = np.array([surface_rate(d / 2.0, tag=f"[{i+1}/{len(d_in)} d={d*1e6:.2f}um]", **kw)
                        for i, d in enumerate(d_in)])
    T2_mc = 1.0 / (1.0 / T2_BULK + rate_mc)
    print()
    for d, rm, t2 in zip(d_in, rate_mc, T2_mc):
        cf = RHO * 4.0 / d
        print(f"  d_in={d*1e6:.2f}um  rate MC={rm:.1f}/s cf={cf:.1f}/s  "
              f"apparent T2={t2*1e3:.1f}ms  {'<-- CROSSES' if t2 < CUT else ''}")
    return d_in, rate_mc, T2_mc


def plot(d_in, rate_mc, T2_mc, outdir):
    dg = np.linspace(0.08e-6, 0.8e-6, 400)
    T2_cf = 1.0 / (1.0 / T2_BULK + RHO * 4.0 / dg)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.axhspan(0, CUT * 1e3, color='0.88', zorder=0)
    ax.text(0.62, CUT * 1e3 * 0.6, 'myelin water\nwindow', fontsize=8, color='0.4')
    ax.axhline(CUT * 1e3, color='0.5', ls=':', lw=1.2)
    ax.axhline(T2_BULK * 1e3, color='0.6', ls='--', lw=1, label='surface-free bulk $T_2$')
    ax.plot(dg * 1e6, T2_cf * 1e3, '-', color='#1f77b4', lw=2,
            label=r'closed form $1/(1/T_{2,\rm b}+\rho\,4/d)$')
    ax.plot(d_in * 1e6, T2_mc * 1e3, 'o', color='#d95f0e', ms=7, mfc='white', mew=1.8,
            label='isolated-axon wall-counting MC', zorder=5)
    ax.axvline(D_STAR * 1e6, color='#d95f0e', ls=':', lw=1.2)
    ax.text(D_STAR * 1e6 + 0.01, 55, r'$d^\ast\!\approx\!%.2f\,\mu$m' % (D_STAR * 1e6),
            fontsize=8, color='#d95f0e')
    ax.set_xlabel(r'inner (axon) diameter  $d$  ($\mu$m)')
    ax.set_ylabel(r'apparent intra-axonal $T_2$  (ms)')
    ax.set_title('Fine axons cross below the myelin window (MC)')
    ax.set_ylim(0, 80); ax.set_xlim(0.08, 0.8)
    ax.legend(fontsize=8, loc='lower right'); ax.grid(alpha=0.25)
    fig.tight_layout()
    out = os.path.join(outdir, 'fig_crossing_mc.pdf')
    fig.savefig(out, bbox_inches='tight'); fig.savefig(out.replace('.pdf', '.png'), dpi=140,
                                                       bbox_inches='tight')
    print('saved', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--quick', action='store_true',
                    help='coarse, CPU-tractable demo (fewer walkers/diameters, ~seconds)')
    ap.add_argument('--outdir', default=HERE,
                    help='where to write the figure (default: alongside this script)')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    try:
        backend = jax.default_backend()
    except Exception as e:
        backend = f'unknown ({e})'
    print(f"JAX backend: {backend}"
          + ('   (CPU -- use --quick or a GPU for the full run)' if backend == 'cpu' else ''))
    print(f"d* = {D_STAR*1e6:.3f} um (inner)")
    d_in, rate_mc, T2_mc = compute(quick=args.quick)
    plot(d_in, rate_mc, T2_mc, args.outdir)
