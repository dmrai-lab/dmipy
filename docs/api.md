# API reference

Rendered from the installed packages' docstrings with
[mkdocstrings](https://mkdocstrings.github.io/): the code is the source of truth. For the
concepts see [the packages](packages.md), [Acquisition](acquisition.md), [Simulate](sim.md),
[the replay guide](replay/index.md), [Fit](fit.md), [Design](design.md) and
[Closed forms](analytic/index.md).

## dmipy-replay — the acquisition

::: dmipy_replay.acquisition.scanner_sequence.ScannerSequence
::: dmipy_replay.acquisition.scanner_sequence.Protocol
::: dmipy_replay.acquisition.scanner_sequence.Encoding

### Builders

::: dmipy_replay.sequences.builders.pgse
::: dmipy_replay.sequences.builders.pgste
::: dmipy_replay.sequences.builders.ogse
::: dmipy_replay.sequences.builders.cpmg
::: dmipy_replay.sequences.builders.splice
::: dmipy_replay.sequences.builders.gre
::: dmipy_replay.sequences.builders.ste
::: dmipy_replay.sequences.builders.pte
::: dmipy_replay.sequences.builders.from_waveform

### RF, timing, scanners, Pulseq

::: dmipy_replay.acquisition.rf.RFEvent
::: dmipy_replay.acquisition.rf.RFSchedule
::: dmipy_replay.acquisition.rf.B1Pulse
::: dmipy_replay.acquisition.timing.SequenceTiming
::: dmipy_replay.acquisition.scanners.ScannerLimits
::: dmipy_replay.sequences.pulseq.from_pulseq
::: dmipy_sim.sequences.pulseq.to_pulseq

## dmipy-replay — the pack

::: dmipy_replay.replay.replay.ReplayPack
::: dmipy_replay.replay.envelope.Envelope
::: dmipy_replay.replay.envelope.envelope_of
::: dmipy_replay.spec.tissue.Tissue
::: dmipy_replay.spec.substrate.SubstrateSpec

## dmipy-sim — the producer

::: dmipy_sim.spec.walk.walk
::: dmipy_sim.replay.bank.build_replay_pack
::: dmipy_sim.engine.core.simulate
::: dmipy_sim.compartments.Compartments
::: dmipy_sim.compartments.Pool
::: dmipy_sim.Sphere
::: dmipy_sim.Cylinder
::: dmipy_sim.MyelinatedCylinder
::: dmipy_sim.Mesh

## dmipy-analytic — the closed forms

[Every form and its source](analytic/forms.md) lists all of them; the modules a fit or a check reaches for
first:

::: dmipy_analytic.gaussian
::: dmipy_analytic.restricted.cylinder

## dmipy-fit — the inverse

::: dmipy_fit.core.acquisition_scheme.AcquisitionScheme
::: dmipy_fit.core.modeling_framework.MultiCompartmentModel
::: dmipy_fit.white_matter.mwf.t2_spectrum_mwf

## dmipy-design — sequence design

::: dmipy_design.design_waveform_now
::: dmipy_design.min_te_for_b
::: dmipy_design.design_stimulated_echo
::: dmipy_design.design_refocusing_rf
::: dmipy_design.NowDesign
::: dmipy_design.certify.certify
::: dmipy_design.certify.deliverable_set

## dmipy-tract — tractography

::: dmipy_tract.field.FODField
::: dmipy_tract.tracker.track
::: dmipy_tract.tractogram.Tractogram
