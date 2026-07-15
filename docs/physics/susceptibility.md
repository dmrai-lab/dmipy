# Susceptibility

!!! note "🔬 Planned — not yet in the released public scope"
    Magnetic susceptibility is part of dmipy's physics-complete model and its roadmap, but is not
    in the released public engines yet. This page is a placeholder describing what is coming; the
    released effects are [Diffusion](diffusion.md), [Permeability & exchange](permeability.md) and
    [Surface relaxivity & relaxation](../surface_relaxivity_bias.md).

Tissue components (notably myelin) perturb the local magnetic field, adding an
orientation-dependent phase and relaxation on top of diffusion. The planned treatment covers the
extra-axonal susceptibility law (a `sin⁴θ` orientation dependence scaling with `B0²`) and its
cross-term with diffusion — the same substrate, read through one more physical effect.

When released it will appear here with its forward (dmipy-sim) and inverse (dmipy-fit)
counterparts and a validation ladder, exactly like the effects above.
