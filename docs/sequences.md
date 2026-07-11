# Acquisition sequences

The physical sequence is owned by **dmipy-sim**, and the free gradient waveform `G(t)` is the base representation — `PGSE`, `OGSE`, `CPMG` and the b-tensor encodings are *factory constructors*, not separate types. The same constructor, called with the same physical parameters, builds the object in either engine, and a single object drives both the analytical inverse (dmipy-fit) and the Monte-Carlo forward truth (dmipy-sim). **You specify the acquisition once.**

## One acquisition, both engines

Build the scheme from PGSE parameters, then hand the *same* object to the analytical model and to the Monte-Carlo simulator:

```python
import numpy as np
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.custom_optimizers import reference_models as models
import dmipy_sim

# --- specify the acquisition ONCE (physical PGSE parameters) ---
bvals = np.array([0.0, 1e9, 2e9])          # s/m^2
dirs  = np.tile([1.0, 0.0, 0.0], (3, 1))   # gradient directions
delta, Delta = 0.01, 0.03                  # pulse duration / separation (s)

# one constructor, one object -- accepted by both engines
scheme = AcquisitionScheme.from_pgse(bvals, dirs, delta, Delta)

# analytical inverse (dmipy-fit): forward-simulate / fit the scheme directly
E_analytic = models.ball_and_stick()(scheme, **{
    'C1Stick_1_mu': [0.0, 0.0], 'C1Stick_1_lambda_par': 1.7e-9,
    'G1Ball_1_lambda_iso': 3e-9, 'partial_volume_0': 0.6, 'partial_volume_1': 0.4})

# forward truth (dmipy-sim): the SAME scheme drives the Monte-Carlo walk
E_mc = dmipy_sim.simulate(20_000, 1.7e-9, scheme.waveform, dmipy_sim.FreeDiffusion())
```

The b-values the analytical model sees are the ones dmipy-sim integrated from `G(t)` — the scheme carries the waveform, and `scheme.waveform` is what `dmipy_sim.simulate` consumes. Starting from the sim side gives the identical object:

```python
from dmipy_sim.sequences import Sequence

# identical signature on the sim side -- the fit scheme just wraps this
seq = Sequence.from_pgse(bvals, dirs, delta, Delta)
seq.bvalues            # == scheme.bvalues, exactly
```

This is by construction, not coincidence: `AcquisitionScheme.from_X` delegates to `dmipy_sim.sequences.Sequence.from_X` with the **identical signature** — dmipy-sim owns the physical sequence, and the fit scheme only adds the analytical shell / spherical-harmonics layer on top. So the parameters you pass are the same whichever engine you start from.

!!! note "Input parity, not output agreement"
    Feeding one acquisition to both engines lets you cross-check the analytical model against the Monte-Carlo ground truth on a matched substrate. Agreement is necessary evidence, not proof — the two engines are correlated and can be wrong the same way.

## Constructors

Each constructor below exists with the identical signature on both `dmipy_sim.sequences.Sequence` and `dmipy_fit.core.acquisition_scheme.AcquisitionScheme`. (The fit side adds `min_b_shell_distance` / `b0_threshold` for analytical shell clustering; the physical parameters are the same.)

### `from_pgse()`

PGSE: two same-direction lobes separated by Delta (180-folded effective G).

```python
from_pgse(bvalues, gradient_directions, delta, Delta, TE=None, n_t=1000, slew_rate=200.0)
```

### `from_ogse()`

Cosine OGSE: two slew-limited trains by default; ``slew_rate=np.inf``

```python
from_ogse(bvalues, gradient_directions, oscillation_frequency, gradient_duration, n_cycles=1, gradient_rise_time=0.0, TE=None, n_t=1000, slew_rate=200.0, refocus_duration=0.0)
```

### `from_cpmg()`

CPMG multi-echo spin echo; optional per-echo bipolar diffusion lobe.

```python
from_cpmg(n_echoes, TE, bvalues=None, gradient_directions=None, beta_deg=180.0, n_t_per_echo=100)
```

### `from_btensor_ste()`

Spherical tensor encoding (b_delta=0): three orthogonal bipolar pairs.

```python
from_btensor_ste(bvalues, delta, Delta, TE=None, n_t=1000)
```

### `from_btensor_pte()`

Planar tensor encoding (b_delta=-0.5): two in-plane bipolar pairs.

```python
from_btensor_pte(bvalues, plane_normal, delta, Delta, TE=None, n_t=1000)
```

### `from_btensor_waveform()`

Wrap a precomputed b-tensor gradient waveform as a spin-echo Sequence.

```python
from_btensor_waveform(G, dt, *, echo_idx=None, TE=None, allow_offcenter_180=False)
```

### `from_waveform()`

Build from an arbitrary gradient waveform; b numerically from G.

```python
from_waveform(G, dt, gradient_directions, delta=None, Delta=None, TE=None, allow_unrefocused=False)
```


## Composite / mixed-encoding schemes

Because a scheme is **waveform-first** — `G(t)` per measurement, with per-measurement `delta`,
`Delta`, `TE` and OGSE fields — the measurements in a *single* scheme need not share an encoding.
You can concatenate shells from different constructors (PGSE, OGSE, b-tensor LTE/PTE/STE, or raw
`from_waveform`) into one scheme, and every model, fitter, and multi-tissue CSD consumes it as a
**single signal**: each measurement is evaluated from its own waveform, so nothing special-cases
the encoding.

```python
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme

# build each block with whatever constructor fits its encoding
# (from_pgse / from_ogse / from_btensor_* / from_waveform) ...
pgse_block = ...   # a PGSE scheme
ogse_block = ...   # an OGSE scheme

# concatenate along the measurement axis -> ONE scheme, per-measurement timing preserved
scheme = AcquisitionScheme.concatenate([pgse_block, ogse_block])   # or: pgse_block + ogse_block

model.fit(scheme, data, solver="jax")     # models / CSD read the mix transparently
```

Mixed PGSE + OGSE concatenation is exercised in the test suite
(`core/tests/test_ogse_acquisition_scheme.py`).

### Normalizing a composite scheme

Because the $b=0$ signal carries no diffusion weighting, it is **independent of the gradient
waveform shape** — PGSE, OGSE and STE all give the same $b=0$ at a given echo time; it depends
only on TE (through $T_2$). Normalization is therefore keyed on **TE, not on encoding**:

- a scheme at a **single TE** is normalized by the mean of all its $b=0$ measurements;
- a scheme spanning **multiple TE** is normalized *per-TE segment* — each measurement is divided
  by the mean of the $b=0$ measurements **at its own TE**.

So mixing OGSE and PGSE at one TE needs a single $b=0$ normalization (nothing to correct — the
relaxation weighting is shared); only different TE (common when OGSE needs a longer TE) requires
separate segments, and the fit does this automatically. Every TE must therefore carry its own
$b=0$ measurement — the scheme raises a `ValueError` otherwise. (When you *fit* $T_2$ explicitly,
normalization is turned off: the model returns the raw $T_2$-weighted signal, so the decay is the
data.)

This is a direct consequence of the free-waveform design, not a bespoke feature — which is why
unusual protocols (for example **mixed OGSE + PGSE multi-tissue CSD**) work for free. It is also
why the analytical models must answer for *any* `G(t)`; see the
[GPA-for-arbitrary-waveforms derivation](derivations/gpa_arbitrary_waveform.md).
