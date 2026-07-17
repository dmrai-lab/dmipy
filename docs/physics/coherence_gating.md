# Coherence gating

Every other page in this section describes *one* loss mechanism. Coherence gating is different in
kind: it is a **meta-effect**. It adds no new term — it sets **when** each of the others acts,
according to where the magnetization points.

The rule is a property of the coherence state itself: whichever fraction of the magnetization lies
**transverse** accrues the transverse channels ($T_2$, surface relaxivity, susceptibility, the
transverse face of MT); whichever fraction is **stored longitudinally** accrues only the
longitudinal channels ($T_1$, and their longitudinal siblings). It makes no difference how the
magnetization came to be along $z$ — a deliberate storage pulse or the residue of an imperfect flip.
A **stimulated echo (PGSTE)** is simply the sequence that exploits this on purpose, parking the
magnetization along $z$ for a mixing time $T_m$ so the transverse channels pause while exchange keeps
running — the lever dmipy uses to **separate** effects a spin echo only sees combined.

## Two apparent rates, one gate

Write $\chi_\perp(t)\in[0,1]$ for the transverse fraction at time $t$ (the rest, $1-\chi_\perp$, is
stored). In the released idealized-pulse limit (instantaneous, perfect $90^\circ/180^\circ$ pulses)
it is a binary mask: a [PGSE](../sequences.md) spin echo is transverse throughout
($\chi_\perp\equiv1$); a [PGSTE](../sequences.md) sets $\chi_\perp=0$ across $T_m$ and is transverse
only over its two encoding lobes.

Every wall and field mechanism collapses into **two apparent rates** — one per coherence state.
While transverse, the magnetization decays at the apparent **transverse** rate

$$
\frac{1}{T_2^{\mathrm{app}}}
   = \underbrace{\frac{1}{T_2}}_{\text{bulk}}
   + \underbrace{\rho_2\,\frac{S}{V}}_{\text{surface relaxivity}}
   + \underbrace{R_2'}_{\text{susceptibility}\;🔬}
   + \underbrace{k_f}_{\text{MT, transverse}\;🔬} ,
$$

while stored, only the apparent **longitudinal** rate acts:

$$
\frac{1}{T_1^{\mathrm{app}}}
   = \underbrace{\frac{1}{T_1}}_{\text{bulk}}
   + \underbrace{\rho_1\,\frac{S}{V}}_{\text{longitudinal surface}}
   + \underbrace{k_{\mathrm{MT}}^{\parallel}}_{\text{MT, saturation transfer}\;🔬} .
$$

The gate is $\chi_\perp$ selecting between them. As the per-compartment log-weight a walk
accumulates,

$$
\log w \;=\; -\!\int_0^{T_E}\!\Big[\;\chi_\perp(t)\,\frac{1}{T_2^{\mathrm{app}}}
             \;+\;\big(1-\chi_\perp(t)\big)\,\frac{1}{T_1^{\mathrm{app}}}\;\Big]\,dt .
$$

The two rates are **exact siblings** — transverse and longitudinal faces of the same walls — each a
bulk term plus one $S/V$-weighted (or field) term per mechanism. (🔬 marks terms that arrive with
their own effect page — [susceptibility](susceptibility.md) and
[magnetization transfer](magnetization_transfer.md); the released engines carry the $T_2$, $\rho_2$,
$T_1$ and $\rho_1$ terms.)

**Diffusion and [permeability/exchange](permeability.md) are outside the gate.** They depend on
molecular motion, not on where the magnetization points, so they act in **both** states: the
diffusion grating keeps decaying by displacement through $T_m$, and walkers keep crossing membranes
while stored. That is exactly why storage separates them from the transverse wall sinks.

!!! warning "Magnetization transfer sits on both sides"
    MT (exchange with a short-$T_2$ bound pool) has **two** pathways, and the gate splits them. Its
    **transverse** pathway ($k_f$) drains the free pool during encoding — the same $S/V$-differential
    $T_2$ form as surface relaxivity — and **is** paused by storage. Its **longitudinal**
    saturation-transfer pathway ($k_{\mathrm{MT}}^{\parallel}$) exchanges $M_z$ in *both* states and
    is **not** paused. So a stimulated echo removes every *transverse* wall sink (surface relaxivity
    and the transverse face of MT) but still pays the longitudinal terms during $T_m$ — the residual,
    non-gated confound. The advantage holds to the extent the dominant mechanism is
    transverse-dephasing rather than a longitudinal population sink.

## Why it matters

The headline is separating **surface relaxivity from permeability** — two rates of the same wall. In
a spin echo, surface relaxivity ($\rho_2\,S/V$ in $T_2^{\mathrm{app}}$) erases the wall-adjacent
spins that carry the exchange signal, so the two entangle. A stimulated echo pauses the whole
$T_2^{\mathrm{app}}$ bundle over $T_m$ while exchange accrues, so the exchange time is read far more
robustly — the PGSE bias is several times the PGSTE bias at the same relaxivity (worked through in
the [surface-relaxivity study](../surface_relaxivity_bias.md)).

Both sides matter. The **transverse** rate is what biases $T_2$/relaxometry and signal-fraction
estimates when ignored — intra- and extra-cellular water carry different $S/V$, hence different
$T_2^{\mathrm{app}}$, so a $b{=}0$-normalized fraction turns TE-dependent. The **longitudinal** rate
opens the $T_1$/exchange window. Modeling both compartment-wise keeps recovered microstructure
consistent across PGSE, PGSTE and mixed protocols (the [inverse side](../fit.md) adds the
longitudinal interval as the exact sibling of the transverse factor).

!!! note "Released vs planned"
    Gating of the released transverse terms ($T_2$, surface relaxivity) with $T_1$ storage is the
    newest public capability (idealized-pulse PGSTE), previewed here on the development site. The
    susceptibility ($R_2'$) and MT ($k_f$, $k_{\mathrm{MT}}^{\parallel}$) terms arrive with their
    effect pages; the equations above already fix how the gate treats each.
