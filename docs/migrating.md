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
tool. The compartment-model grammar carries over unchanged; everything below it was rebuilt, and a
whole forward-simulation half was added. Each row links to where it lives in the docs.

| Capability | 1.x | 2.1 | Docs |
|---|:---:|:---:|---|
| Modular multi-compartment model design & fitting | ✓ | ✓ | [Inverse](fit.md) |
| Orientation dispersion (Watson / Bingham), Gamma diameters | ✓ | ✓ | [Model catalog](catalog.md) |
| CSD / fibre ODFs | ✓ | ✓ | [Inverse](fit.md) |
| Named literature models (NODDI, SMT, VERDICT, SANDI, …) | ✓ | ✓ | [Model catalog](catalog.md) |
| **GPU fitting** — whole-slice `vmap` fits in seconds (`solver="jax"`) | — | ✓ | [Inverse](fit.md) |
| **Noise-aware Rician maximum-likelihood** fitting (not just least-squares) | — | ✓ | [Inverse](fit.md) |
| **Forward Monte-Carlo simulator** (`dmipy_sim`) — no forward model in 1.x | — | ✓ | [Forward](sim.md) |
| **Arbitrary / triangular-mesh substrates** (load a `.ply`) | — | ✓ | [Mesh substrates](mesh_substrates.md) |
| **T2 & surface relaxivity** as composable occupancy-gated factors | — | ✓ | [Surface relaxivity & MWF](surface_relaxivity_bias.md) |
| **Myelin-water fraction** (regularised NNLS T2 spectrum) | — | ✓ | [Surface relaxivity & MWF](surface_relaxivity_bias.md) |
| **Water-exchange** — generalized Kärger / NEXI (analytical, on GPU) | — | ✓ | [Model catalog](catalog.md) |
| **Arbitrary-waveform / b-tensor encoding** (OGSE, LTE/PTE/STE, free `G(t)`) | — | ✓ | [Acquisition sequences](sequences.md) |
| **Composite, sequence-agnostic schemes** (mix encodings in one fit) | — | ✓ | [Acquisition sequences](sequences.md) |
| **Exact analytical spherical harmonics** for Watson/Bingham/Gaussian ODFs | — | ✓ | [Model catalog](catalog.md) |
| **Shared substrate for fit ↔ sim parity** (no conversion layer) | — | ✓ | [WM parity example](examples/canonical_wm_parity.md) |
| **Spin-walk pedagogy movies** (intra / myelin / extra water pools) | — | ✓ | [Pedagogy](pedagogy.md) |
| **Citation graph + auto-generated Methods** & BibTeX | — | ✓ | [Inverse](fit.md) |

Everything in the diffusion-fitting grammar you already wrote still runs (after the `dmipy_fit`
rename); the new rows are additive.
