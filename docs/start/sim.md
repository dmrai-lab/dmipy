# Your first simulation

Pick an acquisition, pick a geometry, walk the spins. The signal is the ensemble average of their
phase, from first principles.

```python
import numpy as np
import dmipy_sim as ds

seq  = ds.pgse([[1, 0, 0]] * 4, delta=0.010, Delta=0.030, bvalues=[0, 5e8, 1e9, 2e9])
geom = ds.Cylinder(radius=3e-6, orientation=(0, 0, 1))        # a 6 µm axon, gradient across it

E = ds.simulate(20_000, 1.7e-9, waveform=seq, geometry=geom, seed=0, require_gpu=False)
E = np.asarray(E) / E[0]
E                                                             # restricted: well above exp(-bD)
```

Rotate the gradient along the axon and the same walk gives free diffusion:

```python
along = ds.pgse([[0, 0, 1]] * 4, 0.010, 0.030, bvalues=[0, 5e8, 1e9, 2e9])
E_par = np.asarray(ds.simulate(20_000, 1.7e-9, waveform=along, geometry=geom, seed=0, require_gpu=False))
np.allclose(E_par / E_par[0], np.exp(-np.asarray(along.b()) * 1.7e-9), atol=0.02)   # Stejskal–Tanner
```

## Then

- **Tissue that looks like tissue**: packed myelinated axons from the cited constants, a
  `Substrate`, or a mesh — [Substrate & geometry](../substrate.md), [Meshes](../mesh_substrates.md).
- **Relaxation and surfaces**: `T2=`, `T1=` on `simulate`; `surface_relaxivity_t2=` and
  `permeability=` on any closed geometry — [Physics](../physics/index.md).
- **Walk once, replay everything**: `simulate_trajectories` → `build_replay_pack` →
  `pack.replay(seq)` for any sequence, field, orientation or relaxation — [Simulate](../sim.md).
- **Finite pulses and stimulated echoes**: `simulate_bloch` propagates the full magnetisation —
  [RF pulses](../rf_pulses.md).
- **Compare with the analytical model on the same object**: the
  [canonical white-matter parity](../physics/canonical_wm_parity.md) example.
