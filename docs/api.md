# API reference

Rendered from the installed engines' docstrings with
[mkdocstrings](https://mkdocstrings.github.io/): the engine code is the source of truth. For the
concepts see [Acquisition](acquisition.md), [Simulate](sim.md), [Fit](fit.md) and
[Design](design.md).

## The acquisition

::: dmipy_sim.acquisition.scanner_sequence.ScannerSequence
::: dmipy_sim.acquisition.scanner_sequence.Protocol
::: dmipy_sim.acquisition.scanner_sequence.Encoding

### Builders

::: dmipy_sim.sequences.builders.pgse
::: dmipy_sim.sequences.builders.pgste
::: dmipy_sim.sequences.builders.ogse
::: dmipy_sim.sequences.builders.cpmg
::: dmipy_sim.sequences.builders.gre
::: dmipy_sim.sequences.builders.ste
::: dmipy_sim.sequences.builders.pte
::: dmipy_sim.sequences.builders.from_waveform

### RF, timing, scanners, Pulseq

::: dmipy_sim.acquisition.rf.RFEvent
::: dmipy_sim.acquisition.rf.RFSchedule
::: dmipy_sim.acquisition.rf.B1Pulse
::: dmipy_sim.acquisition.timing.SequenceTiming
::: dmipy_sim.acquisition.scanners.ScannerLimits
::: dmipy_sim.sequences.pulseq.to_pulseq
::: dmipy_sim.sequences.pulseq.from_pulseq

## dmipy-sim — forward

::: dmipy_sim.simulate
::: dmipy_sim.simulate_bloch
::: dmipy_sim.simulate_trajectories
::: dmipy_sim.replay.replay.ReplayPack
::: dmipy_sim.Sphere
::: dmipy_sim.Cylinder
::: dmipy_sim.MyelinatedCylinder
::: dmipy_sim.Mesh

## dmipy-fit — inverse

::: dmipy_fit.core.acquisition_scheme.AcquisitionScheme
::: dmipy_fit.core.modeling_framework.MultiCompartmentModel
::: dmipy_fit.white_matter.mwf.t2_spectrum_mwf

## dmipy-design — sequence design

::: dmipy_design.design_waveform_now
::: dmipy_design.min_te_for_b
::: dmipy_design.design_stimulated_echo
::: dmipy_design.design_refocusing_rf
::: dmipy_design.NowDesign
