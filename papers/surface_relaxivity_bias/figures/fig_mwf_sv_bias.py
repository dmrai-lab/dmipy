#!/usr/bin/env python
"""fig_mwf_sv_bias.py -- the headline result.

Thesis (the paper's whole point, as a simulation):
  An instantaneous-180 CPMG train carries NO diffusion gradient, yet a proton
  bouncing on a wall still dephases there (surface relaxivity).  The same wall
  collisions that Novikov/Burcaw turn into the time-dependent extra-axonal
  diffusion D(t) of randomly packed media are, from the qMRI side, an extra
  transverse-relaxation rate rho*(S/V): isotropic, linear in TE, and inseparable
  from the bulk 1/T2.  S/V is unobserved (null space).  So the apparent T2 the
  myelin-water analysis fits ALREADY ABSORBS rho*(S/V), and two voxels with
  identical myelin volume but different calibre (different S/V) report different
  apparent T2 -- and a different myelin water fraction (MWF).

Three panels:

  A. PROOF BY MONTE CARLO (real walks).  The simulator counts wall encounters
     (specular reflection + recorded wall local time) with NO analytical
     relaxivity model.  At b=0 (no diffusion gradient) we isolate the surface
     attenuation of the intra/extra (IE) pool and read off its rate.  Across axon
     calibre the MC-measured rate sits on the Brownstein-Tarr line rho*(S/V):
     wall-counting reproduces the closed form, so T2 demonstrably absorbs
     rho*(S/V) even with no gradient.

  B. APPARENT T2 AND MWF vs S/V (standard MWF forward model, MC-validated rate).
     The IE apparent transverse time T2_app = 1/(1/T2_bulk + rho*S/V) swings by
     ~tens of ms (70->51 ms) across the physiological calibre range -- an
     NNLS-independent, rock-solid statement.  Feeding the fixed-myelin-volume decay
     to the STANDARD regularised-NNLS MWF estimator, the thinnest axons' water crosses
     BELOW the 25 ms window and is counted as myelin, so at FIXED myelin volume the
     recovered MWF RISES as calibre falls (fine WM reads myelin-RICHER): grid-free
     short-T2 fraction 13.49->13.75% at cited rho (NNLS 13.41->13.87%), a fine-vs-large
     excess of ~0.10 pp -- a fraction of the demyelination MWF change.

  C. THE BOUND.  Because the relaxivity rho of trapped/wall protons is itself
     poorly known, we bound the fine-vs-large MWF excess over rho: ~0.10 pp at the cited
     rho, ~1.22 pp at 2.5 um/s (super-linear) -- the unquantified uncertainty floor on a
     reported MWF.

Design notes:
  * Panel A is the only part that needs Monte Carlo (one cached b=0 walk).
  * Panels B/C use the STANDARD MWF pipeline (dmipy_fit...t2_spectrum_mwf) on a
    THREE-pool decay (myelin + intra interior + extra exterior) with FIXED material
    bulk T2 + the MC-validated, AREA/SPIN-WEIGHTED surface rate rho*<S/V> -- a real
    multi-component spectrum, isolating the surface confound from protocol artifacts
    (the raw sim CPMG signal is confounded by an under-resolved 12 ms myelin pool
    at TE=10 ms and by the sim's fixed-apparent-T2 parametrisation; we therefore
    inject the validated rate into the forward model, the transparent and standard
    way to quantify a relaxometry bias).

Run (GPU for Panel A; B/C are instant):
  python fig_mwf_sv_bias.py            # compute (walks Panel A if not cached) + plot
  python fig_mwf_sv_bias.py --plot-only
  python fig_mwf_sv_bias.py --panelA-only
"""
import os
import sys
import time
import numpy as np

