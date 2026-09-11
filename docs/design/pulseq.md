# Run it on the scanner — Pulseq

The design you optimised is the sequence the scanner plays: `design_to_pulseq` writes the
designed `ScannerSequence` through dmipy-sim's Pulseq export on the named scanner, and two
offline reports tell you before you book scanner time whether it will be accepted.

```text
   dmipy-design            dmipy-sim              dmipy-fit               scanner
   optimise G(t)   ──▶   simulate on a     ──▶   fit the signal   ──▶   .seq   ──▶  run it
   under real HW         known substrate         with the model         (Pulseq)
        ▲                                                                       │
        └────────────  the acquired data fits with the SAME model  ◀────────────┘
```

```python
# docs: skip  (needs the [pulseq] extra: pypulseq)
from dmipy_design import design_waveform_now, ScannerLimits
from dmipy_design.pulseq_export import design_to_pulseq, pulseq_delivery_report, pulseq_pns_report

d   = design_waveform_now(1.0, limits=ScannerLimits.of("prisma"), TE=0.080, n_t=8001)   # on the 10 µs raster
seq = design_to_pulseq(d, scanner="siemens_prisma", filename="diffusion.seq")
print(pulseq_delivery_report(d, seq))      # timing, realised |G| and slew vs the limits, b round trip
print(pulseq_pns_report(seq))              # SAFE PNS as % of the stimulation limit
```

The export refuses a design whose grid does not sit on the scanner's gradient raster, naming the
`n_t` values that would; design on the raster and the file is what you simulated. The delivery
report recomputes the b-tensor from the assembled `.seq`, so "what we asked" and "what gets
encoded" are compared on the file itself.

## Round trip from a real sequence

A `.seq` from the scanner reads back as a `ScannerSequence` (`dmipy_sim.sequences.pulseq.from_pulseq`)
and its timing budget as a `SequenceTiming` (`from_pulseq`), so the next design starts from the
windows the vendor sequence actually has. See [Scanners & Pulseq](../pulseq.md).
