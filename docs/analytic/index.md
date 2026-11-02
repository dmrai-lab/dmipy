# Closed forms: dmipy-analytic

dmipy-analytic is the closed and semi-closed forms of the diffusion-MRI signal for special cases: free and restricted
diffusion, exchange, relaxation, coherence pathways, orientation distributions and the fields of simple shapes.
Each form states the assumptions it holds under and the source it comes from, and the package is the one copy the
other packages import: dmipy-fit fits these forms, dmipy-replay and dmipy-sim use the ones their engines need, and
the rest check replay packs where a form and a walk describe the same situation.

```python
import numpy as np
from dmipy_analytic import gaussian
from dmipy_analytic.constants import GAMMA
from dmipy_analytic.restricted import cylinder

b = np.array([0.0, 1e9, 2e9])                                          # s/m^2
delta, Delta = 0.010, 0.030
G = np.sqrt(b / (GAMMA ** 2 * delta ** 2 * (Delta - delta / 3)))      # the PGSE amplitude of each b
print(np.round(gaussian.ball(b, 2e-9), 4))                             # free water, exp(-b D)
print(np.round(cylinder.gaussian_phase(G, delta, Delta, diameter=6e-6, diffusivity=2e-9), 4))   # across a 6 µm axon
```

## The forms, module by module

| module | what it holds |
|---|---|
| `constants` | the physical constants, once: `GAMMA`, `GAMMA_BAR`, `MU0` |
| `harmonics` | the orthonormal real spherical-harmonic basis every SH coefficient of the packages is written in, its compact layout and its rotations |
| `orientation` | the Watson and Bingham distributions and their exact SH coefficients |
| `gaussian` | free diffusion, the stick, the zeppelin, the tensor, under a b-value or a b-tensor, and their powder averages |
| `restricted` | the plane, the cylinder and the sphere pore: the short-gradient-pulse and Gaussian-phase closed forms, and the eigenmode (matrix) method for any sampled waveform |
| `exchange` | Kärger exchange between compartments and its spin-echo and stimulated-echo forms |
| `relaxation` | transverse and longitudinal relaxation, surface relaxation, and the two-pool Bloch-McConnell forms of magnetization transfer |
| `epg` | extended phase graphs: the coherence pathways of an RF schedule and their amplitudes |
| `fields` | the field of a hollow cylinder of isotropic and anisotropic susceptibility (infinite and as a finite segment) and of a current segment |

[Every form and its source](forms.md) is the table of all of them, read from the installed package: each form's
first docstring paragraph, the paper and equation it cites, and its JAX twin.

## NumPy definitions, JAX twins

A form's definition is NumPy in float64, and the package imports NumPy alone; a form that needs a special function
imports scipy inside it (`pip install "dmipy-analytic[special]"`). `dmipy_analytic.jax.<module>.<form>` is the same
form in `jax.numpy` for `jit`, `grad` and `vmap`, with the same arguments (`pip install "dmipy-analytic[jax]"`). A
parity test holds every twin to its definition at a tolerance derived from the float32 rounding of the form's
operations.

```python
import jax
from dmipy_analytic.jax import gaussian as gaussian_jax
from dmipy_analytic.jax.restricted import cylinder as cylinder_jax

print(np.allclose(gaussian_jax.ball(b, 2e-9), gaussian.ball(b, 2e-9), rtol=1e-6))
attenuation = lambda d: cylinder_jax.gaussian_phase(G[2], delta, Delta, diameter=d, diffusivity=2e-9).squeeze()
print(float(jax.grad(attenuation)(6e-6)))                              # dE/d(diameter) at b = 2000 s/mm^2
```

## What a form certifies: coverage

A form that a replayed pack reproduces certifies the whole chain in that situation: the geometry and its walls, the
step law, the band representation and its codec, and the contraction. What the collection buys is therefore the
number of distinct failure modes it excludes, not the number of forms: ten approximations of one cylinder exercise
the same machinery ten times. Forms in which two or more tiers of the physics interact are worth the most, since
they test what no single-tier form can, that the tiers combine correctly walker by walker. The model case is a
permeable slab: two compartments with their own T2, one of them magnetised, the membrane between them, replayed
under a free induction decay, a spin echo, a PGSE and a gradient echo from one walk against the exact
one-dimensional Bloch-Torrey solution. One configuration checks positions, compartments, exchange, the field and
the RF at once.

The coverage matrix names, for each part of the replay framework, the single-tier form that checks it alone and the
cross-tier form that checks it together with another tier:

| part of the framework | single-tier form | cross-tier form |
|---|---|---|
| positions and walls (the walk, the step law) | plane, cylinder, sphere: SGP, GPA, the matrix method | dispersion x restriction |
| band representation (arbitrary waveforms) | the matrix method on OGSE and arbitrary G(t) | |
| compartments | T2 and T1 decay per pool | the permeable slab |
| contact | surface relaxivity (the Robin problem) in a sphere and a cylinder | relaxivity x exchange |
| exchange | Kärger | the permeable slab; MT x exchange |
| field | the hollow-cylinder field | the permeable slab; restriction x internal gradient; field x pose |
| vector Bloch and RF (B1, trains, crushers) | EPG | B1 x diffusion |
| pose (orientation distributions) | Watson, Bingham | dispersion x restriction |
| MT bound pool | Bloch-McConnell, the Z-spectrum | MT x exchange |

The matrix, with the test that holds each cell and the cells still open, is kept in
[dmipy-analytic#7](https://github.com/dmrai-lab/dmipy-analytic/issues/7). A check replays a pack (a committed fixture
or a [SubstrateCommons](https://huggingface.co/SubstrateCommons) node) against the form at the pack's stated
standard error, with a tolerance derived from that error and the number of comparisons, never fitted.
[The vector-Bloch route](../replay/bloch.md) shows one cell: a train at 80 % B1 replayed against the EPG pathway sum.
