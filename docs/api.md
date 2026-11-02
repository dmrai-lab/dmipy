# API reference

Rendered live from the installed packages' docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) — the docstrings in
[dmipy-sim](https://github.com/dmrai-lab/dmipy-sim),
[dmipy-replay](https://github.com/dmrai-lab/dmipy-replay),
[dmipy-fit](https://github.com/dmrai-lab/dmipy-fit) and
[dmipy-design](https://github.com/dmrai-lab/dmipy-design) are the source of truth, so this reference
can't drift from the code. For the conceptual entry points see the
[forward](sim.md), [inverse](fit.md) and [design](design.md) overviews.

## dmipy-sim — forward

dmipy-sim walks a substrate and produces replay packs; `simulate` is the walk and the replay in one call.

### The walk and the pack

::: dmipy_sim.walk
::: dmipy_sim.build_replay_pack

### Simulation

::: dmipy_sim.simulate
::: dmipy_sim.simulate_cpmg

### Geometries

::: dmipy_sim.Sphere
::: dmipy_sim.Cylinder
::: dmipy_sim.Mesh

## dmipy-replay — the signal side

dmipy-replay turns a replay pack into a signal or an image, and owns the acquisition object that
every package shares.

### Waveforms & encoding

::: dmipy_replay.pgse
::: dmipy_replay.set_b

### Replay packs

::: dmipy_replay.ReplayPack
::: dmipy_replay.Envelope
::: dmipy_replay.envelope_of

## dmipy-fit — inverse

### Modelling framework

::: dmipy_fit.core.modeling_framework.MultiCompartmentModel

### Acquisition scheme

::: dmipy_fit.core.acquisition_scheme.acquisition_scheme_from_bvalues

### White matter

::: dmipy_fit.white_matter.mwf.t2_spectrum_mwf

## dmipy-design — sequence design

### Waveforms

::: dmipy_design.design_waveform_now
::: dmipy_design.min_te_for_b

### Certificates

::: dmipy_design.certify.certify
::: dmipy_design.certify.deliverable_set
