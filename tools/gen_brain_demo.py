"""Generate the brain demo's data (docs/studio/brain_data/) from the BATMAN replay phantom and its packs.

The page recombines, it never replays: composition is exact in the browser. In ODF mode a pack's pose response
for one measurement is 45 numbers (the n = 0 SO(3) coefficients to lmax = 8), voxel-independent, and a voxel's
signal is its FOD contracted with them, weighted by fraction and m0, summed over tissues. For the gradient-only
replay the response factorises by rotational covariance, c_lm(g, b) = a_l(b) Y_lm(g), so five numbers per b give
any gradient direction at any b. With a field the coefficients depend on B0's direction too, so those are
stored per (head tilt, B0, spin/gradient echo, shell, direction). Everything here is dmipy-sim's own arithmetic;
tools/check_brain.js runs the page against the stored checks.

Run:  python tools/gen_brain_demo.py --stage voxels   (seconds)
      python tools/gen_brain_demo.py --stage field    (half an hour: the field route costs ~60 s per call)
      python tools/gen_brain_demo.py --stage checks   (minutes: the field-mode checks alone, after a tissue value changes)

No physical value is written here: every T2, proton density, diffusivity and susceptibility comes from
``dmipy_sim.substrate.biophysical_constants`` by key, and the page lists each with its citation.
"""
from __future__ import annotations
import argparse
import json
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "studio", "brain_data")
BATMAN = os.environ.get("BATMAN_DIR", "/home/rutger/dmrai-ws/data/batman")
RPH = os.path.join(BATMAN, "out_full", "batman_brain.rph")
ROUNDTRIP = os.path.join(BATMAN, "out_full", "csd_roundtrip.npz")
PACKS = {"wm": os.environ.get("WM_PACK", "/home/rutger/dmrai-ws/packs/cactus_single_bundle_100ms_xframe.rpk"),
         "gm": os.environ.get("GM_PACK", "/home/rutger/dmrai-ws/packs/gm_spheres_100ms.rpk")}
TE, DELTA, DDELTA = 0.100, 0.025, 0.055                       # the capstone's acquisition (the packs are 100 ms walks)
LMAX = 8
B_GRID = np.arange(0.0, 3000.1, 100.0) * 1e6                  # s/m^2
SHELLS = [1000e6, 2000e6, 3000e6]
TILTS = [("sagittal", a) for a in (-30, -20, -10, 0, 10, 20, 30)] + [("coronal", a) for a in (-30, -15, 15, 30)]
B0_T = [1.5, 3.0]                                             # 7 T: the static dephasing band outgrows a demo table
N_FIELD_DIRS = 40
N_CHECK = 300


def _phantom_and_packs():
    from dmipy_sim.phantom import Phantom
    from dmipy_sim.replay import read_rpk
    packs = {k: read_rpk(v) for k, v in PACKS.items()}
    ph = Phantom.read(RPH, packs={"wm": packs["wm"], "gm": packs["gm"]})
    return ph, packs


def _image_rotation():
    """R (image -> scanner) of the FOD image, from the same affine the capstone used (the mask shares it)."""
    from dmipy_sim.io.mrtrix import read_mif
    from dmipy_sim.phantom import Grid
    m = read_mif(os.path.join(BATMAN, "mask_den_unr_preproc_unb.mif"))
    grid, R = Grid.from_oblique_affine(m.affine, m.shape[:3])
    return np.asarray(R, float), m


CONSTANTS = dict(                                              # every physical value on the page, by its table key
    T2_wm=["T2_extra_axonal", "T2_intra_axonal", "T2_myelin"],    # the CACTUS pools, in id order (0 extra, 1 intra, 2 myelin)
    T2_gm="T2_grey_matter", T2_csf="T2_csf", D_csf="D_csf",
    chi_iso="chi_iso_myelin", chi_aniso="delta_chi_a_myelin",
    m0_wm="proton_density_white_matter", m0_gm="proton_density_grey_matter", m0_csf="proton_density_csf",
)
FIELD_T_OF_VALUES = 3.0                                        # the relaxation and susceptibility values' field


