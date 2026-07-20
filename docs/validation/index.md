# Validation &amp; benchmarks — reproducing the literature

`dmipy-sim` is a **forward** engine: walkers diffuse through a substrate under a real `G(t)`
while phase, relaxation and susceptibility accrue. The only way to trust such an engine is to
show it reproduces (i) **exact analytical** results where they exist, and (ii) the **published
Monte-Carlo / experimental findings** of other groups — ideally reimplemented *from scratch*,
so agreement is meaningful rather than shared code.

This section is that evidence, one benchmark per page. Each is a **paper ↔ public data ↔
runnable script ↔ reference number** quadruple (the pattern of *Papers-with-Code*, adapted to
physics: the "metric" is *agreement with a reference*, not a competitive score). Every entry
declares its **reference type**, because "ground truth" means different things:

- **analytical** — an exact closed form (unambiguous truth);
- **consensus-sim** — another group's simulation (agreement = independent cross-code
  consistency, *not* proof either is right);
- **experimental** — matches measured data.

## Reproduction matrix

| Benchmark | Reference (type) | Observable | Reference | dmipy-sim | Reproduce |
|---|---|---|---|---|---|
| Restricted cylinders/spheres | MISST (**analytical**) | signal vs *b* | MISST fixtures | ≤ 2% | [test][misst] |
| Interior surface relaxivity | Brownstein–Tarr (**analytical**) | `T2 = R/(nρ)` | closed form | noise floor | [test][bt] |
| Membrane permeability | Powles 2004 (**analytical**) | κ-monotone, high-κ free limit | closed form | `O(h²)` conv. | [test][powles] |
| Canonical WM: fit ↔ sim | interface contract | diffusion + relaxivity signal | — | agree | [page][parity] |
| Isotropic sphere / cylinder field | Lorentz / Salomir (**analytical**) | internal / dipole field | closed form | ≤ 2% | ‡ |
| Anisotropic hollow cylinder | Wharton–Bowtell 2012 (**analytical**) | intra field `½χ_A sin²θ ln(1/g)` | closed form | ≤ 6% | ‡ |
| Mesoscopic AD orientation-dep. on **real XNH axons** | Winther 2024 (**consensus-sim**) | intra axial-diffusivity orientation-dependence, 7 T | up to ~17% | O(few–17%), morphology-dep. †‡ | ‡ |

‡ **Susceptibility benchmarks are pending the public susceptibility release** (the
[Susceptibility](../physics/susceptibility.md) feature is not yet in the public `dmipy-sim`).
Their runnable scripts/notebooks will publish alongside that release; the numbers shown are from
the internal reproduction.

† Preliminary (on the staging site): the effect is reproduced at the right order and is
morphology-dependent across the axon population, but the per-axon estimate is Monte-Carlo-noise
limited at the walker counts used here; a converged, tensor-fit comparison is in progress. See
the [Winther page](winther2024.md).

!!! note "How to read this"
    The **analytical** rows are correctness proofs. The **consensus-sim** rows show `dmipy-sim`
    lands where the community's bespoke simulators land on the *same public substrates*. The
    matrix is deliberately **not a leaderboard** — it is a reproducibility record, open for other
    simulators to add their own column.

Each analytical row is locked in the public
[`dmipy-sim` test suite](https://github.com/dmrai-lab/dmipy-sim/tree/main/tests) so regressions
fail CI; the "Reproduce" links point there. Standalone Colab notebooks are added per benchmark
as each feature is released publicly.

[misst]: https://github.com/dmrai-lab/dmipy-sim/tree/main/tests
[bt]: https://github.com/dmrai-lab/dmipy-sim/tree/main/tests
[powles]: https://github.com/dmrai-lab/dmipy-sim/tree/main/tests
[parity]: ../examples/canonical_wm_parity.md
