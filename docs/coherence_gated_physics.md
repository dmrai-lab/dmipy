# Coherence-gated physics

Most microstructure models treat the acquisition as if the magnetization were transverse for the
whole echo time: $T_2$ decays, surface relaxivity chips away at wall-adjacent spins, and the
gradient encodes diffusion — all at once, for the full duration. A **stimulated-echo** sequence
breaks that assumption. Between the storage and recall pulses the magnetization is parked *along
the longitudinal axis*, where it neither dephases nor feels the wall. dmipy makes this explicit
with a single per-time-point gate.

## The gate

Write $\chi_\perp(t)\in\{0,1\}$ for the fraction of the magnetization that is **transverse** at
time $t$. Under the idealized-pulse limit dmipy ships (instantaneous, perfect $90^\circ/180^\circ$
pulses, no off-resonance) it is a plain binary mask:

- $\chi_\perp = 1$ — magnetization is in the transverse plane. $T_2$ relaxation, **surface
  relaxivity**, and the gradient phase all accrue.
- $\chi_\perp = 0$ — magnetization is stored longitudinally. Only $T_1$ acts; there is **no
  $T_2$ loss and no surface-relaxivity loss**, and the gradient does not encode phase.

The per-compartment log-weight a walk accumulates is then

$$
\log w \;=\; -\!\int \frac{\chi_\perp(t)}{T_2}\,dt
            \;-\!\int \frac{1-\chi_\perp(t)}{T_1}\,dt
            \;-\!\int \chi_\perp(t)\,\rho\,\frac{\mathrm dA}{V}\,,
$$

with the surface-relaxivity term ($\rho$ = surface relaxivity, $\mathrm dA$ = wall contact) gated
by the *same* $\chi_\perp$ as $T_2$: relaxivity is a transverse-plane effect, so parking the
magnetization switches it off along with $T_2$.

A PGSE spin echo is transverse for the whole echo ($\chi_\perp\equiv 1$, $T_1$ never acts). A
PGSTE stores the magnetization over a mixing time $T_m$: it is transverse only over the two
encoding lobes ($\tau_\perp = 2\delta$) and longitudinal over $\tau_\parallel = T_m$.

!!! note "The idealized $\tfrac12$ amplitude"
    A stimulated echo stores half the magnetization at the storage pulse, so its recalled
    amplitude carries an idealized factor of $\tfrac12$ relative to a spin echo. dmipy-sim applies
    this $\tfrac12$ to the forward signal of a stimulated-echo waveform. It is a **global scale**:
    on the *inverse* (fitting) side it is indistinguishable from the global signal scale
    `S0_global` and changes no fitted microstructure parameter, so the analytical models leave it
    out. It matters only when you compare absolute signal levels.

## Using it

Both engines take the same PGSTE constructor (see [Acquisition sequences](sequences.md)); the
mixing time $T_m$ is the only new parameter.

```python
import numpy as np
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
import dmipy_sim

bvals = np.array([0.0, 1e9, 2e9])
dirs  = np.tile([1.0, 0.0, 0.0], (3, 1))
delta, TM = 0.01, 0.05                      # pulse duration / mixing time (s)

scheme = AcquisitionScheme.from_pgste(bvals, dirs, delta, TM)   # carries TM

# forward truth (dmipy-sim): a longitudinal T1 acts during the mixing time
E_mc = dmipy_sim.simulate(20_000, 1.7e-9, scheme.waveform,
                          dmipy_sim.FreeDiffusion(), T2=80e-3, T1=1.0)
```

On the analytical side the longitudinal interval is a compartment factor, the exact sibling of
the transverse-$T_2$ factor: `LongitudinalRelaxation` contributes $e^{-\tau_\parallel/T_1}$ with
$\tau_\parallel = T_m$, gated on the scheme carrying a mixing time (a PGSE scheme has none, so the
factor is the identity). It composes with the existing occupancy-gated $T_2$ and
surface-relaxivity factors on any compartment — see [Inverse — dmipy-fit](fit.md).

## Why it matters: surface relaxivity and permeability

The gate is not a bookkeeping nicety. It changes which spins survive to be measured, and that
interacts with membrane permeability in a way a spin echo cannot separate.

Surface relaxivity attenuates the magnetization of spins **while they are in contact with a
wall** — it is strongest for the population that spends time at membranes. But that is precisely
the population that **permeates**: a walker only crosses a membrane by being at it. So in a PGSE
acquisition, where the magnetization is transverse for the entire echo, surface relaxivity is
busy erasing the very spins that carry the exchange signal. The permeability you recover is
**depressed by relaxivity at the same surface** — two wall effects, one echo, entangled.

A stimulated echo pulls them apart. During the mixing time the magnetization is longitudinal, so
surface relaxivity is switched off — yet **diffusion and membrane crossing are unaffected by the
coherence state** (a walker's motion is set by geometry and diffusivity, not by where its
magnetization points). Wall-adjacent spins keep permeating throughout $T_m$ *without* paying the
relaxivity toll. Lengthening $T_m$ therefore lets exchange accumulate under a suppressed-relaxivity
window:

- **PGSE** mis-estimates the exchange time, because surface relaxivity acts on the wall-adjacent,
  about-to-permeate spins that carry the exchange signal (the *direction* of the error is
  contrast- and geometry-dependent).
- **PGSTE** reads exchange far more cleanly, because the mixing time accrues membrane crossing while
  the relaxivity clock is paused.

The robust, sequence-level statement is the **differential**: the PGSE exchange-time bias is
several times larger than the PGSTE one at the same surface relaxivity.

!!! warning "A consideration, not yet a calibrated correction"
    The PGSE-vs-PGSTE robustness differential is demonstrated by Monte-Carlo simulation on a
    permeable packed-sphere substrate (a companion study), but the absolute magnitude — and the
    *sign* of the residual PGSE bias — remain contingent on the membrane surface relaxivity, which
    is not independently measured for neural tissue. This is cleanest to study away from myelin —
    a myelinated substrate couples permeability to the sheath and a short myelin-water pool,
    confounding the effect. Isotropic, single-membrane substrates (the regime of
    exchange-sensitive methods such as NEXI / IMPULSED) are the natural place to characterize it.
    See the [generalized Kärger exchange derivation](derivations/karger_exchange.md) for the
    exchange model this connects to.

## Relation to $T_2$ / surface-relaxivity bias

The transverse side of the same gate is what biases diffusion and relaxometry fractions when it
is *ignored*: intra- and extra-axonal water carry different $S/V$, hence different apparent $T_2$,
so a $b=0$-normalized fraction is TE-dependent — quantified in
[Surface relaxivity & MWF](surface_relaxivity_bias.md). Coherence gating is the other half of the
picture: the transverse gate sets the $T_2$/relaxivity weighting, the longitudinal gate opens the
$T_1$/exchange window. Modeling both compartment-wise is how dmipy keeps the recovered
microstructure consistent across PGSE, PGSTE and mixed protocols.
