# Permeability & exchange

Membranes are not perfect walls. `permeability=κ` (m/s) on any closed geometry adds a Powles
(2004) bidirectional crossing: at each wall collision the walker transmits with probability
`p = min(1, 2κ d⊥ / D)`, otherwise reflects. It is baked into the walk (one walk per κ) and works on
spheres, cylinders, packed ensembles, myelin (dual wall) and [meshes](../mesh_substrates.md).

```python
import numpy as np, dmipy_replay as dr, dmipy_sim as ds

seq = dr.pgse([[1, 0, 0]] * 3, 0.005, 0.020, bvalues=[0, 1e9, 2e9])
env = dr.Envelope(name="docs", band_hz=1000.0, G_max=0.3, B0_list=(), chi_max=None, rho2_max=None,
                  max_refocusing_pulses=None)
for kappa in (None, 5e-5):                                    # one walk per permeability
    geom = ds.Cylinder(radius=3e-6, orientation=(0, 0, 1), permeability=kappa)
    walk = ds.walk(geom, 300, T_max=float(seq.T), envelope=env, diffusivity=1.7e-9, seed=0, require_gpu=False)
    pack = ds.build_replay_pack(walk, id="docs/permeable-cylinder", license="CC-BY-4.0", citation="dmipy.org")
    E = np.asarray(pack.replay(seq))
    print("kappa", kappa, (E / E[0]).round(3))                # leakier wall: closer to free
```

**Inverse**: a generalized Kärger model wraps any two compartments (`X0GeneralizedKarger`); NEXI is
its stick + zeppelin + tortuosity special case (`reference_models.nexi()`). The
[derivation](../derivations/karger_exchange.md) connects the microscopic crossing rule to the
exchange time.

**Entangled with relaxation**: permeability and surface relaxivity are two readouts of the same
wall. A model that fits exchange while ignoring the surface-relaxivity weighting between
compartments misreads the exchange clock; the [coherence gate](coherence_gating.md) is how a
stimulated echo separates them.

**Validated against**: 1-D → 2-D → 3-D permeability ladders against exact eigenvalues.