os.environ.setdefault('XLA_PYTHON_CLIENT_PREALLOCATE', 'false')
# Public engines: prepend the source trees if they exist (dev machine), else fall back to the
# installed dmipy_sim / dmipy_fit packages. Override the locations with DMIPY_SIM_PUBLIC /
# DMIPY_FIT_PUBLIC. Guarded so a public checkout on any machine imports without edits.
for _p in (os.environ.get('DMIPY_SIM_PUBLIC'),
           os.environ.get('DMIPY_FIT_PUBLIC')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

HERE = os.path.dirname(os.path.abspath(__file__))
# --outdir redirects WRITES (figure + regenerated data) so reproducers don't dirty the repo;
# committed inputs are always read from HERE. Default keeps the in-place paper-build behaviour.
OUTDIR = HERE
if '--outdir' in sys.argv:
    OUTDIR = os.path.abspath(sys.argv[sys.argv.index('--outdir') + 1])
    os.makedirs(OUTDIR, exist_ok=True)
NPZ = os.path.join(HERE, 'fig_mwf_sv_bias_data.npz')          # committed input (reads)
OUT_NPZ = os.path.join(OUTDIR, 'fig_mwf_sv_bias_data.npz')   # regenerated data (writes)
# This script COMPUTES the wall-counting (Panel-A) + forward MWF-vs-S/V + bias-vs-rho
# + noise-decomposition data (-> NPZ above), and PLOTS the "MWF consequence" figure
# (Fig 3): recovered MWF vs S/V (forward, clean) | recovered MWF vs S/V (engine, with
# Rician noise -- read from fig_cpmg_mwf_engine_data.npz) | the |bias| vs rho bound.
# The wall-counting it computes is plotted by fig_cpmg_mwf_engine.py (Fig 2, signal).
PDF = os.path.join(OUTDIR, 'fig_mwf_bias.pdf')
ENG_NPZ = os.path.join(HERE, 'fig_cpmg_mwf_engine_data.npz')   # engine MWF+noise (Panel B)
CACHE = os.path.join(HERE, '_mwf_cache')

# ── canonical constants: read from the dmipy_sim biophysical-constants catalogue
#    (single source of truth; cannot drift from the sim substrate) ─────────────
from dmipy_sim.substrate.biophysical_constants import canonical_white_matter as _cwm
from dmipy_sim.substrate.substrate import Substrate as _Substrate
_C = _cwm(3.0)
RHO_REF = _C['rho2']         # m/s, cited axon-wall transverse surface relaxivity (catalogue)
G0 = _C['g_ratio']           # canonical g-ratio (catalogue)
F0 = 0.55                    # packing (fibre volume fraction): operating-point choice
MVF = F0 * (1.0 - G0 ** 2)   # myelin volume fraction (held FIXED)
W_M = _Substrate().myelin_water_proton_density   # myelin water content by volume (West 2018, catalogue; renamed from myelin_aqueous_fraction)
SCALE_CAT = _C['gamma_scale_diameter']       # OUTER (fibre) diameter Gamma scale (catalogue)

# ── standard MWF CPMG protocol (Prasloski-style) ──────────────────────────────
N_ECHOES, TE_ECHO = 32, 10e-3
ET = np.arange(1, N_ECHOES + 1) * TE_ECHO
T2_MYELIN = 12e-3            # myelin water T2
T2_BULK_IE = 75e-3          # intrinsic (surface-free) IE bulk T2 -- a MATERIAL constant

# ── Monte Carlo (Panel A): public gradient-free forward walks across TE ──────
# One walk per echo time on the canonical OUTER-convention packed substrate; the
# per-compartment surface attenuation is read from the ensemble surface weight.
# The public engine sub-steps surface relaxivity to the extra-axonal pore scale automatically
# (dmipy_sim.physics.surface_sub_steps), so a modest outer step converges the boundary local
# time for BOTH walls -- no manual fine-step tuning needed.
N_WALK_A, N_CYL_A, N_T_A = 10_000, 400, 128
TES_A = np.array([20., 30., 40., 50., 60., 70., 80.]) * 1e-3
SCALE_A = SCALE_CAT       # canonical OUTER (fibre) gamma-diameter scale (catalogue)
MIN_DOUT_A = 0.4e-6       # floor the pathological Gamma thin tail


# ════════════════════════════════════════════════════════════════════════════
#  Panel A -- Monte Carlo proof that the surface attenuation is rho*(S/V),
#  by wall counting, at the canonical substrate (impermeable myelin so the
#  intra/extra compartments are not contaminated by exchange into the 10 ms
#  myelin pool; surface relaxivity is the only wall effect).
# ════════════════════════════════════════════════════════════════════════════
def compute_panelA(fresh=False):
    # PUBLIC forward Monte Carlo (no private replay master).  Build the canonical
    # OUTER-convention packed myelinated substrate, walk it gradient-free (G=0) with
    # impermeable myelin (kappa=0) and T2 turned off, so the ONLY wall effect is
    # surface relaxivity; the per-compartment surface attenuation B(TE) is then the
    # ensemble surface weight <exp(log_w)> over that compartment's walkers.  One walk
    # per echo time; compartment split via return_compartments (0=intra,1=myelin,2=extra).
    from dmipy_sim import (pack_myelinated_cylinders, PackedMyelinatedCylinders,
                           simulate, pgse)
    from dmipy_sim.substrate.biophysical_constants import canonical_white_matter
    c = canonical_white_matter(3.0)
    ALPHA, D_MC = c['gamma_shape_diameter'], c['D_intra']
    T2i_bulk, T2e_bulk = c['T2_intra'], c['T2_extra']

    rng = np.random.default_rng(0)
    d_out = np.maximum(rng.gamma(ALPHA, SCALE_A, N_CYL_A), MIN_DOUT_A)
    r_in = G0 * d_out / 2.0
    inner, gr, cen = pack_myelinated_cylinders(
        inner_radii=r_in, g_ratios=np.full(N_CYL_A, G0), target_packing=F0, seed=0)
    cell = float(np.sqrt(np.pi * np.sum((inner / gr) ** 2) / F0))
    d_in = 2.0 * np.asarray(inner, float)
    outer = np.asarray(inner / gr, float)
    sv_in = float(np.sum(4.0 * d_in) / np.sum(d_in ** 2))                  # <4/d>_V (1/m)
    sv_ext = float(np.sum(2.0 * np.pi * outer) /
                   (cell ** 2 - np.sum(np.pi * outer ** 2)))               # S_ext/V (1/m)

    geom = PackedMyelinatedCylinders(
        inner_radii=inner, g_ratios=gr, centers=cen, cell_size=cell,
        N_max=len(inner) + 1, D_intra=D_MC, D_extra=D_MC, D_myelin=0.0,
        T2_intra=1e9, T2_extra=1e9, T2_myelin=1e9,      # T2 off -> isolate surface
        rho_inner=RHO_REF, rho_outer=RHO_REF, kappa_inner=0.0, kappa_outer=0.0)
    bvec = np.array([[0., 0., 1.]], dtype=np.float32)

    # PURE surface factor straight from the recorded wall-contact: B(TE) =
    # <exp(log_w)> over the compartment's walkers, where the engine has accumulated
    # log_w = (rho/D) * (boundary local time) by wall counting at G=0 (no gradient
    # phase, T2 off).  This isolates surface relaxivity cleanly -- unlike dividing a
    # surf-on signal by an assumed bulk T2, which conflates the separately
    # parametrised apparent/bulk T2 with the surface term.
    def walk_at(n_t):
        """Per-compartment surface attenuation B(TE) at a given (uniform) step count."""
        Bi, Be = [], []
        for te in TES_A:
            wf = pgse(delta=te / 2 - 1e-4, DELTA=te / 2, G_magnitude=0.0,
                      bvecs=bvec, n_t=n_t)
            sig, comp_o, comp_f, logw, phase = simulate(
                N_WALK_A, waveform=wf, geometry=geom, seed=0,
                return_walker_signals=True, return_compartments='final', require_gpu=False)
            w = np.exp(np.asarray(logw, float))
            ia, ea = np.asarray(comp_o) == 0, np.asarray(comp_o) == 2   # 0=intra, 2=extra
            Bi.append(float(w[ia].mean())); Be.append(float(w[ea].mean()))
        return np.array(Bi), np.array(Be)

    B_ia_mc, B_ea_mc = walk_at(N_T_A)          # engine sub-steps surface relaxivity -> converged
    # analytic surface factors over the SAME realised pack:
    #   interior (Brownstein-Tarr), area/spin-weighted over the inner diameters;
    #   exterior (Novikov-Burcaw long-time), single exterior S/V.
    B_ia_an = np.array([float(np.sum(d_in ** 2 * np.exp(-RHO_REF * (4.0 / d_in) * te))
                              / np.sum(d_in ** 2)) for te in TES_A])
    B_ea_an = np.exp(-RHO_REF * sv_ext * TES_A)
    print(f"[A] canonical mean_d={np.mean(d_in)*1e6:.3f}um  S/V_in={sv_in/1e6:.2f}"
          f"  S_ext/V={sv_ext/1e6:.2f}/um", flush=True)
    print(f"[A] @60ms  intra MC={100*(1-B_ia_mc[4]):.1f}% an={100*(1-B_ia_an[4]):.1f}%"
          f" | extra MC={100*(1-B_ea_mc[4]):.1f}% an={100*(1-B_ea_an[4]):.1f}%", flush=True)
    return dict(tesA=TES_A, B_ia_mc=np.array(B_ia_mc), B_ea_mc=np.array(B_ea_mc),
                B_ia_an=B_ia_an, B_ea_an=B_ea_an, sv_in_A=sv_in, sv_ext_A=sv_ext,
                rho_ref=RHO_REF, T2i_bulk=T2i_bulk, T2e_bulk=T2e_bulk)


# ════════════════════════════════════════════════════════════════════════════
#  Panels B/C -- the MWF consequence via the STANDARD pipeline (MC-validated rate)
#
#  THREE-pool forward model (fixed myelin volume), each pool a separate T2 so the
#  NNLS sees a realistic multi-component spectrum, NOT a single lumped IE exponential
#  (this also honours that the surface term over a distribution is multi-exponential):
#    - myelin water:  A_m = MVF*w_m,         T2 = T2_myelin (fixed)
#    - intra-axonal:  A_i = f_axon*g^2,      R = 1/T2_bulk + rho*<4/d>_V   (interior)
#    - extra-axonal:  A_e = 1 - f_axon,      R = 1/T2_bulk + rho*(S_ext/V) (exterior)
#  Surface-to-volume uses the AREA/SPIN-WEIGHTED moment consistent with the theory
#  and Panel A.  CONVENTION: the swept calibre d_mean is the OUTER (fibre) diameter
#  (histology/Aboitiz); the intra-axonal wall is the INNER diameter d_in = g*d_out.
#  Interior <4/d_in>_V = 4 alpha/((alpha+1) g d_out) (the outer-convention value is the
#  old inner-convention one divided by g); exterior S_ext/V = 4 f/((1-f)(alpha+1)(d_out/alpha))
#  is the public closed form (== Substrate.S_ext_over_V_EA), scaling as 1/d_out at fixed g,f.
# ════════════════════════════════════════════════════════════════════════════
ALPHA = 2.0                                  # Gamma diameter shape
A_I = F0 * G0 ** 2                            # intra-axonal water volume fraction
A_E = (1.0 - F0)                              # extra-axonal water volume fraction
A_M = MVF * W_M                               # myelin water (fixed myelin volume)
_SW = A_I + A_E + A_M
F_I, F_E, F_M = A_I / _SW, A_E / _SW, A_M / _SW   # signal fractions
TRUE_MWF = F_M                                # true myelin water fraction (held fixed)
MYELIN_CUTOFF = 0.025                         # standard myelin window upper bound (25 ms)
# T2 reconstruction grid: 240 log-spaced points (5 ms - 2 s).  NNLS returns a sparse
# spike train (<= rank(A) spikes regardless of grid), so the grid is numerical
# quadrature, not a resolution knob; it must be fine enough that the recovered MWF
# is grid-independent.  At 240 points the calibre sweep is converged and the
# discrete spike-hopping sawtooth (visible at the coarse 60-point grid) is gone.
T2_GRID_BC = np.logspace(np.log10(5e-3), np.log10(2.0), 240)


def _sv_interior(d_out):
    """Area/spin-weighted interior moment over the OUTER-diameter Gamma:
    <4/d_in>_V = 4 alpha / ((alpha+1) g d_out), with inner d_in = g*d_out (== old / g)."""
    return 4.0 * ALPHA / ((ALPHA + 1.0) * G0 * d_out)


def _sv_exterior(d_out):
    """Exterior S_ext/V closed form (== Substrate.S_ext_over_V_EA), 1/d_out at fixed g,f."""
    return 4.0 * F0 / ((1.0 - F0) * (ALPHA + 1.0) * (d_out / ALPHA))


# ── distributed intra-axonal spectrum ───────────────────────────────────────
# The mechanism lives in the DISTRIBUTION, not a lumped mean rate: an axon of OUTER
# (fibre) diameter d has inner (axon) diameter g*d and carries interior S/V = 4/(g*d),
# so intra water relaxes at R(d) = 1/T2_bulk + rho*(4/(g*d)).  The thinnest axons
# (inner g*d < d*) are pushed BELOW the myelin window and are genuinely counted as
# myelin -> fine WM reads myelin-RICHER.
_DQ = np.linspace(0.02e-6, 8e-6, 3000)          # OUTER (fibre) diameter quadrature


def _d_crit(rho):
    """Critical INNER diameter: intra T2 = 1/(1/T2_bulk + rho*4/d_in) = myelin cutoff."""
    return rho * 4.0 / (1.0 / MYELIN_CUTOFF - 1.0 / T2_BULK_IE)


def _intra_weights(d_mean):
    """Volume/spin-weighted Gamma OUTER-diameter density (number ~ d^(a-1), water ~ d^2).
    d_mean is the mean OUTER (fibre) diameter."""
    theta = d_mean / ALPHA
    w = _DQ ** (ALPHA - 1) * np.exp(-_DQ / theta) * _DQ ** 2
    return w / w.sum()


def _intra_decay(d_mean, rho):
    """Distributed intra decay: sum over the OUTER-diameter distribution of exp(-ET*R),
    with per-axon interior rate rho*4/(g*d_out) (inner = g*outer)."""
    w = _intra_weights(d_mean)
    Rk = 1.0 / T2_BULK_IE + rho * (4.0 / (G0 * _DQ))
    return (w[None, :] * np.exp(-ET[:, None] * Rk[None, :])).sum(1)


def _mwf_true(rho, d_mean):
    """Grid-free 'true' MWF = short-T2 signal fraction: myelin water + the intra
    water genuinely dragged below the window.  No NNLS, no reconstruction grid.
    d_mean is the mean OUTER (fibre) diameter; the wall is the inner g*d_out."""
    w = _intra_weights(d_mean)
    T2 = 1.0 / (1.0 / T2_BULK_IE + rho * 4.0 / (G0 * _DQ))
    phi = w[T2 < MYELIN_CUTOFF].sum()            # crossed intra fraction
    return F_M + F_I * phi


def _mwf_3pool(rho, d_mean, reg='x2', T2_grid=None):
    """Realistic pipeline: standard regularised-NNLS MWF on the fixed-myelin-volume
    3-pool decay with a DISTRIBUTED intra pool + exterior surface rate at d_mean."""
    from dmipy_fit.white_matter.mwf import t2_spectrum_mwf
    if T2_grid is None:
        T2_grid = T2_GRID_BC
    Si = _intra_decay(d_mean, rho)
    R_e = 1.0 / T2_BULK_IE + rho * _sv_exterior(d_mean)
    S = F_M * np.exp(-ET / T2_MYELIN) + F_I * Si + F_E * np.exp(-ET * R_e)
    return float(t2_spectrum_mwf(S, ET, T2_grid=T2_grid, cutoff=MYELIN_CUTOFF,
                                 reg=reg)[0])


def _crosscheck_sv():
    """Confirm the analytical closed forms match the public Substrate at canonical."""
    d_out = 0.608e-6
    svi, sve = _sv_interior(d_out) / 1e6, _sv_exterior(d_out) / 1e6
    print(f"[S/V xcheck] d_out=0.608um f={F0} g={G0}: interior {svi:.2f}/um "
          f"(Substrate 6.27), exterior {sve:.2f}/um (Substrate 5.36)")
    assert abs(svi - 6.27) / 6.27 < 0.02, f"interior S/V {svi:.3f} off > 2%"
    assert abs(sve - 5.36) / 5.36 < 0.02, f"exterior S/V {sve:.3f} off > 2%"


def compute_panelsBC():
    _crosscheck_sv()
    # physiological calibre axis (mean OUTER / fibre diameter).  The signal-weighted IE
    # apparent T2 (for display) uses the volume-weighted interior + exterior rates.
    d_um = np.linspace(0.45, 3.0, 34)
    d_m = d_um * 1e-6
    R_i = 1.0 / T2_BULK_IE + RHO_REF * _sv_interior(d_m)
    R_e = 1.0 / T2_BULK_IE + RHO_REF * _sv_exterior(d_m)
    R_ie = (F_I * R_i + F_E * R_e) / (F_I + F_E)       # signal-weighted IE rate
    T2_app = 1.0 / R_ie
    sv = _sv_interior(d_m)                              # interior S/V for x-axis

    # MECHANISM: fine axons' intra T2 is dragged toward (and, in the thin tail, below)
    # the myelin window; that sub-window water is counted as myelin -> fine WM reads
    # myelin-RICHER.  The robust core is grid-free (below-window fraction); the standard
    # NNLS pipeline is shown alongside (it amplifies, reconstruction-dependent).
    mwf_true = np.array([_mwf_true(RHO_REF, d) for d in d_m]) * 100     # analytic, grid-free
    mwf_nnls = np.array([_mwf_3pool(RHO_REF, d) for d in d_m]) * 100    # standard NNLS (240 pt)
    dcrit = _d_crit(RHO_REF)

    # Panel A mechanism: volume-weighted intra-axonal T2 density for fine vs large calibre
    t2_bins = np.logspace(np.log10(8e-3), np.log10(0.13), 90)
    mech = {}
    for tag, dm in (('fine', 0.6e-6), ('large', 2.0e-6)):
        w = _intra_weights(dm)
        T2 = 1.0 / (1.0 / T2_BULK_IE + RHO_REF * 4.0 / (G0 * _DQ))
        h, _ = np.histogram(T2, bins=t2_bins, weights=w * F_I)
        mech[tag] = h

    # Panel C bound: fine(0.6)-vs-large(2.0) MWF bias vs the poorly-known rho, in BOTH
    # measured-MWF (water fraction) and inferred-myelin-content (x 1/W_M) terms.
    rho_axis = np.linspace(0.0, 2.5e-6, 40)
    bias_true = np.array([(_mwf_true(r, 0.6e-6) - _mwf_true(r, 2.0e-6)) * 100
                          for r in rho_axis])            # positive: fine reads richer
    rho_nnls = rho_axis[::8]
    bias_nnls = np.array([(_mwf_3pool(r, 0.6e-6) - _mwf_3pool(r, 2.0e-6)) * 100
                          for r in rho_nnls])             # NNLS, coarser (slow); positive

    # per-voxel noise context (unchanged protocol): a single substrate's recovered MWF
    # scatters far more than the systematic, so the effect is a cohort-level term.
    from dmipy_fit.white_matter.mwf import t2_spectrum_mwf
    rng = np.random.default_rng(0)
    N_NOISE, SNR = 80, 150.0
    Si = _intra_decay(0.6e-6, RHO_REF)
    S_fine = (F_M * np.exp(-ET / T2_MYELIN) + F_I * Si
              + F_E * np.exp(-ET * (1.0 / T2_BULK_IE + RHO_REF * _sv_exterior(0.6e-6))))
    sigma = S_fine[0] / SNR
    m = np.empty(N_NOISE)
    for k in range(N_NOISE):
        Sn = np.sqrt((S_fine + sigma * rng.standard_normal(len(ET))) ** 2
                     + (sigma * rng.standard_normal(len(ET))) ** 2)
        m[k] = t2_spectrum_mwf(Sn, ET, T2_grid=T2_GRID_BC)[0] * 100
    noise_voxel_std = float(m.std())

    return dict(d_um=d_um, sv=sv, T2_app=T2_app, mwf_true=mwf_true, mwf_nnls=mwf_nnls,
                true_mwf=TRUE_MWF, d_crit_um=dcrit * 1e6,
                t2_bins=t2_bins, mech_fine=mech['fine'], mech_large=mech['large'],
                rho_axis=rho_axis, bias_true=bias_true, rho_nnls=rho_nnls, bias_nnls=bias_nnls,
                rho_ref=RHO_REF, rho_cap=2.5e-6, noise_voxel_std=noise_voxel_std,
                T2_bulk_ie=T2_BULK_IE, t2_myelin=T2_MYELIN, myelin_cutoff=MYELIN_CUTOFF,
                f_i=F_I, f_e=F_E, f_m=F_M, w_m=W_M, n_echoes=N_ECHOES, te_echo=TE_ECHO, mvf=MVF)


def compute(fresh_A=False):
    out = {}
    out.update(compute_panelsBC())
    out.update(compute_panelA(fresh=fresh_A))
    np.savez(OUT_NPZ, **out)
    print(f"saved {OUT_NPZ}")
    return dict(np.load(OUT_NPZ))


def compute_bc_only():
    """Recompute only the ANALYTICAL Panels B/C, keeping the cached MC Panel-A data."""
    out = dict(np.load(NPZ)) if os.path.exists(NPZ) else {}
    out.update(compute_panelsBC())
    np.savez(OUT_NPZ, **out)
    print(f"saved {OUT_NPZ} (B/C recomputed, Panel-A kept)")
    return dict(np.load(OUT_NPZ))


# ════════════════════════════════════════════════════════════════════════════
def plot(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                                "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                                "legend.fontsize": 10.5})

    C_TRUE, C_NNLS, C_MY = '#d95f0e', '#8c6bb1', '0.35'
    F_M100 = d['true_mwf'] * 100
    WM = float(d['w_m'])
    fig, ax = plt.subplots(1, 3, figsize=(15.0, 4.4))

    # A: MECHANISM -- fine-axon intra T2 distribution crosses the myelin window
    be = d['t2_bins'] * 1e3
    ax[0].axvspan(be[0], d['myelin_cutoff'] * 1e3, color='0.87', zorder=0)
    ax[0].axvline(d['t2_myelin'] * 1e3, color='k', ls='--', lw=1)
    ax[0].step(be[:-1], d['mech_large'], where='post', color='#1f77b4', lw=1.8,
               label='intra, large (2.0 $\\mu$m)')
    ax[0].step(be[:-1], d['mech_fine'], where='post', color=C_TRUE, lw=1.8,
               label='intra, fine (0.6 $\\mu$m)')
    ax[0].set_xscale('log')
    ax[0].text(d['t2_myelin'] * 1e3, ax[0].get_ylim()[1] * 0.97, ' myelin $T_2$',
               fontsize=8, va='top')
    ax[0].text(d['myelin_cutoff'] * 1e3 * 1.05, ax[0].get_ylim()[1] * 0.5,
               'myelin\nwindow', fontsize=7.5, color='0.4')
    ax[0].set_xlabel('$T_2$  (ms)'); ax[0].set_ylabel('intra signal density')
    ax[0].set_title('A  fine-axon intra $T_2$ crosses the myelin window')
    ax[0].legend(fontsize=8, loc='upper left')

    # B: MWF vs S/V -- true (grid-free short-T2 fraction) + standard NNLS; right axis
    # is the inferred excess-myelin content (bias x 1/W_M).  fine WM reads myelin-RICHER.
    sv = d['sv'] / 1e6                              # m^-1 -> um^-1 for display
    ax[1].axhline(F_M100, color=C_MY, ls=':', lw=1.4, label='true myelin volume ($F_M$)')
    ax[1].plot(sv, d['mwf_true'], '-', color=C_TRUE, lw=2.2,
               label='apparent MWF (short-$T_2$ fraction)')
    ax[1].plot(sv, d['mwf_nnls'], '--', color=C_NNLS, lw=1.6,
               label='standard NNLS (amplifies)')
    rp = os.path.join(HERE, 'real_substrates_data.npz')
    if os.path.exists(rp):
        sv_real = np.load(rp)['sv_in_um']
        y0 = ax[1].get_ylim()[0]
        ax[1].plot(sv_real, np.full_like(sv_real, y0), '|', color='#2ca02c', ms=12,
                   mew=1.6, zorder=6, clip_on=False, label=f'real rat WM $S/V$ (n={len(sv_real)})')
    ax[1].set_xlabel(r'intra $S/V$  ($\mu$m$^{-1}$)'); ax[1].set_ylabel('measured MWF  (%)')
    ax[1].set_title('B  fine WM reads myelin-richer')
    ax[1].legend(fontsize=7.3, loc='upper left'); ax[1].grid(alpha=0.25)
    sec = ax[1].secondary_yaxis('right', functions=(lambda y: (y - F_M100) / WM,
                                                    lambda z: z * WM + F_M100))
    sec.set_ylabel('inferred excess myelin ($\\times 1/W_M$)  (pp)', color=C_MY)

    # C: the rho bound -- fine(0.6)-vs-large(2.0) bias vs poorly-known rho; both the
    # measured-MWF (left) and inferred-myelin-content (right, x 1/W_M) readings.
    ax[2].plot(d['rho_axis'] * 1e6, d['bias_true'], '-', color=C_TRUE, lw=2.2,
               label='true (short-$T_2$ fraction)')
    ax[2].plot(d['rho_nnls'] * 1e6, d['bias_nnls'], 's', color=C_NNLS, ms=4,
               label='standard NNLS')
    ax[2].axvline(d['rho_ref'] * 1e6, color='0.5', ls=':', lw=1)
    ax[2].text(d['rho_ref'] * 1e6 * 1.04, ax[2].get_ylim()[1] * 0.9, 'cited $\\rho$',
               fontsize=8, color='0.4')
    ax[2].set_xlabel(r'surface relaxivity $\rho$  ($\mu$m/s)')
    ax[2].set_ylabel('fine$-$large MWF bias  (pp)')
    ax[2].set_title('C  bias vs the poorly-known $\\rho$')
    ax[2].legend(fontsize=7.5, loc='upper left'); ax[2].grid(alpha=0.25)
    sec2 = ax[2].secondary_yaxis('right', functions=(lambda y: y / WM, lambda z: z * WM))
    sec2.set_ylabel('inferred excess myelin ($\\times 1/W_M$)  (pp)', color=C_MY)

    fig.tight_layout()
    fig.savefig(PDF, bbox_inches='tight')
    fig.savefig(PDF.replace('.pdf', '.png'), dpi=140, bbox_inches='tight')
    print(f"saved {PDF}")
    bt_cited = float(np.interp(d['rho_ref'] * 1e6, d['rho_axis'] * 1e6, d['bias_true']))
    print(f"true MWF F_M = {F_M100:.2f}%   d* (cited rho) = {d['d_crit_um']:.3f} um")
    print(f"[B] IE apparent T2 {d['T2_app'].max()*1e3:.1f}->{d['T2_app'].min()*1e3:.1f} ms; "
          f"MWF true {d['mwf_true'].min():.2f}->{d['mwf_true'].max():.2f}% (fine richer), "
          f"NNLS {d['mwf_nnls'].min():.2f}->{d['mwf_nnls'].max():.2f}%")
    print(f"[C] fine-large bias (true): cited rho {bt_cited:+.3f} pp -> myelin {bt_cited/WM:+.3f} pp; "
          f"upper rho {d['bias_true'][-1]:+.3f} pp -> myelin {d['bias_true'][-1]/WM:+.3f} pp")
    print(f"[noise] per-voxel MWF sd @SNR150 = {d['noise_voxel_std']:.2f} pp "
          f"(>> the {bt_cited:.2f} pp systematic)")


if __name__ == '__main__':
    if '--plot-only' in sys.argv:
        d = dict(np.load(NPZ))
    elif '--bc-only' in sys.argv:
        d = compute_bc_only()
    elif '--panelA-only' in sys.argv:
        a = compute_panelA(fresh='--fresh' in sys.argv)
        out = dict(np.load(NPZ)) if os.path.exists(NPZ) else {}
        out.update(a)                       # merge Panel A into the NPZ, keeping B/C
        np.savez(OUT_NPZ, **out)
        print(f"saved {OUT_NPZ} (Panel A updated, B/C kept)")
        sys.exit(0)
    else:
        d = compute(fresh_A='--fresh' in sys.argv)
    plot(d)
