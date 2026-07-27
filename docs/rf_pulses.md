# RF pulses — watch the spins

dmipy-sim represents an RF pulse the same way it represents a gradient: as the **actual
waveform you play on the coil**. A [`Waveform`](sim.md) is the gradient $G(t)$; a **`B1Pulse`**
is the complex transmit field

$$B_1(t) = B_{1x}(t) + i\,B_{1y}(t) \quad \text{[Tesla]}$$

on a uniform raster. The magnitude sets the nutation rate $\gamma|B_1|$; the phase sets the
rotation axis. Everything else — a 90°, a 180°, a slice-selective sinc — is just a *shape*, and
the forward plays whatever you hand it.

!!! note "The forward has no intent"
    `bloch_simulate` doesn't know a pulse is "excitation" or "refocusing" — it integrates the
    Bloch equation for the $B_1(t)$ you give it and reports what the magnetisation does. The
    *intelligence* — choosing a pulse to hit a goal under hardware limits — lives one layer up, in
    [dmipy-design's RF optimiser](design/rf.md). This page is the forward; that page is the
    optimiser in front of it.

## The zoo: shapes are conveniences on top of $B_1(t)$

```python
from dmipy_sim.rf import B1Pulse, bloch_simulate, slice_profile

# constructors are conveniences — the ground truth is always the B1(t) array
exc  = B1Pulse.hard(flip_deg=90,  duration=1e-3, dt=1e-6)          # rectangular 90°
inv  = B1Pulse.hard(flip_deg=180, duration=1e-3, dt=1e-6)          # rectangular 180°
sinc = B1Pulse.windowed_sinc(90, 2.56e-3, 1e-5, time_bw=4)         # slice-selective
free = B1Pulse.from_samples(my_complex_b1_array, dt=1e-5)          # anything at all

exc.peak_b1, exc.sar_proxy, exc.nominal_flip_deg   # amplitude / SAR / area
inv.is_deliverable("ge_signa_premier_3T")          # vs the scanner catalogue
```

## Excitation vs inversion

Hand the forward a 90° and a 180° hard pulse of the same duration — same code path, different
area. The 90° tips the magnetisation from $+z$ into the transverse plane (signal you can read);
the 180° drives it through to $-z$ (inversion, the basis of a refocusing or an IR prep).

![Bloch-sphere trajectories: a 90° hard pulse tips the magnetisation from +z to the transverse plane; a 180° hard pulse of the same duration drives it through to −z.](media/rf_zoo.gif){ width="90%" }

```python
_, _, hist = bloch_simulate(exc, df_hz=0.0, return_history=True)   # M at every raster step
Mxy, Mz = bloch_simulate(inv, df_hz=0.0)                           # end-state only
```

## Slice selectivity and the frequency dual

Under a slice-select gradient, a spin at position $z$ sees an off-resonance
$\tfrac{\gamma}{2\pi}G_{ss}z$, so the **excitation profile in space is (small-tip) the Fourier
transform of the $B_1$ envelope**. A rectangular hard pulse therefore excites a *sinc* in
frequency/space (ripples everywhere — no selectivity); a windowed **sinc** pulse excites a
near-**rectangular** slice.

![Left: slice profile under a slice-select gradient — a windowed sinc excites a sharp slice, a hard pulse of the same duration has no spatial selectivity. Right: the small-tip frequency dual — a hard (box) pulse gives a sinc frequency profile, a sinc pulse gives a rectangular passband.](media/rf_slice_spectral.png){ width="100%" }

```python
z, Mxy, Mz = slice_profile(sinc, slice_gradient=20e-3, positions_m=z)   # T/m, metres
```

## The forward in full

`bloch_simulate` integrates over an **ensemble** — off-resonance `df_hz` × transmit scale
`b1_scale` both broadcast — with optional `T1`/`T2` relaxation and a full `return_history`. That
ensemble is exactly what the [refocusing-RF optimiser](design/rf.md) scores against when it
designs a $B_1$-robust 180°.

## References

- **Small-tip-angle theorem.** Pauly J, Nishimura D, Macovski A. *A k-space analysis of small-tip-
  angle excitation.* Journal of Magnetic Resonance **81** (1989) 43–56.
  [doi:10.1016/0022-2364(89)90265-5](https://doi.org/10.1016/0022-2364(89)90265-5).
