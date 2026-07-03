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

## Magnitude, not phase — surface relaxivity fans the T2 spike

Everything above tracks the **phase**. This one tracks the **magnitude**: the `|M|` histogram of
each compartment under a CPMG train (no gradient — pure relaxation), so you watch surface
relaxivity turn a spike into a distribution.

<video autoplay loop muted playsinline controls style="width:100%;max-width:900px;border-radius:8px">
  <source src="/media/magnitude_cpmg.mp4" type="video/mp4">
</video>

At `t=0` every spin sits at `|M|=1` — a spike. With no surface relaxivity each compartment would
just slide down as one delta at its bulk-`T2` rate. **Surface relaxivity gives every walker its own
wall-contact history**, so the spike fans out — capped on the right at the bulk-`T2` value, because
relaxivity only ever *subtracts*. The **dashed line** is that bulk-`T2` ceiling (where a
zero-wall-contact spin would sit), sliding left at the bulk rate; the **gap between the line and
the histogram is exactly the surface-relaxivity effect**. And the two pools fan *differently*: **intra-axonal** (small
lumen, high `S/V`) is motionally averaged — it stays a narrow spike that just slides left;
**extra-axonal** (larger, more heterogeneous space) is diffusion-limited — it spreads into a broad
distribution. The width is set by `ρ·a/D`. The **mean** of each histogram at echo *k* is exactly the
CPMG point that `white_matter.t2_spectrum_mwf()` inverts — the microstructure behind the T2 spectrum.

!!! warning "The fan is exaggerated — real white matter barely broadens"
    This clip uses `ρ ≈ 40 µm/s` purely so the distribution is *visible*. The literature axolemma
    relaxivity is `ρ ≈ 1.16 µm/s` ([Barakovic et al. 2023](https://doi.org/10.3389/fnins.2023.1209521);
    swept 0–2.5 µm/s in the surface-relaxivity paper), at which — with µm-scale pores — white matter
    sits **deep in the motional-averaging limit** (`ρa/D ≈ 0.002`): the spike barely widens and surface
    relaxivity acts as a small **apparent-T2 shortening** (a ~1 pp MWF bias), *not* a broad fan. The
    broad, diffusion-limited fan shown here is the large-pore regime (the porous-media setting
    Brownstein–Tarr came from). Substrate: moderate-fibre packed myelin; myelin water (frozen short-`T2`)
    is omitted.

---

The renderer is idealised (hard-pulse rotations + gradient phase + `T2`, not the full walk
kernel) purely for legibility; the **trajectories are the real Monte-Carlo walk**. Regenerate
these with `python tools/gen_pedagogy_media.py`.
