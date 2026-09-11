# Scanners & Pulseq

A scanner is a named entry in a cited catalogue, and a `ScannerSequence` goes to and from a
Pulseq `.seq` file. Both live in dmipy-sim, so the simulator, the designer and the fitter all
mean the same thing by "Prisma".

## The catalogue

```python
from dmipy_sim import ScannerLimits, SCANNERS

lim = ScannerLimits.of("prisma")                     # a class, an alias, a model key, or (G_max, slew)
lim.G_max, lim.slew_max, lim.grad_raster             # 0.08 T/m, 200 T/m/s, 10 µs
ScannerLimits.of("connectom", regime="diffusion").slew_max   # 62.5: the PNS-derated figure that binds
ScannerLimits.of((0.5, 600.0)).kind                  # "envelope": an explicit limit point
sorted(SCANNERS)                                     # the certificate classes
```

`None` in a field means the catalogue does not know; it is never a number standing in for one.
Every builder takes `slew_rate=lim.slew_max`; every dmipy-design optimiser takes `limits=lim`
and reads the SAFE peripheral-nerve model from it.

## Write a sequence the scanner can play

```python
# docs: skip  (needs the pypulseq extra)
import dmipy_sim as ds
from dmipy_sim.sequences.pulseq import to_pulseq, make_system

lim = ds.ScannerLimits.of("prisma")
seq = ds.pgse([[1, 0, 0]], 0.012, 0.030, bvalues=[1e9], n_t=1001, slew_rate=lim.slew_max,
              timing=ds.SequenceTiming.from_readout(t_excite=3e-3, t_refocus=6e-3,
                                                    readout_duration=30e-3, partial_fourier=0.75))
to_pulseq(seq, system=make_system("prisma"), filename="dwi.seq")
```

The export splits the gradient at the pulses, plays each grid step as a linear ramp between its
samples, and **refuses a grid that does not sit on the scanner's gradient raster**, naming the
`n_t` values that would. Design on the raster and the file is what you simulated.

## Read a sequence back

```python
# docs: skip  (needs a .seq file)
from dmipy_sim.sequences.pulseq import from_pulseq
seq = from_pulseq("dwi.seq")              # the gradient, the pulses, the ADC time, the b
budget = ds.SequenceTiming.from_pulseq(seq)   # the timing budget a designer can optimise inside
```

A file written by dmipy carries its schedule in the metadata and is read back exactly; a foreign
spin echo gets its budget from the blocks it contains. Either way the result is the same object
the rest of dmipy consumes, so a sequence that ran on a scanner can be simulated on a substrate
and fit with the model that will fit the acquired data.

See [Run it on the scanner](design/pulseq.md) for the design-side round trip and the offline
acceptance checks.
