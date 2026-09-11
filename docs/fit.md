# Fit — dmipy-fit

Analytical multi-compartment fitting. The signal is

$$S = S_0 \sum_i f_i\, E^{\text{diff}}_i(\text{acquisition})\, e^{-\mathrm{TE}/T_{2,i}}\, \hat B^{\text{surf}}_i$$

with relaxation and surface relaxivity as composable factors on any compartment, evaluated on the
same `ScannerSequence` the simulator plays.

```python
import numpy as np
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.core.modeling_framework import MultiCompartmentModel
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.signal_models.gaussian_models import G1Ball

rng = np.random.default_rng(0)
bvals = np.r_[0.0, np.full(24, 1e9), np.full(24, 2e9)]
bvecs = np.zeros((49, 3)); v = rng.standard_normal((48, 3)); bvecs[1:] = v / np.linalg.norm(v, axis=1, keepdims=True)
scheme = AcquisitionScheme.from_pgse(bvals, bvecs, delta=0.010, Delta=0.030)

model = MultiCompartmentModel([G1Ball(), C1Stick()], eta=True)      # with a Rician noise floor
data  = model.simulate_signal(scheme, model.parameters_to_parameter_vector(
            G1Ball_1_lambda_iso=3e-9, C1Stick_1_lambda_par=1.7e-9, C1Stick_1_mu=[0.5, 1.0],
            partial_volume_0=0.3, partial_volume_1=0.7, eta=0.03))[None, :]
fit = model.fit(scheme, data, solver="jax")                          # vmap over voxels, GPU if there is one
fit.fitted_parameters["partial_volume_1"], fit.fitted_parameters["eta"]   # ≈ 0.7, ≈ 0.03
```

## What is in it

- **Compartments**: stick, cylinders (Gaussian phase, Callaghan, Söderman, matrix method), sphere,
  ball, zeppelin, plane, dot; Watson and Bingham dispersion; Gamma diameter distributions.
- **Physics factors**: `OccupancyGatedModel(compartment, [TransverseRelaxation(),
  LongitudinalRelaxation(), IntraPoreSurfaceRelaxivity(), ExteriorSurfaceRelaxivity()])` — diffusion
  × relaxation × surface, per compartment, on any acquisition family (PGSE, PGSTE, OGSE, CPMG, b-tensor).
- **Replay models**: `C6MonteCarloReplayCylinder`, `S6MonteCarloReplaySphere` fit against a stored
  Monte-Carlo walk instead of a closed form.
- **CSD**: Tournier, cvxpy, OSQP-JAX; multi-tissue; DTI, IVIM.
- **White matter**: `white_matter.build_white_matter_model()` (the canonical model, surface
  relaxivity reweighting intra vs extra) and `white_matter.t2_spectrum_mwf()` (NNLS myelin water).
- **Noise**: `MultiCompartmentModel([...], eta=True)` fits a Rician floor jointly, so high-b
  parameters are not biased upward; the CSD solvers take the same `eta=`.
- **Provenance**: every model and constant carries its citations;
  `dmipy_fit.audit.generate_methods_section(walk_citation_graph(model))` writes the Methods
  paragraph and `generate_bibtex` the references.

Every published model (NODDI, SMT, the Standard Model, NEXI, SANDI, VERDICT, …) is a few lines
of these primitives: the [model catalog](catalog.md).

## The acquisition is the simulator's

`AcquisitionScheme(sequence)` reads a `ScannerSequence` or a `Protocol`; its `from_pgse`,
`from_pgste`, `from_ogse`, `from_cpmg`, `from_btensor_ste`, `from_btensor_pte` and
`from_waveform` are the simulator's builders. The models read b, direction, δ, Δ, TE and the OGSE
fields per measurement from the sequence's encoding; the ones that integrate a waveform read the
effective gradient itself. Schemes concatenate with `+`; a multi-TE scheme is a `Protocol` and is
normalised per TE (every TE needs its own b = 0). See [Acquisition](acquisition.md).

## Fitting on the GPU

Fitting is a JAX program: the forward model is JIT-compiled and a bounded L-BFGS-B (with a
brute-grid initialisation on the sphere) is `vmap`-ed across voxels, so a whole brain fits in one
vectorised call. The same code runs on the CPU with `JAX_PLATFORMS=cpu`.
