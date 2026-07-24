# Susceptibility

!!! note "🔬 Planned — not yet in the released public scope"
    Magnetic susceptibility is part of dmipy's physics-complete model and its roadmap, but is not
    in the released public engines yet. This page is a placeholder describing what is coming; the
    released effects are [Diffusion](diffusion.md), [Permeability & exchange](permeability.md) and
    [Surface relaxivity & relaxation](../surface_relaxivity_bias.md).

Tissue components perturb the local magnetic field — myelin in white matter (an orientation-dependent
extra-axonal law, `sin⁴θ` scaling with `B0²`) and non-heme iron in grey matter (a static-dephasing
field around iron-bearing cells) — adding phase and relaxation on top of diffusion, read through the
same substrate.

**In the [coherence-gating](coherence_gating.md) pair, susceptibility is a purely *transverse*
channel.** It enters the apparent transverse rate as the $R_2'$ term,

$$
\frac{1}{T_2^{\mathrm{app}}} = \frac{1}{T_2} + \rho_2\,\frac{S}{V} + R_2' + k_f ,
$$

so it acts only while the magnetization is transverse ($\chi_\perp{=}1$). The
[echo](../sequences.md) refocuses its *static* part, and longitudinal storage pauses the
diffusion-driven residual over the mixing time — so a stimulated echo removes it alongside surface
relaxivity, with **no** longitudinal counterpart in $1/T_1^{\mathrm{app}}$.

When released it will appear here with its forward (dmipy-sim) and inverse (dmipy-fit)
counterparts and a validation ladder, exactly like the released effects.
