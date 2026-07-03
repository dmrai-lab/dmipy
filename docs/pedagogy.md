# Pedagogy — watch the spins

These are not cartoons. Each clip is a **real dmipy-sim walk**, rendered frame by frame by
`dmipy_sim.pedagogy.spin_movie`: spins random-walk through the substrate, accumulate gradient
phase, get rotated by the RF pulses, and relax by `T2`. The moving arrow is the **net signal**
— the vector sum of every spin — which is exactly the number the analytical model in dmipy-fit
predicts. The physics you fit and simulate, made visible.

```python
import dmipy_sim
from dmipy_sim import pedagogy

wf   = dmipy_sim.pgse(delta=8e-3, DELTA=25e-3, G_magnitude=0.045, bvecs=[[1, 0, 0]], n_t=240)
geom = dmipy_sim.Cylinder(radius=5e-6, orientation=(0, 0, 1))
hist = pedagogy.replay_with_history(geom, wf, 1.7e-9, T2=0.05)
pedagogy.spin_movie(hist, save="pgse.mp4")     # or "pgse.gif"
```

## PGSE — dephase, refocus, attenuate

<video autoplay loop muted playsinline controls style="width:100%;max-width:680px;border-radius:8px">
  <source src="/media/pgse.mp4" type="video/mp4">
</video>

The first gradient lobe winds the spins into a phase fan; the 180° pulse conjugates the phase;
the second lobe unwinds it. Spins that **moved** between the lobes don't fully rewind — the net
vector shrinks. In the restricted cylinder the perpendicular motion is bounded, so the
attenuation saturates: that residual is the diffusion signal the model reads.

## CPMG — the T2 decay you fit for MWF

<video autoplay loop muted playsinline controls style="width:100%;max-width:680px;border-radius:8px">
  <source src="/media/cpmg.mp4" type="video/mp4">
</video>

A train of 180° pulses forms an echo at every `TE`. With no diffusion gradient the echoes trace
the pure `T2` decay — the multi-exponential that `white_matter.t2_spectrum_mwf()` inverts into a
myelin-water fraction.

## OGSE — probing shorter times

<video autoplay loop muted playsinline controls style="width:100%;max-width:680px;border-radius:8px">
  <source src="/media/ogse.mp4" type="video/mp4">
</video>

An oscillating gradient reverses sign many times within one echo, so spins are probed over a
much shorter effective diffusion time — sensitising the signal to smaller length scales than a
single PGSE lobe.

---

The renderer is idealised (hard-pulse rotations + gradient phase + `T2`, not the full walk
kernel) purely for legibility; the **trajectories are the real Monte-Carlo walk**. Regenerate
these with `python tools/gen_pedagogy_media.py`.