def _tissue(packs):
    """Every physical value the demo replays at, from dmipy-sim's biophysical constants table by key, with the
    table entry (value, unit, field, source, location, citation) kept for the page. Free water has no T2 of the
    pack's kind: it takes the catalogued CSF T2 as its own."""
    from dmipy_sim.substrate import biophysical_constants as bc
    from dmipy_sim.substrate.biophysical_constants import get_constant, get_value
    citations = {c["key"]: c for n in dir(bc) if n.startswith("_CITATION_") for c in [getattr(bc, n)] if isinstance(c, dict)}
    for e in bc.BIOPHYSICAL_CONSTANTS.values():
        c = e.get("citation")
        if isinstance(c, dict) and c.get("key"):
            citations.setdefault(c["key"], c)
    def rec(name, field_T=None):
        """The table entry the value came from: the candidate matched to the field (the default, or the alternative
        at that field), with ITS source and location, and the citation of that source."""
        e = get_constant(name); v = get_value(name, field_T, allow_nearest=True) if field_T is not None else get_value(name)
        cands = [e["default"]] + list(e.get("alternatives", []))
        d = next((c for c in cands if c["value"] == v and (field_T is None or c.get("field_T") in (field_T, None))), e["default"])
        return dict(value=float(v), unit=d.get("unit"), field_T=d.get("field_T"), source_key=d.get("source_key"),
                    location=d.get("location"), citation=citations.get(d.get("source_key"), e.get("citation")),
                    description=e.get("description"))
    table = {}
    def val(name, field_T=None):
        table[name] = rec(name, field_T); return table[name]["value"]
    out = dict(T2_wm=[val(k, FIELD_T_OF_VALUES) for k in CONSTANTS["T2_wm"]],
               T2_gm=[val(CONSTANTS["T2_gm"], FIELD_T_OF_VALUES)] * 2,           # both pools of the sphere packing
               T2_csf=val(CONSTANTS["T2_csf"], FIELD_T_OF_VALUES), D_csf=val(CONSTANTS["D_csf"]),
               chi_iso=val(CONSTANTS["chi_iso"]), chi_aniso=val(CONSTANTS["chi_aniso"]),
               m0=dict(wm=val(CONSTANTS["m0_wm"]), gm=val(CONSTANTS["m0_gm"]), csf=val(CONSTANTS["m0_csf"])))
    out["table"] = table
    return out


def _even_sh_map():
    """The axis-density map restricted to even orders: the 45 x 45 matrix taking a voxel's FOD coefficients (even
    orders, compact) to its n = 0 SO(3) coefficients in the same order (dmipy_sim.replay.so3._axis_map)."""
    from dmipy_sim.replay import so3
    M = np.asarray(so3._axis_map(LMAX, 0), float)                                   # (81 so3 n=0, 81 sh full)
    idx = so3.so3_index(LMAX, 0)
    rows = [j for j, (l, m, n) in enumerate(idx) if l % 2 == 0]
    cols = [l * l + l + m for l in range(0, LMAX + 1, 2) for m in range(-l, l + 1)]
    return M[np.ix_(rows, cols)], rows


