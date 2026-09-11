# Physics

One signal carries many effects at once. dmipy reads every one of them out of the **same
substrate** and the **same acquisition**: each is walked forward in [dmipy-sim](../sim.md) and
inverted analytically in [dmipy-fit](../fit.md), and each ships with a validation ladder against
an exact result.

| Effect | Forward (sim) | Inverse (fit) | Validated against |
|---|---|---|---|
| [Diffusion](diffusion.md) | restricted / hindered / free walk under `G_eff(t)` | `E_diff` per compartment, any family | eigenfunction series, MISST |
| [Permeability & exchange](permeability.md) | Powles membrane crossing | generalized Kärger, NEXI | 1-D → 3-D exact eigenvalues |
| [Surface relaxivity & MWF](../surface_relaxivity_bias.md) | Brownstein–Tarr wall loss + T2 | occupancy-gated T2 / ρ factors | Brownstein–Tarr modes |
| [Coherence gating](coherence_gating.md) | the schedule's `chi_perp` selects the rate | T1 storage as the sibling of T2 | PGSTE vs PGSE laws |
| [Susceptibility](susceptibility.md) | off-resonance field on the walk (spheres, myelin, grid) | R₂′ transverse term | sphere / hollow cylinder analytics, Winther 2024 |
| [Magnetization transfer](magnetization_transfer.md) | emergent wall sticking, short-T2 bound pool | two-pool Z-spectrum | full Bloch–McConnell oracle |

The [analytical-vs-Monte-Carlo parity page](canonical_wm_parity.md) runs the canonical white
matter through both engines on one object and shows the agreement, for diffusion and for surface
relaxivity.

**Why one footing matters.** Two effects reading the same wall (diffusion and relaxation,
exchange and surface relaxivity) bias each other's numbers when a model accounts for only one. The
[surface-relaxivity study](../surface_relaxivity_bias.md) is the worked example; the
[coherence gate](coherence_gating.md) is the lever that separates them.
