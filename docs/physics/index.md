# Physics effects

One MRI signal carries **many** physical effects at once — diffusion, relaxation, exchange,
susceptibility. dmipy's mission is to put them on the **same footing**: every effect read out of
the *same* substrate, each simulated forward in [dmipy-sim](../sim.md) and inverted analytically
in [dmipy-fit](../fit.md). This page is the map of that programme — what's released, and what's
next.

| Effect | Status | Forward (sim) | Inverse (fit) |
|---|:---:|---|---|
| **[Diffusion](diffusion.md)** | ✅ Released | restricted / hindered / free random walk | `E_diff(b)` per compartment |
| **[Permeability & exchange](permeability.md)** | ✅ Released | Powles membrane crossing | Kärger / NEXI |
| **[Surface relaxivity & relaxation](../surface_relaxivity_bias.md)** | ✅ Released | Brownstein–Tarr wall loss + T2 | occupancy-gated `T2` / `ρ` factors |
| **[Susceptibility](susceptibility.md)** | 🔬 Planned | — | — |
| **[Magnetization transfer](magnetization_transfer.md)** | 🔬 Planned | — | — |

!!! note "Released vs planned"
    ✅ **Released** effects are in the public engines today and validated effect-by-effect
    (analytics ↔ Monte Carlo). 🔬 **Planned** effects are part of the physics-complete model and
    the internal roadmap, but not yet in the released public scope — their pages describe what is
    coming. The boundary is a *release* boundary, not the ceiling.

Every released effect ships with a first-principles validation ladder and a matched analytical
inverse, so a number that comes out of a fit can be traced to the wall collisions that produced
it. The [surface-relaxivity study](../surface_relaxivity_bias.md) is the worked example of *why
this matters* — two effects (diffusion and relaxation) reading the same wall, and the bias that
follows when a model accounts for only one.

## The orthogonal axis: coherence gating

The effects above are *what* the signal loses. **[Coherence gating](coherence_gating.md)** is a
meta-effect that sets *when* each acts. The transverse wall/field channels collapse into one apparent
rate $1/T_2^{\mathrm{app}} = 1/T_2 + \rho_2\,S/V + R_2' + k_f$, their longitudinal siblings into
another $1/T_1^{\mathrm{app}} = 1/T_1 + \rho_1\,S/V + k_{\mathrm{MT}}^{\parallel}$, and the coherence
state $\chi_\perp$ selects between them — the transverse bundle acts only while transverse, the
longitudinal bundle only while stored, and diffusion and permeability/exchange act in both. A
stimulated echo (PGSTE) parks the magnetization along $z$ for a mixing time to pause the whole
$T_2^{\mathrm{app}}$ bundle while exchange keeps running — the lever dmipy uses to *separate* effects
a spin echo sees only in combination, most directly surface relaxivity from permeability.
