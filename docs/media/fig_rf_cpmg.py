#!/usr/bin/env python3
"""Regenerates ``rf_cpmg.png`` — Carr-Purcell vs Meiboom-Gill refocusing.

A CPMG echo train with an IMPERFECT 180° (here B1⁺ = 0.8, so the refocusing flip is ~144°, not
180°). The refocusing axis is the only difference:

  * Carr-Purcell (CP): 180ₓ — axis PERPENDICULAR to the transverse magnetisation. The flip-angle
    error tips magnetisation out of plane a little each echo, and the errors ACCUMULATE — the
    echo train decays and oscillates.
  * Meiboom-Gill (MG): 180_y — axis PARALLEL to the magnetisation (the 90ₓ put M along ∓y). Now
    the error on an odd echo is undone on the next even echo, so the train is SELF-CORRECTING and
    stays flat. Same imperfect pulse, opposite outcome — purely from the rotation axis.

Built on dmipy-sim's B1Pulse forward (the phase of a hard pulse sets its rotation axis).

    OMP_NUM_THREADS=1 JAX_PLATFORMS=cpu PYTHONPATH=/path/sim python fig_rf_cpmg.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dmipy_sim.rf import B1Pulse, bloch_simulate
GAMMA = 2.675e8
CP, MG = "#c1440e", "#1b6ca8"
dt = 2e-5


def _hard(flip_deg, dur, phase_deg):
    n = int(round(dur / dt))
    amp = np.deg2rad(flip_deg) / (GAMMA * n * dt)
    return np.full(n, amp) * np.exp(1j * np.deg2rad(phase_deg))


def cpmg(refoc_phase_deg, n_echo=10, t90=0.2e-3, t180=0.4e-3, techo=4e-3):
    gap = int(round((techo / 2 - t180 / 2) / dt))
    s = [_hard(90, t90, 0.0)]
    idx = []
    cur = len(s[0])
    for _ in range(n_echo):
        s.append(np.zeros(gap)); cur += gap
        s.append(_hard(180, t180, refoc_phase_deg)); cur += len(s[-1])
        s.append(np.zeros(gap)); cur += gap
        idx.append(cur)
    return B1Pulse.from_samples(np.concatenate(s), dt), idx


df = np.linspace(-120, 120, 41)     # off-resonance spread
b1 = 0.8                            # miscalibrated 180 (~144°)
n_echo = 10
echo_n = np.arange(1, n_echo + 1)
curves = {}
LBL_CP = r"Carr-Purcell ($180_x$, axis $\perp$ M)"
LBL_MG = r"Meiboom-Gill ($180_y$, axis $\parallel$ M)"
for name, phase in [(LBL_CP, 0.0), (LBL_MG, 90.0)]:
    p, idx = cpmg(phase, n_echo=n_echo)
    _, _, h = bloch_simulate(p, df_hz=df, b1_scale=b1, return_history=True)
    Mxy = h[:, 0, :] + 1j * h[:, 1, :]
    curves[name] = np.array([np.abs(Mxy[i].mean()) for i in idx])

plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=100)   # 720×400 (width %4==0)
ax.plot(echo_n, curves[LBL_CP], "o-", color=CP, lw=2, label=LBL_CP)
ax.plot(echo_n, curves[LBL_MG], "s-", color=MG, lw=2, label=LBL_MG)
ax.set_xlabel("echo number"); ax.set_ylabel(r"echo amplitude  $|\langle M_{xy}\rangle|$")
ax.set_title("Same imperfect 180° (~144°), opposite outcome — it's the rotation axis")
ax.set_ylim(0, 1.02); ax.set_xticks(echo_n); ax.legend(loc="lower left", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "rf_cpmg.png")
fig.savefig(out, dpi=100)
print("figure ->", out)
