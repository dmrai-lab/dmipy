"""Generate docs/catalog.md from dmipy_fit's reference-model factories (single source
of truth). Run: python tools/gen_catalog.py  (needs dmipy-fit importable)."""
import inspect, re, textwrap, ast
from dmipy_fit.custom_optimizers import reference_models as rm
from dmipy_fit.white_matter import composition as wm

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
    """Source of a factory's body — everything after the (possibly multi-line) def
    signature and the docstring. AST-based so multi-line signatures strip cleanly."""
    src = textwrap.dedent(inspect.getsource(fn))
    lines = src.splitlines()
    stmts = ast.parse(src).body[0].body
    # skip a leading string-literal docstring
    start = 1 if (stmts and isinstance(stmts[0], ast.Expr)
                  and isinstance(getattr(stmts[0], 'value', None), ast.Constant)
                  and isinstance(stmts[0].value.value, str)) else 0
    first = stmts[start] if start < len(stmts) else stmts[0]
    return textwrap.dedent('\n'.join(lines[first.lineno - 1:])).strip()

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
       'Each compartment is a diffusion primitive wrapped in an `OccupancyGatedModel` '
       'carrying the occupancy-gated factors (surface relaxivity + `T2`) — one Gamma '
       'outer-diameter distribution drives both surface factors:', '',
       '```python',
       'from dmipy_fit.signal_models.cylinder_models import C1Stick',
       'from dmipy_fit.signal_models.gaussian_models import G2Zeppelin',
       'from dmipy_fit.signal_models.sphere_models import S1Dot',
       'from dmipy_fit.signal_models.attenuation import (',
       '    OccupancyGatedModel, TransverseRelaxation,',
       '    IntraPoreSurfaceRelaxivity, ExteriorSurfaceRelaxivity)',
       'from dmipy_fit.white_matter.surface import exterior_surface_to_volume',
       '',
       body(wm.white_matter_compartments),
       '```', '',
       'then assembled into a standard `MultiCompartmentModel` with one shared fibre '
       'orientation — no bespoke class:', '',
       '```python',
       'from dmipy_fit.core.modeling_framework import MultiCompartmentModel',
       '',
       body(wm.build_white_matter_model),
       '```', '',
       'That composition is packaged with canonical healthy-WM-at-3 T defaults as one '
       'call — `model, params = build_white_matter_model()` — then '
       '`model(scheme, **params)` forward-simulates and `model.fit(scheme, data, '
       'solver="jax")` fits, exactly like the literature models below.', '',
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
