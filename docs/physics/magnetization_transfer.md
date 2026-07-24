# Magnetization transfer

!!! success "✅ Operational in dmipy-sim"
    Magnetization transfer (MT) is a **released** effect in the Bloch Monte-Carlo forward engine. It
    is modeled as an **emergent** effect, not an imposed two-pool kernel: free spins physically stick
    to the wall for a dwell time and exchange magnetization, and the two-pool behaviour falls out of
    the walk. See the implementation note below on the required **burn-in**.

A large pool of protons bound to macromolecules (myelin lipids, proteins) exchanges magnetization
with the free water pool; its ultra-short $T_2$ and the exchange rate set how strongly it drains the
observable signal — a contrast complementary to diffusion and relaxation on the same substrate.

## How it is implemented — emergent wall sticking

MT is not a rate law bolted onto the signal. A walking spin that reaches the wall has a probability
of **binding**: it sticks in place for a dwell time (drawn from the release rate $k_r$), during which
it carries the bound pool's ultra-short $T_2$, then releases back into free diffusion. The forward
$k_f$ and reverse $k_r$ exchange, and the bound pool's fast dephasing, are all **consequences of
spins actually sitting on the wall** — the same wall the geometry already defines — rather than a
prescribed Bloch–McConnell kernel. Because binding is tied to wall encounters, the effective rate
carries the substrate's surface-to-volume ratio, $k_f = \kappa_{\mathrm{MT}}\,(S/V)$, exactly as
surface relaxivity does.

!!! warning "Burn-in to equilibrium is required"
    A fresh walk starts with **every** spin free (the bound pool empty), which is not the thermal
    equilibrium a real acquisition sees. dmipy-sim runs an **RF-off engine burn-in** first, letting
    binding and release equilibrate until the bound-pool occupancy reaches its steady state
    $k_f/(k_f+k_r)$, and only then fires the actual sequence. dmipy-sim **tests that the occupancy
    has equilibrated before firing** — if the pool has not reached steady state the run is flagged,
    so an under-burned simulation cannot silently bias the signal.

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

The emergent Z-spectrum this produces matches a two-pool Bloch–McConnell oracle to the Monte-Carlo
noise floor once the pool is burned in. The analytical inverse (dmipy-fit) counterpart follows.
