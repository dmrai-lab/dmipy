"""Render the pedagogy animations shown on dmipy.org into docs/media/*.mp4.

Uses dmipy-sim's idealised-magnetisation pedagogy renderer (a real walk on the canonical
packed-myelin white-matter substrate -> phase + hard-pulse rotations + per-compartment T2).
Needs dmipy-sim + matplotlib + ffmpeg. The docs build itself stays engine-independent -- it
just serves these committed .mp4 files.

Run: python tools/gen_pedagogy_media.py
"""
import os
import numpy as np
import dmipy_sim
from dmipy_sim import pedagogy
from dmipy_sim.substrate import Substrate

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'media')
os.makedirs(OUT, exist_ok=True)

# --- canonical white-matter substrate: packed myelinated cylinders -----------------
# Outer (fibre) diameters drawn from the substrate's Gamma law; inner radius = g*outer/2.
SUB = Substrate()
_PACKING = 0.35                                    # RSA-achievable demo packing
_rng = np.random.default_rng(0)
_outer_d = _rng.gamma(SUB.gamma_shape_diameter, SUB.gamma_scale_diameter, 16)
_inner_radii = 0.5 * SUB.g_ratio * _outer_d
_ir, _gr, _centers = dmipy_sim.pack_myelinated_cylinders(
    _inner_radii, np.full(_inner_radii.size, SUB.g_ratio), target_packing=_PACKING, seed=1)
_L = float(np.sqrt(np.pi * np.sum((_ir / _gr) ** 2) / _PACKING))
GEOM = dmipy_sim.PackedMyelinatedCylinders(
    _ir, _gr, _centers, _L,
    D_intra=SUB.D_intra, D_myelin=SUB.D_myelin, D_extra=SUB.D_extra)
# per-compartment T2, ordered to match the 3-class label (0=intra, 1=myelin, 2=extra)
T2_PER_COMP = [SUB.T2_intra, SUB.T2_myelin, SUB.T2_extra]
BVEC = np.array([[1.0, 0.0, 0.0]])


def movie(waveform, name, title):
    hist = pedagogy.replay_with_history(GEOM, waveform, SUB.D_intra,
                                        T2_per_comp=T2_PER_COMP, n_walkers=4000, seed=1)
    path = os.path.join(OUT, name)
    pedagogy.spin_movie(hist, save=path, stride=3, fps=20, dpi=90, title=title)
    print(f'  {name}: {os.path.getsize(path) / 1024:.0f} KB')


print('rendering pedagogy media (canonical packed-myelin WM substrate) ->',
      os.path.normpath(OUT))
movie(dmipy_sim.pgse(delta=8e-3, DELTA=25e-3, G_magnitude=0.05, bvecs=BVEC, n_t=240),
      'pgse.mp4', 'PGSE on packed myelinated white matter')
movie(dmipy_sim.cpmg(n_echoes=4, TE=12e-3, G_magnitude=0.0, bvecs=BVEC, n_t_per_echo=60),
      'cpmg.mp4', 'CPMG on packed myelinated white matter')
movie(dmipy_sim.ogse(frequency=100.0, T_total=40e-3, G_magnitude=0.06, bvecs=BVEC, n_t=300),
      'ogse.mp4', 'OGSE on packed myelinated white matter')

# --- magnitude-distribution movie: intra vs extra under surface relaxivity ---------
# A moderate-fibre packed substrate (inner radius ~3 um) so the surface-relaxivity fan is
# legible: intra (small lumen, high S/V) stays a narrow, fast-relaxing spike (motional
# averaging), extra (larger, heterogeneous) fans into a broad distribution.
_mir = np.full(6, 3e-6)
_mirr, _mgrr, _mctr = dmipy_sim.pack_myelinated_cylinders(
    _mir, np.full(6, SUB.g_ratio), target_packing=0.30, seed=2)
_mL = float(np.sqrt(np.pi * np.sum((_mirr / _mgrr) ** 2) / 0.30))
MAG_GEOM = dmipy_sim.PackedMyelinatedCylinders(
    _mirr, _mgrr, _mctr, _mL, D_intra=SUB.D_intra, D_myelin=SUB.D_myelin, D_extra=SUB.D_extra)
# same walk (n_walkers, seed, substrate, waveform, rho) drives BOTH the histogram and the
# spatial cross-section, so the two clips play in lock-step.
_cpmg = dmipy_sim.cpmg(n_echoes=4, TE=12e-3, G_magnitude=0.0, bvecs=BVEC, n_t_per_echo=800)
_mag_kw = dict(rho=40e-6, T2_per_comp=[SUB.T2_intra, SUB.T2_myelin, SUB.T2_extra],
               n_walkers=4000, seed=0)
_mag_title = ('CPMG |M| distribution: intra vs extra  '
              '(ρ = 40 µm/s, exaggerated ~30x vs the 1.16 µm/s literature)')
pedagogy.magnitude_movie(MAG_GEOM, _cpmg, os.path.join(OUT, 'magnitude_cpmg.mp4'),
                         stride=16, title=_mag_title, **_mag_kw)
print(f"  magnitude_cpmg.mp4: {os.path.getsize(os.path.join(OUT, 'magnitude_cpmg.mp4')) / 1024:.0f} KB")
pedagogy.magnitude_spatial_movie(MAG_GEOM, _cpmg, os.path.join(OUT, 'magnitude_spatial_cpmg.mp4'),
                                 n_show=1500, stride=20, dpi=80,
                                 title='CPMG — |M| across the substrate (ρ exaggerated ~30x)', **_mag_kw)
print(f"  magnitude_spatial_cpmg.mp4: {os.path.getsize(os.path.join(OUT, 'magnitude_spatial_cpmg.mp4')) / 1024:.0f} KB")

# the honest one: REAL rho = 1.16 um/s, effect revealed by a moving zoom (no exaggeration).
pedagogy.magnitude_zoom_movie(
    MAG_GEOM, _cpmg, os.path.join(OUT, 'magnitude_zoom_cpmg.mp4'), rho=1.16e-6,
    T2_per_comp=[SUB.T2_intra, SUB.T2_myelin, SUB.T2_extra], n_walkers=8000, stride=16,
    title='CPMG |M| distribution at REAL ρ = 1.16 µm/s (Barakovic 2023) — zoomed')
print(f"  magnitude_zoom_cpmg.mp4: {os.path.getsize(os.path.join(OUT, 'magnitude_zoom_cpmg.mp4')) / 1024:.0f} KB")
print('done')
