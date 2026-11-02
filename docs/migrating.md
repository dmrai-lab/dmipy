# Migrating

## From dmipy 1.x (the 2019 toolbox)

From 2.0 the toolbox is separate packages, and `pip install dmipy` gives no importable `dmipy`
package. The analytical toolbox you knew **is** `dmipy_fit`: submodule layout and class
names are preserved, so a find-replace of `dmipy.` → `dmipy_fit.` is most of the migration.

| 1.x | now |
|---|---|
| `pip install dmipy` → `import dmipy` | `pip install dmipy` → `import dmipy_fit` (+ `dmipy_sim`, `dmipy_replay`, `dmipy_design`, `dmipy_analytic`) |
| `from dmipy.core...`, `.signal_models...`, `.distributions...` | `from dmipy_fit.core...`, `.signal_models...`, `.distributions...` |
| `acquisition_scheme_from_bvalues(bvals, bvecs, delta, Delta)` | unchanged, and now a `ScannerSequence` underneath |
| `model.fit(scheme, data)` | unchanged; add `solver="jax"` for the vectorised GPU fit |
| no forward model | `dmipy_sim` (Monte Carlo), `dmipy_replay` (the replay of its packs) and `dmipy_design` (sequence design) |

```python
# docs: skip  (the 1.x half needs the 2019 package)
from dmipy.core.modeling_framework import MultiCompartmentModel       # 1.x
from dmipy_fit.core.modeling_framework import MultiCompartmentModel   # now: same names, new namespace
```

Double-check: b-values are in s/m² (multiply s/mm² by 1e6); the 1.x `dipy`-based helpers are
gone (nothing in the engines imports `dipy` at runtime); the CSD and dispersion models keep their
names but run on JAX. To stay on the original toolbox, `pip install "dmipy<2"`.

## From 2.x to 3.0

3.0 is [six packages](packages.md). The signal side, everything that turns a stored walk into a signal or an
image, is dmipy-replay's, and so is the acquisition object every package shares; dmipy-sim produces packs; the
closed forms and the physical constants are dmipy-analytic's. A name has one spelling: a name that moved is
refused by name, and the refusal names its one spelling and the import that brings it.

| 2.x | 3.0 |
|---|---|
| `dmipy_sim.pgse`, `pgste`, `ogse`, `cpmg`, `gre`, `ste`, `pte`, `splice`, `dmipy_sim.sequences` | `dmipy_replay.pgse`, ..., `dmipy_replay.sequences` |
| `ScannerSequence`, `Protocol`, `Encoding`, `Prescription`, `RFEvent`, `RFSchedule`, `B1Pulse`, `SequenceTiming`, `ScannerLimits`, `set_b` from `dmipy_sim` | the same names from `dmipy_replay` |
| `dmipy_sim.acquisition.rf`, `.scanners`, `.timing`; `dmipy_sim.sequences.pulseq.from_pulseq` | `dmipy_replay.acquisition.rf`, `.scanners`, `.timing`; `dmipy_replay.sequences.pulseq.from_pulseq` (the writer, `to_pulseq`, is `dmipy_sim.sequences.pulseq`'s) |
| `dmipy_sim.ReplayPack`, `read_rpk`, `dmipy_sim.phantom`, the pose and study modules of `dmipy_sim.replay` | `dmipy_replay.ReplayPack`, `read_rpk`, `dmipy_replay.phantom`, `dmipy_replay.replay.pose`, `.study`, `.so3`, `.fod` |
| `dmipy_sim.spec.tissue.Tissue`, `dmipy_sim.spec.SubstrateSpec` | `dmipy_replay.Tissue`, `dmipy_replay.SubstrateSpec` |
| `walk_spec(spec, n, T)`, `simulate_trajectories(...)` | `dmipy_sim.walk(spec, n, T_max=, envelope=envelope_of("prisma"))`: one producer, the envelope required |
| `build_replay_pack(walk, K=)` | `dmipy_sim.build_replay_pack(walk)`: the band is the envelope's |
| `simulate_bloch(n, D, seq, geometry)` | `pack.replay_bloch(seq, b1_scale=, off_resonance_T=)` on a pack of the walk ([the vector-Bloch route](replay/bloch.md)) |
| `pack.replay(seq, T2=, B0=, b0_dir=, chi_iso=)` | `pack.replay(seq, tissue=Tissue(T2={pool: seconds}, chi_iso=...), scanner=B0, orientation=...)` |
| `calc_b(seq)`, `calc_btensor(seq)` | `seq.b()`, `seq.btensor()` |
| `GAMMA` from `dmipy_sim`, `dmipy_sim.math.matrix_method`, the MT forms of `dmipy_sim.engine.mt` | `dmipy_analytic.constants.GAMMA`, `dmipy_analytic.restricted.matrix_method`, `dmipy_analytic.relaxation` |
| `MyelinatedCylinder(D_intra=, D_extra=, D_myelin=, water_fractions=)`, pool-wide `T2_intra=` scalars | `compartments=Compartments(intra=Pool(D=, T2=), extra=Pool(...), myelin=Pool(...))` |
| the spec's `Pool` in dmipy-replay; `columnar.Source` | `PoolSpec`; `columnar.ColumnSource` |
| `dmipy_design.certify.ReplayEnvelope`, `replay_envelope()` | `DeliverableSet`, `deliverable_set()` |
| `dmipy_fit.audit.biophysical_constants` | `dmipy_sim.substrate.biophysical_constants` |

## The acquisition, one object

The acquisition is one object, `ScannerSequence`, built by the builders and read by every package
([Acquisition](acquisition.md)):

| 2.x | 3.0 |
|---|---|
| `Sequence.from_pgse(bvals, dirs, delta, Delta)` | `dmipy_replay.pgse(dirs, delta, Delta, bvalues=bvals)` |
| `Sequence.from_ogse(..., n_cycles=)` | `dmipy_replay.ogse(dirs, f, sigma, shape="cosine")`, whole periods, σ per block |
| `Sequence.from_cpmg(...)`, `from_btensor_ste/pte` | `cpmg(...)`, `ste(sigma)`, `pte(normal, sigma)` |
| `set_b(pgse(delta=, DELTA=, G_magnitude=, bvecs=), b)` | `pgse(dirs, delta, Delta, bvalues=b)` |
| `scheme.waveform` (fit → sim) | `scheme.protocol`; `AcquisitionScheme(seq)` |
| `Waveform`, `BlochSequence`, `rf_events=`, `echo_idx=`, `refocus_time=` | fields and derived properties of the one object (`rf`, `readout`, `echo_idx`, `rf.refocus_time`) |
| `design_waveform_now(G_max=, slew_rate_max=)` | `design_waveform_now(limits=ScannerLimits.of("prisma"))` |
| `design.to_sim_waveform()` | `design.to_sequence()` |
| `HardwareConstraints` (design) | `dmipy_replay.ScannerLimits` |
