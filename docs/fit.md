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
