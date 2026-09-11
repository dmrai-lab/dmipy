"""Generate the Monte-Carlo reference for the canonical-WM parity flagship.

Runs the step-resolved dmipy-sim forward on the canonical packed-myelin substrate and caches
the signals to ``flagship_mc_reference.npz``. GPU recommended (fine steps). The flagship MyST
page recomputes the *analytical* signal live (fast, CPU) and asserts parity against this cache
-- the same pattern dmipy-fit uses for its Monte-Carlo ground truth. Re-run to regenerate.

Run:  python generate_mc_reference.py
"""
import os
import numpy as np
from dmipy_sim.substrate.biophysical_constants import canonical_white_matter
from dmipy_fit.white_matter import composition as comp
from dmipy_sim import pack_myelinated_cylinders, PackedMyelinatedCylinders, simulate, pgse

HERE = os.path.dirname(os.path.abspath(__file__))
C = canonical_white_matter(3.0); D = C['D_intra']; G = C['g_ratio']; RHO = C['rho2']
T2I, T2E, T2M = C['T2_intra'], C['T2_extra'], C['T2_myelin']
AL = comp.DEFAULTS['gamma_shape']; SC = comp.DEFAULTS['gamma_scale_outer_diameter']; FA = comp.DEFAULTS['f_axon']
N_CYL, N_WALK = 40, 5000


def geom(surf, seed=0):
    rng = np.random.default_rng(seed); d_out = np.maximum(rng.gamma(AL, SC, N_CYL), 0.4e-6)
    inner, gr, cen = pack_myelinated_cylinders(inner_radii=G * d_out / 2,
        g_ratios=np.full(N_CYL, G), target_packing=FA, seed=seed)
    cell = float(np.sqrt(np.pi * np.sum((inner / gr) ** 2) / FA))
    return PackedMyelinatedCylinders(inner_radii=inner, g_ratios=gr, centers=cen, cell_size=cell,
        N_max=len(inner) + 1, D_intra=D, D_extra=D, D_myelin=0.0,
        T2_intra=T2I, T2_extra=T2E, T2_myelin=T2M,
        rho_inner=(RHO if surf else 0.0), rho_outer=(RHO if surf else 0.0),
        kappa_inner=0.0, kappa_outer=0.0)


# diffusion scheme (surface off), step-resolved
bvals = np.r_[0., 1e9, 2e9, 1e9, 2e9]
bvecs = np.array([[1, 0, 0], [0, 0, 1], [0, 0, 1], [1, 0, 0], [1, 0, 0]], np.float32)  # ∥z twice, ⊥
delta, DELTA = 0.015, 0.025
step = (0.4e-6 * G / 2) / 3.0                                     # resolve smallest inner fibre
n_t = int(np.ceil((delta + DELTA) / (step ** 2 / (6 * D))))
wf = pgse(bvecs, delta, DELTA, bvalues=bvals, TE=TE, n_t=n_t, slew_rate=np.inf)   # the object the fit reads
TE = float(wf.dt * wf.G.shape[1])
S_mc_diff = np.asarray(simulate(N_WALK, waveform=wf, geometry=geom(False), seed=1, require_gpu=False)).ravel()
print("diffusion MC:", np.round(S_mc_diff / S_mc_diff[0], 4), f"(n_t={n_t}, TE={TE*1e3:.1f}ms)")

# surface OFF/ON at b=0 (gradient-free)
wf0 = pgse([[0, 0, 1.]], TE / 2 - 1e-4, TE / 2, gradient_strengths=[0.0], TE=TE, n_t=3000)   # a bare spin echo at TE
S_mc_surf = {}
for surf in (False, True):
    g = geom(surf); g.surface_substep_frac = (2.0 if surf else 0.0)
    S_mc_surf[surf] = float(np.asarray(simulate(N_WALK, waveform=wf0, geometry=g, seed=1, require_gpu=False)).ravel()[0])
print("surface S0  OFF %.4f  ON %.4f" % (S_mc_surf[False], S_mc_surf[True]))

out = os.path.join(HERE, 'flagship_mc_reference.npz')
np.savez(out, bvals=bvals, bvecs=bvecs, delta=delta, DELTA=DELTA, TE=TE,
         S_mc_diff=S_mc_diff, S0_mc_surf_off=S_mc_surf[False], S0_mc_surf_on=S_mc_surf[True],
         N_walk=N_WALK, N_cyl=N_CYL, n_t=n_t)
print("saved", out)
