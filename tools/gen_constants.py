"""Generate docs/constants.md — the biophysical-constants table.

Single source of truth: introspects dmipy-sim's cited constant catalogue
(``dmipy_sim.substrate.biophysical_constants``, which dmipy-fit re-exports verbatim).
Every value links to its source paper via a clickable DOI.

Run: python tools/gen_constants.py   (needs dmipy-sim importable)
"""
from dmipy_sim.substrate import biophysical_constants as bc

CAT = bc.BIOPHYSICAL_CONSTANTS

# ordered (title, predicate) groups
GROUPS = [
    ('Diffusivities', lambda n: n.startswith('D_')),
    ('Relaxation times', lambda n: n.startswith(('T1_', 'T2_'))),
    ('Microstructure & geometry',
     lambda n: n.startswith(('axon_radius', 'g_ratio', 'gamma_shape', 'gamma_scale'))
     or n == 'myelin_water_fraction'),
    ('Membrane & surface', lambda n: n.startswith(('kappa', 'rho1', 'rho2'))),
    ('Susceptibility', lambda n: n.startswith('delta_chi')),
    ('Physical constants', lambda n: n == 'gamma_proton'),
]


def ref_link(cit):
    """`First-author Year` linking to the DOI (parens percent-encoded)."""
    if not cit:
        return '—'
    authors = cit.get('authors', '') or ''
    first = authors.split(',')[0].split()[0] if authors else '?'
    year = cit.get('year', '')
    label = f'{first} {year}'.strip()
    doi = cit.get('doi')
    if not doi:
        j = cit.get('journal', '')
        return f'{label}, {j}' if j else label
    url = 'https://doi.org/' + doi.replace('(', '%28').replace(')', '%29')
    return f'[{label}]({url})'


def value_str(default):
    v, u = default.get('value'), default.get('unit', '')
    if v is None:
        return '—'
    num = f'{v:.4g}' if isinstance(v, float) else str(v)
    return f'{num} {u}'.strip() if u and u != 'dimensionless' else num


out = [
    '# Biophysical constants', '',
    'Every physical constant in the substrate is defined once, with a cited source. '
    'The catalogue lives in `dmipy_sim.substrate.biophysical_constants` (the forward-truth '
    'engine owns the ground truth) and dmipy-fit re-exports it verbatim as '
    '`dmipy_fit.audit.biophysical_constants`, so there is exactly one value — and one '
    'reference — for each. Read them through the accessor, never hard-code:', '',
    '```python',
    'from dmipy_sim.substrate import biophysical_constants as bc',
    "bc.get_value('D_intra_axonal')      # 1.7e-9  (m^2/s)",
    "bc.get_constant('D_intra_axonal')   # full record: value, unit, citation, note",
    '```', '',
    'Every value below links to its source paper.', '',
]

seen = set()
for title, pred in GROUPS:
    names = [n for n in CAT if pred(n) and n not in seen]
    if not names:
        continue
    seen.update(names)
    out += ['', f'## {title}', '',
            '| Constant | Default | Description | Reference |',
            '| --- | --- | --- | --- |']
    for n in sorted(names):
        rec = CAT[n]
        desc = (rec.get('description', '') or '').replace('|', '\\|')
        out.append(f'| `{n}` | {value_str(rec.get("default", {}))} | {desc} '
                   f'| {ref_link(rec.get("citation"))} |')

# anything uncategorised (guard against drift)
rest = [n for n in CAT if n not in seen]
if rest:
    out += ['', '## Other', '',
            '| Constant | Default | Description | Reference |',
            '| --- | --- | --- | --- |']
    for n in sorted(rest):
        rec = CAT[n]
        desc = (rec.get('description', '') or '').replace('|', '\\|')
        out.append(f'| `{n}` | {value_str(rec.get("default", {}))} | {desc} '
                   f'| {ref_link(rec.get("citation"))} |')

open('docs/constants.md', 'w').write('\n'.join(out) + '\n')
print(f'wrote docs/constants.md — {len(CAT)} constants, {len(rest)} uncategorised')
