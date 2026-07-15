# Diffusion

**Status: ✅ released.** The core effect — water molecules diffusing, and the gradient waveform
`G(t)` encoding their displacement into signal attenuation.

## Forward (dmipy-sim)

Spins random-walk through the geometry and accumulate phase `φ = γ∫G·r dt`; the ensemble signal
is `S/S₀ = ⟨cos φ⟩`, from first principles. Restriction, hindrance and free diffusion all emerge
from the same walk — the walls the walker meets are the only difference.

- **Free / hindered / restricted** in `FreeDiffusion`, `Box1D`, `Sphere`, `Cylinder`,
  `Ellipsoid`, packed ensembles, myelinated cylinders, and arbitrary
  [meshes](../mesh_substrates.md).
- **Arbitrary encoding** — PGSE, OGSE, b-tensor (LTE/PTE/STE) and free `G(t)`; see
  [Acquisition sequences](../sequences.md).

See the [forward-engine overview](../sim.md).

## Inverse (dmipy-fit)

Each compartment contributes an analytical attenuation `E_diff(b)` (or the b-tensor generalisation),
combined in a `MultiCompartmentModel` and fit on the GPU. Orientation dispersion (Watson / Bingham),
diameter distributions, CSD and the named literature models (NODDI, SMT, NEXI, VERDICT, SANDI, …)
are all built on this — see the [inverse overview](../fit.md) and the [Model catalog](../catalog.md).

## Validated against

Free/box/sphere/cylinder/ellipsoid diffusion vs analytical and MISST reference signals, and the
extra-axonal tortuosity scale sweep — see the sim repo's `examples/validation/` and the
[canonical-WM parity example](../examples/canonical_wm_parity.md).
