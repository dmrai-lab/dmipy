# Your first designed sequence

Name the scanner, give the timing budget, ask for the most b a spin echo can encode at a TE. The
answer is a `ScannerSequence` the simulator plays and the scanner can run.

```python
import dmipy_sim as ds
from dmipy_design import design_waveform_now, ScannerLimits, SequenceTiming

prisma = ScannerLimits.of("prisma")                           # 80 mT/m, 200 T/m/s, from the catalogue
budget = SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3)

d = design_waveform_now(1.0, limits=prisma, TE=0.070, timing=budget, n_t=100, n_restarts=3, seed=0)
d.b_value * 1e-6, d.feasible                                  # s/mm², and every constraint met
seq = d.to_sequence()                                         # the physical gradient with its pulses
seq.b(), seq.refocusing_residual                              # the b the designer reported, refocused
```

Simulate it and fit it like any other acquisition:

```python
E = ds.simulate(10_000, 2e-9, waveform=seq, geometry=ds.FreeDiffusion(), seed=0, require_gpu=False)
float(E[0]), float(__import__("numpy").exp(-d.b_value * 2e-9))        # Stejskal–Tanner on the designed pulse
```

## Then

- **The shortest TE that reaches a b** (the SNR-optimal design): `min_te_for_b(1e9, limits=prisma)`
  — [Max-b vs min-TE](../design/snr.md).
- **Why the optimum is asymmetric**, and the constraints (slew, moments, Maxwell, PNS, heat):
  [Deliverable waveforms](../design/deliverable.md).
- **OGSE by frequency**: `spectral_freq=80` — [OGSE spectral design](../design/spectral.md).
- **A stimulated echo**: `design_stimulated_echo(1.0, limits=prisma, TM=0.05, TE=0.12)`.
- **Run it**: `design_to_pulseq(d, scanner="siemens_prisma", filename="dwi.seq")` and the offline
  acceptance report — [Run it on the scanner](../design/pulseq.md).
