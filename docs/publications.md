# Publications

## Preprint

!!! quote "Two observables of one wall"
    **Two observables of one wall: how surface relaxivity can bias the diffusion intra-axonal
    fraction and the myelin water fraction.**
    Rutger H.J. Fick (2026). arXiv:[2607.09401](https://arxiv.org/abs/2607.09401) [physics.med-ph].

Surface relaxivity and time-dependent diffusion are two readouts of the *same* wall collisions on
one substrate: the transverse rate a microstructure model fits is a bulk rate plus a surface rate
`ρ·(S/V)`, and because intra- and extra-axonal water carry different `S/V`, their T2 differ — so
any compartment estimate normalised by a TE-weighted `b=0` is biased. The paper derives closed
forms for the interior (Brownstein–Tarr) and exterior (Novikov–Burcaw) surface rates over
myelinated cylinders, validates them with wall-counting Monte Carlo, and quantifies the resulting
bias on the diffusion intra-axonal signal fraction `f_intra` and on the myelin water fraction
(MWF). The [surface relaxivity & MWF](surface_relaxivity_bias.md) page is the reproducible
walkthrough, and every figure regenerates from the engines here.

## The original dmipy toolbox

!!! quote "Dmipy (2019)"
    **The Dmipy Toolbox: Diffusion MRI Multi-Compartment Modeling and Microstructure Recovery
    Made Easy.**
    Rutger H.J. Fick, Demian Wassermann, Rachid Deriche (2019). *Frontiers in Neuroinformatics*
    13:64. DOI:[10.3389/fninf.2019.00064](https://doi.org/10.3389/fninf.2019.00064).

The paper behind the [original 2019 toolbox](migrating.md) — the modular multi-compartment
model-design grammar that the analytical inverse ([dmipy-fit](fit.md)) carries forward. If you use
the fitting framework, please cite this alongside the specific models you compose (dmipy-fit's
[citation graph](fit.md) generates the full reference list automatically).

## Citing the Monte-Carlo engine

The forward engine's core Brownian-walk physics follows the same lineage as
[disimpy](https://github.com/kerkelae/disimpy), MISST and Camino; for basic Monte-Carlo
functionality cite those, and for the dmipy-sim extensions (permeability, surface relaxivity,
b-tensor encoding, the shared free-waveform interface) cite the dmrai ecosystem.

> Kerkelä L, Nery F, Hall M, Clark C (2020). *disimpy: A massively parallel Monte Carlo simulator
> for generating diffusion MRI data in Python.* JOSS 5(52), 2527.
