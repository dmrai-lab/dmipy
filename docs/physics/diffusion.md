# Diffusion

Spins random-walk through the geometry and accumulate phase φ = γ ∫ G_eff · r dt; the signal is
the ensemble average of e^{iφ}. Restriction, hindrance and free diffusion come out of the same walk;
the walls the walker meets are the only difference.

```python
import numpy as np, dmipy_sim as ds

seq = ds.pgse([[1, 0, 0]] * 3, 0.010, 0.030, bvalues=[0, 1e9, 2e9])
for geom in (ds.FreeDiffusion(), ds.Cylinder(radius=3e-6, orientation=(0, 0, 1))):
    E = np.asarray(ds.simulate(10_000, 1.7e-9, waveform=seq, geometry=geom, seed=0, require_gpu=False))
    print(type(geom).__name__, (E / E[0]).round(3))          # free: exp(-bD); axon: held up by the wall
```

**Forward**: `FreeDiffusion`, `Box1D`, `Sphere`, `Cylinder`, `Ellipsoid`, packed ensembles,
myelinated cylinders and [meshes](../mesh_substrates.md), under any
[acquisition](../acquisition.md): PGSE, PGSTE, OGSE, CPMG, b-tensor, free waveforms.

**Inverse**: each compartment contributes an analytical attenuation on the same object (closed
forms for PGSE, the Gaussian-phase integral of the played waveform for OGSE and b-tensor
encodings, the matrix method and replay models for the rest), composed in a
`MultiCompartmentModel` — the [model catalog](../catalog.md).

**Validated against**: analytical free, box, sphere, cylinder and ellipsoid signals, MISST
reference signals, the extra-axonal tortuosity sweep, and the
[canonical-WM parity](canonical_wm_parity.md) between the two engines.
