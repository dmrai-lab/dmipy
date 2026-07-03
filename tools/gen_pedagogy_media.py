"""Render the pedagogy animations shown on dmipy.org into docs/media/*.mp4.

Uses dmipy-sim's idealised-magnetisation pedagogy renderer (a real walk -> phase +
hard-pulse rotations + T2). Needs dmipy-sim + matplotlib + ffmpeg. The docs build itself
stays engine-independent -- it just serves these committed .mp4 files.

Run: python tools/gen_pedagogy_media.py
"""
import os
import numpy as np
import dmipy_sim
from dmipy_sim import pedagogy

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'media')
os.makedirs(OUT, exist_ok=True)

CYL = dmipy_sim.Cylinder(radius=5e-6, orientation=(0.0, 0.0, 1.0))
BVEC = np.array([[1.0, 0.0, 0.0]])


def movie(waveform, name, title, T2=0.05):
    hist = pedagogy.replay_with_history(CYL, waveform, 1.7e-9, T2=T2,
                                        n_walkers=3000, seed=1)
    path = os.path.join(OUT, name)
    pedagogy.spin_movie(hist, save=path, stride=3, fps=20, dpi=90, title=title)
    print(f'  {name}: {os.path.getsize(path) / 1024:.0f} KB')


print('rendering pedagogy media ->', os.path.normpath(OUT))
movie(dmipy_sim.pgse(delta=8e-3, DELTA=25e-3, G_magnitude=0.045, bvecs=BVEC, n_t=240),
      'pgse.mp4', 'PGSE - spin echo, restricted cylinder')
movie(dmipy_sim.cpmg(n_echoes=4, TE=12e-3, G_magnitude=0.0, bvecs=BVEC, n_t_per_echo=60),
      'cpmg.mp4', 'CPMG - multi-echo T2 decay')
movie(dmipy_sim.ogse(frequency=100.0, T_total=40e-3, G_magnitude=0.06, bvecs=BVEC, n_t=300),
      'ogse.mp4', 'OGSE - oscillating gradient')
print('done')
