# dmipy

**Diffusion Microstructure Imaging in Python.** Design the sequence, simulate the signal, fit
the tissue — three engines that read the same two objects: one **acquisition** (what the scanner
plays, from t = 0 to the readout) and one **substrate** (the tissue the spins walk through).

<div class="dm-loop" markdown>

| | | |
|---|---|---|
| **[Design](design.md)** a deliverable sequence under a real scanner's limits | **[Simulate](sim.md)** the signal it produces on a known substrate, from first principles | **[Fit](fit.md)** the acquired data with a model validated against that simulation |
| `design_waveform_now(...).to_sequence()` | `simulate(..., waveform=seq, geometry=...)` | `MultiCompartmentModel(...).fit(AcquisitionScheme(seq), data)` |

</div>

The sequence you designed, the one you simulated and the one you fit are **one object**, so
agreement between the engines is a statement about the physics, not about a conversion layer.

## Start here

- **I have diffusion data** → [your first fit](start/fit.md)
- **I have a substrate, or want one** → [your first simulation](start/sim.md)
- **I have a scanner** → [your first designed sequence](start/design.md)

```bash
pip install dmipy            # dmipy-design + dmipy-sim + dmipy-fit
```

```python
import numpy as np
import dmipy_sim as ds
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.signal_models.cylinder_models import C4CylinderGaussianPhaseApproximation

seq  = ds.pgse([[1, 0, 0]] * 3, 0.010, 0.030, bvalues=[0, 1e9, 2e9])         # the acquisition, once
axon = ds.Cylinder(radius=4e-6, orientation=(0, 0, 1))                       # the tissue, once

E_mc = ds.simulate(20_000, 1.7e-9, waveform=seq, geometry=axon, seed=0, require_gpu=False)   # forward truth
E_an = C4CylinderGaussianPhaseApproximation(mu=[0., 0.], lambda_par=1.7e-9, diameter=8e-6)(
           AcquisitionScheme(seq))                                            # analytical model, same object
np.abs(E_mc / E_mc[0] - E_an).max()                                           # < 0.01: they agree
```

## Watch it

One dmipy-sim walk per substrate, replayed over a grid of acquisitions offline; the page only
draws. Move the radius: restriction holds the PGSE signal above free water, and the OGSE
apparent diffusivity climbs with frequency.

<iframe src="studio/signal.html" style="width:100%;height:300px;border:1px solid #2a2f3a;border-radius:8px" title="Live signal: one walk, every acquisition"></iframe>

More knobs: the [sequence explorer](studio/explorer.md) and the [spin studio](studio/spins.md).

## What is in the box

- **[Acquisition](acquisition.md)** — `ScannerSequence`: PGSE, PGSTE, OGSE, CPMG, gradient echo,
  b-tensor STE/PTE, or any waveform; RF pulses and timing budgets; scanner catalogue and Pulseq.
- **[Tissue](substrate.md)** — analytic geometries, packed ensembles, myelinated axons, meshes;
  every constant cited once.
- **[Simulate](sim.md)** — the fused Monte-Carlo walk, the vector-Bloch engine, and replay packs
  that answer any acquisition from one stored walk.
- **[Fit](fit.md)** — multi-compartment models with relaxation and surface relaxivity as
  composable factors, CSD, myelin water; GPU fitting with a Rician noise floor.
- **[Design](design.md)** — deliverable waveforms (NOW), spectral and min-TE design, B1-robust
  refocusing RF, export to the scanner.
- **[Physics](physics/index.md)** — each effect, what it does to your numbers, and what it was
  validated against.

!!! quote "Physics is the specification"
    Physical laws and known analytical results are the correctness criteria, not "the code
    runs". Every analytical model is checked, effect by effect, against the Monte-Carlo forward.
    The lab behind it: **[dmrai-lab.org](https://dmrai-lab.org)**.
