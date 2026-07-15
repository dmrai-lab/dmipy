# Forward — dmipy-sim

The Monte-Carlo **ground truth**. Spins random-walk through an explicit tissue geometry and
accumulate phase under an arbitrary free gradient waveform `G(t)`; the ensemble signal is
`S/S₀ = ⟨cos φ⟩`, from first principles with no analytical shortcut. **Surface relaxivity**,
**membrane permeability** and **T2** are baked into the walk. Magnetisation is treated as fully
transverse (ideal instantaneous pulses).

```python
import numpy as np, dmipy_sim as ds

wf = ds.set_b(ds.pgse(delta=5e-3, DELTA=20e-3, G_magnitude=0.05,
                      bvecs=np.array([[1., 0, 0]]), n_t=300), b_target=np.array([1e9]))
signal = ds.simulate(50_000, diffusivity=2e-9, waveform=wf,
                     geometry=ds.Cylinder(radius=5e-6, orientation=(0, 0, 1)))
```

- **Encodings:** `pgse`, `ogse`, `cpmg`, `ste`, `pte`, `trapezoidal_ogse` — factory constructors
  over the free waveform (`G(t)` of shape `(n_measurements, n_t, 3)`, the base representation).
- **Multi-echo:** `simulate_cpmg(n_walkers, D, cpmg_waveform, geometry)` returns the full CPMG
  echo train from a *single* walk.
- **Substrate properties:** set `surface_relaxivity_t2=ρ` / `permeability=κ` on any closed
  geometry — baked into the walk (one walk per ρ/κ).
- **Noise:** Rician / non-central-χ measurement noise (`add_rician_noise`, `add_nc_chi_noise`).
- **Sequence I/O:** Pulseq `.seq` interop + per-vendor gradient/RF/SAR deliverability limits.

### Geometries

| Geometry | Restriction | Surface relaxivity | Permeability |
|---|---|:---:|:---:|
| `FreeDiffusion` | none | — | — |
| `Box1D` | 1-D slab | ✓ | — |
| `Sphere`, `Cylinder`, `Ellipsoid` | closed wall | ✓ | ✓ |
| `PackedCylinders`, `PackedSpheres` | periodic ensemble | ✓ | ✓ |
| `MyelinatedCylinder`, `PackedMyelinatedCylinders` | multi-wall myelin | ✓ | ✓ dual-wall |
| `Mesh` (load a `.ply`) | arbitrary closed **or** 3-D-periodic mesh | ✓ | ✓ |

Load an arbitrary microstructure with `Mesh.from_ply(...)` — spatially accelerated (≈10⁶ triangles
tractable), closed or 3-D periodic. See **[Mesh substrates](mesh_substrates.md)**.

---

## What this adds over the original dmipy

The 2019 dmipy had **no forward model** — it fit analytical compartment signals but could not
*generate* a ground-truth one. dmipy-sim is that missing half, and it reads the **same**
`Waveform` and substrate objects as the analytical [dmipy-fit](fit.md), so a fit and a simulation
built from the same parameters describe the same tissue with no conversion layer. That is what
lets every analytical model be checked, effect by effect, against Monte Carlo — the
[canonical-WM parity example](examples/canonical_wm_parity.md) shows the agreement.

- **First-principles restriction** in spheres, cylinders, ellipsoids, packed ensembles and
  multi-wall myelin — and in **arbitrary meshes**.
- **Surface relaxivity** (Brownstein–Tarr, interior + exterior) and **membrane permeability /
  exchange** (Powles) baked into the walk — the ground truth for the factors dmipy-fit fits.
- **Arbitrary-waveform / b-tensor** encoding (OGSE, LTE/PTE/STE, free `G(t)`) — see
  **[Acquisition sequences](sequences.md)** and **[Substrate & geometry](substrate.md)**.
- **Watch the spins** — real Monte-Carlo-walk movies of the intra / myelin / extra pools in
  **[Pedagogy](pedagogy.md)**.

Every physical effect ships a first-principles 1D→2D→3D validation ladder against exact
eigenvalues (the repo's `examples/validation/`).

### Current scope (this release)

The **mission** is a physics-complete, sequence- and substrate-agnostic forward model — the free
waveform `G(t)` and an arbitrary substrate as the base representation, every physical effect on
the same footing — paired with its analytical inverse. *This release* is the
transverse-magnetisation slice: diffusion + T2 + surface relaxivity + permeable exchange, with
ideal instantaneous pulses. Susceptibility, gradient-/stimulated-echo and T1 are part of the
model but not in the released public scope yet — the boundary above is a *release* boundary, not
the ceiling.
