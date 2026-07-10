#!/usr/bin/env python
"""gather_real_substrates.py -- download every manually-segmented cross-section in
the public AxonDeepSeg SEM dataset (rat spinal cord; Zaimi 2018 / BIDS
data_axondeepseg_sem), fit myelinated cylinders to each (real positions, per-axon
inner diameter and g-ratio), and tabulate the surface-to-volume ratio S/V each
yields. Many cross-sections from several animals -> shows the real-WM S/V range and
that the single crop used in Fig 1 was not cherry-picked.

Masks are cached under figures/_real_xsec/ so the figure regenerates offline.
"""
import os, json, io, urllib.request
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '_real_xsec')
RAW = 'https://raw.githubusercontent.com/axondeepseg/data_axondeepseg_sem/master'
os.makedirs(CACHE, exist_ok=True)


def _fetch(url, binary=True):
    cache = os.path.join(CACHE, url.split('/master/')[-1].replace('/', '__'))
    if not os.path.exists(cache):
        data = urllib.request.urlopen(url, timeout=40).read()
        open(cache, 'wb').write(data)
    raw = open(cache, 'rb').read()
    return raw if binary else raw.decode('utf-8', 'replace')


def _samples():
    tsv = _fetch(RAW + '/samples.tsv', binary=False)
    rows = [l.split('\t') for l in tsv.strip().splitlines()[1:]]
    return [(r[1], r[0]) for r in rows]            # (sub, sample-id)


def _pixel_size(sub, sample):
    for cand in (f'{sub}/micr/{sub}_{sample}_SEM.json', f'{sub}/micr/{sub}_SEM.json'):
        try:
            j = json.loads(_fetch(RAW + '/' + cand, binary=False))
            ps = j['PixelSize']
            return float(ps[0] if isinstance(ps, (list, tuple)) else ps) * 1e-6
        except Exception:
            continue
    return None


def load_segmentation(sub, sample):
    """Return (seg in 255/127/0 convention, pixel_size_m) or (None, None)."""
    base = f'{sub}/micr/derivatives'  # not used; labels live under derivatives/labels
    axp = f'derivatives/labels/{sub}/micr/{sub}_{sample}_SEM_seg-axon-manual.png'
    myp = f'derivatives/labels/{sub}/micr/{sub}_{sample}_SEM_seg-myelin-manual.png'
    try:
        ax = np.array(Image.open(io.BytesIO(_fetch(RAW + '/' + axp))))
        my = np.array(Image.open(io.BytesIO(_fetch(RAW + '/' + myp))))
    except Exception as e:
        print(f'  [skip {sub}/{sample}] {e}')
        return None, None
    ax = ax[..., 0] if ax.ndim == 3 else ax
    my = my[..., 0] if my.ndim == 3 else my
    seg = np.zeros(ax.shape, np.uint8)
    seg[my > 0] = 127
    seg[ax > 0] = 255
    return seg, _pixel_size(sub, sample)


def main():
    from real_substrate import substrate_summary
    import sys
    sys.path.insert(0, HERE)
    rows = []
    for sub, sample in _samples():
        seg, px = load_segmentation(sub, sample)
        if seg is None or px is None:
            continue
        try:
            _, _, _, s = substrate_summary(seg, px)
        except Exception as e:
            print(f'  [fit-fail {sub}/{sample}] {e}'); continue
        s['sub'] = sub; s['sample'] = sample; s['px_um'] = px * 1e6
        rows.append(s)
        print(f"{sub:9s} {sample:22s} px={px*1e6:.3f}um n={s['n']:4d} "
              f"mean_d={s['mean_d_um']:.2f}um g={s['g']:.2f} f={s['f_fibre']:.2f} "
              f"S/V_in={s['sv_in_um']:.2f}  S/V_ext={s['sv_ext_mask_um']:.2f}/um")
    svs = np.array([r['sv_in_um'] for r in rows])
    print(f"\n{len(rows)} cross-sections | interior S/V range {svs.min():.2f}-{svs.max():.2f}/um "
          f"(median {np.median(svs):.2f})")
    np.savez(os.path.join(HERE, 'real_substrates_data.npz'),
             **{k: np.array([r[k] for r in rows]) for k in
                ('mean_d_um', 'g', 'f_fibre', 'sv_in_um', 'sv_ext_mask_um', 'n', 'px_um')},
             sub=np.array([r['sub'] for r in rows]),
             sample=np.array([r['sample'] for r in rows]))


if __name__ == '__main__':
    main()
