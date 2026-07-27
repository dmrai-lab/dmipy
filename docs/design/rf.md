# B1-robust refocusing RF

The rest of dmipy-design works in the **instant-pulse** approximation — an ideal hard 180° that
inverts every spin perfectly, everywhere. A real refocusing pulse does not. Across a head the
transmit field $B_1^+$ varies by tens of percent, and off-resonance (susceptibility, $B_0$
shim) spreads the spins in frequency. A hard 180° that is exactly π at the coil centre is
under- or over-flipped everywhere else, and the spin echo it forms is incomplete — signal you
simply lose. `design_refocusing_rf` designs the *RF envelope itself* to refocus well across that
whole operating ensemble, while staying scanner-deliverable.

It is the **RF analogue of the [NOW gradient box](deliverable.md)**: same idea — maximise a
physical objective subject to the real hardware/safety limits — applied to $B_1(t)$ instead of
$G(t)$.

![Each dot is one spin in the transverse plane, coloured by the transmit strength B1⁺ it feels (0.7–1.3×); the black arrow is their vector sum, which is the signal the scanner measures, read out on the meter below. After the 90° excitation the spins dephase, the 180° pulse (shown as the B1(t) inset) flips them, and symmetric free precession refocuses them into an echo. Under the hard 180° the off-nominal-B1⁺ spins under/over-flip and stay scattered, so their sum is small (signal 0.22); the designed pulse flips them all closer to 180°, so they realign and the sum is large (signal 0.61).](media/rf_refocus.gif){ width="100%" }

New to RF pulses? The [RF pulses — watch the spins](../rf_pulses.md) page (dmipy-sim) shows what
a $B_1(t)$ envelope *is* and how the Bloch forward plays any pulse — this page is what happens
when you put an optimiser in front of that forward.

## Idealized vs real refocusing

| Idealized theory | Real hardware |
|---|---|
| instantaneous, perfect π everywhere | finite-duration pulse; flip scales with local $B_1^+$ |
| single on-resonance spin | a spread of static **off-resonance** ($B_0$, susceptibility) |
| unbounded RF | **peak $B_1$** cap (body-coil watts) and **SAR** (heating) budget |
| any shape | bandwidth / **RF slew** limited by the transmit chain |

## The objective — refocused fraction over an ensemble

The pulse is scored by a **spin-echo Bloch forward**: a 90° excitation, then free precession
through the shaped 180°, evaluated over a grid of $(B_1^+ \text{ scale} \times \text{static
off-resonance})$. The score is the **ensemble-mean transverse magnitude at the echo** — the
fraction of signal that actually refocuses. A hard 180° peaks sharply at the nominal operating
point and falls away from it; a robust pulse trades a little peak performance for a flat response
across the ensemble, and keeps coherence the hard pulse loses.

![Left and centre: each isochromat's echo projected onto the refocus axis over the (off-resonance × B1⁺ scale) plane — red refocuses, blue is anti-phase. The hard 180° concentrates refocusing at the nominal point and loses it toward the corners of the design box (dashed); the designed pulse spreads red across the box, lifting the ensemble refocused fraction from 0.22 to 0.61. Right: the two B1 envelopes — a flat hard 180° vs the band-limited designed shape, both well under the peak-B1 limit and at the 1.30× SAR budget.](media/rf_profile.png){ width="100%" }

## The deliverability box

The optimisation variable is a **band-limited** envelope — a handful of low-frequency cosine
(DCT-II) coefficients. Band-limiting bounds the RF slew and bandwidth *structurally* (the RF
analogue of a gradient slew limit), so the result stays within the transmit chain by
construction. Two soft penalties enforce the rest:

| Constraint | RF analogue of | Why it's there |
|---|---|---|
| **peak $B_1 \le B_1^{\max}$** | gradient amplitude box | body-coil / SAR-per-pulse hardware ceiling |
| **SAR $\propto \int B_1^2\,dt \le$ budget** | gradient heat limit | patient heating; set as a headroom multiple of a plain hard 180° |

## Use it

```python
from dmipy_design import design_refocusing_rf

d = design_refocusing_rf(
    rf_duration=6e-3, dt=1e-4,      # 6 ms pulse on a 100 µs RF raster
    B1_max=19e-6,                   # GE SIGNA Premier body coil ≈ 19 µT
    sar_headroom=1.30,              # ≤ 1.3× the hard-180° power
    b1_range=(0.7, 1.3), n_b1=7,    # ±30 % transmit inhomogeneity
    off_resonance_hz=250.0, n_off_resonance=7,   # ±250 Hz B0 spread
)

d.refocused_fraction        # ensemble-mean refocused signal (0–1)
d.refocused_fraction_hard   # same metric for a plain hard 180° — the baseline
d.B1                        # optimised B1 envelope, Tesla
d.peak_B1, d.sar_ratio, d.max_rf_slew   # delivered peak, SAR (× hard), RF slew
d.feasible                  # peak-B1 and SAR within box
```

For that ±30 % / ±250 Hz operating window the plain hard 180° refocuses only **0.22** of the
ensemble; the designed pulse reaches **0.61** — a **2.8× gain** — at **3.5 µT** peak (well under
the 19 µT ceiling) and exactly the **1.30×** SAR budget. Same echo time, more signal, purely from
respecting the transmit physics.

!!! note "Scope"
    This designs the **refocusing pulse in isolation** — it is not coupled to the gradient
    design. The scanner limits (`B1_max`, SAR headroom) are plain arguments; source them from the
    dmipy-sim scanner catalogue (the `[sim]` extra) if you have it. NumPy/SciPy only.

## References

Optimising an RF envelope through a Bloch / optimal-control forward is an established technique;
the band-limited + peak-$B_1$ + SAR deliverability recipe here is dmipy-design's formulation, not
lifted from an external library.

- **Optimal-control RF design.** Conolly S, Nishimura D, Macovski A. *Optimal control solutions to
  the magnetic resonance selective excitation problem.* IEEE Transactions on Medical Imaging
  **5** (1986) 106–115. [doi:10.1109/TMI.1986.4307754](https://doi.org/10.1109/TMI.1986.4307754).
- **GRAPE (gradient-ascent pulse engineering).** Khaneja N, Reiss T, Kehlet C,
  Schulte-Herbrüggen T, Glaser SJ. *Optimal control of coupled spin dynamics: design of NMR pulse
  sequences by gradient ascent algorithms.* Journal of Magnetic Resonance **172** (2005) 296–305.
  [doi:10.1016/j.jmr.2004.11.004](https://doi.org/10.1016/j.jmr.2004.11.004).
