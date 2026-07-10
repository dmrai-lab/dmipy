"""Appendix: surface-relaxation per-collision estimator comparison.

Two Monte-Carlo estimators of the Brownstein--Tarr Robin boundary condition
(D dM/dn = -rho M) differ only in what each *wall collision* costs the transverse
magnetisation:

  * realized-overshoot (ours) : |M| *= exp(-(rho/D) * 2 * d_perp)
        d_perp = perpendicular overshoot of the step that crossed the wall.
        This is a pathwise estimator of the boundary local time L_dOmega:
        sum(2 d_perp) -> L_dOmega, and exp(-(rho/D) L) is the Robin-BC survival.

  * fixed-per-collision (Cottaar et al. 2026, MCMRSimulator.jl v1.0.0, doi:10.1162/IMAG.a.1177,
        git tag v1.0.0 = commit 716f5337, src/evolve.jl:566-570) : |M| *= exp(-x * sqrt(dt))
        every detected collision costs the same, x = surface_relaxation rate
        [ms^-1/2]. A mean-field estimator: it replaces the realized penetration
        depth with its expectation.

Both converge to the same continuum answer as dt->0. This benchmark isolates the
*estimator* (not two codebases): one reflecting walk in a disk, both penalties
accumulated on the SAME collision events, so trajectory + collision detection are
common-mode and the only variable is the per-collision formula. We sweep the step
size (dt) and compare each scheme's recovered surface-relaxation rate against the
closed-form fast-diffusion Brownstein--Tarr rate rho*(S/V) = rho*(2/R).

Run: python appendix_estimator_comparison.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                            "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
                            "legend.fontsize": 10.5})
from scipy.special import j0, j1
from scipy.optimize import brentq

# ---- physical setup: single cylinder cross-section (2D disk), fast diffusion ----
R      = 3.0          # um   cylinder radius
D      = 3.0          # um^2/ms
RHO    = 0.03         # um/ms  physical surface relaxivity (rho*R/D = 0.03 << 1: deep fast-diffusion)
N      = 6000         # walkers
T      = 60.0         # ms   total evolution
BT     = RHO * 2.0 / R          # leading-order Brownstein-Tarr rate, S/V = 2/R
# exact lowest Robin-BC eigenvalue for the disk: (kR) J1(kR)/J0(kR) = rho R/D.
# BT above is only its rho R/D -> 0 limit; the true rate is lower by ~rho R/(4 D).
_kR   = brentq(lambda x: x * j1(x) / j0(x) - RHO * R / D, 1e-6, 2.0)
EXACT = D * (_kR / R) ** 2
X_THEORY = RHO * np.sqrt(np.pi / D)   # documented rho -> x mapping for the sqrt-dt scheme
SEED   = 0

# step sizes as a fraction of R; each maps to dt via step = sqrt(2 D dt)
STEP_FRAC = np.array([0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50])


def run_walk(dt, x_their, rho=RHO, Ttot=T):
    """One reflecting walk in the disk; return (t_checkpoints, S_our, S_their).
    Both weights accumulate on the SAME collisions. x_their is used as given (their
    documented rho->x mapping) -- no calibration to any analytical target."""
    rng = np.random.default_rng(SEED)          # SAME stream -> comparable
    step_sigma = np.sqrt(2.0 * D * dt)
    n_steps = int(np.ceil(Ttot / dt))
    ang = rng.uniform(0, 2 * np.pi, N)
    rad = R * np.sqrt(rng.uniform(0, 1, N))
    pos = np.stack([rad * np.cos(ang), rad * np.sin(ang)], axis=1)

    accum_our = np.zeros(N)     # sum of 2*d_perp  (boundary local time estimator)
    n_coll    = np.zeros(N)     # collision count
    check_ts = np.linspace(0, n_steps, 31, dtype=int)[1:]
    t_cp, S_our, S_their = [], [], []
    ci = 0
    for s in range(1, n_steps + 1):
        pos = pos + rng.standard_normal((N, 2)) * step_sigma
        nrm = np.hypot(pos[:, 0], pos[:, 1])
        out = nrm > R
        if out.any():
            d_perp = nrm[out] - R
            accum_our[out] += 2.0 * d_perp
            n_coll[out]    += 1.0
            # radial reflection back inside (production scheme): r -> 2R - |r|
            pos[out] *= ((2.0 * R - nrm[out]) / nrm[out])[:, None]
        if ci < len(check_ts) and s == check_ts[ci]:
            t_cp.append(s * dt)
            S_our.append(np.exp(-(rho / D) * accum_our).mean())
            S_their.append(np.exp(-x_their * np.sqrt(dt) * n_coll).mean())
            ci += 1
    return np.array(t_cp), np.array(S_our), np.array(S_their)


def rate(t, S):
    """Lowest-eigenvalue rate: slope of -ln S over the asymptotic tail."""
    m = t > 0.4 * t.max()
    A = np.vstack([t[m], np.ones(m.sum())]).T
    return np.linalg.lstsq(A, -np.log(np.asarray(S)[m]), rcond=None)[0][0]


def exact_eig(rho):
    """Exact lowest Robin-BC eigenvalue for the disk: (kR)J1(kR)/J0(kR)=rho R/D."""
    kR = brentq(lambda x: x * j1(x) / j0(x) - rho * R / D, 1e-9, 2.2)
    return D * (kR / R) ** 2


print(f"leading BT rho(2/R) = {BT:.5f} /ms   exact eigenvalue = {EXACT:.5f} /ms "
      f"({100*(EXACT/BT-1):+.2f}%)")

# --- (B) step-size robustness at fixed rho, error vs the EXACT eigenvalue ----------
# no calibration: ours is parameter-free; theirs uses the documented x = rho sqrt(pi/D).
print(f"\n{'step/R':>7} {'our %exact':>11} {'their %exact':>13}")
rows = []
for frac in STEP_FRAC:
    dt = (R * frac) ** 2 / (2.0 * D)
    t, So, St = run_walk(dt, x_their=X_THEORY)
    eo, et = 100 * (rate(t, So) / EXACT - 1), 100 * (rate(t, St) / EXACT - 1)
    rows.append((frac, eo, et))
    print(f"{frac:7.2f} {eo:11.2f} {et:13.2f}")
rows = np.array(rows)
LEAD_VS_EXACT = 100 * (BT / EXACT - 1)      # leading-order BT offset from the truth

# --- (C) does ours track the exact eigenvalue as rho R/D grows? (fixed fine step) --
FRAC_FINE = STEP_FRAC[0]
HLIST = np.array([0.03, 0.06, 0.10, 0.15, 0.22])
print(f"\n{'rhoR/D':>7} {'our %exact':>11} {'their %exact':>13} {'leadBT %exact':>14}")
sweep = []
for h in HLIST:
    rho, bt_h, ex_h = h * D / R, h * D / R * 2.0 / R, exact_eig(h * D / R)
    dt = (R * FRAC_FINE) ** 2 / (2.0 * D)
    t, So, St = run_walk(dt, x_their=(h * D / R) * np.sqrt(np.pi / D), rho=rho, Ttot=3.0 / bt_h)
    eo, et = 100 * (rate(t, So) / ex_h - 1), 100 * (rate(t, St) / ex_h - 1)
    el = 100 * (bt_h / ex_h - 1)
    sweep.append((h, eo, et, el))
    print(f"{h:7.2f} {eo:11.2f} {et:13.2f} {el:14.2f}")
sweep = np.array(sweep)

# --- (D) scale invariance: is the <1% accuracy radius-independent down to sub-micron? -
# The estimator error is a function of the two dimensionless groups (rho R/D, step/R) alone,
# so fixing both and sweeping R should give a radius-INDEPENDENT error -- the rigorous basis
# for carrying the interior rate to the sub-micron calibres that dominate the bias (which, at
# physical rho, have even smaller rho R/D, i.e. sit deeper in fast diffusion; cf. panel C).
def _exact_eig_R(rho, R):
    kR = brentq(lambda x: x * j1(x) / j0(x) - rho * R / D, 1e-9, 2.2)
    return D * (kR / R) ** 2


def _run_R(R, rho, frac=0.05, Nw=4000):
    rng = np.random.default_rng(SEED); bt = rho * 2.0 / R; Ttot = 3.0 / bt
    dt = (R * frac) ** 2 / (2.0 * D); n = int(np.ceil(Ttot / dt)); ss = np.sqrt(2.0 * D * dt)
    ang = rng.uniform(0, 2 * np.pi, Nw); rad = R * np.sqrt(rng.uniform(0, 1, Nw))
    pos = np.stack([rad * np.cos(ang), rad * np.sin(ang)], 1); acc = np.zeros(Nw)
    cts = np.linspace(0, n, 31, dtype=int)[1:]; ci = 0; tcp = []; S = []
    for s in range(1, n + 1):
        pos = pos + rng.standard_normal((Nw, 2)) * ss
        nrm = np.hypot(pos[:, 0], pos[:, 1]); out = nrm > R
        if out.any():
            acc[out] += 2.0 * (nrm[out] - R); pos[out] *= ((2.0 * R - nrm[out]) / nrm[out])[:, None]
        if ci < len(cts) and s == cts[ci]:
            tcp.append(s * dt); S.append(np.exp(-(rho / D) * acc).mean()); ci += 1
    tcp = np.array(tcp); S = np.array(S); m = tcp > 0.4 * tcp.max()
    A = np.vstack([tcp[m], np.ones(m.sum())]).T
    return np.linalg.lstsq(A, -np.log(S[m]), rcond=None)[0][0]


print(f"\nscale invariance (rho R/D=0.03, step/R=0.05 fixed):")
print(f"{'R(um)':>7} {'err vs exact %':>15}")
for R_ in [3.0, 1.0, 0.5, 0.2, 0.1]:
    rho_ = 0.03 * D / R_
    print(f"{R_:7.2f} {100*(_run_R(R_, rho_)/_exact_eig_R(rho_, R_)-1):15.2f}")

# ---- figure ---------------------------------------------------------------------
import matplotlib.gridspec as gridspec

C_OUR, C_THEIR = "C0", "C1"


def draw_schematic(ax):
    """Rays of EQUAL step length hitting a wall at different angles; the perpendicular
    overshoot d_perp = L*cos(theta) sets our per-hit cost (variable), while the fixed-dt
    scheme charges the same cost to every hit regardless of angle."""
    ax.set_xlim(-0.3, 15.4); ax.set_ylim(-2.15, 2.15); ax.set_aspect("equal"); ax.axis("off")
    # water below, obstruction above, wall at y=0
    ax.axhspan(0, 2.15, color="0.86", zorder=0)
    ax.axhspan(-2.15, 0, color="#eaf3fb", zorder=0)
    ax.axhline(0, color="k", lw=2, zorder=5)
    ax.text(0.0, 1.9, "axon wall  (relaxation sink)", ha="left", va="top", fontsize=8.5, color="0.30")
    ax.text(0.0, -2.05, "water (spins diffuse, step length $L$ fixed)", ha="left", va="bottom",
            fontsize=8.5, color="#3a6ea5")

    thetas = np.radians([16.0, 45.0, 74.0])
    hit_x  = [1.5, 4.1, 6.6]
    labels = ["near-perpendicular", "oblique", "glancing"]
    L = 1.35
    cos = np.cos(thetas)
    ours_rel   = cos / cos.max()                 # variable: 1.00, 0.74, 0.29
    theirs_rel = np.full(3, float(cos.mean() / cos.max()))   # fixed = mean of the hits

    for i, (th, hx, lab, orel, trel) in enumerate(zip(thetas, hit_x, labels, ours_rel, theirs_rel)):
        s, c = np.sin(th), np.cos(th)
        # incoming solid ray from inside up to the wall
        start = (hx - L * s, -L * c)
        ax.annotate("", xy=(hx, 0), xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color="0.25", lw=1.7))
        # dashed overshoot beyond the wall to the virtual endpoint (height = d_perp)
        E = (hx + L * s, L * c)
        ax.plot([hx, E[0]], [0, E[1]], ls=(0, (3, 2)), color="0.55", lw=1.3, zorder=6)
        ax.plot([E[0]], [E[1]], marker="o", ms=3.5, color="0.55", zorder=6)
        # reflected solid ray back into the water
        ax.annotate("", xy=(hx + L * s, -L * c), xytext=(hx, 0),
                    arrowprops=dict(arrowstyle="-|>", color=C_OUR, lw=1.7))
        # d_perp bracket (label the formula only once, on the first ray)
        bx = E[0] + 0.18
        ax.annotate("", xy=(bx, 0), xytext=(bx, E[1]),
                    arrowprops=dict(arrowstyle="<->", color="k", lw=0.9))
        lab_d = r"$d_\perp\!=\!L\cos\theta$" if i == 0 else r"$d_\perp$"
        ax.text(bx + 0.08, E[1] / 2, lab_d, fontsize=7.5, va="center")
        ax.text(hx, 0.10, lab, ha="center", va="bottom", fontsize=7.5, color="0.15")
        # per-hit cost mini-bars in the water, below the arrow tips
        bx0, by = hx - 0.55, -1.52
        w = 1.15
        ax.add_patch(plt.Rectangle((bx0, by), w * orel, 0.16, color=C_OUR, zorder=6))
        ax.add_patch(plt.Rectangle((bx0, by - 0.26), w * trel, 0.16, color=C_THEIR, zorder=6))
        ax.text(bx0, by + 0.24, "cost / hit:", fontsize=6.8, color="0.3")
        ax.text(bx0 + w * orel + 0.05, by + 0.08, f"{orel:.2f}", fontsize=6.8, va="center", color=C_OUR)
        ax.text(bx0 + w * trel + 0.05, by - 0.18, f"{trel:.2f}", fontsize=6.8, va="center", color=C_THEIR)

    # key on the right (all glyphs kept above the wall to avoid the glancing d_perp label)
    kx = 9.35
    ax.text(kx, 1.82, "per wall hit, $|M|$ is multiplied by:", fontsize=8.5, color="0.15")
    ax.plot([kx, kx + 0.5], [1.28, 1.28], color=C_OUR, lw=3)
    ax.text(kx + 0.65, 1.28, r"ours: $e^{-2\rho\,d_\perp/D}$" + "  (varies with angle)",
            fontsize=8, va="center", color=C_OUR)
    ax.plot([kx, kx + 0.5], [0.72, 0.72], color=C_THEIR, lw=3)
    ax.text(kx + 0.65, 0.72, r"Cottaar et al.: $e^{-x\sqrt{\Delta t}}$" + "  (same every hit)",
            fontsize=8, va="center", color=C_THEIR)
    ax.text(kx, -0.55, "Glancing hits barely touch the wall\n(small $d_\\perp$): ours charges little,\n"
                       "Cottaar et al. over-charges. Head-on\nhits penetrate ($d_\\perp\\!\\approx\\!L$): ours\n"
                       "charges more, Cottaar et al. under-charges.",
            fontsize=7.2, va="top", color="0.25")


fig = plt.figure(figsize=(10, 7.4))
gs = gridspec.GridSpec(2, 2, height_ratios=[1.02, 1.0], hspace=0.30, wspace=0.26)
axS = fig.add_subplot(gs[0, :])
axB = fig.add_subplot(gs[1, 0])
axC = fig.add_subplot(gs[1, 1])

draw_schematic(axS)
axS.set_title("A   Per-collision cost: what each wall hit charges the magnetisation",
              loc="left", fontsize=10)

# B: step-size robustness at fixed rho, everything referenced to the EXACT eigenvalue
axB.axhline(0, color="0.35", ls=":", lw=1.4, label="exact Robin eigenvalue")
axB.axhline(LEAD_VS_EXACT, color="k", ls="--", lw=1, label="leading BT $\\rho\\,2/R$ (approx.)")
axB.plot(rows[:, 0], rows[:, 1], "o-", color=C_OUR, label="realized overshoot (ours)")
axB.plot(rows[:, 0], rows[:, 2], "s-", color=C_THEIR, label="fixed $\\sqrt{\\Delta t}$ (Cottaar et al.)")
axB.set_xlabel("step size / R"); axB.set_ylabel("error vs exact eigenvalue  [%]")
axB.set_title("B   Step-size robustness ($\\rho R/D=0.03$)", loc="left", fontsize=10)
axB.legend(fontsize=7.2)

# C: tracking the exact rate as rho R/D grows (fixed fine step, no calibration)
axC.axhline(0, color="0.35", ls=":", lw=1.4, label="exact Robin eigenvalue")
axC.plot(sweep[:, 0], sweep[:, 3], "^--", color="k", label="leading BT $\\rho\\,2/R$ (approx.)")
axC.plot(sweep[:, 0], sweep[:, 1], "o-", color=C_OUR, label="realized overshoot (ours)")
axC.plot(sweep[:, 0], sweep[:, 2], "s-", color=C_THEIR, label="fixed $\\sqrt{\\Delta t}$ (Cottaar et al.)")
axC.set_xlabel("$\\rho R/D$"); axC.set_ylabel("error vs exact eigenvalue  [%]")
axC.set_title("C   Tracking the exact rate (fixed fine step)", loc="left", fontsize=10)
axC.legend(fontsize=7.2)

fig.suptitle(f"Surface-relaxation estimator comparison "
             f"($R={R}\\,\\mu m,\\ D={D}\\,\\mu m^2/ms$; $\\rho R/D=0.03$ in A, B)", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.98])
out = "figures/appendix_estimator_comparison.pdf"
fig.savefig(out, dpi=150); fig.savefig(out.replace(".pdf", ".png"), dpi=150)
print(f"\nsaved {out}")
