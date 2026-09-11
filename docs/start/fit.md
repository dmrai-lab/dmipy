# Your first fit

You have diffusion-weighted volumes, their b-values and directions, and the pulse timings from
the protocol. Build the acquisition, pick a model, fit.

```python
import numpy as np
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.core.modeling_framework import MultiCompartmentModel
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.signal_models.gaussian_models import G1Ball

# the acquisition, from the protocol: b in s/m² (multiply s/mm² by 1e6), unit directions, δ and Δ in s
rng   = np.random.default_rng(0)
bvals = np.r_[0.0, np.full(32, 1e9), np.full(32, 2e9)]
bvecs = np.zeros((65, 3)); v = rng.standard_normal((64, 3)); bvecs[1:] = v / np.linalg.norm(v, axis=1, keepdims=True)
scheme = AcquisitionScheme.from_pgse(bvals, bvecs, delta=0.010, Delta=0.030)

# your data: (n_voxels, n_measurements); here a synthetic ball-and-stick voxel
model  = MultiCompartmentModel([G1Ball(), C1Stick()])
truth  = dict(G1Ball_1_lambda_iso=3e-9, C1Stick_1_lambda_par=1.7e-9, C1Stick_1_mu=[0.6, 1.2],
              partial_volume_0=0.35, partial_volume_1=0.65)
data   = model.simulate_signal(scheme, model.parameters_to_parameter_vector(**truth))[None, :]

fit = model.fit(scheme, data, solver="jax")          # vmap over voxels, GPU if there is one
fit.fitted_parameters["partial_volume_1"]            # ≈ 0.65, the stick fraction
```

`AcquisitionScheme.from_pgse` builds the same `ScannerSequence` the simulator plays
([Acquisition](../acquisition.md)); the analytical models read their δ, Δ, TE and b from it.
Multi-shell, multi-TE, OGSE and b-tensor data use the other constructors (`from_ogse`,
`from_pgste`, `from_cpmg`, `from_btensor_ste`, `from_btensor_pte`, `from_waveform`) and
concatenate with `+`.

## Then

- Real data: `fit = model.fit(scheme, dwi.reshape(-1, n_meas), mask=...)`, and
  `fit.fitted_parameters[name].reshape(shape)` per map.
- Noise: `MultiCompartmentModel([...], eta=True)` fits a Rician floor jointly, so high-b
  parameters are not biased upward.
- Relaxation and surface relaxivity as factors on any compartment: [Fit](../fit.md).
- Every published model in a few lines: the [model catalog](../catalog.md).
- The Methods paragraph and BibTeX for what you composed: `dmipy_fit.audit`.
