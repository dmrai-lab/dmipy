# Simulate — dmipy-sim

Spins random-walk through an explicit geometry and accumulate phase under the acquisition's
gradient; the signal is the ensemble average, from first principles. Surface relaxivity,
permeability, T2 and T1, susceptibility and magnetization transfer are part of the same walk.

```python
import dmipy_replay as dr
import dmipy_sim as ds

seq = dr.pgse([[1, 0, 0]] * 3, 0.010, 0.030, bvalues=[0, 1e9, 2e9])
E   = ds.simulate(8_000, 2e-9, waveform=seq, geometry=ds.Cylinder(radius=4e-6, orientation=(0, 0, 1)),
                  seed=0, require_gpu=False)
E / E[0]                       # the signal, normalised to b = 0
```

## Two ways to get a signal

**One call**: `simulate(n_walkers, diffusivity, waveform, geometry)` walks the spins and replays the
acquisition on that walk, and returns the signal.

**A pack**: walk once, keep the walk, replay any acquisition on it. `walk(spec, n_walkers, T_max=,
envelope=)` is the one producer: it reads a substrate spec (or a geometry, reduced to its spec) and
accumulates every walker's path as sine bands while it runs; `build_replay_pack` stores them as a
`.rpk` replay pack, certified for the envelope it was walked for (a scanner class's band and gradient
amplitude, `envelope_of("connectom")`, and the field and tissue bounds). dmipy-replay reads the pack:
`pack.replay(seq)` contracts it with any waveform, and `pack.replay_bloch(seq)` carries the magnetisation
through the sequence's own pulses. The pack is what [SubstrateCommons](https://huggingface.co/SubstrateCommons)
distributes and what dmipy-fit's replay models fit against.

```python
from dmipy_replay import envelope_of

walk = ds.walk(ds.Cylinder(radius=4e-6, orientation=(0, 0, 1)), 2_000, T_max=0.09,
               envelope=envelope_of("connectom"), diffusivity=2e-9, seed=0, require_gpu=False)   # 90 ms of walk
pack = ds.build_replay_pack(walk, id="docs/cylinder", license="CC-BY-4.0", citation="dmipy.org")
E_pgse = pack.replay(dr.pgse([[1, 0, 0]], 0.010, 0.030, bvalues=[1e9]))
E_ogse = pack.replay(dr.ogse([[1, 0, 0]], 50.0, 0.040, shape="cosine", bvalues=[1e9]))
```

The walk depends only on the substrate, the diffusivity and the seed; the acquisition, the field,
the relaxation times and the pose are replay knobs. That invariant is why one walk answers every
sequence within its envelope. **[The replay guide](replay/index.md)** is the manual for that side: one
page per object (pack, sequence, tissue, scanner, orientation), the table of what each knob touches
and which channel it needs, [the vector-Bloch route](replay/bloch.md), images from a pack opened by
reference, and two recipes. [The workflow, end to end](start/workflow.md) runs the whole loop.

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
