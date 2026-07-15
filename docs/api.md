# API reference

Rendered live from the installed engine docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) — the docstrings in
[dmipy-sim](https://github.com/dmrai-lab/dmipy-sim) and
[dmipy-fit](https://github.com/dmrai-lab/dmipy-fit) are the source of truth, so this reference
can't drift from the code. For the conceptual entry points see the
[forward](sim.md) and [inverse](fit.md) overviews.

## dmipy-sim — forward

### Simulation

::: dmipy_sim.simulate
::: dmipy_sim.simulate_cpmg

### Geometries

::: dmipy_sim.Sphere
::: dmipy_sim.Cylinder
::: dmipy_sim.Mesh

### Waveforms & encoding

::: dmipy_sim.pgse
::: dmipy_sim.set_b

## dmipy-fit — inverse

### Modelling framework

::: dmipy_fit.core.modeling_framework.MultiCompartmentModel

### Acquisition scheme

::: dmipy_fit.core.acquisition_scheme.acquisition_scheme_from_bvalues

### White matter

::: dmipy_fit.white_matter.mwf.t2_spectrum_mwf
