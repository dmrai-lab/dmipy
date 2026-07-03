# Biophysical constants

Every physical constant in the substrate is defined once, with a cited source. The catalogue lives in `dmipy_sim.substrate.biophysical_constants` (the forward-truth engine owns the ground truth) and dmipy-fit re-exports it verbatim as `dmipy_fit.audit.biophysical_constants`, so there is exactly one value — and one reference — for each. Read them through the accessor, never hard-code:

```python
from dmipy_sim.substrate import biophysical_constants as bc
bc.get_value('D_intra_axonal')      # 1.7e-9  (m^2/s)
bc.get_constant('D_intra_axonal')   # full record: value, unit, citation, note
```

Every value below links to its source paper.


## Diffusivities

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `D_csf` | 3e-09 m^2/s | CSF diffusivity at body temperature | [Pierpaoli 1996](https://doi.org/10.1148/radiology.201.3.8939209) |
| `D_extra_axonal` | 1.2e-09 m^2/s | Extra-axonal hindered diffusivity (typical WM) | [Fieremans 2011](https://doi.org/10.1016/j.neuroimage.2011.06.006) |
| `D_extra_axonal_intrinsic` | 1.7e-09 m^2/s | Intrinsic (pre-tortuosity) extra-axonal diffusivity used by the Monte Carlo substrate, where the apparent perpendicular reduction emerges from the explicit packed geometry. | [Beaulieu 2002](https://doi.org/10.1002/nbm.782) |
| `D_intra_axonal` | 1.7e-09 m^2/s | In vivo intra-axonal parallel diffusivity | [Beaulieu 2002](https://doi.org/10.1002/nbm.782) |
| `D_water_25C` | 2.299e-09 m^2/s | Free water self-diffusion coefficient at 25 deg C (lab temperature) | [Mills 1973](https://doi.org/10.1021/j100624a025) |
| `D_water_37C` | 3.05e-09 m^2/s | Free water self-diffusion coefficient at 37 deg C (in vivo body temperature) | [Mills 1973](https://doi.org/10.1021/j100624a025) |

## Relaxation times

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `T1_csf` | 4 s | T1 relaxation time of CSF | [Rooney 2007](https://doi.org/10.1002/mrm.21122) |
| `T1_extra_axonal` | 1 s | T1 relaxation time of extra-axonal (hindered) water in WM at 3T. No direct compartment-specific measurement exists; value from mcDESPOT IE-compartment simulation ground truth (Deoni 2012). | [Deoni 2013](https://doi.org/10.1002/mrm.24429) |
| `T1_intra_axonal` | 1.2 s | T1 relaxation time of white matter at 3T | [Wright 2008](https://doi.org/10.1007/s10334-008-0104-8) |
| `T1_myelin` | 0.44 s | T1 relaxation time of myelin water at 3T, in vivo human WM | [Deoni 2015](https://doi.org/10.1002/mrm.25108) |
| `T2_csf` | 2 s | T2 relaxation time of CSF | [Piechnik 2009](https://doi.org/10.1002/mrm.21897) |
| `T2_extra_axonal` | 0.08 s | T2 relaxation time of extra-axonal water | [MacKay 1994](https://doi.org/10.1002/mrm.1910310614) |
| `T2_intra_axonal` | 0.07 s | T2 relaxation time of intra-axonal water | [MacKay 1994](https://doi.org/10.1002/mrm.1910310614) |
| `T2_myelin` | 0.015 s | T2 relaxation time of myelin water | [MacKay 1994](https://doi.org/10.1002/mrm.1910310614) |

## Microstructure & geometry

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `axon_radius_mean` | 3.05e-07 m | Mean axon radius in human corpus callosum | [Aboitiz 1992](https://doi.org/10.1016/0006-8993%2892%2990178-C) |
| `axon_radius_std` | 2.15e-07 m | Standard deviation of axon radius in corpus callosum | [Aboitiz 1992](https://doi.org/10.1016/0006-8993%2892%2990178-C) |
| `g_ratio_corpus_callosum` | 0.7 dimensionless (inner/outer radius) | Mean g-ratio (inner axon radius / outer myelin radius) in human corpus callosum.  Relatively conserved across WM tracts in healthy adults (range ~0.65–0.75).  Used as canonical value in the hollow-cylinder susceptibility model: Δχ_a·(1−g²) determines the dipolar field amplitude. | [Stikov 2015](https://doi.org/10.1016/j.neuroimage.2015.05.023) |
| `g_ratio_typical` | 0.7 | Typical g-ratio (inner/outer myelin radius) in WM | [Stikov 2015](https://doi.org/10.1016/j.neuroimage.2015.05.023) |
| `gamma_scale_diameter` | 3.04e-07 m (Gamma scale over diameter) | Gamma scale parameter (diameter) of the canonical axon-diameter distribution. | [Aboitiz 1992](https://doi.org/10.1016/0006-8993%2892%2990178-C) |
| `gamma_shape_diameter` | 2 dimensionless (Gamma shape α over diameter) | Gamma shape parameter of the axon-diameter distribution used in the canonical packed-cylinder white-matter substrate. | [Aboitiz 1992](https://doi.org/10.1016/0006-8993%2892%2990178-C) |
| `myelin_water_fraction` | 0.15 | Typical myelin water fraction in normal-appearing WM. CAUTION: values differ by method (~10% STAIR, ~10-15% MESE/GRASE at 3T) and by region (CST ~0.21 vs CC genu ~0.09-0.15). mcDESPOT yields ~2x higher values than MESE (known positive bias). | [MacKay 1994](https://doi.org/10.1002/mrm.1910310614) |

## Membrane & surface

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `kappa_membrane` | 1e-05 m/s | Axonal membrane permeability | [Nilsson 2013](https://doi.org/10.1002/mrm.24395) |
| `rho1_axon_membrane` | 8.7e-08 m/s | T1 surface relaxivity of the axon membrane (axolemma). Use paired with corrected T1_bulk_intra (~1.40 s), not T1_apparent. | [Barakovic 2023](https://doi.org/10.3389/fnins.2023.1209521) |
| `rho2_axon_membrane` | 1.16e-06 m/s | T2 surface relaxivity of the axon membrane (axolemma). Use paired with corrected T2_bulk_intra, not T2_apparent. | [Barakovic 2023](https://doi.org/10.3389/fnins.2023.1209521) |

## Susceptibility

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `delta_chi_a_myelin` | -1e-07 SI (dimensionless) | Susceptibility anisotropy of myelinated white matter: difference between susceptibility parallel and perpendicular to the fibre axis, Δχ_a = χ_∥ − χ_⊥.  Negative because myelin is more diamagnetic along the axon than perpendicular to it (phospholipid bilayer geometry).  In SI units (dimensionless); 1 ppm = 1×10⁻⁶.  Enters the hollow-cylinder dipolar field as: ΔB_ea = (Δχ_a·B₀·sin²θ/2)·b²(1−g²)/r²·cos(2φ). | [Liu 2010](https://doi.org/10.1002/mrm.22482) |

## Physical constants

| Constant | Default | Description | Reference |
| --- | --- | --- | --- |
| `gamma_proton` | 2.675e+08 rad/s/T | Proton gyromagnetic ratio | [CODATA 2021](https://doi.org/10.1103/RevModPhys.93.025010) |
