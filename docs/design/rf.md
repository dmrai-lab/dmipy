# B1-robust refocusing RF

The rest of dmipy-design works in the **instant-pulse** approximation — an ideal hard 180° that
inverts every spin perfectly, everywhere. A real refocusing pulse does not. Across a head the
transmit field $B_1^+$ varies by tens of percent, so a hard 180° that is exactly π at the coil
centre becomes a 126° at $B_1^+=0.7$ and a 234° at $B_1^+=1.3$ — the off-nominal spins are never
properly flipped, the spin echo built on them is incomplete, and that is signal you simply lose.
`design_refocusing_rf` designs the *RF envelope itself* to flip **every** spin by ~180° across
that operating range, while staying scanner-deliverable.

It is the **RF analogue of the [NOW gradient box](deliverable.md)**: same idea — maximise a
physical objective, evaluated through the Bloch equation, subject to the real hardware limits —
applied to $B_1(t)$ instead of $G(t)$.

![Three spins are followed on the Bloch sphere (rotating frame) as each pulse plays: one weak-transmit (B1⁺ 0.7×, purple), one nominal (1.0×, black), one strong (1.3×, gold). A 180° pulse should invert every one of them, +z → −z. Under the hard 180° (left) only the nominal spin reaches the south pole; the weak and strong spins under/over-rotate and stall near the equator (Mz ≈ −0.6, not inverted). Under the designed 180° (right) — a phase-modulated, composite/adiabatic-like waveform, shown playing at the bottom — all three spiral down to −z (Mz ≈ −1). That is the robustness the optimiser buys.](media/rf_refocus.gif){ width="100%" }

New to RF pulses? The [RF pulses — watch the spins](../rf_pulses.md) page (dmipy-sim) shows what
a $B_1(t)$ envelope *is* and how the Bloch forward plays any pulse — this page is what happens
when you put an optimiser in front of that forward.

## Idealized vs real refocusing

| Idealized theory | Real hardware |
|---|---|
| instantaneous, perfect π everywhere | finite-duration pulse; flip scales with local $B_1^+$ |
| single on-resonance spin | a spread of static **off-resonance** ($B_0$, susceptibility) |
| unbounded RF | **peak $B_1$** cap (body-coil hardware limit) and **SAR** (heating) |
| any shape | bandwidth / **RF slew** limited by the transmit chain |

## The objective — per-spin refocusing fidelity

A refocusing pulse should act as a true 180° rotation for **every** spin, whatever $B_1^+$ and
off-resonance it sees. The figure of merit is the crushed spin-echo **refocusing efficiency**

$$\eta = \tfrac{1}{2}\,(1 - M_z) \in [0,1],\qquad M_z = \text{the pulse acting on } +z,$$

which is $1$ for a perfect 180° ($M_z\!\to\!-1$) and $0$ for no rotation ($\eta=|\beta|^2$ in
Shinnar–Le-Roux terms). The optimiser maximises the **mean of $\eta$ over the ensemble** of
$(B_1^+\text{ scale} \times \text{off-resonance})$, evaluated by the Bloch equation itself.

Because $\eta$ is a **per-spin scalar**, the objective cannot be gamed by cross-spin phase
cancellation — *every* spin must genuinely invert. (An earlier version maximised the coherent
signal sum $|\langle M_{xy}\rangle|$; that is gameable and produced a pulse that inverted no spin
well, so it was replaced.)

![Left: refocusing efficiency η vs B1⁺ transmit scale, on resonance — the hard 180° is a sharp peak at B1⁺=1 and collapses either side, while the designed pulse holds η≈1 flat across (and beyond) the ±30% design range. Centre: η vs off-resonance at B1⁺=1 — the designed pulse holds a flat passband across the ±250 Hz band where the hard pulse is a narrow spike. Right: the designed waveform — amplitude |B1(t)| plus a swept phase (dotted) — the composite/adiabatic-like structure that buys the robustness, versus the flat hard 180°.](media/rf_profile.png){ width="100%" }

## The deliverability box — and the price of robustness

