# Magnetization transfer

!!! note "🔬 Planned — not yet in the released public scope"
    Magnetization transfer (MT) is part of dmipy's physics-complete model and its roadmap, but is
    not in the released public engines yet. This page is a placeholder describing what is coming;
    the released effects are [Diffusion](diffusion.md), [Permeability & exchange](permeability.md)
    and [Surface relaxivity & relaxation](../surface_relaxivity_bias.md).

A large pool of protons bound to macromolecules (myelin lipids, proteins) exchanges magnetization
with the free water pool; its ultra-short $T_2$ and the exchange rate set how strongly it drains the
observable signal — a contrast complementary to diffusion and relaxation on the same substrate.

**In the [coherence-gating](coherence_gating.md) pair, MT is the one effect the gate *splits*,**
because it has two pathways on opposite sides of the gate:

- a **transverse** pathway — the short-$T_2$ bound pool draining the free pool during encoding —
  enters the apparent transverse rate as $k_f$ (the same $S/V$-differential $T_2$ form as surface
  relaxivity), and **is** paused by storage:

$$
\frac{1}{T_2^{\mathrm{app}}} = \frac{1}{T_2} + \rho_2\,\frac{S}{V} + R_2' + k_f ;
$$

- a **longitudinal** saturation-transfer pathway enters the apparent longitudinal rate as
  $k_{\mathrm{MT}}^{\parallel}$, exchanging $M_z$ in *both* coherence states, so it is **not** paused:

$$
\frac{1}{T_1^{\mathrm{app}}} = \frac{1}{T_1} + \rho_1\,\frac{S}{V} + k_{\mathrm{MT}}^{\parallel} .
$$

A stimulated echo therefore pauses MT's transverse face during the mixing time but still pays the
longitudinal one — so MT's net gain from gating is smaller than for the purely transverse channels
(surface relaxivity, susceptibility), leaving the longitudinal term as a residual, non-gated
confound.

When released it will appear here with its forward (dmipy-sim) and inverse (dmipy-fit)
counterparts and a validation ladder, exactly like the released effects.
