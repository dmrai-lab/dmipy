# Design — dmipy-design

Which waveform should the scanner play? dmipy-design answers with **deliverable** diffusion
gradient waveforms: optimised under a named scanner's limits and a real timing budget, returned
as the same `ScannerSequence` the simulator and the fitter read.

```python
from dmipy_design import design_waveform_now, ScannerLimits, SequenceTiming

d = design_waveform_now(1.0, limits=ScannerLimits.of("prisma"), TE=0.080,        # LTE, Prisma
                        timing=SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3),
                        n_t=100, n_restarts=3, seed=0)
d.b_value, d.feasible, d.max_slew, d.max_amplitude      # every constraint met, at machine precision
seq = d.to_sequence()                                   # play it, simulate it, fit against it
```

The optimiser is a NumPy/SciPy reimplementation of **NOW** (Sjölund et al. 2015): maximise
b = gᵀQg with active-set SQP under slew, amplitude, refocusing, moment nulling, b-tensor shape,
Maxwell, spectral, PNS (SAFE) and heating constraints, with analytic Jacobians. The physics of
deliverability is prior work; what dmipy-design adds is the ecosystem integration, the min-TE
mode, the stimulated-echo layout, the refocusing-RF designer and the Pulseq round trip.

## What it does

- **[Deliverable waveforms](design/deliverable.md)** — the constraint set, why each exists, and
  why the optimum is asymmetric once the timing budget is real.
- **[OGSE spectral design](design/spectral.md)** — target the encoding frequency directly.
- **[Max-b vs min-TE](design/snr.md)** — the most b at a TE, or the shortest TE for a b.
- **[B1-robust refocusing RF](design/rf.md)** — an adiabatic-plus-GRAPE 180 scored by the
  vector-Bloch forward.
- **[Run it on the scanner](design/pulseq.md)** — export, offline acceptance, round trip.

Every designer takes `limits=` (dmipy-sim's `ScannerLimits`: the cited catalogue, whose SAFE
coefficients the PNS constraint reads) and `timing=` (dmipy-sim's `SequenceTiming`). A
stimulated echo is `design_stimulated_echo(b_delta, limits=, TM=, TE=)`; a substrate-informed
waveform (maximise the contrast between two replay packs) is
`replay_design.design_discriminating_waveform`.

## References

- Sjölund J, Szczepankiewicz F, Nilsson M, Topgaard D, Westin C-F, Knutsson H. *Constrained
  optimization of gradient waveforms for generalized diffusion encoding.* JMR 261 (2015).
- Szczepankiewicz F, Westin C-F, Nilsson M. *Maxwell-compensated design of asymmetric gradient
  waveforms for tensor-valued diffusion encoding.* MRM 82 (2019).
- Hebrank FX, Gebhardt M. *SAFE-model — a new method for predicting peripheral nerve stimulations
  in MRI.* Proc. ISMRM 8 (2000). Regulatory limit: IEC 60601-2-33.
