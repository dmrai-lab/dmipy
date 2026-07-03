# Surface relaxivity & myelin water fraction

The forthcoming paper *"Surface relaxivity and bulk T2 are inseparable in multi-echo MRI"*
establishes the central result below (it will be included here on release): surface relaxivity
applies a b-independent, per-compartment attenuation that reweights intra vs extra — so the
apparent myelin-water fraction carries a surface term before any estimator sees it.

## End to end from the public pair

Simulate a CPMG echo train (one walk) with dmipy-sim, then fit the myelin-water fraction with
dmipy-fit — no private code:

```python
import numpy as np
import dmipy_sim as ds
from dmipy_fit.white_matter.mwf import t2_spectrum_mwf

geom = ds.MyelinatedCylinder(inner_radius=2.5e-6, outer_radius=3.57e-6, orientation=(0, 0, 1),
    D_intra=1.7e-9, D_myelin_radial=0.1e-9, D_myelin_tangential=0.5e-9, D_extra=1.7e-9,
    T2_intra=0.080, T2_myelin=0.015, T2_extra=0.080)

TE, n_echoes = 8e-3, 32
wf = ds.cpmg(n_echoes=n_echoes, TE=TE, G_magnitude=0.0, bvecs=[[1, 0, 0]], n_t_per_echo=60)
S = np.asarray(ds.simulate_cpmg(40_000, None, wf, geom)).ravel()     # (n_echoes,), one walk
mwf, T2_grid, spectrum = t2_spectrum_mwf(S / S[0], np.arange(1, n_echoes + 1) * TE)
```

## Consistent geometry across the pair

Both engines take the **outer (fibre) diameter** Gamma distribution. In the analytical white-
matter model the exterior surface-to-volume ratio is *derived* from it (the same closed form
the simulator uses), so a fit and a simulation built from the same `gamma_shape`,
`gamma_scale_outer_diameter`, and `f_axon` describe the same tissue:

```python
from dmipy_fit.white_matter.composition import build_white_matter_model
model, params = build_white_matter_model(gamma_shape=2.0,
                                         gamma_scale_outer_diameter=0.30e-6,
                                         f_axon=0.55, rho2=15e-6)
```
