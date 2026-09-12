# The brain, replayed

An open-source subject, one Monte-Carlo walk per tissue, replayed anywhere in the head at any
gradient direction and any b — live, in this page, exactly. The subject is the
[B.A.T.M.A.N.](https://osf.io/fkyht/) tutorial's (Tahedl 2018, CC BY 4.0); MRtrix3 gives its fibre
orientation distribution and tissue fractions per voxel; dmipy-sim composes them into a replay
phantom that cites two walks (a CACTUS white-matter bundle, a grey-matter sphere packing) and one
closed form (free water). This page walks through how the phantom is made, then hands you the
result.

<iframe src="../../studio/brain.html" style="width:100%;height:820px;border:1px solid #2a2f3a;border-radius:8px" title="The brain, replayed"></iframe>

<p style="margin:.8em 0"><a href="../../studio/brain.html" target="_blank" rel="noopener"><strong>Open full-screen ↗</strong></a> &nbsp;·&nbsp; runs entirely in your browser, best on a desktop.</p>

**What is real here.** Every pixel is a replay-phantom composition: per voxel, fraction × proton
density × the tissue's response, summed over tissues. The white-matter response is the voxel's FOD
contracted with the pack's pose response — and for a gradient-only acquisition that response
factorises by rotational covariance into one kernel per harmonic order, `a_l(b)`, which is what the
engine computes and stores (`tools/gen_brain_demo.py`). The page evaluates real harmonics and dot
products; it never replays, and it is checked in CI against `ph.replay` on 300 stored voxels at the
tutorial's own 113-measurement scheme (`tools/check_brain.js`, agreement to 10⁻³). Nothing here is
a stored image: the measured mean b = 0 is offered only as an underlay to compare against.

## Step 1 — the subject's data

The tutorial subject is a 2.5 mm, 96 × 96 × 60 diffusion scan with b = 1000 / 2000 / 3000 s/mm² in
17 / 31 / 50 directions and 18 b = 0 volumes, plus a 1 mm T1. MRtrix3's tutorial pipeline (denoise,
unring, preprocess, bias-correct) ends with two derived images this phantom reads:

- `wmfod_norm.mif` — the white-matter FOD per voxel, multi-shell multi-tissue CSD, order 8, in
  MRtrix3's harmonic basis;
- `5tt_coreg.mif` — the five-tissue segmentation (cortical GM, subcortical GM, WM, CSF, pathology),
  on the T1 grid, coregistered to the diffusion image.

```python
# docs: skip  (needs the tutorial's data; run examples/rph/brain_from_csd.py in dmipy-sim for the whole pipeline)
from dmipy_sim.io.mrtrix import read_mif
fod = read_mif("wmfod_norm.mif")      # (96, 96, 60, 45), MRtrix3 basis, affine included
tt = read_mif("5tt_coreg.mif")        # (nx, ny, nz, 5) on the T1 grid
```

## Step 2 — the image grid is the phantom's grid

The acquisition is 2.6° oblique to the scanner axes. `Grid.from_oblique_affine` hands back the image
grid and the rotation `R` (image → scanner); the FOD coefficients are rotated by the same `R` so a
fibre that points along the scanner's z in the image points along it in the phantom. The 5TT
fractions are supersampled onto the diffusion grid, so tissue boundaries carry genuine partial volume.

```python
# docs: skip
import numpy as np
from dmipy_sim.phantom import Grid
from dmipy_sim.replay import so3
grid, R = Grid.from_oblique_affine(fod.affine, fod.shape[:3])
c = so3.rotate_sh(fod.data.reshape(-1, 45), R.T)                # the FODs in the grid's own frame
```

## Step 3 — compose

Three tissues, declared as objects: two packs and one closed form. The white matter is oriented by
the FOD, the grey matter by an isotropic ODF (a cortex has no fibre axis), the CSF is `exp(-bD)` with its T2,
and what is not tissue is `Inert()`. The file that comes out (64 MB) is the arrangement — fractions
and FODs per voxel — citing the packs by URI; the physics stays in the packs.

```python
# docs: skip
from dmipy_sim.phantom import Phantom, PackSubstrate, FreeWater, Inert, ODF
from dmipy_sim.substrate.biophysical_constants import get_value as v      # every value by key, with its citation
wm = PackSubstrate(wm_pack, m0=v("proton_density_white_matter"),          # CACTUS bundle: extra / intra / myelin pools
                   T2_s=[v(k, 3.0) for k in ("T2_extra_axonal", "T2_intra_axonal", "T2_myelin")])
gm = PackSubstrate(gm_pack, m0=v("proton_density_grey_matter"), T2_s=[v("T2_grey_matter", 3.0)] * 2)   # packed spheres
csf = FreeWater(D_m2_s=v("D_csf"), m0=v("proton_density_csf"), T2_s=v("T2_csf", 3.0))
ph = Phantom.compose(grid, fractions={wm: f_wm, gm: f_gm, csf: f_csf}, remainder=Inert(),
                     orientation={wm: ODF(c, basis="mrtrix3"), gm: ODF(iso, basis="mrtrix3")})
ph.write("batman_brain.rph", id="phantoms/batman-brain", license="CC-BY-4.0", citation="Tahedl 2018 ...")
```

