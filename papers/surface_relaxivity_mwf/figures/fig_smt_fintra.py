"""fig_smt_fintra.py -- firm up the lead: a REAL SMT fit returns the surface-biased
f_intra, and injecting a histology prior corrects it (single-TE), on PUBLIC engines.

Forward (dmipy-fit public analytical WM model): dense white matter, surface relaxivity ON,
multi-shell dMRI at several echo times -> the differential compartment T2 reweights the
2-compartment (myelin gone) signal. Inverse: the standard Kaden spherical-mean technique
(C1Stick + G2Zeppelin) recovers f_intra. Because the surface T2 factor is b-INDEPENDENT it
propagates through the whole multi-shell fit, so the recovered f_intra IS the surface-biased
signal weight and DRIFTS with TE. Injecting the region's histology prior (gamma calibre + rho
-> rho*(S/V)_int, rho*(S/V)_ext) de-biases it at a SINGLE TE: f_intra/(1-f_intra) is rescaled
by exp(+TE*rho*((S/V)_int-(S/V)_ext)). This harmonizes a cohort scanned at different TEs.

Run: python fig_smt_fintra.py
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                            "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                            "legend.fontsize": 10.5})

for _p in (os.environ.get('DMIPY_SIM_PUBLIC'),
           os.environ.get('DMIPY_FIT_PUBLIC')):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
HERE = os.path.dirname(os.path.abspath(__file__))

from dmipy_fit.core.modeling_framework import MultiCompartmentSphericalMeanModel
from dmipy_fit.core.acquisition_scheme import acquisition_scheme_from_bvalues
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.signal_models.gaussian_models import G2Zeppelin
from dmipy_fit.white_matter import composition as comp
from dmipy_fit.white_matter.surface import exterior_surface_to_volume, mean_inv_diameter_4
from dmipy_sim.substrate.biophysical_constants import canonical_white_matter

c = canonical_white_matter(3.0)
ALPHA, BETA_OUT, G = c['gamma_shape_diameter'], c['gamma_scale_diameter'], c['g_ratio']
RHO = c['rho2']
VF = 0.68                                    # dense WM (above crossover VF*=1/(1+g)=0.588)
TES = np.array([50., 60., 70., 80., 90.]) * 1e-3   # both compartments survive across this range

# injected histology prior -> the two surface rates (interior uses inner = g*outer)
SV_INT = mean_inv_diameter_4(ALPHA, G * BETA_OUT, volume_weighted=True)   # 1/m
SV_EXT = exterior_surface_to_volume(VF, ALPHA, BETA_OUT)                  # 1/m
print(f"prior: S/V_int={SV_INT/1e6:.2f} S/V_ext={SV_EXT/1e6:.2f} /um  rho*dSV={RHO*(SV_INT-SV_EXT):.2f}/s")

rng = np.random.default_rng(0)
def dirs(n):
    v = rng.standard_normal((n, 3)); return v / np.linalg.norm(v, axis=1, keepdims=True)
bsh = np.array([1., 2., 3.]) * 1e9; nd = 90
bvals = np.concatenate([[0.] * 8] + [[b] * nd for b in bsh])
bvecs = np.concatenate([dirs(8)] + [dirs(nd) for _ in bsh])

def forward(TE, rho):
    m, p = comp.build_white_matter_model(rho2=rho, f_axon=VF, g_ratio=G,
        gamma_shape=ALPHA, gamma_scale_outer_diameter=BETA_OUT)
    sch = acquisition_scheme_from_bvalues(bvals, bvecs, 0.012, 0.040, TE=np.full(bvals.shape, TE))
    return m.simulate_signal(sch, p), sch

D_PAR = 1.7e-9
LAM_PERP = D_PAR * (1.0 - G ** 2 * VF)             # tortuosity (NODDI lambda_par*(1-v_ic))
def blind_smt(data, sch):
    # standard SMT with the compartment diffusivities FIXED to their (known) values, so the
    # only free parameter is the fraction -- the fit then returns the signal weight w_intra
    # cleanly (free-diffusivity brute2fine is degenerate on this heavily T2-reweighted signal).
    smt = MultiCompartmentSphericalMeanModel(models=[C1Stick(), G2Zeppelin()])
    smt.set_fixed_parameter('C1Stick_1_lambda_par', D_PAR)
    smt.set_fixed_parameter('G2Zeppelin_1_lambda_par', D_PAR)
    smt.set_fixed_parameter('G2Zeppelin_1_lambda_perp', LAM_PERP)
    return float(np.ravel(smt.fit(sch, data[None], solver='brute2fine')
                          .fitted_parameters['partial_volume_0'])[0])

def correct(f_app, TE):                       # inject prior: undo the odds rescaling
    odds = f_app / (1 - f_app) * np.exp(+TE * RHO * (SV_INT - SV_EXT))
    return odds / (1 + odds)

# Isolate the SURFACE effect from the SMT model-mismatch: at each TE fit the SAME blind SMT
# to surface-ON and surface-OFF forwards. surface-OFF is TE-independent (shared T2 cancels in
# the b=0 normalisation) and defines this fitter's unbiased fraction; the ON-OFF gap is the
# pure surface bias, and applies the prior correction to the ON estimate.
f_on, f_off, f_corr = [], [], []
for TE in TES:
    d_on, sch = forward(TE, RHO); d_off, _ = forward(TE, 0.0)
    fon = blind_smt(d_on, sch); foff = blind_smt(d_off, sch)
    f_on.append(fon); f_off.append(foff); f_corr.append(correct(fon, TE))
f_on, f_off, f_corr = np.array(f_on), np.array(f_off), np.array(f_corr)
f_true = float(f_off.mean())                  # TE-independent surface-free fraction
print(f"true f_intra (surface off, TE-indep) = {f_true:.4f} (spread {f_off.std():.4f})")
for i, TE in enumerate(TES):
    print(f"  TE={TE*1e3:3.0f}ms  ON {f_on[i]:.4f} ({100*(f_on[i]-f_off[i])/f_off[i]:+.1f}% surface)  "
          f"prior-corrected {f_corr[i]:.4f} (resid {100*(f_corr[i]-f_off[i])/f_off[i]:+.1f}%)")
f_blind = f_on

# ---- figure ----
fig, ax = plt.subplots(1, 2, figsize=(10.0, 4.2))
teg = TES * 1e3
ax[0].axhline(f_true, color='0.5', ls='--', lw=1.6, label='true $f_{\\rm intra}$ (surface-free)')
ax[0].plot(teg, f_blind, 'o-', color='#d95f0e', lw=2.2, ms=6, label='standard SMT (surface-blind)')
ax[0].plot(teg, f_corr, 's-', color='#1f77b4', lw=2.2, ms=6, label='prior-injected (surface-aware)')
ax[0].set_xlabel('echo time TE (ms)'); ax[0].set_ylabel(r'recovered $f_{\rm intra}$')
ax[0].set_title(f'A  SMT $f_{{\\rm intra}}$ vs TE (dense WM, VF={VF})')
ax[0].legend(fontsize=8, loc='center right'); ax[0].grid(alpha=0.25)

# B: the cohort story -- healthy controls scanned at different TE (bias vs the fitter's own
# surface-free fraction, isolating the surface term from SMT model-mismatch)
biasb = 100 * (f_blind - f_off) / f_off
biasc = 100 * (f_corr - f_off) / f_off
ax[1].axhline(0, color='0.6', lw=1)
ax[1].plot(teg, biasb, 'o-', color='#d95f0e', lw=2.2, ms=6, label='surface-blind')
ax[1].plot(teg, biasc, 's-', color='#1f77b4', lw=2.2, ms=6, label='prior-injected')
ax[1].fill_between(teg, biasb, biasc, color='0.85', zorder=0)
ax[1].set_xlabel('echo time TE (ms)'); ax[1].set_ylabel(r'$f_{\rm intra}$ relative bias (%)')
ax[1].set_title('B  same tissue, different TE:\nspurious spread removed by the prior')
ax[1].annotate(f'blind spread {biasb.min():.0f} to {biasb.max():.0f}%\nacross a routine TE range',
               xy=(teg[-1], biasb[-1]), xytext=(0.05, 0.85), textcoords='axes fraction',
               fontsize=8, color='#d95f0e', va='top')
ax[1].legend(fontsize=8, loc='lower right'); ax[1].grid(alpha=0.25)
fig.tight_layout()
out = os.path.join(HERE, "fig_smt_fintra.pdf")
fig.savefig(out, bbox_inches='tight'); fig.savefig(out.replace('.pdf', '.png'), dpi=140, bbox_inches='tight')
print("saved", out)
