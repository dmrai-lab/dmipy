# Validation &amp; benchmarks

**dmipy-sim reproduces the published literature — analytical results exactly, and other
groups' Monte-Carlo findings on their own data — each reimplemented independently, so the
agreement is evidence, not shared code.**

| Benchmark | Reference | We match | Type |
|---|---|:--:|:--:|
| Restricted cylinders / spheres | MISST | **≤ 2 %** | exact |
| Surface relaxivity `T₂ = R/(nρ)` | Brownstein–Tarr | **noise floor** | exact |
| Membrane permeability | Powles 2004 | **O(h²) → exact** | exact |
| Isotropic sphere / cylinder field | Lorentz / Salomir | **≤ 2 %** | exact |
| Anisotropic hollow-cylinder intra field | Wharton–Bowtell 2012 | **≤ 6 %** | exact |
| Intra AD orientation-dep. on **real monkey axons** | [Winther 2024](winther2024.md) | **under investigation** | cross-sim |
| Fit ↔ sim on canonical WM | interface contract | [agree](../examples/canonical_wm_parity.md) | — |

*Type:* **exact** = closed-form ground truth (locked in CI). **cross-sim** = agreement with
another group's simulator on the same public substrate — independent cross-check, not proof
either is right.

!!! note "Susceptibility rows"
    Publish with the [susceptibility](../physics/susceptibility.md) feature release; numbers
    shown are from the internal reproduction.
