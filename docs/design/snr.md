# Max-b vs min-TE — designing for SNR

There are two dual questions you can ask a waveform designer, and dmipy-design answers both from
the same core.

## Two modes

**Max-b at a fixed TE** — `design_waveform_now(b_delta, TE=…)`. You have a TE (fixed by the
protocol, a relaxometry requirement, or the readout), and you want the **strongest diffusion
weighting** that fits inside it under the hardware limits.

**Min-TE for a target b** — `min_te_for_b(b_target, b_delta, …)`. You have a **required** b-value
(the contrast your model needs), and you want the **shortest echo time** that still reaches it.

## Why min-TE is the SNR-optimal design

The measured magnitude decays with echo time as $\;S \propto e^{-\mathrm{TE}/T_2}\;$ before you
ever read it out. Two waveforms that deliver the *same* b but at different TE therefore give
*different* SNR: the shorter-TE one has lost less signal to transverse relaxation. So for a fixed
required b, **minimising TE maximises SNR** — often the single biggest lever on image quality in a
diffusion protocol, larger than the waveform shape itself.

Concretely, at a required $b$:

$$
\mathrm{SNR}(b) \;\propto\; e^{-\mathrm{TE}(b)/T_2}, \qquad\text{so minimise } \mathrm{TE}(b).
$$

## It's one primitive, not two solvers

The achievable b is **monotonically increasing in TE** — a longer TE simply gives more area under
$q(t)$. That monotonicity is what makes the inverse cheap: `min_te_for_b` **bisects TE around the
max-b primitive**, calling the same NOW design at each candidate TE, with no separate solver and no
hand-rolled scan.

```python
from dmipy_design import min_te_for_b, SequenceTiming

timing = SequenceTiming(t_excite=3e-3, t_refocus=6e-3, t_readout_pre_echo=14e-3)
design, te = min_te_for_b(b_target=1e9, b_delta=1.0, timing=timing)   # 1000 s/mm²
print(f"shortest deliverable TE = {te*1e3:.1f} ms")
```

## Which to use

- **Fixed TE** (multi-contrast / relaxometry protocols, or a shared TE across shells) → **max-b**.
- **Fixed b requirement** (a model needs a specific diffusion weighting, and you want the best
  SNR) → **min-TE**.

Both respect the same [deliverability constraints](deliverable.md) and the derived
[asymmetric windows](deliverable.md#asymmetric-encoding-windows), and both hand you a `G(t)` that
[dmipy-sim](../sim.md) can simulate and [dmipy-fit](../fit.md) can fit.
