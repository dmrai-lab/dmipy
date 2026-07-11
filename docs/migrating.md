# Migrating from dmipy 1.x (the 2019 toolbox)

If you used the original **dmipy** (Fick–Wassermann–Deriche, 2019), most of your analysis code
carries over with a **namespace rename**. The big change is structural: dmipy 2.x is split into
two engines, and `pip install dmipy` no longer gives you an importable `dmipy` package.

## The one-minute version

| 1.x | 2.x |
|---|---|
| `pip install dmipy` → `import dmipy` | `pip install dmipy` → `import dmipy_fit` (+ `import dmipy_sim`) |
| `from dmipy.core...` | `from dmipy_fit.core...` |
| `from dmipy.signal_models...` | `from dmipy_fit.signal_models...` |
| `from dmipy.distributions...` | `from dmipy_fit.distributions...` |
| (no forward simulator) | `import dmipy_sim` — GPU Monte-Carlo forward model (new) |

The analytical / fitting toolbox you knew **is** `dmipy_fit`: the submodule layout and the class
names are preserved. In most scripts a mechanical find-replace of `dmipy.` → `dmipy_fit.` is the
whole migration.

```python
# 1.x
from dmipy.core.acquisition_scheme import acquisition_scheme_from_bvalues
from dmipy.signal_models import cylinder_models, gaussian_models
from dmipy.core.modeling_framework import MultiCompartmentModel

# 2.x — identical names, dmipy_fit namespace
from dmipy_fit.core.acquisition_scheme import acquisition_scheme_from_bvalues
from dmipy_fit.signal_models import cylinder_models, gaussian_models
from dmipy_fit.core.modeling_framework import MultiCompartmentModel

stick = cylinder_models.C1Stick()
ball  = gaussian_models.G1Ball()
model = MultiCompartmentModel(models=[stick, ball])   # unchanged
```

Watson/Bingham distributed models (`SD1WatsonDistributed`, …) live under
`dmipy_fit.distributions.distribute_models`, as before.

## Things to double-check

- **b-values are in `s/m²`, not `s/mm²`** — as in 1.x. Multiply your `s/mm²` values by `1e6`
  (`1000 s/mm² → 1e9 s/m²`). 2.x now emits a `RuntimeWarning` if the max b-value looks like it was
  passed in `s/mm²`, so a silent all-b0 scheme won't bite you anymore.
- **Import the engines directly.** There is no importable `dmipy` in 2.x — it is a meta-package
  that installs `dmipy_fit` (inverse) and `dmipy_sim` (forward). See [Install](install.md).
- **To pin the old toolbox:** `pip install "dmipy<2"` still resolves to the 2019 releases on PyPI.

## What's genuinely new in 2.x

2.x is **not just a rename** — the toolbox you knew (`dmipy_fit`) is now one half of a much larger
tool. Beyond the analytical fitting that carried over:

- **A forward Monte-Carlo engine (`dmipy_sim`)** — spins random-walk through explicit geometries
  under arbitrary `G(t)`, with **surface relaxivity, membrane permeability / exchange, and T2**
  baked into the walk. 1.x had no forward model. See [Forward — dmipy-sim](sim.md).
- **GPU fitting (JAX)** — whole-slice fits in seconds (`solver="jax"`), with **noise-aware Rician
  maximum-likelihood** losses, not only least-squares. See [Inverse — dmipy-fit](fit.md).
- **Water-exchange models** — a generalized Kärger model (`X0GeneralizedKarger`, wraps *any two*
  compartments) and **NEXI** (`X2NEXIModel`), analytical and on the GPU.
- **Arbitrary-waveform / b-tensor encoding** — OGSE, LTE/PTE/STE and free `G(t)`; the
  Gaussian-Phase cylinder now answers for rotating / tensor-valued waveforms, not just PGSE
  (see the [GPA derivation](derivations/gpa_arbitrary_waveform.md)).
- **Composite, sequence-agnostic schemes** — one scheme can *mix* encodings (e.g. **mixed
  OGSE + PGSE multi-tissue CSD**) and every model, fit, and CSD reads it as a single signal.
  See [Acquisition sequences](sequences.md).
- **Relaxation on the diffusion signal** — T2 and surface relaxivity as composable,
  occupancy-gated factors on any compartment; plus CPMG and NNLS myelin-water fraction. See
  [Surface relaxivity & MWF](surface_relaxivity_bias.md).
- **Exact analytical spherical harmonics** for Watson / Bingham / Gaussian ODFs — closed form,
  no numerical projection.
- **One shared substrate/sequence interface** — the simulator and the analytical models eat the
  same `Waveform` and substrate, so a fit and a simulation describe the same tissue with no
  conversion layer. The [canonical-WM parity example](examples/canonical_wm_parity.md) shows
  analytic ↔ Monte-Carlo agreement.
- **Pedagogy** — real Monte-Carlo-walk movies of the intra / myelin / extra water pools. See
  [Pedagogy](pedagogy.md).
- **Citation governance + automatic Methods generation** — every model, distribution, optimiser
  and acquisition carries its literature attribution in a citation graph. `walk_citation_graph(model)`
  collects who to cite for a fitted or constructed model, and `generate_methods_section(...)` emits
  a ready-to-paste Markdown Methods paragraph + numbered references (and BibTeX) — so the people
  who invented each approach get credited automatically, without you hunting down DOIs.
