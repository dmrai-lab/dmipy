# Bloch studio — real pulses on a brain slice

An in-browser demonstration that runs the real dmipy-sim physics **client-side** — no install, no server, nothing to download. Pick a sequence (**PGSE · PGSTE · OGSE · GRE**) built from real finite-duration RF pulses, then sweep the B0 orientation, susceptibility, off-resonance and B1⁺ inhomogeneity and watch the signal form across the slice.

## What you're looking at — the slice is *replayed*, not an image

You are **not** looking at a stock picture. Every pixel of the brain slice is **synthesised live by replaying three tissue substrates**, per voxel:

1. **A 3-tissue CSD fit** (single-shell, 3-tissue constrained spherical deconvolution) of an in-vivo diffusion scan gives, at every voxel, its **white-matter / grey-matter / CSF volume fractions** and the local **white-matter fibre orientation**.
2. dmipy-sim supplies **one stored Monte-Carlo walk per tissue** — the canonical myelinated white matter (intra-axonal / extra-axonal / myelin water), grey matter, and CSF. Each is walked **once**.
3. For each voxel the studio **replays those three substrates on the spot**:
    - the white-matter walk is replayed at that voxel's **fibre orientation** — using the replay's orientation knob, which rotates the *waveform* (and field direction), never the stored walk;
    - the three tissue signals are then **re-weighted by that voxel's CSD volume fractions**. Grey matter and CSF are isotropic, so they need no orientation.
4. **B1⁺ inhomogeneity is injected spatially** — a per-voxel transmit-field scale multiplies the flip angles, so excitation and refocusing vary across the slice the way they really do at high field.

The reason this works is the **replay invariant**: a walk depends only on geometry, diffusivity and seed — *never* on the gradient waveform, field strength, orientation, relaxation, susceptibility or B1. Those are all **replay knobs**. So the entire slice is the **same three walks, replayed** at each voxel's (fibre-angle × B1⁺ × off-resonance) and fraction-weighted — nothing is re-simulated when you move a knob; every adjustment is a re-evaluated replay, live.

(You can also switch the field to a synthetic **circular white-matter** test substrate to see a single fibre population sweep cleanly through orientation.)

<p style="margin:1.2em 0"><a href="bloch_studio.html" target="_blank" rel="noopener"><strong>▶ Open the Bloch studio</strong></a></p>

*Runs entirely in your browser (a single self-contained page). Best on a desktop.*