def _a_l(pack, T2, b_grid):
    """a_l(b): the per-order kernel of the pack's gradient-only response, from the closed-form pose expansion at a
    few directions per b (their agreement is the factorisation check, reported)."""
    from dmipy_sim import sequences
    from dmipy_sim.replay import so3
    dirs = np.array([[0, 0, 1.0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 1], [1, 1, 1]], float)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    nb, nd = len(b_grid), len(dirs)
    G = np.tile(dirs, (nb, 1)); bv = np.repeat(b_grid, nd)
    seq = sequences.pgse(G, DELTA, DDELTA, bvalues=bv, TE=TE)
    P = pack.pose_response(seq, tissue=False, T2=T2, keep=(LMAX, 0))
    idx = so3.so3_index(LMAX, 0); Y = so3.real_sh(LMAX, dirs, full=True)
    a = np.zeros((nb, LMAX // 2 + 1)); spread = 0.0
    for l in range(0, LMAX + 1, 2):
        cols = [j for j, (L, m, n) in enumerate(idx) if L == l]
        ys = np.array([[Y[k, l * l + l + m] for (L, m, n) in [idx[j] for j in cols]] for k in range(nd)])   # (nd, 2l+1)
        for i in range(nb):
            c = P.coeffs[i * nd:(i + 1) * nd, cols].real                                                   # (nd, 2l+1)
            per_dir = (c * ys).sum(1) / (ys * ys).sum(1)
            a[i, l // 2] = per_dir.mean()
            if l == 0 or i > 0:
                spread = max(spread, float(np.ptp(per_dir)))
    return a, spread


def _check_phantom(ph, packs, voxels, tissue, wm_only=False):
    """A one-row phantom of the check voxels, with the demo's tissue on each pack: what the browser's numbers are
    compared against through the full phantom route."""
    from dmipy_sim.phantom import Grid, ODF, PackSubstrate, FreeWater, Inert, Phantom
    f = ph.file
    n = len(voxels)
    fr = np.asarray(f.arrays["geometric_fraction"])[voxels]; sid = np.asarray(f.arrays["substrate_id"])[voxels]
    sh = np.asarray(f.arrays["odf_sh"])[voxels]
    def slot(i):
        out_f = np.zeros(n); out_sh = np.zeros((n, sh.shape[2]))
        for v in range(n):
            k = np.flatnonzero(sid[v] == i)
            if k.size:
                out_f[v] = fr[v, k[0]]; out_sh[v] = sh[v, k[0]]
        return out_f, out_sh
    f_wm, sh_wm = slot(0); f_gm, sh_gm = slot(1); f_csf, _ = slot(2)
    wm = PackSubstrate(packs["wm"], m0=tissue["m0"]["wm"], name="wm", T2_s=tissue["T2_wm"])
    gm = PackSubstrate(packs["gm"], m0=tissue["m0"]["gm"], name="gm", T2_s=tissue["T2_gm"])
    csf = FreeWater(D_m2_s=tissue["D_csf"], m0=tissue["m0"]["csf"], T2_s=tissue["T2_csf"])
    grid = Grid(shape=(n, 1, 1), voxel_size_m=(2.5e-3,) * 3)
    iso = np.zeros_like(sh_gm); iso[:, 0] = 1.0 / np.sqrt(4 * np.pi)
    sh_gm = np.where(np.abs(sh_gm).sum(1, keepdims=True) > 0, sh_gm, iso)
    sh_wm = np.where(np.abs(sh_wm).sum(1, keepdims=True) > 0, sh_wm, iso)
    if wm_only:                                                    # the field mode's reference: the GM pack has no field
        return Phantom.compose(grid, fractions={wm: f_wm.reshape(n, 1, 1)}, remainder=Inert(),      # tier and would refuse B0
                               orientation={wm: ODF(sh_wm.reshape(n, 1, 1, 1, -1), basis="tournier07")})
    ph_c = Phantom.compose(grid, fractions={wm: f_wm.reshape(n, 1, 1), gm: f_gm.reshape(n, 1, 1), csf: f_csf.reshape(n, 1, 1)},
                           remainder=Inert(),
                           orientation={wm: ODF(sh_wm.reshape(n, 1, 1, 1, -1), basis="tournier07"),
                                        gm: ODF(sh_gm.reshape(n, 1, 1, 1, -1), basis="tournier07")})
    return ph_c


def stage_voxels():
    from dmipy_sim import sequences
    from dmipy_sim.replay import so3
    t0 = time.time()
    ph, packs = _phantom_and_packs(); f = ph.file
    R, mask_img = _image_rotation()
    tissue = _tissue(packs); m0 = tissue["m0"]
    declared = {sub["id"]: sub["m0"] for sub in f.meta["substrates"]}
    for k, sid_ in (("wm", "wm"), ("gm", "gm"), ("csf", "csf/free-water")):
        if abs(declared[sid_] - m0[k]) > 1e-9:
            raise ValueError(f"the phantom file declares m0 = {declared[sid_]} for {sid_} but the table says {m0[k]}: rebuild the phantom")
    idx = np.asarray(f.arrays["voxel_index"], np.int16)
    sid = np.asarray(f.arrays["substrate_id"]); fr = np.asarray(f.arrays["geometric_fraction"]); sh = np.asarray(f.arrays["odf_sh"])
    n = idx.shape[0]
    frac = np.zeros((n, 3), np.float32); sh_wm = np.zeros((n, sh.shape[2]), np.float32)
    for i in range(3):
        m = sid == i
        rows = np.flatnonzero(m.any(1)); k = np.argmax(m[rows], axis=1)
        frac[rows, i] = fr[rows, k]
        if i == 0:
            sh_wm[rows] = sh[rows, k]
    from dmipy_sim.io.mrtrix import read_mif
    b0 = read_mif(os.path.join(BATMAN, "mean_b0_preprocessed.mif")).data
    b0v = np.asarray(b0)[tuple(idx.T.astype(int))]
    b0u = np.clip(255.0 * b0v / np.percentile(b0v, 99.5), 0, 255).astype(np.uint8)
    z = np.load(ROUNDTRIP)
    ang = np.full(n, 255, np.uint8)
    lut = {tuple(v): i for i, v in enumerate(map(tuple, idx.tolist()))}
    for v, a in zip(z["voxels"], z["angle_deg"]):
        j = lut.get(tuple(int(x) for x in v))
        if j is not None:
            ang[j] = min(254, int(round(float(a))))
    os.makedirs(OUT, exist_ok=True)
    parts = [("idx", idx.astype("<i2")), ("frac", frac.astype("<f2")),          # fractions to 1e-3: uint8 was 0.4% of signal
             ("b0", b0u), ("angle", ang), ("sh", sh_wm.astype("<f2"))]
    layout, off = [], 0
    with open(os.path.join(OUT, "voxels.bin"), "wb") as fh:
        for name, arr in parts:
            b = np.ascontiguousarray(arr).tobytes(); fh.write(b)
            layout.append(dict(name=name, dtype=str(arr.dtype).replace("<", ""), shape=list(arr.shape), offset=off, nbytes=len(b))); off += len(b)
    print(f"voxels.bin: {off / 1e6:.1f} MB for {n} voxels  [{time.time() - t0:.0f}s]", flush=True)
    # the tables
    a_wm, spread = _a_l(packs["wm"], tissue["T2_wm"], B_GRID)
    print(f"a_l(b) wm: factorisation spread {spread:.2e}  [{time.time() - t0:.0f}s]", flush=True)
    seq_b = sequences.pgse(np.tile([[0, 0, 1.0]], (len(B_GRID), 1)), DELTA, DDELTA, bvalues=B_GRID, TE=TE)
    E_gm = np.asarray(packs["gm"].replay(seq_b, tissue=False, T2=tissue["T2_gm"]), float)
    M, _rows = _even_sh_map()
    # the checks: the browser against the phantom route, on random brain voxels, at the tutorial's own scheme
    g = np.loadtxt(os.path.join(BATMAN, "dwipreproc_grad.b")); dirs_s, bv = g[:, :3], g[:, 3] * 1e6
    nrm = np.linalg.norm(dirs_s, axis=1); dirs_s = np.where(nrm[:, None] > 0, dirs_s / np.where(nrm[:, None] > 0, nrm[:, None], 1), [0, 0, 1.0])
    dirs_img = dirs_s @ R
    rng = np.random.default_rng(0)
    wm_rows = np.flatnonzero(frac[:, 0] > 0.3); other = np.flatnonzero(frac[:, 0] <= 0.3)
    chk = np.sort(np.concatenate([rng.choice(wm_rows, N_CHECK * 2 // 3, replace=False), rng.choice(other, N_CHECK // 3, replace=False)]))
    ph_c = _check_phantom(ph, packs, chk, tissue)
    seq_real = sequences.pgse(dirs_img, DELTA, DDELTA, bvalues=bv, TE=TE)
    S_chk = np.asarray(ph_c.replay(seq_real))[:, 0, 0, :]
    print(f"check phantom: {len(chk)} voxels x {seq_real.n_meas} measurements  [{time.time() - t0:.0f}s]", flush=True)
    Yd = rng.normal(size=(24, 3)); Yd /= np.linalg.norm(Yd, axis=1, keepdims=True)
    Y_chk = so3.real_sh(LMAX, Yd, full=False)
    index = dict(
        generated=time.strftime("%Y-%m-%d"), dmipy_sim=_sim_version(),
        grid=dict(shape=[int(x) for x in ph.grid.shape], voxel_size_mm=[float(v) * 1e3 for v in ph.grid.voxel_size_m], axes=ph.grid.axes,
                  R_image_to_scanner=R.tolist()),
        acquisition=dict(TE_ms=TE * 1e3, delta_ms=DELTA * 1e3, Delta_ms=DDELTA * 1e3, b_grid_smm2=(B_GRID / 1e6).tolist()),
        tissues=[dict(id="wm", kind="pack", m0=m0["wm"], T2_s=tissue["T2_wm"], pack=os.path.basename(PACKS["wm"]),
                      line=f'PackSubstrate(wm_pack, m0={m0["wm"]:g}, T2_s={[round(v, 4) for v in tissue["T2_wm"]]})',
                      keys=dict(m0=CONSTANTS["m0_wm"], T2_s=CONSTANTS["T2_wm"]),
                      note="CACTUS bundle, 366 strands, 120k walkers, 100 ms; pools extra / intra / myelin"),
                 dict(id="gm", kind="pack", m0=m0["gm"], T2_s=tissue["T2_gm"], pack=os.path.basename(PACKS["gm"]),
                      line=f'PackSubstrate(gm_pack, m0={m0["gm"]:g}, T2_s={[round(v, 4) for v in tissue["T2_gm"]]})',
                      keys=dict(m0=CONSTANTS["m0_gm"], T2_s=[CONSTANTS["T2_gm"]] * 2),
                      note="packed spheres 2-9 um, 20k walkers, 100 ms; isotropic"),
                 dict(id="csf", kind="analytic", m0=m0["csf"], D_m2_s=tissue["D_csf"], T2_s=tissue["T2_csf"],
                      line=f'FreeWater(D_m2_s={tissue["D_csf"]:g}, m0={m0["csf"]:g}, T2_s={tissue["T2_csf"]:g})',
                      keys=dict(m0=CONSTANTS["m0_csf"], D_m2_s=CONSTANTS["D_csf"], T2_s=CONSTANTS["T2_csf"]),
                      note="exp(-b D) exp(-TE / T2): the one closed form the format defines, full-tier with zeros (RPH.md 3.1)")],
        constants=dict(field_T=FIELD_T_OF_VALUES, table=tissue["table"],
                       note="every physical value on the page, by its key in dmipy_sim.substrate.biophysical_constants, with its citation"),
        response=dict(lmax=LMAX, wm_a_l=a_wm.tolist(), wm_factorisation_spread=spread, gm_E=E_gm.tolist(),
                      note="wm_a_l[b][l/2]: c_lm(g, b) = a_l(b) Y_lm(g); gm_E[b]: the isotropic pack's signal; csf: exp(-b D) exp(-TE / T2)"),
        sh=dict(order="even l to lmax, m = -l..l, orthonormal real (RPH.md 4.1), the pack's own basis",
                axis_map=M.tolist(), Y_check=dict(dirs=Yd.tolist(), Y=Y_chk.tolist())),
        voxels=dict(file="voxels.bin", n=int(n), layout=layout, frac_order=["wm", "gm", "csf"], angle="CSD round-trip peak angle (deg), 255 = not WM"),
        check=dict(voxels=chk.tolist(), scheme=dict(b_smm2=(bv / 1e6).tolist(), dirs_image=dirs_img.tolist()),
                   S=np.round(S_chk, 6).tolist(), tol=1e-3),
        roundtrip=dict(n_wm=int(len(z["angle_deg"])), angle_median_deg=float(np.median(z["angle_deg"])),
                       angle_below_10_deg=float(np.mean(z["angle_deg"] < 10)), acc_mean=float(np.mean(z["acc"]))),
        field=None,
    )
    prev = os.path.join(OUT, "index.json")
    if os.path.exists(prev):                                       # the field stage's tables survive a regenerated voxel stage
        with open(prev) as fh:
            index["field"] = json.load(fh).get("field")
    with open(prev, "w") as fh:
        json.dump(index, fh)
    print(f"index.json written  [{time.time() - t0:.0f}s]", flush=True)


def _sim_version():
    from importlib.metadata import version, PackageNotFoundError
    try:
        return version("dmipy-sim")
    except PackageNotFoundError:
        return "git"


def _tilt_matrix(kind, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    if kind == "sagittal":                         # nod: about the scanner's left-right axis (x)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])   # roll: about the anterior-posterior axis (y)


def stage_field():
    from dmipy_sim import sequences
    from dmipy_sim.replay import so3
    t0 = time.time()
    ph, packs = _phantom_and_packs()
    R, _ = _image_rotation(); tissue = _tissue(packs)
    with open(os.path.join(OUT, "index.json")) as fh:
        index = json.load(fh)
    # the direction set: a Fibonacci hemisphere in the SCANNER frame, the same for every tilt
    k = np.arange(N_FIELD_DIRS) + 0.5; zc = 1.0 - k / N_FIELD_DIRS; r = np.sqrt(1 - zc ** 2); phi = k * np.pi * (3 - np.sqrt(5))
    dirs_s = np.stack([r * np.cos(phi), r * np.sin(phi), zc], 1)
    M, rows = _even_sh_map()
    chk = np.asarray(index["check"]["voxels"])[:100]
    ph_c = _check_phantom(ph, packs, chk, tissue)
    tables, checks = [], []
    seqs = os.environ.get("BRAIN_SEQS", "se").split(",")          # the gradient echo's static dephasing at high field pushes
    z_bore = np.array([0.0, 0.0, 1.0])                             # the closed form's band (and memory) far beyond a spin echo's
    for ti, (kind, deg) in enumerate(TILTS):
        T = _tilt_matrix(kind, deg)
        b0_img = R.T @ (T.T @ z_bore); g_img = (dirs_s @ T) @ R                       # head tilted by T: field and gradients seen tilted back
        for B0 in B0_T:
            for seq_kind in seqs:
                G = np.tile(g_img, (len(SHELLS), 1)); bv = np.repeat(SHELLS, len(dirs_s))
                seq = (sequences.pgse(G, DELTA, DDELTA, bvalues=bv, TE=TE) if seq_kind == "se"
                       else sequences.gre(TE, gradient_directions=G, bvalues=bv, delta=DELTA, Delta=DDELTA))
                t1 = time.time()
                try:
                    P = packs["wm"].pose_response(seq, tissue=False, T2=tissue["T2_wm"], B0=B0, b0_dir=tuple(b0_img),
                                                  chi_iso=tissue["chi_iso"], chi_aniso=tissue["chi_aniso"], keep=(LMAX, 0))
                    C = np.asarray(P.coeffs)[:, rows].real.astype("<f2")              # (n_shell * n_dir, 45)
                except (MemoryError, ValueError) as e:
                    print(f"tilt {kind} {deg:+d} B0 {B0} {seq_kind}: refused ({str(e)[:120]})", flush=True)
                    C = np.full((len(SHELLS) * len(dirs_s), len(rows)), np.nan, "<f2"); P = None
                tables.append(C)
                if P is None:
                    continue
                if seq_kind == "se" and B0 == 3.0 and kind == "sagittal" and deg in (0, 20):
                    sub = list(range(0, len(SHELLS) * len(dirs_s), 7))
                    seq_c = (sequences.pgse(G[sub], DELTA, DDELTA, bvalues=bv[sub], TE=TE))
                    S = np.asarray(ph_c.replay(seq_c, B0_T=B0, b0_dir=tuple(b0_img), chi_iso=tissue["chi_iso"],
                                               chi_aniso=tissue["chi_aniso"]))[:, 0, 0, :]
                    checks.append(dict(tilt=ti, B0=B0, seq="se", meas=sub, S=np.round(S, 6).tolist(),
                                       note="the whole voxel through the phantom: the WM pack's field response, the GM pack at its zero field, CSF's closed form"))
                print(f"tilt {kind} {deg:+d} B0 {B0} {seq_kind}: {P.n_meas} measurements in {time.time() - t1:.0f}s "
                      f"(field lmax {P.field_lmax})  [{time.time() - t0:.0f}s]", flush=True)
    arr = np.stack(tables).reshape(len(TILTS), len(B0_T), len(seqs), len(SHELLS), len(dirs_s), -1).astype("<f2")
    with open(os.path.join(OUT, "field.bin"), "wb") as fh:
        fh.write(np.ascontiguousarray(arr).tobytes())
    index["field"] = dict(file="field.bin", dtype="f2", shape=list(arr.shape), axes=["tilt", "B0", "seq", "shell", "dir", "coeff"],
                          tilts=[dict(kind=k, deg=d, T=_tilt_matrix(k, d).tolist(), b0_image=(R.T @ (_tilt_matrix(k, d).T @ z_bore)).tolist()) for k, d in TILTS],
                          B0_T=B0_T, seqs=seqs, shells_smm2=[s / 1e6 for s in SHELLS], dirs_scanner=dirs_s.tolist(),
                          chi_iso=tissue["chi_iso"], chi_aniso=tissue["chi_aniso"],
                          note="WM coefficients per (tilt, B0, se|gre, shell, direction); the GM substrate declares no "
                               "susceptibility source, so its field is zero and its response its gradient-only one; CSF is a "
                               "closed form, full-tier with zeros (RPH.md 3.1)",
                          checks=checks)
    with open(os.path.join(OUT, "index.json"), "w") as fh:
        json.dump(index, fh)
    print(f"field.bin: {arr.nbytes / 1e6:.2f} MB  [{time.time() - t0:.0f}s]", flush=True)


def stage_checks():
    """Recompute the field-mode checks against the phantom route (the tables stay): what a changed tissue value
    needs."""
    from dmipy_sim import sequences
    t0 = time.time()
    ph, packs = _phantom_and_packs(); tissue = _tissue(packs)
    with open(os.path.join(OUT, "index.json")) as fh:
        index = json.load(fh)
    F = index["field"]; dirs_s = np.asarray(F["dirs_scanner"]); R = np.asarray(index["grid"]["R_image_to_scanner"])
    chk = np.asarray(index["check"]["voxels"])[:100]
    ph_c = _check_phantom(ph, packs, chk, tissue)
    checks = []
    for c in F["checks"]:
        t = F["tilts"][c["tilt"]]; T = np.asarray(t["T"]); b0_img = np.asarray(t["b0_image"]); g_img = (dirs_s @ T) @ R
        G = np.tile(g_img, (len(SHELLS), 1)); bv = np.repeat(SHELLS, len(dirs_s)); sub = c["meas"]
        seq_c = sequences.pgse(G[sub], DELTA, DDELTA, bvalues=bv[sub], TE=TE)
        S = np.asarray(ph_c.replay(seq_c, B0_T=c["B0"], b0_dir=tuple(b0_img), chi_iso=tissue["chi_iso"],
                                   chi_aniso=tissue["chi_aniso"]))[:, 0, 0, :]
        checks.append(dict(c, S=np.round(S, 6).tolist()))
        print(f"field check tilt {c['tilt']} B0 {c['B0']}: {len(sub)} measurements  [{time.time() - t0:.0f}s]", flush=True)
    index["field"]["checks"] = checks
    with open(os.path.join(OUT, "index.json"), "w") as fh:
        json.dump(index, fh)
    print(f"field checks rewritten  [{time.time() - t0:.0f}s]", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", choices=["voxels", "field", "checks"], default="voxels")
    a = ap.parse_args()
    {"voxels": stage_voxels, "field": stage_field, "checks": stage_checks}[a.stage]()
