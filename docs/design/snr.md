# Max-b vs min-TE — designing for SNR

Two questions, one primitive.

**Max-b at a fixed TE** — `design_waveform_now(b_delta, limits=, TE=)`: the TE is given (by the
protocol, the readout, a matched multi-contrast series) and you want the most diffusion weighting
it can hold.

**Min-TE for a target b** — `min_te_for_b(b_target, b_delta, limits=)`: the b is given (the
model needs it) and you want the shortest TE that reaches it. Shorter TE means less T2 decay,
so this is the SNR-optimal design: the signal scales as e^{−TE/T2}, and 15 ms saved at
T2 = 80 ms is 1.2× the signal for the same contrast.

```python
from dmipy_design import min_te_for_b, ScannerLimits, SequenceTiming

budget = SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3)
design, te = min_te_for_b(1e9, 1.0, limits=ScannerLimits.of("prisma"), timing=budget,
                          n_t=80, n_restarts=2, seed=0)                      # 1000 s/mm²
round(te * 1e3, 1), design.feasible                                          # the shortest TE, ms
```

`min_te_for_b` bisects TE around the max-b design: achievable b is monotonic in TE, so the
bracket search converges to the floor without a second solver. The result is a `NowDesign` like
any other; `to_sequence()` gives the `ScannerSequence`.

Use max-b when the TE is fixed for you. Use min-TE whenever it is not — which is most of the
time, and why the [asymmetric encoding windows](deliverable.md) matter: the budget's natural
asymmetry is exactly what lets the min-TE design finish sooner.
