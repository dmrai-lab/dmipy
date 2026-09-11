# RF pulses & timing

An RF pulse is represented the way the gradient is: as the waveform played on the coil. In a
`ScannerSequence` the pulses are an `RFSchedule` of `RFEvent`s (time, flip, phase, duration, an
optional finite `B1Pulse` envelope), and everything the sequence *means* — the sign of the
effective gradient, which coherence pathway is transverse when, the mixing time of a stimulated
echo — is derived from that schedule. The forward has no intent: it plays what you hand it.

```python
import dmipy_sim as ds

seq = ds.pgse([[1, 0, 0]], 0.010, 0.030, bvalues=[1e9],
              timing=ds.SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3))
[(e.label, round(e.t_s * 1e3, 1), e.flip_deg, e.duration_s) for e in seq.rf]   # a 90 and a 180, finite
seq.rf.refocus_time                     # follows the labelled refocusing pulse
stim = ds.pgste([[1, 0, 0]], 0.006, 0.040, bvalues=[1e9])
[e.label for e in stim.rf], stim.TM     # ['Mz→Mxy', 'store', 'recall'], 40 ms along z
```

## The timing budget

`SequenceTiming` holds what the scanner needs around the encoding: the excitation lead-in, the
refocusing window, the readout before the echo, an optional preparation. Build it from a readout
(`from_readout(..., partial_fourier=)`), read it from a Pulseq file (`from_pulseq`), or state it.
A builder places its blocks inside those windows and derives the TE; `validate()` refuses a
sequence whose pulses do not fit.

```python
budget = ds.SequenceTiming.from_readout(t_excite=3e-3, t_refocus=6e-3,
                                        readout_duration=30e-3, partial_fourier=0.75)
budget.min_TE(), budget.t_readout_pre_echo          # the floor, and the tail partial Fourier leaves
```

## Finite pulses: the shapes are conveniences on top of B1(t)

```python
from dmipy_sim.acquisition.rf import B1Pulse, bloch_simulate, slice_profile

exc  = B1Pulse.hard(flip_deg=90,  duration=1e-3, dt=1e-6)            # rectangular 90°
inv  = B1Pulse.hard(flip_deg=180, duration=1e-3, dt=1e-6)            # rectangular 180°
sinc = B1Pulse.windowed_sinc(90, 2.56e-3, 1e-5, time_bw=4)           # slice-selective
adia = B1Pulse.adiabatic_hs(6e-3, 1e-5, peak_b1=19e-6, mu=2.0)       # HS full passage
comp = B1Pulse.composite([(90, 0), (180, 90), (90, 0)], dt=1e-5, peak_b1=15e-6)
bir4 = B1Pulse.bir4(flip_deg=180, duration=4e-3, dt=1e-5, peak_b1=19e-6)

exc.peak_b1, exc.nominal_flip_deg                    # amplitude and area
Mxy, Mz = bloch_simulate(inv, df_hz=0.0)             # the end state of one pulse
_, _, hist = bloch_simulate(exc, return_history=True)   # M at every raster step
```

![Bloch-sphere trajectories: a 90° hard pulse tips the magnetisation into the transverse plane; a 180° hard pulse inverts it.](media/rf_zoo.gif){ width="100%" }

Put an envelope on an event and the vector-Bloch engine plays it inside the sequence:

```python
ev  = ds.RFEvent(seq.rf.refocus_time, adia.nominal_flip_deg, "refocus",      # the label carries the role;
                 axis_deg=90.0, duration_s=adia.duration, envelope=adia)     # the flip is the envelope's area
fin = ds.ScannerSequence(G=seq.G, dt=seq.dt, rf=ds.RFSchedule((seq.rf[0], ev)), readout=seq.readout,
                         timing=seq.timing, encoding=seq.encoding, family=seq.family)
E = ds.simulate_bloch(4_000, 2e-9, fin, ds.FreeDiffusion(), seed=0, require_gpu=False)
```

## What the shape buys you

- **Slice selectivity**: a windowed sinc under a slice-select gradient excites a sharp slab, a
  hard pulse of the same duration does not — `slice_profile(sinc, slice_gradient=20e-3, positions_m=z)`.
- **Refocusing trains**: with an imperfect 180 the Carr–Purcell train (every pulse about x) collapses
  and the Meiboom–Gill train (refocusing about y, a quarter turn from the excitation) self-corrects.
  `cpmg(n, TE, beta_deg=144)` is Meiboom–Gill; `refocus_axis_deg=0` makes it Carr–Purcell.
- **Robustness to B1⁺**: a hard 180 is exact only at B1⁺ = 1; a composite is flat over ±20 %; an
  adiabatic HS or BIR-4 pulse inverts over ±50 % once above threshold, at a SAR price.

![Inversion Mz vs B1⁺ transmit scale for a hard 180°, a composite, an adiabatic HS and a BIR-4 pulse.](media/rf_robustness.png){ width="100%" }

Choosing a pulse to hit a goal under hardware limits lives one layer up, in
[dmipy-design's refocusing-RF optimiser](design/rf.md); it hands back an `RFEvent` for a schedule.
