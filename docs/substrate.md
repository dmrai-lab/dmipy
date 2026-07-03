# Substrate & geometry

The microstructural substrate is owned by **dmipy-sim** in two linked forms: explicit `Geometry` objects that the Monte-Carlo walkers diffuse inside, and the physical-parameter `Substrate` (plus the cited `biophysical_constants` catalogue). The same physical description feeds both engines — dmipy-sim walks an explicit geometry, dmipy-fit's analytical model takes the same parameters — and every physical constant is defined exactly once. **You describe the tissue once.**

## One substrate, both engines

A `Substrate` is the physical ground truth. Its derived accessors (volume fractions, tortuosity, mean radii, surface-relaxation rates) are the numbers the analytical model needs, computed in one place:

```python
import dmipy_sim
from dmipy_sim.substrate import Substrate
from dmipy_fit.white_matter import build_white_matter_model
from dmipy_fit.audit import biophysical_constants as fit_consts
from dmipy_sim.substrate import biophysical_constants as sim_consts

# --- describe the microstructure ONCE (dmipy-sim owns the physical ground truth) ---
sub = Substrate()          # canonical healthy white matter; override any field
# derived quantities the analytical model needs are computed here, once:
#   sub.f_intra, sub.f_extra, sub.lambda_perp_extra (tortuosity), sub.mean_inner_radius, ...

# forward truth (dmipy-sim): an explicit geometry the walkers diffuse in,
# its inner/outer radii and diffusivities taken from the substrate
geom = dmipy_sim.MyelinatedCylinder(
    inner_radius=sub.mean_inner_radius, outer_radius=sub.mean_outer_radius,
    orientation=(0, 0, 1), D_intra=sub.D_intra, D_extra=sub.D_extra,
    D_myelin=sub.D_myelin)   # myelin water is stuck (D_myelin = 0) by default

# analytical inverse (dmipy-fit): the SAME physical numbers parametrize the model
model, params = build_white_matter_model(
    gamma_shape=sub.gamma_shape_diameter,
    gamma_scale_outer_diameter=sub.gamma_scale_diameter,
    g_ratio=sub.g_ratio, f_axon=sub.f_axon, D_intra=sub.D_intra)

# every physical CONSTANT is defined once: fit re-exports the sim catalogue
assert fit_consts.get_value is sim_consts.get_value
```

The geometry and the model are parametrised from the *same* `Substrate` fields, and the tissue constants come from a single catalogue: `dmipy_fit.audit.biophysical_constants` re-exports `dmipy_sim.substrate.biophysical_constants` verbatim, so there is exactly one definition (with citation provenance) of every physical constant. Derived geometric quantities — the exterior surface-to-volume ratio, the intra-pore ⟨4/d⟩ average, the tortuosity `lambda_perp_extra` — use the same closed forms on both sides.

!!! note "Input parity, not output agreement"
    One substrate feeding both engines lets you check the analytical model against the Monte-Carlo ground truth on matched tissue. Agreement is necessary evidence, not proof — the two engines are correlated and can be wrong the same way.

## Geometries

The forward substrate: closed pores, packed ensembles, and free diffusion the walkers sample. Each is a `dmipy_sim` `Geometry` accepted by `dmipy_sim.simulate(n_walkers, D, waveform, geometry)`.

### `FreeDiffusion`

Unbounded free diffusion — walkers move without any reflection.

```python
FreeDiffusion(*args, **kwargs)
```

### `Sphere`

Reflecting sphere of given radius centred at the origin.

```python
Sphere(radius: float, surface_relaxivity_t2=None, permeability=None)
```

### `Cylinder`

Reflecting infinite cylinder of given radius and orientation.

```python
Cylinder(radius: float, orientation, surface_relaxivity_t2=None, permeability=None)
```

### `MyelinatedCylinder`

Three-compartment myelinated cylinder: intra-axonal, myelin sheath, extra-axonal.

```python
MyelinatedCylinder(inner_radius, outer_radius, orientation, D_intra, D_extra, D_myelin=0.0, kappa_inner=None, kappa_outer=None, T2_intra=None, T2_myelin=None, T2_extra=None, water_fractions=(1.0, 0.15, 1.0))
```

### `Ellipsoid`

Reflecting axis-aligned ellipsoid with semi-axes (a, b, c) along (x, y, z).

```python
Ellipsoid(semiaxes, surface_relaxivity_t2=None, permeability=None)
```

### `Box1D`

1D reflecting slab with walls at x=0 and x=length.

```python
Box1D(length: float, surface_relaxivity_t2=None)
```

### `PermeableSlab1D`

Closed 1-D two-compartment slab: a permeable membrane at x=L/2 with reflecting

```python
PermeableSlab1D(length, permeability, surface_relaxivity_t2=None)
```

### `PackedSpheres`

Extra-axonal diffusion in a periodic cubic domain packed with spheres.

```python
PackedSpheres(radii, centers, L, surface_relaxivity_t2=None, permeability=None)
```

### `PackedCylinders`

Extra-axonal diffusion in a periodic square domain packed with cylinders.

```python
PackedCylinders(radii, centers, L, orientation=(0.0, 0.0, 1.0), surface_relaxivity_t2=None, permeability=None)
```

### `PackedMyelinatedCylinders`

Periodic RVE with N_actual myelinated cylinders — three-compartment.

```python
PackedMyelinatedCylinders(inner_radii, g_ratios, centers, cell_size, N_max=128, orientation=(0.0, 0.0, 1.0), D_intra=2e-09, D_myelin=1e-10, D_extra=2e-09, T2_intra=None, T2_myelin=None, T2_extra=None, kappa_inner=0.0, kappa_outer=0.0, rho_inner=0.0, rho_outer=0.0)
```

## Substrate parameters

A `dmipy_sim.substrate.Substrate` carries the canonical white-matter physics — volume fractions (`f_axon`, `f_csf`), the axon-diameter Gamma law (`gamma_shape_diameter`, `gamma_scale_diameter`), `g_ratio`, the intrinsic diffusivities (`D_intra`, `D_extra`, `D_myelin_*`, `D_csf`), transverse relaxation (`T2_*`) and the transverse surface relaxivity `rho2` — and derives the model-facing quantities from them:

| accessor | meaning |
| --- | --- |
| `f_intra`, `f_extra`, `f_myelin` | compartment volume fractions from `f_axon`, `g_ratio` |
| `mean_inner_radius`, `mean_outer_radius` | Gamma-law radii (inner = `g_ratio`·outer) |
| `lambda_perp_extra` | extra-axonal tortuosity (perpendicular diffusivity) |
| `intra_surface_rate`, `extra_surface_rate` | surface-relaxation rates from `rho2` and S/V |

Override any field (`Substrate(f_axon=0.6, g_ratio=0.65)`) to describe a different tissue; both the geometry you build and the model parameters follow.

