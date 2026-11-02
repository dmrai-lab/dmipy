# Publications

## The replay paper

!!! quote "Replayable Monte Carlo MRI (2026)"
    **Replayable Monte Carlo MRI: From Persistent Tissue Microphysics to Queryable Virtual Phantoms.**
    Rutger H.J. Fick (2026). Preprint.<!-- ARXIV_URL: the replay paper's arXiv link goes here once it has an identifier -->

The method under dmipy-sim's replay packs and dmipy-replay: a Monte-Carlo walk stored once as the sine-band
projections of every walker's path, its pool and its wall contact, certified, and replayed against any
acquisition, tissue and scanner within its certificate. Its DiSCo phantom is the
[DiSCo Space](https://huggingface.co/spaces/rfick/disco-replay), and its packs are on
[SubstrateCommons](https://huggingface.co/SubstrateCommons). The [replay guide](replay/index.md) is the manual.

## Surface relaxivity

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
walkthrough; the paper's figure scripts are in `papers/surface_relaxivity_bias/`.

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
