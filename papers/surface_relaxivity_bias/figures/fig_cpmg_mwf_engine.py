#!/usr/bin/env python
"""fig_cpmg_mwf_engine.py -- the MWF bias from the ENGINE, not a forward model.

Fig 2 fed the MC-validated surface RATE into an analytical 3-pool decay and ran
NNLS on that. This figure instead simulates the full multi-echo CPMG signal with the
Monte Carlo (the master walk's per-compartment relaxation + first-principles wall
relaxivity), with and without surface relaxivity, on substrates of different calibre,
adds realistic Rician noise, and runs the SAME standard NNLS myelin-water estimator
on the genuinely simulated signal. It complements/lifts Fig 2 by removing the
forward-model hand-roll: the bias is now read off engine-simulated decays.

Causal setup (the physical one): the intrinsic BULK T2 is a fixed material constant;
surface relaxivity adds rho*(S/V) at the actual walls, so the IE apparent T2 -- and
the recovered MWF -- vary with calibre even though bulk T2 and myelin volume are
fixed. We realise this by setting the (settable) apparent T2 so the derived bulk T2
equals T2FIX, then letting the simulator's wall relaxivity produce the apparent decay.

Panels:
  A. Engine-simulated multi-echo decay S(TE_n) for small vs large calibre, surface
     on vs off (one noise-free realisation) -- surface speeds the IE decay.
  B. NNLS T2 spectra (one SNR-=cap realisation) -- the myelin (short-T2) and IE
     (long-T2) pools, and how surface shifts the IE pool toward the window.
  C. Recovered MWF vs calibre, surface on vs off, Rician noise (mean +/- s.d.),
     at fixed bulk T2 and fixed myelin volume -- the engine MWF bias.

Run (GPU; public forward MC, one gradient-free walk per echo time, cached):
     python fig_cpmg_mwf_engine.py
     python fig_cpmg_mwf_engine.py --plot-only

Engine: PUBLIC dmipy-sim ORDINARY forward Monte Carlo (no private replay master).
An OUTER-diameter-convention packed myelinated substrate is walked gradient-free
(G=0) with per-compartment bulk T2 + first-principles wall relaxivity; the CPMG
decay S(TE_n) is read off as the ensemble signal exp(<log_w>) at each echo time
(at G=0 the CPMG sign flips carry no phase, so the decay is the pure T2 + surface
weight).  SCALES are now OUTER (fibre) gamma diameter scales.
"""
import os, sys
import numpy as np

