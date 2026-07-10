#!/usr/bin/env python
"""real_substrate.py -- represent a real axon+myelin EM segmentation as a pack of
fitted MYELINATED CYLINDERS (per-axon inner radius from the axon lumen, outer radius
from the watershed-assigned myelin ring -> per-axon g-ratio), at the axons' true
centroids.

Why fit cylinders rather than walk the raw label map: the irregular-segmentation
(SDF) walk does not confine the extra-axonal walkers (a separate engine limitation),
whereas the exact-circle reflection of PackedCylinders is validated and confines
correctly. Fitting myelinated cylinders preserves the quantity the surface/diffusion
physics depends on -- the per-axon inner diameter and g-ratio (hence S/V) at the real
positions and packing -- while using the trusted engine. The fitted cross-section is
shown next to the raw segmentation (Fig 1) for transparency.

Convention (AxonDeepSeg): axon lumen = 255, myelin = 127, extra = 0.
"""
import numpy as np
from scipy import ndimage


def extract_myelinated_cylinders(seg, pixel_size_m, axon_label=255,
                                 myelin_label=127, min_axon_px=8):
    """Return (centers_xy (N,2) m, r_inner (N,) m, r_outer (N,) m) for each axon.

    Inner radius = area-equivalent radius of the axon lumen. Outer radius =
    area-equivalent radius of (axon + its watershed-assigned myelin ring), so the
    myelin (a connected network) is partitioned to the nearest axon, giving a
    per-axon g-ratio.
    """
    seg = seg[..., 0] if seg.ndim == 3 else seg
    axon = seg == axon_label
    myelin = seg == myelin_label
    lab_ax, n = ndimage.label(axon)
    # nearest-axon label for every pixel (EDT watershed of the axon markers)
    _, (iy, ix) = ndimage.distance_transform_edt(lab_ax == 0, return_indices=True)
    nearest = lab_ax[iy, ix]
    cx, cy, ri, ro = [], [], [], []
    for i in range(1, n + 1):
        am = lab_ax == i
        a_ax = int(am.sum())
        if a_ax < min_axon_px:
            continue
        a_my = int(((nearest == i) & myelin).sum())
        yc, xc = ndimage.center_of_mass(am)
        cx.append(xc * pixel_size_m); cy.append(yc * pixel_size_m)
        ri.append(np.sqrt(a_ax / np.pi) * pixel_size_m)
        ro.append(np.sqrt((a_ax + a_my) / np.pi) * pixel_size_m)
    centers = np.column_stack([cx, cy])
    return centers, np.asarray(ri), np.asarray(ro)


def substrate_summary(seg, pixel_size_m, **kw):
    """(centers, r_in, r_out, stats) for a crop. The headline geometric quantity is
    the INTERIOR area/spin-weighted moment sv_in = <4/d>_V over the axon inner
    diameters -- robust to packing (no circle-overlap artefact), and the quantity
    that sets the intra-axonal surface relaxivity. Also reports the mask-based
    exterior S/V (true fibre/extra perimeter over extra area)."""
    centers, ri, ro = extract_myelinated_cylinders(seg, pixel_size_m, **kw)
    seg2 = seg[..., 0] if seg.ndim == 3 else seg
    L = seg2.shape[0] * pixel_size_m
    d = 2 * ri
    sv_in = float(np.sum(4.0 * d) / np.sum(d ** 2))           # <4/d>_V (area-weighted)
    # mask-based exterior S/V (robust; no fitted-circle overlap)
    fibre = (seg2 == 255) | (seg2 == 127)
    edge = (fibre[1:] != fibre[:-1]).sum() + (fibre[:, 1:] != fibre[:, :-1]).sum()
    extra_area = float((~fibre).sum()) * pixel_size_m ** 2
    sv_ext_mask = (edge * pixel_size_m) / extra_area if extra_area > 0 else np.nan
    f_fibre = float(fibre.sum()) / fibre.size
    stats = dict(n=len(ri), mean_d_um=float(d.mean() * 1e6),
                 g=float(np.mean(ri / ro)), f_fibre=f_fibre,
                 sv_in_um=sv_in / 1e6, sv_ext_mask_um=sv_ext_mask / 1e6, L_um=L * 1e6)
    return centers, ri, ro, stats


def packed_outer(centers, r_outer, L):
    """PackedCylinders of the OUTER (myelin) circles -- the obstacles that hinder
    extra-axonal water; walkers diffuse outside them (extra-axonal D(t))."""
    from dmipy_sim.geometries import PackedCylinders
    return PackedCylinders(radii=np.asarray(r_outer), centers=np.asarray(centers), L=L)


if __name__ == '__main__':
    import os
    from PIL import Image
    HERE = os.path.dirname(os.path.abspath(__file__))
    seg = np.array(Image.open(os.path.join(HERE, 'rat_sem_crop.png')))
    _, _, _, s = substrate_summary(seg, 0.13e-6)
    print(s)
