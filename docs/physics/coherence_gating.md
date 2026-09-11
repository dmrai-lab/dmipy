# Coherence gating

Every other page here describes one loss mechanism. Coherence gating adds no term; it sets
**when** each of the others acts, by where the magnetization points. The transverse fraction
accrues the transverse channels (T2, surface relaxivity, susceptibility, the transverse face of
MT); the fraction stored along z accrues only the longitudinal ones (T1 and their siblings).
Diffusion and exchange depend on motion, not on coherence, and act in both states.

In dmipy the gate is not a flag. It is `chi_perp`, derived from the acquisition's RF schedule
([Acquisition](../acquisition.md)): a spin echo is transverse throughout; a stimulated echo
(`pgste`) is transverse only over its two encoding lobes and stored across the mixing time.

```python
import numpy as np, dmipy_sim as ds

se  = ds.pgse([[1, 0, 0]], 0.006, 0.046, bvalues=[1e9])
ste = ds.pgste([[1, 0, 0]], 0.006, 0.040, bvalues=[1e9])
se.chi_perp is None, np.asarray(ste.chi_perp).mean(), ste.TM      # transverse throughout; ≈0.2 transverse; 40 ms stored
```

## Two apparent rates, one gate

While transverse the magnetization decays at

$$\frac{1}{T_2^{\mathrm{app}}} = \frac{1}{T_2} + \rho_2\,\frac{S}{V} + R_2' + k_f ,$$

while stored only

$$\frac{1}{T_1^{\mathrm{app}}} = \frac{1}{T_1} + \rho_1\,\frac{S}{V} + k_{\mathrm{MT}}^{\parallel}$$

acts, and the weight a walker carries is

$$\log w = -\int_0^{T_E}\Big[\chi_\perp(t)\,\frac{1}{T_2^{\mathrm{app}}} + \big(1-\chi_\perp(t)\big)\,\frac{1}{T_1^{\mathrm{app}}}\Big]\,dt .$$

The two rates are siblings: a bulk term plus one S/V-weighted (or field) term per mechanism. MT
sits on both sides — its transverse pathway k_f is paused by storage, its longitudinal saturation
transfer is not — so a stimulated echo removes every transverse wall sink but still pays the
longitudinal terms during the mixing time.

## Why it matters

Surface relaxivity and permeability are two rates of the same wall. In a spin echo the surface
term erases the wall-adjacent spins that carry the exchange signal, so the two entangle; a
stimulated echo pauses the whole T2 bundle over the mixing time while exchange keeps running, and
the exchange time is read far more robustly. The
[surface-relaxivity study](../surface_relaxivity_bias.md) works the bias through for both
sequences, and dmipy-fit's `LongitudinalRelaxation` factor is the exact sibling of its
`TransverseRelaxation` on the same `chi_perp`.
