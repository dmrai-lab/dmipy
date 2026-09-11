# Migrating

## From dmipy 1.x (the 2019 toolbox)

dmipy 2.x split the toolbox into engines, and `pip install dmipy` no longer gives an importable
`dmipy` package. The analytical toolbox you knew **is** `dmipy_fit`: submodule layout and class
names are preserved, so a find-replace of `dmipy.` → `dmipy_fit.` is most of the migration.

| 1.x | now |
|---|---|
| `pip install dmipy` → `import dmipy` | `pip install dmipy` → `import dmipy_fit` (+ `dmipy_sim`, `dmipy_design`) |
| `from dmipy.core...`, `.signal_models...`, `.distributions...` | `from dmipy_fit.core...`, `.signal_models...`, `.distributions...` |
| `acquisition_scheme_from_bvalues(bvals, bvecs, delta, Delta)` | unchanged, and now a `ScannerSequence` underneath |
| `model.fit(scheme, data)` | unchanged; add `solver="jax"` for the vectorised GPU fit |
| no forward model | `dmipy_sim` (Monte Carlo) and `dmipy_design` (sequence design) |

```python
# docs: skip  (the 1.x half needs the 2019 package)
from dmipy.core.modeling_framework import MultiCompartmentModel       # 1.x
from dmipy_fit.core.modeling_framework import MultiCompartmentModel   # now: same names, new namespace
```

Double-check: b-values are in s/m² (multiply s/mm² by 1e6); the 1.x `dipy`-based helpers are
gone (nothing in the engines imports `dipy` at runtime); the CSD and dispersion models keep their
names but run on JAX. To stay on the original toolbox, `pip install "dmipy<2"`.

## From 2.x to the sequence object (the 3.0 line)

The acquisition became one object, `ScannerSequence`, built by the simulator's builders and read
by every engine ([Acquisition](acquisition.md)). The old spellings are gone, not aliased:

| 2.x | now |
|---|---|
| `Sequence.from_pgse(bvals, dirs, delta, Delta)` | `dmipy_sim.pgse(dirs, delta, Delta, bvalues=bvals)` |
| `Sequence.from_ogse(..., n_cycles=)` | `dmipy_sim.ogse(dirs, f, sigma, shape="cosine")`, whole periods, σ per block |
| `Sequence.from_cpmg(...)`, `from_btensor_ste/pte` | `cpmg(...)`, `ste(sigma)`, `pte(normal, sigma)` |
| `set_b(pgse(delta=, DELTA=, G_magnitude=, bvecs=), b)` | `pgse(dirs, delta, Delta, bvalues=b)` |
| `scheme.waveform` (fit → sim) | `scheme.protocol`; `AcquisitionScheme(seq)` (sim → fit) |
| `Waveform`, `BlochSequence`, `rf_events=`, `echo_idx=`, `refocus_time=` | fields and derived properties of the one object (`rf`, `readout`, `echo_idx`, `rf.refocus_time`) |
| `run_bloch_sequence(seq, ...)`, `spin_echo(TE)` | `simulate_bloch(n, D, seq, geometry)` on any `ScannerSequence` |
| `dmipy_sim.rf` | `dmipy_sim.acquisition.rf` |
| `design_waveform_now(G_max=, slew_rate_max=)` | `design_waveform_now(limits=ScannerLimits.of("prisma"))` |
| `design.to_sim_waveform()` | `design.to_sequence()` |
| `HardwareConstraints` (design) | `dmipy_sim.ScannerLimits` |

Until the 3.0 wheels ship, this site at `/dev/` documents the engines' git `main`; the root site
documents the released 2.x line.
