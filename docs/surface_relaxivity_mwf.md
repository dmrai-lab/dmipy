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
    D_intra=1.7e-9, D_extra=1.7e-9, D_myelin=0.1e-9,
    T2_intra=0.080, T2_myelin=0.015, T2_extra=0.080)

# Gradient-free multi-echo T2 decay: one walk per echo time, per-compartment T2 baked into
# the geometry (myelin ~15 ms vs intra/extra ~80 ms). The short-T2 myelin pool is the MWF.
echo_times = np.arange(1, 33) * 8e-3
S = np.array([
    float(np.asarray(ds.simulate(
        40_000,
        waveform=ds.pgse(delta=te / 2 - 1e-4, DELTA=te / 2, G_magnitude=0.0,
                         bvecs=[[0, 0, 1]], n_t=400),
        geometry=geom, seed=1)).ravel()[0])
    for te in echo_times])
mwf, T2_grid, spectrum = t2_spectrum_mwf(S / S[0], echo_times)   # NNLS T2 spectrum -> MWF
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
