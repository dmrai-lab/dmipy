# Inverse — dmipy-fit

Analytical multi-compartment fitting. The measured signal is

$$S = S_0 \sum_i f_i\, E^{\text{diff}}_i(b)\, e^{-\mathrm{TE}/T_{2,i}}\, \hat B^{\text{surf}}_i$$

with T2 and **surface relaxivity** as composable occupancy-gated factors on any compartment.

```python
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.signal_models.gaussian_models import G1Ball, G2Zeppelin
from dmipy_fit.core.modeling_framework import MultiCompartmentModel

noddi = MultiCompartmentModel([G1Ball(), G2Zeppelin(), C1Stick()])
fit = noddi.fit(scheme, data, solver="jax")
fractions = fit.fitted_parameters["partial_volume_2"]
```

- **Compartments:** sticks/cylinders, sphere, ball/zeppelin, plane, capped cylinder.
- **Dispersion:** Watson / Bingham; Gamma diameter distributions.
- **CSD:** Tournier / cvxpy / OSQP-JAX; DTI, IVIM.
- **White matter:** `white_matter.build_white_matter_model()` (a decoupled diffusion-only
  canonical model — surface relaxivity reweights intra vs extra) and
  `white_matter.t2_spectrum_mwf()` (standard NNLS myelin-water fraction).

See the **[Model catalog](catalog.md)** for every published inverse model (NODDI, Ball&Stick,
Standard Model, SMT, NEXI, VERDICT, SANDI, …) built from these primitives in a few lines.

---

## What's new since the original dmipy

The original **dmipy** ([Fick, Wassermann & Deriche 2019](https://doi.org/10.3389/fninf.2019.00064))
established the compartment-model *grammar* — compose sticks, zeppelins, spheres and
dispersion distributions into a `MultiCompartmentModel` and fit it. This engine keeps that
grammar verbatim and rebuilds the machinery underneath it. The headline changes:

### GPU fitting (`solver="jax"`)

Fitting is a JAX program. The forward model is JIT-compiled and the optimiser
(bounded L-BFGS-B, with a coarse spherical brute-grid initialisation) is **`vmap`-ed across
voxels**, so a whole brain fits in one vectorised GPU call instead of the original's
per-voxel CPU loop. The *same* code runs on CPU (`JAX_PLATFORMS=cpu`) for reference and CI.

```python
fit = model.fit(scheme, data, solver="jax")   # vmap over voxels, GPU if available
```

### `OccupancyGatedModel` — physics beyond diffusion

The original was diffusion-only: one compartment, one `E(b)`. Here any compartment can be
wrapped in an `OccupancyGatedModel` that carries **composable, opt-in physics factors** —
transverse relaxation (`T2`) and intra-pore + exterior **surface relaxivity** — so the signal
is diffusion × relaxation × surface, per compartment:

```python
from dmipy_fit.signal_models.attenuation import (
    OccupancyGatedModel, TransverseRelaxation, ExteriorSurfaceRelaxivity)

extra = OccupancyGatedModel(G2Zeppelin(), [
    ExteriorSurfaceRelaxivity(S_ext_over_V=...), TransverseRelaxation()])
```

This is what lets the **[unified white-matter model](catalog.md)** carry the surface-relaxivity
inter-compartment weighting (surface relaxivity reweights intra vs extra) that plain
stick+zeppelin cannot represent.

### Noise-aware fitting

The signal magnitude is Rician, not Gaussian, at the SNR of real dMRI. Pass `eta=True` and the
forward model carries a **Rician noise floor** `η`, fitting against $\sqrt{S^2 + \eta^2}$ so
parameters are not biased upward by the noise floor at high *b*:

```python
model = MultiCompartmentModel([G1Ball(), C1Stick()], eta=True)  # jointly fit the noise floor
fit = model.fit(scheme, data, solver="jax")
noise_floor = fit.fitted_parameters["eta"]                      # dimensionless, ~ 1/SNR
```

The CSD solvers accept a matching `eta=` bias correction ($\sqrt{\max(S^2-\eta^2,\,0)}$) before
the QP solve.

### Citation graph & auto-generated methods

Every signal model and every physical constant carries its own `_citations`. Walk the graph of
whatever you composed and get a ready-to-paste **Methods paragraph and BibTeX** — reproducibility
falls out of the model object itself:

```python
from dmipy_fit.audit import walk_citation_graph, generate_methods_section, generate_bibtex

graph = walk_citation_graph(model)
print(generate_methods_section(graph))          # "...modeled using ... Zhang H et al. (2012) ..."
open("refs.bib", "w").write(generate_bibtex(graph))
```

Physical constants come from one cited catalogue — see **[Biophysical constants](constants.md)**.

### One physical representation, shared with the forward truth

The acquisition and substrate objects are **sim-owned and shared**: the same `from_pgse(...)`
scheme drives both the analytical fit here and the Monte-Carlo ground truth in dmipy-sim, and
the same `Substrate` parametrises both. There was no forward-simulation counterpart in the
original. See **[Acquisition sequences](sequences.md)** and **[Substrate & geometry](substrate.md)**.

### Current scope (this release)

The **mission** is a physics-complete, sequence- and substrate-agnostic MRI computational
forward model — the free waveform `G(t)` and an arbitrary substrate as the base representation,
every physical effect on the same footing — paired with its analytical inverse. *This release*
is the transverse-magnetisation slice of it: diffusion + T2 + surface relaxivity + permeable
exchange, with ideal instantaneous pulses. Susceptibility, gradient-/stimulated-echo and T1 are
part of the model but not in the released public scope yet — so the boundary above is a
*release* boundary, not the ceiling.
