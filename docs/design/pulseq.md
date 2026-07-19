# Run it on the scanner — Pulseq interoperability

This is the piece that closes the loop to hardware: **the sequence you optimise, simulate, and fit
is the exact same sequence you run.** No reimplementation on the scanner, no drift between "what I
simulated" and "what I acquired."

[Pulseq](https://pulseq.github.io/) is a vendor-agnostic open format for MR pulse sequences — a
`.seq` file plays on Siemens, GE, Philips and others through the same interpreter. Both engines
speak it:

- **dmipy-sim** reads and writes `.seq` (`from_pulseq` / `to_pulseq`) and carries a catalogue of
  real per-vendor hardware limits (`PULSEQ_SYSTEMS`).
- **dmipy-design** exports a design to a scanner-runnable `.seq` (`design_to_pulseq`) on those real
  limits, and checks it offline the way a scanner would at acceptance.

## The full cycle — one sequence

```text
   dmipy-design            dmipy-sim              dmipy-fit               scanner
   ───────────             ─────────              ─────────               ───────
   optimise G(t)   ──▶   simulate the      ──▶   fit a model to    ──▶   export .seq  ──▶  run
   under real HW         MC ground truth         the signal              (Pulseq)          it
        ▲                                                                                   │
        └──────────────  the acquired data fits with the SAME model  ◀──────────────────────┘
```

Because every stage reads the same `G(t)` object, the loop is literal, not conceptual:

```python
from dmipy_design import design_waveform_now
from dmipy_design.pulseq_export import design_to_pulseq, pulseq_delivery_report

d   = design_waveform_now(b_delta=1.0, TE=0.08)     # optimise on real hardware limits
sig = d.to_sim_waveform()                           # -> dmipy-sim: Monte-Carlo ground truth
# ...fit the simulated (or acquired) signal with a dmipy-fit model on the same scheme...

seq = design_to_pulseq(d, scanner="siemens_prisma", filename="diffusion.seq")   # -> run it
print(pulseq_delivery_report(d, seq))               # offline acceptance, no scanner needed
```

## Offline acceptance — before you book scanner time

`design_to_pulseq` builds a native spin echo (90 — pre-180 lobe — 180 — post-180 lobe — ADC) on
the real `{Gmax, slew, raster, dead-time}` of the chosen system, and `pulseq_delivery_report` /
`pulseq_pns_report` run the checks a scanner does at acceptance:

- **timing** — raster, dead-time, block contiguity (`check_timing`);
- **realized peak G and slew** on the fine raster vs the system limits;
- the **b-tensor round-trip** — recomputed from the assembled `.seq` — so *what you asked for* is
  *what actually gets encoded*;
- **PNS** via the same SAFE model the scanner uses (IEC 60601-2-33).

## Round-trip from a real sequence

You can also start from an existing scanner sequence: `SequenceTiming.from_pulseq(seq)` reads its
90/180/ADC schedule (and native TE), you design a diffusion waveform *inside that budget*, and
`to_pulseq` writes it back — the recomputed b-tensor matches the design. The scanner's timing
constrains the design; the design fills it optimally.

The result: a single artefact travels the whole ecosystem — optimiser → simulator → fitter →
scanner — with nothing lost in translation.
