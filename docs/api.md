# API reference

Full per-symbol autodoc is wired in at release (once the engines are pip-installable by tag).
For now, the key public entry points — the authoritative reference is each engine's own
docstrings:

## dmipy-sim — [github.com/dmrai-lab/dmipy-sim](https://github.com/dmrai-lab/dmipy-sim)
- `simulate(n_walkers, diffusivity, waveform, geometry, T2=None, ...)` — walker-ensemble signal.
- `simulate_cpmg(n_walkers, D, cpmg_waveform, geometry, T2=None)` — full CPMG echo train from one walk.
- `simulate_mixture(compartments, waveform)` — fraction-weighted multi-compartment signal.
- Encodings: `pgse`, `ogse`, `cpmg`, `ste`, `pte`, `trapezoidal_ogse`; `set_b`, `calc_b`, `calc_btensor`.
- Geometries: `FreeDiffusion`, `Box1D`, `Sphere`, `Cylinder`, `Ellipsoid`, `PackedCylinders`,
  `PackedSpheres`, `MyelinatedCylinder`, `PackedMyelinatedCylinders`.

## dmipy-fit — [github.com/dmrai-lab/dmipy-fit](https://github.com/dmrai-lab/dmipy-fit)
- `core.modeling_framework.MultiCompartmentModel` — build + `fit(scheme, data, solver=...)`.
- `signal_models.*` — `C1Stick`, `G1Ball`, `G2Zeppelin`, sphere/plane/capped-cylinder.
- `signal_models.attenuation.OccupancyGatedModel` + `TransverseRelaxation`,
  `IntraPoreSurfaceRelaxivity`, `ExteriorSurfaceRelaxivity`.
- `white_matter.build_white_matter_model(...)` — decoupled diffusion-only canonical WM model.
- `white_matter.t2_spectrum_mwf(signal, echo_times, ...)` — standard NNLS myelin-water fraction.
- `white_matter.surface.exterior_surface_to_volume(f_axon, gamma_shape, gamma_scale_outer_diameter)`.
