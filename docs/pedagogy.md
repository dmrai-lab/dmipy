# Pedagogy — watch the spins

These are not cartoons. Each clip is a **real dmipy-sim walk on the canonical white-matter
substrate** — packed myelinated cylinders, so the walkers live in three pools:
**intra-axonal / myelin / extra-axonal**. Rendered frame by frame by
`dmipy_sim.pedagogy.spin_movie` as synced views. **On top**, one panel per compartment: the
**transverse spin cloud** (each dot is one walker's magnetisation) with the bold arrow their
vector sum. **On the bottom**, a **pulse-program player** marking the instantaneous
**90°/180° flips** and the diffusion gradient `G(t)`, with a playhead sweeping in time so you can
see exactly which event drives each motion. Sum the compartments and you get the net signal the
analytical model in dmipy-fit predicts. The physics you fit and simulate, made visible.

(The player is the transverse-only, instant-pulse counterpart of the full Bloch pulse-program
player — it shows *where* the 90°/180° fire, not a finite `B1(t)` shape.)

```python
import numpy as np, dmipy_sim
from dmipy_sim import pedagogy
from dmipy_sim.substrate import Substrate

sub = Substrate()                                    # canonical white matter
rng = np.random.default_rng(0)
outer_d = rng.gamma(sub.gamma_shape_diameter, sub.gamma_scale_diameter, 16)   # fibre diameters
ir, gr, centers = dmipy_sim.pack_myelinated_cylinders(
    0.5 * sub.g_ratio * outer_d, np.full(16, sub.g_ratio), target_packing=0.35)
L = float(np.sqrt(np.pi * np.sum((ir / gr) ** 2) / 0.35))
geom = dmipy_sim.PackedMyelinatedCylinders(ir, gr, centers, L, D_intra=sub.D_intra,
                                           D_myelin=sub.D_myelin, D_extra=sub.D_extra)

wf   = dmipy_sim.pgse(delta=8e-3, DELTA=25e-3, G_magnitude=0.05, bvecs=[[1, 0, 0]], n_t=240)
hist = pedagogy.replay_with_history(geom, wf, sub.D_intra,
                                    T2_per_comp=[sub.T2_intra, sub.T2_myelin, sub.T2_extra])
pedagogy.spin_movie(hist, save="pgse.mp4")           # or "pgse.gif"
```

## PGSE — dephase, refocus, attenuate

<video autoplay loop muted playsinline controls style="width:100%;max-width:900px;border-radius:8px">
  <source src="/media/pgse.mp4" type="video/mp4">
</video>

The first gradient lobe winds the spins into a phase fan; the 180° pulse conjugates the phase;
the second lobe unwinds it. Spins that **moved** between the lobes don't fully rewind — the net
vector shrinks. In the intra-axonal and myelin pools the perpendicular motion is bounded (the extra-axonal pool
diffuses more freely), so the attenuation saturates: that residual is the diffusion signal the
model reads — compartment by compartment.

## CPMG — the T2 decay you fit for MWF

<video autoplay loop muted playsinline controls style="width:100%;max-width:900px;border-radius:8px">
  <source src="/media/cpmg.mp4" type="video/mp4">
</video>

A train of 180° pulses forms an echo at every `TE`. With no diffusion gradient the echoes trace
the pure `T2` decay — the multi-exponential that `white_matter.t2_spectrum_mwf()` inverts into a
myelin-water fraction.

## OGSE — probing shorter times

<video autoplay loop muted playsinline controls style="width:100%;max-width:900px;border-radius:8px">
  <source src="/media/ogse.mp4" type="video/mp4">
</video>

An oscillating gradient reverses sign many times within one echo, so spins are probed over a
much shorter effective diffusion time — sensitising the signal to smaller length scales than a
single PGSE lobe.

## Magnitude, not phase — surface relaxivity below the T2 ceiling

Everything above tracks the **phase**. This tracks the **magnitude**: the `|M|` histogram of each
compartment under a CPMG train (no gradient — pure relaxation). Without surface relaxivity each
pool would slide down as a single delta at its bulk-`T2` rate; surface relaxivity gives every walker
its own wall-contact history, pushing it **below** that bulk-`T2` ceiling — and since it only ever
*subtracts*, the ceiling is a hard cap.

### The real effect, at ρ = 1.16 µm/s — zoomed

At the literature relaxivity ([Barakovic et al. 2023](https://doi.org/10.3389/fnins.2023.1209521),
`ρ ≈ 1.16 µm/s`, swept 0–2.5 in the surface-relaxivity paper) white matter is deep in the
motional-averaging limit: each pool is a **narrow spike just below its bulk-`T2` ceiling** — you
have to zoom to see it. The left panel is the full `|M|` scale (the spike hugs the ceiling); the
moving box marks the thin sliver below it; the middle/right panels blow that box up with fine bins
and a smooth **KDE** curve, so you can watch each pool's spread slowly grow as TE advances.

<video autoplay loop muted playsinline controls style="width:100%;max-width:1000px;border-radius:8px">
  <source src="/media/magnitude_zoom_cpmg.mp4" type="video/mp4">
</video>

Zoomed, the real effect is unmistakable with **no exaggeration**: **intra-axonal** sits ~4% below
its dashed bulk-`T2` ceiling, **extra-axonal** only ~1% — intra has the higher `S/V`, so more wall
contact per unit time. That gap to the ceiling *is* the surface-relaxivity apparent-`T2` shortening,
and each histogram's mean is the CPMG point `white_matter.t2_spectrum_mwf()` inverts — the
microstructure behind the T2 spectrum.

### The spread and the spatial pattern (ρ exaggerated)

The *shift* above is real; the *spread* (a fan) is tiny at physiological ρ, because white matter is
motionally averaged. To make the fan — and where it comes from — visible, here is the same setup
with `ρ` exaggerated ~30×. Left: the distribution fans out below the ceiling (**intra** stays a
narrow spike, **extra** broadens — the `ρa/D` regime), with the dashed bulk-`T2` ceiling sliding
left. Right: the same walk in space — near-wall spins **go dark first**, extra-axonal hole-interiors
**stay bright**.

<video autoplay loop muted playsinline controls style="width:100%;max-width:640px;border-radius:8px">
  <source src="/media/magnitude_cpmg.mp4" type="video/mp4">
</video>
<video autoplay loop muted playsinline controls style="width:100%;max-width:460px;border-radius:8px">
  <source src="/media/magnitude_spatial_cpmg.mp4" type="video/mp4">
</video>

(Real WM sits in the narrow-spike limit above — a ~1 pp MWF bias, not a broad fan; the broad,
diffusion-limited fan is the large-pore / porous-media regime Brownstein–Tarr came from. Substrate:
moderate-fibre packed myelin; frozen short-`T2` myelin water omitted.)

---

The renderer is idealised (hard-pulse rotations + gradient phase + `T2`, not the full walk
kernel) purely for legibility; the **trajectories are the real Monte-Carlo walk**. Regenerate
these with `python tools/gen_pedagogy_media.py`.
