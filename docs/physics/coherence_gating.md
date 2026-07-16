# Coherence gating

The other pages in this section each describe *one* loss or contrast mechanism. Coherence gating is
different in kind: it is a **meta-effect** — it does not add a new physical term, it sets **when**
each of the other effects is allowed to act.

The rule is a property of the **coherence state itself**, not of any particular sequence: whenever a
component of the magnetization lies along the **longitudinal** axis, it accrues only $T_1$ — no
$T_2$, no surface relaxivity, no susceptibility dephasing — no matter how it came to be there. Any
magnetization parked along $z$ is gated this way. Imperfect (non-ideal $90^\circ/180^\circ$) pulses
leave such longitudinal components between pulses just as surely as a deliberate storage pulse does;
a **stimulated echo (PGSTE)** is simply the sequence that exploits the effect *on purpose*, parking
(nearly) all the magnetization along $z$ for a controlled mixing time $T_m$ so that exchange accrues
while the transverse-plane effects are paused. That selective pause is what lets dmipy **separate**
effects a spin echo only ever sees in combination.

## The coherence-state gate

Write $\chi_\perp(t)\in[0,1]$ for the **fraction** of the magnetization that is transverse at time
$t$; the remaining $1-\chi_\perp$ is stored longitudinally and gated. The released engines work in
the idealized-pulse limit (instantaneous, perfect $90^\circ/180^\circ$ pulses, no off-resonance),
where $\chi_\perp$ is a clean binary mask: a [PGSE](../sequences.md) spin echo is transverse for the
whole echo ($\chi_\perp\equiv1$); a [PGSTE](../sequences.md) stores the magnetization over the mixing
time ($\chi_\perp=0$ there) and is transverse only over the two encoding lobes. (With non-ideal
pulses $\chi_\perp$ takes intermediate values — a full treatment is beyond the released
idealized-pulse scope, but the gating rule is unchanged.)

The per-compartment log-weight a walk accumulates makes the gating explicit — every transverse-plane
term is multiplied by the *same* $\chi_\perp$:

$$
\log w \;=\; -\!\int \frac{\chi_\perp(t)}{T_2}\,dt
            \;-\!\int \frac{1-\chi_\perp(t)}{T_1}\,dt
            \;-\!\int \chi_\perp(t)\,\rho\,\frac{\mathrm dA}{V}\,dt .
$$

## What each base effect does in each state

The base effects fall into three classes by how they respond to the gate:

| Base effect | Transverse ($\chi_\perp{=}1$) | Stored ($\chi_\perp{=}0$, mixing time) | Released scope |
|---|:---:|:---:|:---:|
| [Diffusion](diffusion.md) encoding | encodes gradient phase | grating decays by motion | ✅ |
| [Permeability / exchange](permeability.md) | acts | **acts** — crossing continues | ✅ |
| $T_2$ (bulk relaxation) | acts | — paused | ✅ |
| [Surface relaxivity](../surface_relaxivity_bias.md) ($T_2$-type) | acts | — paused | ✅ |
| $T_1$ (longitudinal) | recovers $M_z$ | **acts** — stored $M_z$ decays by $T_1$ | ✅ |
| [Susceptibility](susceptibility.md) ($T_2^\ast$ / off-resonance) | acts | — refocused | 🔬 |
| [Magnetization transfer](magnetization_transfer.md) | acts | **acts** — population sink | 🔬 |

- **Transverse-plane effects** — $T_2$, surface relaxivity, susceptibility-induced dephasing — act
  only while $\chi_\perp=1$. Storing the magnetization switches them off; these are the effects a
  stimulated echo can *pause*.
- **Coherence-independent effects** — diffusion and membrane permeability/exchange — depend on
  molecular motion, not on where the magnetization points, so they continue in **both** states. The
  diffusion grating imprinted before storage keeps decaying by displacement throughout $T_m$, and a
  walker keeps crossing membranes.
- **The longitudinal effect** — $T_1$ — governs the stored magnetization: during $T_m$ it is the
  *only* relaxation acting.

!!! warning "Magnetization transfer is **not** gated off"
    MT is an exchange of magnetization with a bound macromolecular pool — a **population** sink, not
    a transverse-plane dephasing. It proceeds whether the free-water magnetization is transverse or
    stored, so a stimulated echo does **not** pause it: during $T_m$, both $T_1$ and MT act. This is
    the boundary of what coherence gating buys you. It cleanly separates the *transverse* surface
    effects (surface relaxivity, susceptibility dephasing) from permeability, but a **longitudinal
    or MT-type sink at the same membrane is not separated this way** — the stimulated-echo advantage
    holds only to the extent the dominant membrane mechanism is transverse/dephasing.

## Why it matters

The headline application is separating **surface relaxivity from permeability** — two rates of the
same wall. In a spin echo, surface relaxivity erases the wall-adjacent spins that carry the exchange
signal, entangling the two. A stimulated echo lets exchange accumulate over $T_m$ while the
relaxivity clock is paused, so the exchange time is read far more robustly: the PGSE bias is several
times the PGSTE bias at the same surface relaxivity (worked through in the
[surface-relaxivity study](../surface_relaxivity_bias.md)).

The two sides of the gate are complementary. The **transverse** side is what biases
$T_2$/relaxometry and signal-fraction estimates when it is *ignored* — intra- and extra-cellular
water carry different $S/V$, hence different apparent $T_2$, so a $b=0$-normalized fraction becomes
TE-dependent. The **longitudinal** side opens the $T_1$/exchange window. Modeling both
compartment-wise — the transverse gate for $T_2$/relaxivity, the longitudinal gate for $T_1$/exchange
— is how dmipy keeps recovered microstructure consistent across PGSE, PGSTE and mixed protocols
(the [inverse side](../fit.md) adds the longitudinal interval as the exact sibling of the
transverse-$T_2$ factor).

!!! note "Released vs planned"
    Coherence gating of the released transverse effects ($T_2$, surface relaxivity) together with
    $T_1$ storage is the newest capability landing in the public engines (idealized-pulse PGSTE),
    previewed here on the development site. Gating of [susceptibility](susceptibility.md) and
    [magnetization transfer](magnetization_transfer.md) arrives with those effects — the matrix rows
    above already state how the gate treats them (susceptibility paused, MT not).
