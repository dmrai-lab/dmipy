# Design — dmipy-design

The **acquisition-design** layer of the dmipy ecosystem. [dmipy-sim](sim.md) simulates a signal
from a substrate and a waveform, and [dmipy-fit](fit.md) inverts it — but *which* waveform should
you play on a real scanner? dmipy-design answers that: it produces **deliverable diffusion
gradient waveforms** under real hardware limits, and the resulting waveform drops straight into
both engines.

Its waveform optimiser is a **reimplementation of [NOW](https://github.com/jsjol/NOW)** (Numerical
Optimization of gradient Waveforms; Sjölund et al. 2015), re-cast in NumPy/SciPy specifically to
**integrate with dmipy-sim and dmipy-fit**. The deliverability physics and constraints below are
established prior work (see [References](#references)) — **not ours**; what dmipy-design adds is that
ecosystem integration, the min-TE mode, and the Pulseq round-trip.

!!! note "The newest dmipy engine"
    ```bash
    pip install dmipy-design
    ```
    Source: [github.com/dmrai-lab/dmipy-design](https://github.com/dmrai-lab/dmipy-design). It
    shares the **same free-waveform interface** as dmipy-sim and dmipy-fit, so a designed waveform
    is a first-class citizen everywhere in the ecosystem.

It works in the **instant-pulse** approximation (ideal hard RF) — the same regime as the released
sim/fit scope — and focuses on the *gradient* waveform: the thing that actually encodes diffusion.

## What it does

- **[Deliverable waveforms](design/deliverable.md)** — the gap between idealized dMRI theory
  (instant, rectangular, symmetric) and what a scanner can actually play (finite slew and
  amplitude, gradient raster, asymmetric encoding windows, peripheral-nerve-stimulation and heat
  limits). The **NOW** design oracle maximises the b-value subject to the *full* deliverability
  set, so its output is hardware-realizable by construction — and exports to a scanner-runnable
  Pulseq `.seq`.
- **[OGSE spectral design](design/spectral.md)** — OGSE and PGSE share the same b-tensor; what
  distinguishes them is *spectral* content. dmipy-design targets the encoding power spectrum
  directly, and the designed waveform is simulated in dmipy-sim and fit in dmipy-fit on the same
  object — one waveform, both engines.
- **[Max-b vs min-TE (SNR)](design/snr.md)** — two dual modes: maximise b at a fixed TE, or find
  the *shortest* TE that reaches a required b. The latter is SNR-optimal, because a shorter TE
  means less $T_2$ decay before the echo.
- **[Run it on the scanner](design/pulseq.md)** — export a design to a scanner-runnable
  [Pulseq](https://pulseq.github.io/) `.seq`, checked offline (timing, PNS, b-tensor round-trip),
  so the *same* waveform you optimise and simulate is the one the scanner plays.

## One waveform, three tools

```python
from dmipy_design import design_waveform_now

d = design_waveform_now(b_delta=1.0, G_max=0.08, slew_rate_max=200.0, TE=0.08)  # LTE, Prisma
wf = d.to_sim_waveform()          # -> dmipy-sim: simulate the ground-truth signal
# the same designed scheme drives a dmipy-fit forward model / fit — no conversion layer
```

The b-tensor shape is set by `b_delta` (1 = LTE, 0 = STE, −0.5 = PTE); OGSE is a spectral
constraint on top; PGSTE reuses the same core with a stimulated-echo timing. Every design is a
gradient waveform `G(t)` — exactly the representation dmipy-sim and dmipy-fit already speak.

## References

The constrained gradient-waveform optimisation and its deliverability constraints are prior work;
dmipy-design reimplements them in NumPy/SciPy for integration with the dmipy engines and does not
claim them as original.

- **NOW — the solver.** Sjölund J, Szczepankiewicz F, Nilsson M, Topgaard D, Westin C-F, Knutsson H.
  *Constrained optimization of gradient waveforms for generalized diffusion encoding.* Journal of
  Magnetic Resonance **261** (2015) 157–168.
  [doi:10.1016/j.jmr.2015.10.012](https://doi.org/10.1016/j.jmr.2015.10.012). Reference
  implementation: [github.com/jsjol/NOW](https://github.com/jsjol/NOW).
- **Maxwell (concomitant-field) compensation.** Szczepankiewicz F, Westin C-F, Nilsson M.
  *Maxwell-compensated design of asymmetric gradient waveforms for tensor-valued diffusion
  encoding.* Magnetic Resonance in Medicine **82** (2019) 1424–1437.
  [doi:10.1002/mrm.27828](https://doi.org/10.1002/mrm.27828).
- **Peripheral nerve stimulation — the SAFE model.** Hebrank FX, Gebhardt M. *SAFE-Model — A new
  method for predicting peripheral nerve stimulations in MRI.* Proc. ISMRM **8** (2000) 2007.
  Regulatory limit: **IEC 60601-2-33** (Consolidated Ed. 3.2, 2015).
