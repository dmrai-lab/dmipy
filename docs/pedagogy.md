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

---

The renderer is idealised (hard-pulse rotations + gradient phase + `T2`, not the full walk
kernel) purely for legibility; the **trajectories are the real Monte-Carlo walk**. Regenerate
these with `python tools/gen_pedagogy_media.py`.
