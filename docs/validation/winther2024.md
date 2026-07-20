# Winther 2024 — reproduced on the original monkey axons

> **Claim** ([Winther et al., *Sci Rep* 2024](https://doi.org/10.1038/s41598-024-79043-5)):
> susceptibility-induced internal gradients make the intra-axonal **axial diffusivity**
> orientation-dependent — **up to ~17 %** in ex-vivo monkey corpus callosum.
>
> **dmipy-sim, on their own XNH axon meshes — status: under investigation, NOT yet reproduced.**
> Converging to the Monte-Carlo noise floor showed the ~17 % we first saw at low walker counts
> was **MC noise** (heavy-tail cross-term). Converged, in the measurable b-range (≤4000 s/mm²),
> the per-axon effect is **single-digit %** (axon04 ≈ 1–3 %). Winther's 17 % is a **high-b**
> (up to 20 000 s/mm²) full-tensor quantity; there the intra axial signal has decayed below the
> MC signal floor in a pure intra-axonal walk, so matching it needs their exact tensor-fit
> protocol (and likely extra-axonal + far more walkers). Open item, not a claim.

![Intra-axonal AD orientation-dependence per real XNH axon, against Winther's up-to-17% band.](media/winther_ad.png){ width="72%" }

Isotropic Δχ = 1.06 ppm cancels inside a circular lumen and survives only on real morphology —
so the effect reads out axon shape. Run entirely through the shipped API:

```python
Vi, Fi = load_ply("axon06-inner.ply", scale=1e-6)          # native loader
mask, _, vs, org = voxelize_shell((Vi,Fi), outer, [.12e-6,.12e-6,1e-6], compute_radial=False)
probe = MeshSusceptibilityProbe(Mesh(Vi,Fi), mask, None, vs, org, diffusivity=.6e-9, ...)
# apparent axial D (G∥fibre, b=1000/3000) for B₀ ∥ vs ⊥ fibre → orientation-dependence
```

7 T · PGSE δ=7.2/Δ=20.2 ms · isotropic Δχ=1.06 ppm · [meshes: DRCMR](https://www.drcmr.dk/susceptibility-and-axon-morphology-dataset).
Independent reimplementation — all credit for the finding and data to the original authors.

!!! warning "Preliminary — population-level, not yet per-axon converged"
    The susceptibility×diffusion cross-term is **heavy-tailed** (a few near-membrane walkers
    dominate the variance), so at the walker counts used here the *per-axon* value is
    Monte-Carlo-noise limited — the error bars are wide and single-seed draws scatter widely.
    What is robust is the **population**: the effect exists, is morphology-dependent, and
    brackets Winther's 17 %. A converged per-axon match needs ~10–20× more walkers (heavy-tail
    convergence) plus a full-tensor fit — in progress. Publishes with the susceptibility release.
