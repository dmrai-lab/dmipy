# Susceptibility

Myelin, iron and deoxyhaemoglobin perturb the local field. Each source gives an off-resonance
field ΔB_z(r); a diffusing spin accrues the extra phase γ ∫ ΔB_z(r(t)) dt on top of the gradient
phase, read through the same substrate as diffusion, relaxation and exchange.

![Same susceptibility, same B0, same spins, only the axon shape differs: a circular lumen's internal field is uniform so the spins stay coherent; a real segmented monkey axon's field varies point to point and the net magnetization collapses.](media/susceptibility_morphology.gif){ width="100%" }

Inside a circular lumen the internal field is uniform, so every spin precesses together and the
signal only rotates. Inside a real, non-circular lumen the field varies, the spins fan out and the
signal collapses: susceptibility-induced dephasing reads out the morphology (Winther 2024).

## One engine, three sources

- **`SusceptibilitySources`**: isotropic magnetised spheres (grey-matter iron, vasculature) as
  superposed dipoles (Schenck 1996).
- **`MyelinSusceptibility`**: the anisotropic hollow-cylinder myelin field (Wharton & Bowtell
  2012) in closed form; the intra-axonal offset ½ Δχ_A B₀ sin²θ ln(1/g) is uniform inside the
  lumen and zero when B₀ is along the fibre.
- **`GridSusceptibility`**: any distribution voxelised onto a grid and solved by the
  Lorentz-corrected k-space dipole model (Salomir 2003; Marques & Bowtell 2005). The route for
  real morphology: a segmented axon, an undulating sheath, any mesh.

![Off-resonance field ΔBz(r) for the three source types.](media/susceptibility_fields.png){ width="100%" }

The field precesses the spin at its current position, so it composes with every other effect in
one pass, and the sequence's own 180 refocuses its *static* part exactly as in a real spin echo:
only the diffusion-driven residual survives, the part that carries microstructure.

![Spin-echo phase trajectories: a static field refocuses to full signal at the echo; diffusion through the field leaves a residual.](media/susceptibility_refocusing.png){ width="80%" }

```python
import numpy as np
import dmipy_sim as ds

susc = ds.MyelinSusceptibility(centers=np.array([[0., 0.]]), inner_radii=np.array([2e-6]),
                               outer_radii=np.array([3e-6]), L=20e-6,
                               delta_chi_a=-0.1e-6, B0=7.0, theta=1.57)         # B0 ⊥ fibre
seq = ds.pgse([[0, 0, 1]], 0.005, 0.020, gradient_strengths=[0.0], TE=0.040, n_t=400)   # a bare spin echo
S   = ds.simulate_bloch(5_000, 0.6e-9, seq, ds.Cylinder(radius=2e-6, orientation=(0, 0, 1)),
                        susceptibility=susc, seed=0, require_gpu=False)
abs(S[0])                     # the static field refocuses; diffusion through it does not
```

In the [coherence-gating](coherence_gating.md) law susceptibility is the purely transverse R₂′
term: longitudinal storage pauses it over the mixing time. The field solver is validated against
the exact sphere and cylinder fields, the hollow-cylinder intra-axonal law, and Winther et al.
2024's Monte Carlo on segmented monkey axons.