No number in this phantom is typed by hand: every T2, proton density, diffusivity and susceptibility is
read from dmipy-sim's biophysical constants table by key, and the page lists each with its source, its
location in the paper and its DOI.

## Step 4 — prescribe the acquisition

The tutorial's own gradient table, as one PGSE with δ = 25 ms, Δ = 55 ms, TE = 100 ms (the walks are
100 ms long), prescribed on the image: the isocenter, the axes and the matrix travel with the
sequence, so the phantom refuses an acquisition whose frame is not its own.

```python
# docs: skip
from dmipy_sim import Prescription, sequences
g = np.loadtxt("dwipreproc_grad.b"); dirs, b = g[:, :3], g[:, 3] * 1e6
seq = sequences.pgse(dirs @ R, 0.025, 0.055, bvalues=b, TE=0.100)
seq = seq.with_prescription(Prescription(isocenter_m=(0, 0, 0), axes=grid.axes, voxel_size_m=grid.voxel_size_m,
                                         matrix=grid.shape, origin_m=grid.origin_m))
```

## Step 5 — replay

One call: 84,987 voxels × 113 measurements in a few seconds on a CPU, through the closed-form pose
expansion (every voxel's FOD contracts the same pack response). The result is written back as a DWI
on the subject's grid.

```python
# docs: skip
S = ph.replay(seq, b0_dir=tuple(R.T @ [0.0, 0.0, 1.0]))       # (96, 96, 60, 113)
```

## Step 6 — the round trip

CSD on the synthetic DWI, with dmipy-fit's own estimator, recovers the FODs it was composed from:
over the 23,389 white-matter voxels the peak angle between the recovered and the input FOD has a
median of 0° and 88 % of voxels within 10°; the angular correlation coefficient averages 0.95. The
per-voxel angle is a layer on the page.

```python
# docs: skip
from dmipy_fit.tissue_response.white_matter_response import estimate_TR2_anisotropic_tissue_response_model
from dmipy_fit.core.modeling_framework import MultiCompartmentSphericalHarmonicsModel
S0, tr2 = estimate_TR2_anisotropic_tissue_response_model(scheme, S_wm)
fod_fit = MultiCompartmentSphericalHarmonicsModel(models=[tr2]).fit(scheme, S, solver="csd")
```

## What the page can and cannot do

- **Any voxel, any direction, any b (0–3000 s/mm²)**, exactly, for the gradient-only spin echo at the
  acquisition above; b between the engine's 100 s/mm² grid points is interpolated linearly.
- **The head tilted in the bore**: a rigid tilt is the gradient turned the other way in the tissue,
  exact at any angle.
- **With the B0 field on** (the myelin's susceptibility, through the white-matter pack's field tier
  and the closed-form pose expansion): stored per head tilt (sagittal and coronal, 10–15° steps), B0
  at 1.5 and 3 T, spin echo, three shells and 40 directions — exact where stored, nearest neighbour
  between. The grey-matter substrate declares no susceptibility source, so its field is zero and its
  response at any B0 is its gradient-only one; free water is a closed form, full-tier with zeros —
  `exp(-bD) exp(-TE/T2)` at any field. A gradient echo keeps the static
  dephasing a spin echo refocuses, and 7 T multiplies it; either pushes the closed form's band, and
  the table's memory, past what a demo should carry, so neither is offered here.
- **Not here:** transmit and bias fields (the Bloch route), T2 beyond the catalogued per-tissue values at 3 T,
  exchange, and other sequence families. The old brain-slice Bloch studio, which this page
  supersedes, hand-coded its susceptibility as an off-resonance formula; nothing here is hand-coded.

**The file.** The phantom (`batman_brain.rph`) and the two packs it cites will be published on
SubstrateCommons, so that the page's one-liner becomes literal
([dmipy-sim#211](https://github.com/dmrai-lab/dmipy-sim/issues/211)); the author is contacted before
that. Until then, the pipeline above reproduces it from the tutorial's data.

```python
# docs: skip  (the file is not published yet)
from dmipy_sim.phantom import Phantom
ph = Phantom.read("hf://SubstrateCommons/batman-brain/batman_brain.rph")
S = ph.replay(seq)
```
