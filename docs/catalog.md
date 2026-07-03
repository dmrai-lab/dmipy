# Model catalog

The framework has one model of its own — the **unified white-matter model** below — and reproduces the published literature as thin factories around the *same* shared primitives. Every entry is an ordinary `MultiCompartmentModel`: forward-simulate with `model(scheme, **params)`, fit with one `model.fit(scheme, data)` call.

## The unified white-matter model

*The framework's own model — the analytical inverse of the dmipy-sim Monte-Carlo forward truth.*

It is **not** a bespoke class: the canonical white-matter substrate is an ordinary `MultiCompartmentModel` built from the same primitives as everything below — `C1Stick` (intra-axonal), `G2Zeppelin` (extra-axonal) and `S1Dot` (stuck myelin), each wrapped in an `OccupancyGatedModel` that carries the opt-in occupancy-gated factors: transverse relaxation (`T2`) and intra-pore + exterior **surface relaxivity**. A single Gamma outer-diameter distribution drives both surface factors, and the whole thing forward-simulates and fits through the standard machinery, exactly like NODDI. Diffusion-only — no susceptibility, gradient-/stimulated-echo, or T1 physics.

The whole thing is built from primitives in a couple dozen lines: three occupancy-gated compartments assembled into one `MultiCompartmentModel`, sharing one fibre orientation.

```python
from dmipy_fit.core.modeling_framework import MultiCompartmentModel
from dmipy_fit.signal_models.cylinder_models import C1Stick
from dmipy_fit.signal_models.gaussian_models import G2Zeppelin
from dmipy_fit.signal_models.sphere_models import S1Dot
from dmipy_fit.signal_models.attenuation import (
    OccupancyGatedModel, TransverseRelaxation,
    IntraPoreSurfaceRelaxivity, ExteriorSurfaceRelaxivity)
from dmipy_fit.white_matter.surface import exterior_surface_to_volume

# one Gamma OUTER (fibre) diameter distribution drives both surface factors
gamma_shape, gamma_scale = 2.0, 0.304e-6      # mean outer diameter = shape * scale
f_axon = 0.55                                 # intra-axonal (lumen) volume fraction
S_ext_over_V = exterior_surface_to_volume(f_axon, gamma_shape, gamma_scale)

# each compartment = a diffusion primitive + opt-in occupancy-gated factors (surface relaxivity + T2)
intra  = OccupancyGatedModel(C1Stick(), [
    IntraPoreSurfaceRelaxivity(gamma_shape=gamma_shape,
                               gamma_scale_outer_diameter=gamma_scale,
                               volume_weighted=True),
    TransverseRelaxation()])
extra  = OccupancyGatedModel(G2Zeppelin(), [
    ExteriorSurfaceRelaxivity(S_ext_over_V=S_ext_over_V),
    TransverseRelaxation()])
myelin = OccupancyGatedModel(S1Dot(), [TransverseRelaxation()])   # stuck myelin water (radial D ~ 0)

# assemble into a standard MultiCompartmentModel with one shared fibre orientation
model = MultiCompartmentModel([intra, extra, myelin], S0_global=True)
model.set_equal_parameter('OccupancyGatedModel_1_mu', 'OccupancyGatedModel_2_mu')
```

Then `model(scheme, **params)` forward-simulates and `model.fit(scheme, data, solver="jax")` fits, exactly like the literature models below. This exact composition, with canonical healthy-WM defaults at 3T, is packaged as one call: `model, params = build_white_matter_model()`.

---

## Literature models

Each factory below lives in `dmipy_fit.custom_optimizers.reference_models` and returns a configured `MultiCompartmentModel` (or spherical-mean model) in a few lines.

```python
from dmipy_fit.custom_optimizers import reference_models as models
mcm = models.noddi()          # any factory below
fit = mcm.fit(scheme, data, solver="jax")
```


### Gaussian / tensor

#### `ball()` <small>A1</small>

Isotropic Gaussian (single ADC).

