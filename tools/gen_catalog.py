"""Generate docs/catalog.md from dmipy_fit's reference-model factories (single source
of truth). Run: python tools/gen_catalog.py  (needs dmipy-fit importable)."""
import inspect, re, textwrap
from dmipy_fit.custom_optimizers import reference_models as rm

FAMILIES = {
    'A': 'Gaussian / tensor', 'B': 'Two-compartment white matter',
    'C': 'Orientation-dispersion', 'D': 'Multi-fascicle', 'E': 'Cylinder / axon diameter',
    'F': 'Soma / sphere', 'G': 'Membrane exchange', 'H': 'Time-dependent',
    'I': 'Relaxometry (multi-TE)',
}

# parse the module header table:  "C1  noddi()  9  ODF dispersion  Zhang et al. 2012, ..."
hdr = inspect.getdoc(rm) or ""
rows = {}
for line in hdr.splitlines():
    m = re.match(r'^([A-I]\d+)\s+(\w+)\(\)\s+\d+\s+(.+?)\s{2,}(.+)$', line.strip())
    if m:
        code, name, cat, cite = m.groups()
        rows[name] = (code, cat.strip(), cite.strip())

def body(fn):
    src = inspect.getsource(fn)
    src = re.sub(r'^\s*def [^\n]*\n', '', src, count=1)          # drop def line
    src = re.sub(r'^\s*(?:"""|\'\'\').*?(?:"""|\'\'\')\s*\n', '', src, count=1, flags=re.S)
    return textwrap.dedent(src).strip()

def desc(fn):
    d = inspect.getdoc(fn) or ""
    return d.splitlines()[0] if d else ""

def cite_link(fn, cite):
    """Clickable citation: link the short reference to its DOI (from the docstring)."""
    d = inspect.getdoc(fn) or ""
    m = re.search(r'(?:doi:|https?://doi\.org/)\s*(10\.\S+)', d)
    doi = m.group(1).rstrip('.,);') if m else None
    if not doi:
        return cite
    url = 'https://doi.org/' + doi.replace('(', '%28').replace(')', '%29')  # keep md link intact
    return f'[{cite}]({url})'

funcs = [(n, getattr(rm, n)) for n in dir(rm)
         if not n.startswith('_') and callable(getattr(rm, n))
         and getattr(getattr(rm, n), '__module__', '') == rm.__name__ and n in rows]
funcs.sort(key=lambda t: (rows[t[0]][0][0], int(rows[t[0]][0][1:])))   # by code

out = ['# Model catalog', '',
       'The framework has one model of its own — the **unified white-matter model** below — '
       'and reproduces the published literature as thin factories around the *same* shared '
       'primitives. Every entry is an ordinary `MultiCompartmentModel`: forward-simulate with '
       '`model(scheme, **params)`, fit with one `model.fit(scheme, data)` call.', '',
       '## The unified white-matter model',
       '',
       "*The framework's own model — the analytical inverse of the dmipy-sim Monte-Carlo "
       'forward truth.*', '',
       'It is **not** a bespoke class: the canonical white-matter substrate is an ordinary '
       '`MultiCompartmentModel` built from the same primitives as everything below — `C1Stick` '
       '(intra-axonal), `G2Zeppelin` (extra-axonal) and `S1Dot` (stuck myelin), each wrapped in '
       'an `OccupancyGatedModel` that carries the opt-in occupancy-gated factors: transverse '
       'relaxation (`T2`) and intra-pore + exterior **surface relaxivity**. A single Gamma '
       'outer-diameter distribution drives both surface factors, and the whole thing '
       'forward-simulates and fits through the standard machinery, exactly like NODDI. '
       'Diffusion-only — no susceptibility, gradient-/stimulated-echo, or T1 physics.', '',
       '```python',
       'from dmipy_fit.white_matter import build_white_matter_model',
       '',
       'model, params = build_white_matter_model()      # canonical healthy WM @ 3 T',
       'signal = model(scheme, **params)                # forward-simulate',
       'fit    = model.fit(scheme, data, solver="jax")  # fit to data',
       '```', '',
       '---', '',
       '## Literature models',
       '',
       'Each factory below lives in `dmipy_fit.custom_optimizers.reference_models` and returns a '
       'configured `MultiCompartmentModel` (or spherical-mean model) in a few lines.', '',
       '```python',
       'from dmipy_fit.custom_optimizers import reference_models as models',
       'mcm = models.noddi()          # any factory below',
       'fit = mcm.fit(scheme, data, solver="jax")',
       '```', '']
cur = None
for name, fn in funcs:
    code, cat, cite = rows[name]
    fam = code[0]
    if fam != cur:
        cur = fam
        out += ['', f'### {FAMILIES.get(fam, fam)}', '']
    out += [f'#### `{name}()` <small>{code}</small>', '',
            f'{desc(fn)}', '',
            f'*{cite_link(fn, cite)}*', '',
            '```python', body(fn), '```', '']
open('docs/catalog.md', 'w').write('\n'.join(out) + '\n')
print(f'wrote docs/catalog.md — {len(funcs)} models')
