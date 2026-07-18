# Design — dmipy-design

The **acquisition-design** layer of the dmipy ecosystem. [dmipy-sim](sim.md) simulates a signal
from a substrate and a waveform, and [dmipy-fit](fit.md) inverts it — but *which* waveform should
you play on a real scanner? dmipy-design answers that: it produces **deliverable diffusion
gradient waveforms** under real hardware limits, and the resulting waveform drops straight into
both engines.

!!! note "Newest engine — rolling out"
    dmipy-design is the acquisition-design layer; the physics and API below are current. It shares
    the **same free-waveform interface** as dmipy-sim and dmipy-fit, so a designed waveform is a
    first-class citizen everywhere in the ecosystem.

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
