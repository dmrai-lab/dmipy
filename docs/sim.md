# Simulate — dmipy-sim

Spins random-walk through an explicit geometry and accumulate phase under the acquisition's
gradient; the signal is the ensemble average, from first principles. Surface relaxivity,
permeability, T2 and T1, susceptibility and magnetization transfer are part of the same walk.

```python
import dmipy_sim as ds

seq = ds.pgse([[1, 0, 0]] * 3, 0.010, 0.030, bvalues=[0, 1e9, 2e9])
E   = ds.simulate(20_000, 2e-9, waveform=seq, geometry=ds.Cylinder(radius=4e-6, orientation=(0, 0, 1)),
                  seed=0, require_gpu=False)
E / E[0]                       # the signal, normalised to b = 0
```

## Two ways to get a signal

**Fused** — `simulate(n_walkers, diffusivity, waveform, geometry)` walks the spins under one
acquisition and returns the signal. `simulate_bloch(...)` propagates the full vector
magnetisation through the actual RF, gradient, relaxation, exchange and MT operators when the
transverse-only picture is not enough (finite pulses, stimulated echoes, T1).

**Persistent** — walk once, keep the walk, replay any acquisition on it. A `.rpk` replay pack is
the compressed, self-certifying form of a walk; it is what the substrate bank distributes and what
dmipy-fit's replay models fit against.

```python
walk = ds.simulate_trajectories(4_000, 2e-9, ds.Cylinder(radius=4e-6, orientation=(0, 0, 1)),
                                T_max=0.10, dt_save=2e-4, seed=0, require_gpu=False)   # 100 ms of walk
pack = ds.build_replay_pack(walk, id="docs/cylinder", license="CC-BY-4.0", citation="dmipy.org", K=32)
E_pgse = pack.replay(ds.pgse([[1, 0, 0]], 0.010, 0.030, bvalues=[1e9]), tissue=False)
E_ogse = pack.replay(ds.ogse([[1, 0, 0]], 50.0, 0.040, shape="cosine", bvalues=[1e9]), tissue=False)
```

The walk depends only on the geometry, the diffusivity and the seed; the acquisition, the field,
the relaxation times and the pose are replay knobs. That invariant is why one walk answers every
sequence.

## Geometries

| Geometry | Restriction | Surface relaxivity | Permeability |
|---|---|:---:|:---:|
| `FreeDiffusion` | none | — | — |
| `Box1D`, `PermeableSlab1D` | 1-D slab | ✓ | ✓ |
| `Sphere`, `Cylinder`, `Ellipsoid`, `CurvedCylinder` | closed wall | ✓ | ✓ |
| `PackedCylinders`, `PackedSpheres`, `PackedCurvedCylinders` | periodic ensemble | ✓ | ✓ |
| `MyelinatedCylinder`, `PackedMyelinatedCylinders` | multi-wall myelin | ✓ | ✓ dual-wall |
| `SphereUnion` | overlapping spheres (CATERPillar-style) | ✓ | ✓ |
| `Mesh` (`.ply`) | arbitrary closed or 3-D-periodic mesh | ✓ | ✓ |

Every geometry has a `.spec` (a `SubstrateSpec`, saved as `.sub.json`) that writes out what the
constructor leaves implicit, and every driver accepts the spec or the object. See
[Substrate & geometry](substrate.md), [Mesh substrates](mesh_substrates.md) and the
[biophysical constants](constants.md) the canonical white matter is built from.

## Noise

`add_rician_noise(S, sigma)` and `add_nc_chi_noise(S, sigma, n_coils)` add measurement noise to a
signal; `estimate_sigma` recovers it from data.

## Correctness

Physics is the specification: every effect ships a validation ladder against exact analytical
solutions (eigenfunction series, Brownstein–Tarr, exchange laws, MISST references) in the
repository's `examples/validation/`. The [Physics](physics/index.md) pages show each effect and
what it was validated against.