The optimisation variable is a **band-limited complex** envelope (a few low-frequency cosine
coefficients per quadrature): amplitude *and* phase, because robust refocusing needs both (a
real, amplitude-only pulse cannot fix a wrong flip angle). Band-limiting bounds the RF slew and
bandwidth structurally.

| Limit | RF analogue of | Role |
|---|---|---|
| **peak $B_1 \le B_1^{\max}$** | gradient amplitude box | hard hardware ceiling — always enforced |
| **SAR $\propto \int \lvert B_1\rvert^2 dt$** | gradient heat limit | the **price of robustness** — see below |

Robustness costs RF **energy**: a genuinely robust 180° spends several× the energy of a minimal
hard 180° (the pulse below spends ≈40×). `sar_headroom` optionally caps that as a multiple of
the hard-180° energy; left at its default (`None`) the design is **peak-limited** — the most
robust pulse the coil can deliver — and simply *reports* the SAR it spent, so the trade is
explicit.

## Use it

```python
from dmipy_design import design_refocusing_rf

d = design_refocusing_rf(
    rf_duration=6e-3, dt=1e-4,      # 6 ms pulse on a 100 µs RF raster
    B1_max=19e-6,                   # GE SIGNA Premier body coil ≈ 19 µT (hard peak limit)
    sar_headroom=None,              # peak-limited (most robust); or e.g. 3.0 to cap SAR
    b1_range=(0.7, 1.3), n_b1=7,    # ±30 % transmit inhomogeneity
    off_resonance_hz=250.0, n_off_resonance=7,   # ±250 Hz B0 spread
)

d.refocusing_efficiency        # ensemble-mean η (0–1); 1 = every spin inverted
d.refocusing_efficiency_hard   # same metric for a plain hard 180° — the baseline
d.B1                           # optimised complex B1 envelope, Tesla
d.peak_B1, d.sar_ratio, d.max_rf_slew   # delivered peak, SAR (× hard), RF slew
d.feasible                     # peak-B1 (and SAR, if budgeted) within box
```

Peak-limited on a 19 µT body coil, the hard 180° refocuses only **η = 0.25** of the ±30 % /
±250 Hz ensemble; the designed pulse reaches **η = 1.00** — every spin inverted — at **18.3 µT**
peak (under the ceiling), for **≈42×** the RF energy of a hard 180°. Same echo time, far more
signal; the SAR is the honest cost you trade against.

!!! note "Scope"
    This designs the **refocusing pulse in isolation** — it is not coupled to the gradient
    design. The scanner limits (`B1_max`, `sar_headroom`) are plain arguments; source `B1_max`
    from the dmipy-sim scanner catalogue (the `[sim]` extra) if you have it. NumPy/SciPy only;
    `d.to_b1pulse()` hands the design to dmipy-sim's Bloch forward.

## References

Optimising an RF envelope through a Bloch / optimal-control forward is an established technique;
the band-limited + peak-$B_1$ + SAR recipe and the crushed-echo refocusing objective here are
dmipy-design's formulation, not lifted from an external library.

- **Optimal-control RF design.** Conolly S, Nishimura D, Macovski A. *Optimal control solutions to
  the magnetic resonance selective excitation problem.* IEEE Transactions on Medical Imaging
  **5** (1986) 106–115. [doi:10.1109/TMI.1986.4307754](https://doi.org/10.1109/TMI.1986.4307754).
- **GRAPE (gradient-ascent pulse engineering).** Khaneja N, Reiss T, Kehlet C,
  Schulte-Herbrüggen T, Glaser SJ. *Optimal control of coupled spin dynamics: design of NMR pulse
  sequences by gradient ascent algorithms.* Journal of Magnetic Resonance **172** (2005) 296–305.
  [doi:10.1016/j.jmr.2004.11.004](https://doi.org/10.1016/j.jmr.2004.11.004).
- **Refocusing efficiency / SLR.** Pauly J, Le Roux P, Nishimura D, Macovski A. *Parameter
  relations for the Shinnar–Le Roux selective excitation pulse design algorithm.* IEEE
  Transactions on Medical Imaging **10** (1991) 53–65.
  [doi:10.1109/42.75611](https://doi.org/10.1109/42.75611).
