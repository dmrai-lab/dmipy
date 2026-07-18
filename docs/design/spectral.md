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