*[Stejskal & Tanner 1965, JCP 42](https://doi.org/10.1063/1.1695690)*

```python
return MultiCompartmentModel([G1Ball()])
```

#### `zeppelin()` <small>A2</small>

Axially symmetric Gaussian (DTI-like, single fascicle).

*[Basser et al. 1994, Biophys J 66](https://doi.org/10.1016/S0006-3495%2894%2980775-1)*

```python
return MultiCompartmentModel([G2Zeppelin()])
```

#### `temporal_zeppelin()` <small>A3</small>

Anisotropic compartment with structural-disorder time dependence.

*[Novikov et al. 2019, NMR Biomed 32](https://doi.org/10.1002/nbm.3998)*

```python
return MultiCompartmentModel([G3TemporalZeppelin()])
```


### Two-compartment white matter

#### `ball_and_stick()` <small>B1</small>

Isotropic Ball + zero-radius Stick (intra-axonal).

*[Behrens et al. 2003, MRM 50](https://doi.org/10.1002/mrm.10609)*

```python
return MultiCompartmentModel([C1Stick(), G1Ball()])
```

#### `ball_and_zeppelin()` <small>B2</small>

Isotropic Ball + anisotropic Zeppelin (tissue DTI tensor).

*[Panagiotaki et al. 2012, NeuroImage 59](https://doi.org/10.1016/j.neuroimage.2011.09.081)*

```python
return MultiCompartmentModel([G2Zeppelin(), G1Ball()])
```

#### `stick_tortuous_zeppelin()` <small>B3</small>

Intra-axonal Stick + tortuous extra-axonal Zeppelin.

*[Novikov et al. 2019, NMR Biomed 32](https://doi.org/10.1002/nbm.3998)*

```python
mcm = MultiCompartmentModel([C1Stick(), G2Zeppelin()])
mcm.set_tortuous_parameter(          # must come before set_equal_parameter
    'G2Zeppelin_1_lambda_perp',
    'C1Stick_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter('C1Stick_1_mu', 'G2Zeppelin_1_mu')
mcm.set_equal_parameter('C1Stick_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm
```

#### `free_water_elimination()` <small>B4</small>

Tissue Zeppelin + fixed free-water Ball (D_iso = 3.0e-9 m²/s).

*[Pasternak et al. 2009, MRM 62](https://doi.org/10.1002/mrm.22055)*

```python
mcm = MultiCompartmentModel([G2Zeppelin(), G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```

#### `ivim()` <small>B5</small>

IVIM: tissue diffusion + vascular pseudo-diffusion.

*[Le Bihan et al. 1988, Radiology 161](https://doi.org/10.1148/radiology.168.2.3393671)*

```python
mcm = MultiCompartmentModel([G1Ball(), G1Ball()])
mcm.set_fixed_parameter('G1Ball_2_lambda_iso', 7e-9)
mcm.set_parameter_optimization_bounds('G1Ball_1_lambda_iso', [0.5e-9, 6e-9])
return mcm
```


### Orientation-dispersion

#### `noddi()` <small>C1</small>

NODDI: Watson-dispersed Stick + tortuous Zeppelin + CSF Ball.

*[Zhang et al. 2012, NeuroImage 61](https://doi.org/10.1016/j.neuroimage.2012.03.072)*

```python
bundle = SD1WatsonDistributed(models=[C1Stick(), G2Zeppelin()])
bundle.set_tortuous_parameter(       # tortuosity before set_equal
    'G2Zeppelin_1_lambda_perp',
    'G2Zeppelin_1_lambda_par',
    'partial_volume_0',
)
bundle.set_equal_parameter('G2Zeppelin_1_lambda_par', 'C1Stick_1_lambda_par')
bundle.set_fixed_parameter('G2Zeppelin_1_lambda_par', _Da)
mcm = MultiCompartmentModel([bundle, G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```

#### `bingham_noddi()` <small>C2</small>

Bingham-NODDI: Bingham-dispersed Stick + tortuous Zeppelin + CSF Ball.

*[Tariq et al. 2016, NeuroImage 133](https://doi.org/10.1016/j.neuroimage.2016.01.046)*

```python
bundle = SD2BinghamDistributed(models=[C1Stick(), G2Zeppelin()])
bundle.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp',
    'G2Zeppelin_1_lambda_par',
    'partial_volume_0',
)
bundle.set_equal_parameter('G2Zeppelin_1_lambda_par', 'C1Stick_1_lambda_par')
bundle.set_fixed_parameter('G2Zeppelin_1_lambda_par', _Da)
mcm = MultiCompartmentModel([bundle, G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```

#### `noddida()` <small>C3</small>

NODDIDA: Stick + tortuous Zeppelin + free Ball — all diffusivities free.

*[Jelescu et al. 2015, NMR Biomed 28](https://doi.org/10.1002/nbm.3450)*

```python
mcm = MultiCompartmentModel([C1Stick(), G2Zeppelin(), G1Ball()])
mcm.set_tortuous_parameter(          # tortuosity before set_equal
    'G2Zeppelin_1_lambda_perp',
    'C1Stick_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter('C1Stick_1_mu', 'G2Zeppelin_1_mu')
mcm.set_equal_parameter('C1Stick_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm
```

#### `mcsmt()` <small>C4</small>

MC-SMT: Multi-Compartment Spherical Mean Technique.

*[Kaden et al. 2016, NeuroImage 139](https://doi.org/10.1016/j.neuroimage.2016.06.002)*

```python
mcm = MultiCompartmentSphericalMeanModel([C1Stick(), G2Zeppelin()])
mcm.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp',
    'C1Stick_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter('C1Stick_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm
```


### Multi-fascicle

#### `two_fascicle_noddi()` <small>D1</small>

Two independently oriented Watson-NODDI bundles + shared CSF Ball.

*[Behrens et al. 2007, NeuroImage 34](https://doi.org/10.1016/j.neuroimage.2006.09.018)*

```python
bundle1 = SD1WatsonDistributed(models=[C1Stick(), G2Zeppelin()])
bundle1.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp', 'G2Zeppelin_1_lambda_par', 'partial_volume_0')
bundle1.set_equal_parameter('G2Zeppelin_1_lambda_par', 'C1Stick_1_lambda_par')
bundle1.set_fixed_parameter('G2Zeppelin_1_lambda_par', _Da)

bundle2 = SD1WatsonDistributed(models=[C1Stick(), G2Zeppelin()])
bundle2.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp', 'G2Zeppelin_1_lambda_par', 'partial_volume_0')
bundle2.set_equal_parameter('G2Zeppelin_1_lambda_par', 'C1Stick_1_lambda_par')
bundle2.set_fixed_parameter('G2Zeppelin_1_lambda_par', _Da)

mcm = MultiCompartmentModel([bundle1, bundle2, G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```


### Cylinder / axon diameter

#### `charmed()` <small>E1</small>

CHARMED: Callaghan cylinder (restricted) + tortuous Zeppelin (hindered).

*[Assaf & Basser 2005, NeuroImage 27](https://doi.org/10.1016/j.neuroimage.2005.03.042)*

```python
cyl  = C3CylinderCallaghanApproximation()
zepp = G2Zeppelin()
mcm  = MultiCompartmentModel([cyl, zepp])
mcm.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp',
    'C3CylinderCallaghanApproximation_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter(
    'C3CylinderCallaghanApproximation_1_mu', 'G2Zeppelin_1_mu')
mcm.set_equal_parameter(
    'C3CylinderCallaghanApproximation_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm
```

#### `axcaliber()` <small>E2</small>

AxCaliber: Gamma-distributed Callaghan cylinders + Zeppelin.

*[Assaf et al. 2008, MRM 59](https://doi.org/10.1002/mrm.21577)*

```python
gamma_cyl = DD1GammaDistributed([C3CylinderCallaghanApproximation()])
mcm = MultiCompartmentModel([gamma_cyl, G2Zeppelin()])
mcm.set_equal_parameter(
    'DD1GammaDistributed_1_C3CylinderCallaghanApproximation_1_mu',
    'G2Zeppelin_1_mu',
)
return mcm
```

#### `active_ax()` <small>E3</small>

ActiveAx: single-diameter Callaghan cylinder + Zeppelin + free Ball.

*[Alexander et al. 2010, NeuroImage 52](https://doi.org/10.1016/j.neuroimage.2010.05.043)*

```python
mcm = MultiCompartmentModel([
    C3CylinderCallaghanApproximation(), G2Zeppelin(), G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```


### Soma / sphere

#### `verdict()` <small>F1</small>

VERDICT: Sphere (cell body) + Stick (membrane/vascular) + Ball (EES).

*[Panagiotaki et al. 2014, Cancer Res 74](https://doi.org/10.1158/0008-5472.can-13-2511)*

```python
return MultiCompartmentModel([
    S4SphereGaussianPhaseApproximation(), C1Stick(), G1Ball()])
```

#### `sandi()` <small>F2</small>

SANDI: Sphere (soma) + Stick (neurite) + Ball (extra-cellular).

*[Palombo et al. 2020, NeuroImage 215](https://doi.org/10.1016/j.neuroimage.2020.116835)*

```python
soma = S4SphereGaussianPhaseApproximation(diffusion_constant=_Din)
mcm  = MultiCompartmentModel([soma, C1Stick(), G1Ball()])
mcm.set_fixed_parameter('C1Stick_1_lambda_par', _Da)
return mcm
```

#### `impulsed()` <small>F3</small>

IMPULSED: Sphere + isotropic Ball (two-compartment, fixed D_in).

*[Xu et al. 2019, Magn Reson Med](https://doi.org/10.1002/mrm.28056)*

```python
soma = S4SphereGaussianPhaseApproximation(diffusion_constant=_Din)
return MultiCompartmentModel([soma, G1Ball()])
```


### Membrane exchange

#### `nexi()` <small>G1</small>

NEXI: Neurite Exchange Imaging — Stick + Zeppelin with Kärger exchange.

*[Jelescu et al. 2022, NeuroImage 256](https://doi.org/10.1016/j.neuroimage.2022.119277)*

```python
stick, zeppelin = C1Stick(), G2Zeppelin()
karger = X0GeneralizedKarger(
    stick, zeppelin,
    parameter_links=[(zeppelin, 'lambda_perp', T1_tortuosity(),
                      [(zeppelin, 'lambda_par'), (None, 'f')])])
return MultiCompartmentModel([karger])
```

#### `karger_two_compartment()` <small>G2</small>

Generic Kärger two-compartment model: Ball + Ball with exchange.

*[Kärger 1985, Adv Colloid Interface Sci 23](https://doi.org/10.1016/0001-8686%2885%2980018-X)*

```python
return MultiCompartmentModel([X0GeneralizedKarger(G1Ball(), G1Ball())])
```

#### `fexi()` <small>G3</small>

FEXI: Filter EXchange Imaging — two isotropic pools with exchange.

*[Lasič et al. 2011, MRM 66](https://doi.org/10.1002/mrm.22782)*

```python
slow = G1Ball()
fast = G1Ball()
mcm  = MultiCompartmentModel([X0GeneralizedKarger(slow, fast)])
mcm.set_fixed_parameter('X0GeneralizedKarger_1_G1Ball_2_lambda_iso', 2.0e-9)  # fast pool D
return mcm
```

#### `sandix()` <small>G4</small>

SANDIX: SANDI with exchange between soma (sphere) and extracellular (Ball).

*[SANDI (Palombo 2020) + Kärger 1985](https://doi.org/10.1016/j.neuroimage.2020.116835)*

```python
soma  = S4SphereGaussianPhaseApproximation(diffusion_constant=_Din)
extra = G1Ball()
mcm   = MultiCompartmentModel([X0GeneralizedKarger(soma, extra), C1Stick()])
mcm.set_fixed_parameter('C1Stick_1_lambda_par', _Da)
return mcm
```

#### `exchange_impulsed()` <small>G5</small>

EXCHANGE: IMPULSED + transcytolemmal Kärger exchange (tumour).

*[Shi et al. 2025, Magn Reson Imaging](https://doi.org/10.1016/j.mri.2025.110433)*

```python
soma  = S4SphereGaussianPhaseApproximation(diffusion_constant=_Din)
extra = G1Ball()
return MultiCompartmentModel([X0GeneralizedKarger(soma, extra)])
```


### Time-dependent

#### `temporal_zeppelin_model()` <small>H1</small>

Temporal Zeppelin + free Ball: Standard Model with structural disorder.

*[Novikov et al. 2019, NMR Biomed 32](https://doi.org/10.1002/nbm.3998)*

```python
mcm = MultiCompartmentModel([G3TemporalZeppelin(), G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm
```


### Relaxometry (multi-TE)

#### `mte_ball_stick()` <small>I1</small>

Multi-TE Ball-and-Stick with per-compartment T2 relaxation.

*[Gong et al. 2020, NeuroImage 217](https://doi.org/10.1016/j.neuroimage.2020.116906)*

```python
mcm = MultiCompartmentModel([C1Stick(), G1Ball()])
return mcm   # T2 on both compartments is free by default
```

#### `mte_noddi()` <small>I2</small>

MTE-NODDI: NODDI extended with per-compartment T2 relaxation.

*[Gong et al. 2020, NeuroImage 217](https://doi.org/10.1016/j.neuroimage.2020.116906)*

```python
bundle = SD1WatsonDistributed(models=[C1Stick(), G2Zeppelin()])
bundle.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp', 'G2Zeppelin_1_lambda_par', 'partial_volume_0')
bundle.set_equal_parameter('G2Zeppelin_1_lambda_par', 'C1Stick_1_lambda_par')
bundle.set_fixed_parameter('G2Zeppelin_1_lambda_par', _Da)
mcm = MultiCompartmentModel([bundle, G1Ball()])
mcm.set_fixed_parameter('G1Ball_1_lambda_iso', _Dcsf)
return mcm   # T2 on Stick and Zeppelin inside bundle are free parameters
```

#### `mte_sandi()` <small>I3</small>

MTE-SANDI: SANDI with per-compartment T2 relaxation.

*ISMRM 2023 abstract #0766*

```python
soma = S4SphereGaussianPhaseApproximation(diffusion_constant=_Din)
mcm  = MultiCompartmentModel([soma, C1Stick(), G1Ball()])
mcm.set_fixed_parameter('C1Stick_1_lambda_par', _Da)
return mcm   # T2 on Stick and Ball compartments are free; soma has no T2 param
```

#### `wmti()` <small>I4</small>

WMTI: White Matter Tract Integrity — biophysical Standard Model structure.

*[Fieremans et al. 2011, NeuroImage 58](https://doi.org/10.1016/j.neuroimage.2011.06.006)*

```python
mcm = MultiCompartmentModel([C1Stick(), G2Zeppelin()])
mcm.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp',
    'C1Stick_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter('C1Stick_1_mu', 'G2Zeppelin_1_mu')
mcm.set_equal_parameter('C1Stick_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm
```

#### `noddida_mte()` <small>I5</small>

NODDIDA-MTE: unconstrained NODDIDA with per-compartment T2.

*[Jelescu 2015 + Gong 2020](https://doi.org/10.1002/nbm.3450)*

```python
mcm = MultiCompartmentModel([C1Stick(), G2Zeppelin(), G1Ball()])
mcm.set_tortuous_parameter(
    'G2Zeppelin_1_lambda_perp',
    'C1Stick_1_lambda_par',
    'partial_volume_0',
    'partial_volume_1',
)
mcm.set_equal_parameter('C1Stick_1_mu', 'G2Zeppelin_1_mu')
mcm.set_equal_parameter('C1Stick_1_lambda_par', 'G2Zeppelin_1_lambda_par')
return mcm   # T2 on all three compartments are free parameters
```

#### `mte_impulsed()` <small>I6</small>

MTE-IMPULSED: IMPULSED with per-compartment T2 relaxation.

*[Jiang et al. 2025, MRM](https://doi.org/10.1002/mrm.30254)*

```python
return MultiCompartmentModel([S4SphereGaussianPhaseApproximation(), G1Ball()])
```

