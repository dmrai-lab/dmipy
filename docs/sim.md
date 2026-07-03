# Forward — dmipy-sim

GPU Monte-Carlo of spins diffusing under an arbitrary free waveform `G(t)`, with surface
relaxivity, membrane permeability, and T2 baked into the walk. Magnetisation is treated as
fully transverse (ideal instantaneous pulses).

```python
import numpy as np, dmipy_sim as ds

wf = ds.set_b(ds.pgse(delta=5e-3, DELTA=20e-3, G_magnitude=0.05,
                      bvecs=np.array([[1., 0, 0]]), n_t=300), b_target=np.array([1e9]))
signal = ds.simulate(50_000, diffusivity=2e-9, waveform=wf,
                     geometry=ds.Cylinder(radius=5e-6, orientation=(0, 0, 1)))
```

**Encodings:** `pgse`, `ogse`, `cpmg`, `ste`, `pte`, `trapezoidal_ogse`.
**Multi-echo:** `simulate_cpmg(n_walkers, D, cpmg_waveform, geometry)` returns the full CPMG
echo train from a *single* walk.
**Geometries:** `FreeDiffusion`, `Box1D`, `Sphere`, `Cylinder`, `Ellipsoid`, `PackedCylinders`,
`PackedSpheres`, `MyelinatedCylinder`, `PackedMyelinatedCylinders`.

Every physical effect ships a first-principles 1D→2D→3D validation ladder against exact
eigenvalues (see the repo's `examples/validation/`).
