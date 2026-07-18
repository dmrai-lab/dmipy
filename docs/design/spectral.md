# OGSE spectral design

## Why frequency, not just b

Two waveforms can have the **identical b-tensor** and still probe different tissue. PGSE and OGSE
(oscillating-gradient spin echo) are both *linear* encodings — same b-tensor — yet OGSE reports on
shorter length scales. The distinguishing quantity is **spectral**: to first order the diffusion
attenuation is

$$
\ln S \;\approx\; -\int_0^\infty D(\omega)\,\lvert \tilde q(\omega)\rvert^2 \, d\omega,
$$

where $\tilde q(\omega)$ is the Fourier content of the encoding wavevector $q(t)=\gamma\!\int s\,g\,dt$
and $D(\omega)$ is the **frequency-dependent** diffusivity of the restricted/exchanging tissue.
Sweeping the encoding frequency $\omega$ is therefore a direct probe of restriction and exchange —
which is exactly what OGSE is for. The b-tensor alone is blind to it.

## Designing to a spectrum

dmipy-design treats the spectrum as a first-class design target rather than assuming a pure,
monochromatic oscillation:

- **`spectral_freq=f`** drives the **RMS encoding frequency** to `f` — an OGSE-like oscillating
  waveform, for *any* b-tensor shape — using a differentiable, FFT-free constraint
  ($f_\mathrm{rms} = \tfrac{1}{2\pi}\sqrt{\gamma^2 \sum|g|^2 / \sum|q|^2}$).
- The **realized** spectrum is always reported — `spectral_rms`, and via `encoding_spectrum` the
  centroid and **bandwidth** (how monochromatic it actually is). Frequency precision is thus a
  measured, propagatable quantity, not an assumption.

```python
from dmipy_design import design_waveform_now

pgse_like = design_waveform_now(b_delta=1.0, TE=0.08)                    # f_rms ~ a few Hz
ogse      = design_waveform_now(b_delta=1.0, TE=0.08, spectral_freq=80)  # f_rms -> 80 Hz
print(ogse.spectral_rms)   # ~80 Hz (at the OGSE efficiency cost: less b than PGSE at equal TE)
```

### Vanilla vs optimized OGSE — asymmetric windows, cleaner spectrum

Exactly as for PGSE, a **symmetric** OGSE dead-times the long pre-180 window (amber below), while
the **asymmetric-window** design fills it with more oscillation periods. At the *same* b and the
*same* RMS encoding frequency, that buys two things at once: a **shorter TE** (more SNR — the
optimized echoes ~19 ms sooner here) **and a cleaner, more monochromatic encoding spectrum**,
because more periods concentrate the power at the target frequency:

![Vanilla symmetric OGSE versus the asymmetric-window optimized OGSE, same b and same 40 Hz encoding on a Siemens Prisma, playing at the same speed with their encoding power spectra side by side: the optimized fills the pre-180 window with more oscillation periods, echoes ~19 ms sooner, and concentrates its spectral power at the target frequency.](media/ogse_vanilla_vs_optimized.gif){ width="100%" }

Both waveforms are only a few periods long, so their spectra also carry low-frequency
(bulk-diffusion) content; the panel is normalised to the oscillatory band so the frequency
selectivity is what you see. That is why `spectral_rms` / `spectral_bandwidth` are *reported*
quantities — "the same frequency" can mean visibly different spectral content, and the
frequency-dependent diffusivity `D(ω)` you recover is weighted by the whole spectrum.

## Interoperability with dmipy-sim and dmipy-fit

The designed OGSE waveform is an ordinary `G(t)` — the base representation the whole ecosystem
speaks — so the loop closes with no conversion layer:

1. **Design** a deliverable OGSE waveform here (`design_waveform_now(..., spectral_freq=f)`).
2. **Simulate** it in [dmipy-sim](../sim.md): `d.to_sim_waveform()` → `simulate(...)` gives the
   Monte-Carlo ground-truth signal for that *exact* realized spectrum on a restricted substrate —
   including the spectral dispersion the b-tensor can't see.
3. **Fit** it in [dmipy-fit](../fit.md): the same waveform drives the analytical forward model, so
   an OGSE-aware fit is checked against the simulator on the identical acquisition.

Because all three read one waveform object, "design → simulate → fit" is a single pipeline: you can
optimise a frequency sweep for a tissue model, verify the recovered $D(\omega)$ against Monte
Carlo, and only then take the deliverable `.seq` to the scanner. See
[Acquisition sequences](../sequences.md) for the shared free-waveform interface.