os.environ.setdefault('XLA_PYTHON_CLIENT_PREALLOCATE', 'false')
for _p in (os.environ.get('DMIPY_SIM_PUBLIC'),
           os.environ.get('DMIPY_FIT_PUBLIC')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ = os.path.join(HERE, 'fig_cpmg_mwf_engine_data.npz')
# This script COMPUTES the engine decay / T2 spectra / noisy-MWF data (-> NPZ above),
# and PLOTS the "signal & T2" figure (Fig 2): wall-counting surface attenuation (read
# from the sibling fig_mwf_sv_bias_data.npz) + engine CPMG decay + recovered T2
# spectra.  The noisy engine MWF-vs-S/V it computes is plotted by fig_mwf_sv_bias.py
# (Fig 3, the MWF-consequence figure).  Figure groupings deliberately cross the two
# compute scripts; the committed npz files are the hand-off.
PDF = os.path.join(HERE, 'fig_signal.pdf')
SIB_NPZ = os.path.join(HERE, 'fig_mwf_sv_bias_data.npz')   # wall-counting (Panel A)

N_ECHOES, TE_ECHO = 32, 10e-3
ET = np.arange(1, N_ECHOES + 1) * TE_ECHO
T2_FIX = 0.075                      # fixed intrinsic (surface-free) bulk T2 of intra+extra
SCALES = [0.304e-6, 0.50e-6, 0.75e-6, 1.00e-6]   # OUTER (fibre) gamma-diameter scales
SNR, N_NOISE = 200, 150

# ── public-MC controls (OUTER convention) ────────────────────────────────────
N_CYL = 300                         # fibres in the packed cell
N_WALK = 60_000                     # walkers per gradient-free walk
N_T = 8_000                         # timesteps per walk (fixed -> JIT reused across echoes)
MIN_DOUT = 0.4e-6                   # floor the pathological Gamma thin tail
F_AXON, G_RATIO, SEED = 0.55, 0.70, 0

# canonical constants from the catalogue (do NOT hardcode)
from dmipy_sim.substrate.biophysical_constants import canonical_white_matter
_C = canonical_white_matter(3.0)
ALPHA, RHO, D_MC, T2_MYELIN = (_C['gamma_shape_diameter'], _C['rho2'],
                               _C['D_intra'], _C['T2_myelin'])


def _build_geom(scale, surf):
    """OUTER-convention packed myelinated substrate.  Bulk T2 fixed at T2_FIX for
    intra+extra (surface adds on top via wall relaxivity); myelin at catalogue T2.
    surf toggles the wall relaxivity rho (surface off -> rho=0)."""
    from dmipy_sim import pack_myelinated_cylinders, PackedMyelinatedCylinders
    rng = np.random.default_rng(SEED)
    d_out = np.maximum(rng.gamma(ALPHA, scale, N_CYL), MIN_DOUT)
    r_in = G_RATIO * d_out / 2.0
    inner, gr, cen = pack_myelinated_cylinders(
        inner_radii=r_in, g_ratios=np.full(N_CYL, G_RATIO),
        target_packing=F_AXON, seed=SEED)
    cell = float(np.sqrt(np.pi * np.sum((inner / gr) ** 2) / F_AXON))
    rho = RHO if surf else 0.0
    geom = PackedMyelinatedCylinders(
        inner_radii=inner, g_ratios=gr, centers=cen, cell_size=cell,
        N_max=len(inner) + 1, D_intra=D_MC, D_extra=D_MC, D_myelin=0.0,
        T2_intra=T2_FIX, T2_extra=T2_FIX, T2_myelin=T2_MYELIN,
        rho_inner=rho, rho_outer=rho, kappa_inner=0.0, kappa_outer=0.0)
    d_in = 2.0 * np.asarray(inner, float)
    sv_in = float(np.sum(4.0 * d_in) / np.sum(d_in ** 2))       # <4/d>_V
    return geom, float(d_in.mean() * 1e6), sv_in / 1e6


def _sim(scale, surf, fresh=False):
    """Engine-simulated b=0 CPMG decay for one calibre (public forward MC): one
    gradient-free walk per echo time, ensemble signal = mean_w exp(log_w).  Bulk T2
    fixed, surface relaxivity on/off.  Returns (S(TE_n), mean inner d um, S/V_in)."""
    from dmipy_sim import simulate, pgse
    geom, dm, sv = _build_geom(scale, surf)
    # Surface sub-stepping at pore/2 (coarser than Fig 2A's pore/8): resolving the full
    # pore/8 over the whole 320ms CPMG train is ~10x this; pore/2 already matches the
    # brute-force accuracy (~0.3-0.6pp on the extra factor, negligible for the decay) at a
    # tractable one-off cost (~2-3h GPU). The surface RATE is validated at full resolution in Fig 2A.
    geom.surface_substep_frac = 2.0
    bvec = np.array([[0., 0., 1.]], dtype=np.float32)
    S = np.empty(N_ECHOES, dtype=float)
    # Fixed n_t across echoes: the (1, N_T, 3) waveform SHAPE is constant so the
    # JITted walk compiles ONCE and is reused for every echo time (only dt scales),
    # avoiding a per-echo recompile.  N_T resolves the mean inner radius at the
    # longest echo (surface attenuation at G=0 is robust to step size).
    for k, te in enumerate(ET):
        wf = pgse(delta=te / 2 - 1e-4, DELTA=te / 2, G_magnitude=0.0,
                  bvecs=bvec, n_t=N_T)
        # G=0 -> phi==0 -> ensemble signal = mean_w exp(log_w) (pure T2 + surface)
        sig = simulate(N_WALK, waveform=wf, geometry=geom, seed=SEED,
                       require_gpu=False)
        S[k] = float(np.asarray(sig).ravel()[0])
    return S, dm, sv


def _mwf_noisy(S, rng):
    """Standard NNLS MWF on Rician-noised copies of the engine signal."""
    from dmipy_fit.white_matter.mwf import t2_spectrum_mwf
    sigma = S[0] / SNR
    out = []
    for _ in range(N_NOISE):
        n1 = rng.standard_normal(len(ET)); n2 = rng.standard_normal(len(ET))
        Sn = np.sqrt((S + sigma * n1) ** 2 + (sigma * n2) ** 2)
        out.append(t2_spectrum_mwf(Sn / Sn[0], ET)[0])
    return np.array(out) * 100


def compute(fresh=False):
    rng = np.random.default_rng(0)
    out = {'et': ET, 'scales_um': []}
    mwf_on, mwf_off, sd_on, sd_off, svs, dmean = [], [], [], [], [], []
    # surface OFF: bulk T2 fixed + no wall relaxivity -> calibre-INDEPENDENT
    # (pool volume fractions are set by g_ratio + f_axon, not the calibre scale),
    # so simulate one representative off decay and reuse it for every calibre.
    Soff0, _, _ = _sim(SCALES[0], False, fresh)
    for sc in SCALES:
        Son, dm, sv = _sim(sc, True, fresh)
        Soff = Soff0
        moff = _mwf_noisy(Soff, rng); mon = _mwf_noisy(Son, rng)
        out[f'Soff_{sc:.0e}'] = Soff; out[f'Son_{sc:.0e}'] = Son
        mwf_off.append(moff.mean()); sd_off.append(moff.std())
        mwf_on.append(mon.mean()); sd_on.append(mon.std())
        svs.append(sv); dmean.append(dm); out['scales_um'].append(dm)
        print(f"d={dm:.2f}um S/V={sv:.2f}/um  MWF off={moff.mean():.1f}+/-{moff.std():.1f}  "
              f"on={mon.mean():.1f}+/-{mon.std():.1f}  (drift {mon.mean()-moff.mean():+.1f}pp)",
              flush=True)
    out.update(dict(dmean=np.array(dmean), sv_in=np.array(svs),
                    mwf_on=np.array(mwf_on), mwf_off=np.array(mwf_off),
                    sd_on=np.array(sd_on), sd_off=np.array(sd_off),
                    scales=np.array(SCALES), snr=SNR, t2fix=T2_FIX))
    np.savez(NPZ, **out)
    print(f"saved {NPZ}")
    return dict(np.load(NPZ, allow_pickle=True))


def plot(d):
    """Fig 2 -- "surface relaxivity enters the signal and the apparent T2":
    A wall-counting MC vs analytic surface attenuation (from fig_mwf_sv_bias_data.npz)
    | B engine CPMG decay (surface on/off) | C recovered T2 spectra (stacked)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                                "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                                "legend.fontsize": 10.5})
    from dmipy_fit.white_matter.mwf import t2_spectrum_mwf
    et = d['et']; sc = d['scales']
    C_SMALL, C_LARGE, C_OFF = '#2c7fb8', '#d95f0e', '0.35'
    CIA, CEA = '#2c7fb8', '#d95f0e'
    fig = plt.figure(figsize=(15.5, 4.6))
    # 3 visual columns; the third (T2 spectra) is two thin vertically-stacked panels.
    gs = fig.add_gridspec(2, 3, width_ratios=[1.08, 1.05, 1.0],
                          wspace=0.34, hspace=0.5)
    axA = fig.add_subplot(gs[:, 0])
    axB = fig.add_subplot(gs[:, 1])
    axCt = fig.add_subplot(gs[0, 2]); axCb = fig.add_subplot(gs[1, 2])

    # --- A: wall-counting surface attenuation vs TE on the analytic BT/NB lines
    # (read from the sibling Panel-A data; the MC walk is owned by fig_mwf_sv_bias.py).
    w = np.load(SIB_NPZ, allow_pickle=True)
    te = w['tesA'] * 1e3
    rm = lambda B: 100 * (1 - np.asarray(B))
    # closed-form lines (interior BT, exterior NB) with the wall-counting MC markers on top.
    axA.plot(te, rm(w['B_ia_an']), '-', color=CIA, lw=1.8)
    axA.plot(te, rm(w['B_ia_mc']), 'o', color=CIA, ms=7, mfc='white', mew=1.6)
    axA.plot(te, rm(w['B_ea_an']), '-', color=CEA, lw=1.8)
    axA.plot(te, rm(w['B_ea_mc']), 's', color=CEA, ms=7, mfc='white', mew=1.6)
    axA.plot([], [], 'o', color=CIA, mfc='white', mew=1.6,
             label='intra (interior, Brownstein--Tarr)')
    axA.plot([], [], 's', color=CEA, mfc='white', mew=1.6,
             label='extra (exterior, Novikov--Burcaw)')
    axA.plot([], [], '-', color='0.4', lw=1.8, label='closed form $\\rho\\,(S/V)$')
    axA.set_xlabel('echo time TE (ms)')
    axA.set_ylabel('compartment signal removed by surface (%)')
    axA.set_title('A  wall counting reproduces $\\rho\\,(S/V)$')
    axA.legend(fontsize=8, loc='upper left'); axA.grid(alpha=0.25)

    # --- B: engine CPMG decay.  Surface OFF is calibre-independent (bulk T2 fixed),
    # so the small/large "off" decays coincide -> single bulk-only reference.
    Soff = d[f'Soff_{sc[0]:.0e}']
    axB.semilogy(et * 1e3, Soff / Soff[0], '--', color=C_OFF, lw=1.8,
                 label='surface off (bulk only,\nboth calibres)')
    for scv, c, nm in [(sc[0], C_SMALL, 'small'), (sc[-1], C_LARGE, 'large')]:
        Son = d[f'Son_{scv:.0e}']
        axB.semilogy(et * 1e3, Son / Son[0], '-', color=c, lw=2, label=f'{nm}, surface on')
    axB.set_xlabel('echo time (ms)'); axB.set_ylabel('signal (norm., log scale)')
    axB.set_title('B  engine CPMG decay')
    axB.legend(fontsize=7.5); axB.grid(alpha=0.25, which='both')

    # --- C (stacked): on-vs-off T2 spectra, one calibre per panel.
    T2g = np.logspace(np.log10(5e-3), np.log10(2.0), 60)

    def _spec(key):
        S = d[key]; return t2_spectrum_mwf(S / S[0], et, T2_grid=T2g)[2]
    for axc, scv, c, tag in [(axCt, sc[0], C_SMALL, 'small'),
                             (axCb, sc[-1], C_LARGE, 'large')]:
        axc.semilogx(T2g * 1e3, _spec(f'Son_{scv:.0e}'), '-', color=c, lw=1.8,
                     label=f'{tag}, surface on')
        axc.semilogx(T2g * 1e3, _spec(f'Soff_{scv:.0e}'), '--', color=c, lw=1.6,
                     label=f'{tag}, surface off')
        axc.axvline(25, color='0.5', ls=':', lw=1)
        axc.set_ylabel('NNLS ampl.'); axc.legend(fontsize=7, loc='upper left')
        axc.grid(alpha=0.25)
    axCt.set_title('C  recovered $T_2$ spectra')
    axCt.text(26, axCt.get_ylim()[1] * 0.62, 'myelin\nwindow', fontsize=6.5, color='0.4')
    axCt.tick_params(labelbottom=False)
    axCb.set_xlabel(r'$T_2$ (ms)')
    fig.savefig(PDF, bbox_inches='tight')
    fig.savefig(PDF.replace('.pdf', '.png'), dpi=140, bbox_inches='tight')
    print(f"saved {PDF}")


if __name__ == '__main__':
    d = dict(np.load(NPZ, allow_pickle=True)) if '--plot-only' in sys.argv else compute('--fresh' in sys.argv)
    plot(d)
