# Permeability & exchange

**Status: ✅ released.** Membranes are not perfect walls — water crosses them, and that exchange
between compartments leaves a measurable, time-dependent signature.

## Forward (dmipy-sim)

`permeability=κ` (m/s) on any closed geometry adds a **Powles (2004)** bidirectional crossing:
at each wall collision the walker transmits with probability `p = min(1, 2κ·d⊥/D)`, otherwise
reflects. It is baked into the walk (one walk per κ) and works on spheres, cylinders, packed
ensembles, myelin (dual-wall) and [meshes](../mesh_substrates.md). The
[generalized Kärger derivation](../derivations/karger_exchange.md) connects the microscopic
crossing rule to the macroscopic exchange time.

## Inverse (dmipy-fit)

Exchange is fit with a generalized **Kärger** model (`X0GeneralizedKarger`, wrapping any two
compartments); **NEXI** is the stick + zeppelin + tortuosity special case
(`reference_models.nexi()`), analytical and on the GPU — see the [Model catalog](../catalog.md).

## Why it's entangled with relaxation

Permeability and **surface relaxivity** are two readouts of the *same* wall. A model that fits
exchange while ignoring the surface-relaxivity weighting between compartments can misread the
exchange clock — the [surface-relaxivity study](../surface_relaxivity_bias.md) and the
[preprint](../publications.md) quantify this coupling on the intra-axonal fraction and the myelin
water fraction.

## Validated against

First-principles 1D→2D→3D permeability ladders against exact eigenvalues (the sim repo's
`slow`-marked `tests/validation/`).
