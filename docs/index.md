# dmipy

**Diffusion Microstructure Imaging in Python** — one physical substrate, two engines:

- **[dmipy-sim](https://github.com/dmrai-lab/dmipy-sim)** — a JAX Monte-Carlo simulator: spins
  random-walk through geometric substrates under arbitrary free gradient waveforms `G(t)`, with
  surface relaxivity and membrane permeability baked into the walk. *The forward-truth oracle.*
- **[dmipy-fit](https://github.com/dmrai-lab/dmipy-fit)** — analytical multi-compartment signal
  models + JAX GPU fitting, with T2 and surface relaxivity as composable occupancy-gated
  factors, CSD, and a standard NNLS myelin-water-fraction estimator. *The analytical inverse.*

They share **one** free-waveform sequence/substrate interface; the dependency is
one-directional, `fit → sim`. Build a fit and a simulation from the *same* parameters and they
describe the same tissue.

!!! quote "Physics is the specification"
    Physical laws, invariants, and known analytical results are the correctness criteria — not
    "the code runs". Every analytical model is validated effect-by-effect against Monte Carlo.
    (More on the philosophy at [dmrai-lab.org](https://dmrai-lab.org).)

```python
from dmipy_fit.signal_models.gaussian_models import G1Ball
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.core.modeling_framework import MultiCompartmentModel

ball_stick = MultiCompartmentModel([G1Ball(), C1Stick()])
fit = ball_stick.fit(scheme, data, solver="jax")     # whole slice on GPU
```

Start with **[Install](install.md)**, then the forward ([dmipy-sim](sim.md)) or inverse
([dmipy-fit](fit.md)) quickstart, or the worked
[surface-relaxivity / MWF walkthrough](surface_relaxivity_mwf.md).
