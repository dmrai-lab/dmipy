#!/usr/bin/env python3
"""Regenerates ``mt_burnin.mp4`` — the MT engine burn-in, made visible.

A 2-D cross-section of a single myelinated cylinder in a small periodic cell. Free water
walkers (intra + extra) random-walk; when one contacts the myelin wall it *sticks* with a
local-time-weighted probability and freezes there for a dwell time, then releases — the
emergent bind/release exchange the vector-Bloch engine runs. Left: the walk, walkers
coloured free vs bound. Right: the bound-pool occupancy climbing from an empty start to its
thermal equilibrium f_b = k_f / (k_f + k_r) — which is exactly why a fresh (all-free) walk
must be *burned in* before the sequence fires.

The binding law and equilibrium mirror ``dmipy_sim.mt`` verbatim (kept inline so this doc
figure needs only numpy + matplotlib, no engine import):
    stick_probability(d_perp, kappa_MT, D) = min(1, 2 * (kappa_MT/D) * d_perp)   # mt.py eq.(1)
    k_f = kappa_MT * (S/V);  k_r = 1/dwell_time;  f_b = k_f / (k_f + k_r)         # mt.py

Run:  python docs/media/fig_mt_burnin.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Circle

# ── dmipy.org dark palette ──────────────────────────────────────────────────────
BG, PANEL, TEXT, MUTED = "#0d1120", "#111827", "#e8edf5", "#7a8499"
FREE, BOUND, TEAL = "#4af0c4", "#f0a24a", "#4af0c4"
MYELIN, AXON = "#2b3350", "#161d2e"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.edgecolor": "#2a3550", "font.size": 12,
})

# ── substrate (single myelinated cylinder, tight periodic cell) ─────────────────
R_I  = 2.5e-6                       # axon inner radius (m)
G    = 0.7                          # g-ratio -> myelin outer radius
R_O  = R_I / G                      # 3.57 um
L    = 2.0 * R_O + 2.6e-6           # tight cell: a thin extra-axonal rim
C    = np.array([L / 2, L / 2])     # cylinder centre

D        = 1.0e-9                   # free-water diffusivity (m^2/s)
KAPPA_MT = 3.2e-5                   # MT wall reactivity (m/s)
DWELL    = 1.0 / 50.0              # bound dwell time -> k_r = 50 /s
DT       = 4.0e-5                   # timestep (s)
SIGMA    = np.sqrt(2.0 * D * DT)    # per-axis 2-D Gaussian step (m)
N        = 500                      # walkers
N_STEPS  = 2600                     # ~ several 1/(k_f+k_r)
REC_EVERY = 14                      # frames = N_STEPS / REC_EVERY

# emergent-rate bookkeeping (mt.py): S/V of THIS cell, analytic equilibrium
S_OVER_V = (2 * np.pi * R_I + 2 * np.pi * R_O) / (np.pi * R_I**2 + (L**2 - np.pi * R_O**2))
K_F = KAPPA_MT * S_OVER_V
K_R = 1.0 / DWELL
F_B = K_F / (K_F + K_R)             # bound_fraction()
TAU = 1.0 / (K_F + K_R)


def _seed(n, rng):
    """Uniformly seed n walkers in the free water (intra r<R_I or extra r>R_O)."""
    pts = np.empty((n, 2))
    k = 0
    while k < n:
        p = rng.uniform(0, L, (n, 2))
        rad = np.linalg.norm(p - C, axis=1)
        ok = p[(rad < R_I) | (rad > R_O)]
        take = min(len(ok), n - k)
        pts[k:k + take] = ok[:take]
        k += take
    return pts


def run():
    rng = np.random.default_rng(0)
    p = _seed(N, rng)
    bound_rem = np.zeros(N)                          # >0 => frozen (steps left bound)
    frames_p, frames_b, occ_t = [], [], []

    for step in range(N_STEPS):
        free = bound_rem <= 0
        rad0 = np.linalg.norm(p - C, axis=1)
        dp = np.zeros((N, 2))
        dp[free] = rng.normal(0.0, SIGMA, (free.sum(), 2))
        pn = (p + dp) % L                            # periodic cell
        rvec = pn - C
        rad = np.linalg.norm(rvec, axis=1)
        ur = rvec / np.maximum(rad, 1e-30)[:, None]

        # free walkers that stepped INTO the myelin annulus -> wall contact
        inside = free & (rad > R_I) & (rad < R_O)
        from_in = inside & (rad0 <= R_I)             # hit inner wall from the axon
        from_out = inside & (rad0 >= R_O)            # hit outer wall from extra space
        d_perp = np.where(from_in, rad - R_I, np.where(from_out, R_O - rad, 0.0))

        # stick with local-time-weighted probability (mt.py eq.1); else specular reflect
        p_stick = np.minimum(1.0, 2.0 * (KAPPA_MT / D) * d_perp)
        u = rng.uniform(size=N)
        newly = inside & (u < p_stick)
        refl = inside & ~newly

        # reflected free walkers: mirror the radial overshoot back into their pool
        wall = np.where(from_in, R_I, R_O)
        pr = C + ur * (2 * wall - rad)[:, None]
        pn[refl] = pr[refl]
        # newly bound: freeze exactly on the wall contact point
        pn[newly] = (C + ur * wall[:, None])[newly]
        dwell_steps = np.ceil(-np.log(np.maximum(rng.uniform(size=N), 1e-20)) * (DWELL / DT))
        bound_rem[newly] = dwell_steps[newly]

        # advance bound clocks; frozen walkers don't move
        pn[~free] = p[~free]
        bound_rem[~free] -= 1.0

        p = pn
        if step % REC_EVERY == 0:
            frames_p.append(p.copy())
            frames_b.append((bound_rem > 0).copy())
            occ_t.append(float((bound_rem > 0).mean()))
    return frames_p, frames_b, np.array(occ_t)


def render(frames_p, frames_b, occ):
    nf = len(frames_p)
    t_ms = np.arange(nf) * REC_EVERY * DT * 1e3
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5.2),
                                   gridspec_kw={"width_ratios": [1, 1.05]})
    fig.subplots_adjust(left=0.02, right=0.94, top=0.88, bottom=0.13, wspace=0.22)

    # ── left: the cross-section walk ─────────────────────────────────────────────
    axL.set_xlim(0, L * 1e6); axL.set_ylim(0, L * 1e6); axL.set_aspect("equal")
    axL.set_xticks([]); axL.set_yticks([])
    axL.set_title("one myelinated cylinder — the walk", color=TEXT, fontsize=13, pad=8)
    axL.add_patch(Circle(C * 1e6, R_O * 1e6, facecolor=MYELIN, edgecolor="#5566aa",
                         lw=1.2, zorder=1))
    axL.add_patch(Circle(C * 1e6, R_I * 1e6, facecolor=AXON, edgecolor="#5566aa",
                         lw=1.0, zorder=2))
    axL.text(C[0] * 1e6, C[1] * 1e6, "axon", color=MUTED, ha="center", va="center",
             fontsize=10, zorder=3)
    axL.text(C[0] * 1e6, (C[1] + R_O) * 1e6 - 0.35, "myelin", color="#9fb0d8",
             ha="center", va="top", fontsize=9, zorder=3)
    sc = axL.scatter([], [], s=14, zorder=5)

    # ── right: the equilibrating occupancy ──────────────────────────────────────
    axR.set_xlim(0, t_ms[-1]); axR.set_ylim(0, max(F_B * 1.9, occ.max() * 1.25))
    axR.set_xlabel("burn-in time  (ms)"); axR.set_ylabel("pool fraction")
    axR.set_title("bound / free reaching equilibrium", color=TEXT, fontsize=13, pad=8)
    axR.axhline(F_B, ls="--", lw=1.4, color=BOUND, alpha=0.9)
    axR.text(t_ms[-1] * 0.5, F_B, f"equilibrium  $f_b = k_f/(k_f+k_r)$ = {F_B:.2f}",
             color=BOUND, ha="center", va="bottom", fontsize=10)
    axR.axvline(TAU * 1e3, ls=":", lw=1.0, color=MUTED, alpha=0.7)
    axR.text(TAU * 1e3 + 1.0, axR.get_ylim()[1] * 0.5, r"$\tau=1/(k_f+k_r)$",
             color=MUTED, ha="left", va="center", fontsize=9, rotation=90)
    (line_b,) = axR.plot([], [], color=BOUND, lw=2.4, label="bound pool (stuck to myelin)")
    (dot_b,) = axR.plot([], [], "o", color=BOUND, ms=6)
    axR.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=10)
    for s in axR.spines.values():
        s.set_color("#2a3550")
    time_txt = axL.text(0.03, 0.035, "", transform=axL.transAxes, color=TEAL, fontsize=11,
                        ha="left", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec="none", alpha=0.7))

    fig.suptitle("Magnetization transfer: spins stick to the wall until the bound pool fills",
                 color=TEXT, fontsize=14, y=0.975)

    def update(i):
        pts = frames_p[i] * 1e6
        b = frames_b[i]
        sc.set_offsets(pts)
        sc.set_color(np.where(b, BOUND, FREE))
        sc.set_sizes(np.where(b, 26, 13))
        line_b.set_data(t_ms[:i + 1], occ[:i + 1])
        dot_b.set_data([t_ms[i]], [occ[i]])
        time_txt.set_text(f"t = {t_ms[i]:5.1f} ms    bound = {occ[i] * 100:4.1f}%")
        return sc, line_b, dot_b, time_txt

    anim = FuncAnimation(fig, update, frames=nf, interval=55, blit=False)
    out = os.path.join(os.path.dirname(__file__), "mt_burnin.mp4")
    anim.save(out, writer=FFMpegWriter(fps=18, bitrate=2400), dpi=110)
    plt.close(fig)
    print(f"wrote {out}")
    print(f"  S/V={S_OVER_V:.3e} /m  k_f={K_F:.1f}/s  k_r={K_R:.1f}/s  "
          f"f_b(analytic)={F_B:.3f}  f_b(walk plateau)={occ[-20:].mean():.3f}")


if __name__ == "__main__":
    fp, fb, occ = run()
    render(fp, fb, occ)
