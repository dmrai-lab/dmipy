"""Generate docs/substrate.md — the substrate/geometry parity page.

Single source of truth: introspects dmipy-sim's Geometry classes and the shared
``Substrate`` + ``biophysical_constants`` catalogue. The parity example is exec'd at
build time so it is guaranteed to run against the real API.

Run: python tools/gen_substrate.py   (needs dmipy-sim + dmipy-fit importable)
"""
import inspect
import dmipy_sim

# --- parity example, shown verbatim and exec'd to prove it runs ---------------------
SUBSTRATE_SNIPPET = '''\
import dmipy_sim
from dmipy_sim.substrate import Substrate
from dmipy_fit.white_matter import build_white_matter_model
from dmipy_fit.audit import biophysical_constants as fit_consts
from dmipy_sim.substrate import biophysical_constants as sim_consts

# --- describe the microstructure ONCE (dmipy-sim owns the physical ground truth) ---
sub = Substrate()          # canonical healthy white matter; override any field
# derived quantities the analytical model needs are computed here, once:
#   sub.f_intra, sub.f_extra, sub.lambda_perp_extra (tortuosity), sub.mean_inner_radius, ...

# forward truth (dmipy-sim): an explicit geometry the walkers diffuse in,
# its inner/outer radii and diffusivities taken from the substrate
geom = dmipy_sim.MyelinatedCylinder(
    inner_radius=sub.mean_inner_radius, outer_radius=sub.mean_outer_radius,
    orientation=(0, 0, 1), D_intra=sub.D_intra, D_extra=sub.D_extra,
    D_myelin_radial=sub.D_myelin_radial, D_myelin_tangential=sub.D_myelin_tangential)

# analytical inverse (dmipy-fit): the SAME physical numbers parametrize the model
model, params = build_white_matter_model(
    gamma_shape=sub.gamma_shape_diameter,
    gamma_scale_outer_diameter=sub.gamma_scale_diameter,
    g_ratio=sub.g_ratio, f_axon=sub.f_axon, D_intra=sub.D_intra)

# every physical CONSTANT is defined once: fit re-exports the sim catalogue
assert fit_consts.get_value is sim_consts.get_value
'''

_ns = {}
exec(SUBSTRATE_SNIPPET, _ns)
assert len(_ns['model'].models) == 3, 'substrate parity example changed'

# --- the public geometry set (walkers diffuse in these) -----------------------------
_GEOMS = ['FreeDiffusion', 'Sphere', 'Cylinder', 'MyelinatedCylinder', 'Ellipsoid',
          'Box1D', 'PermeableSlab1D', 'PackedSpheres', 'PackedCylinders',
          'PackedMyelinatedCylinders']
_GEOMS = [g for g in _GEOMS if hasattr(dmipy_sim, g)]


def _sig(cls):
    s = inspect.signature(cls.__init__)
    params = [str(p) for n, p in s.parameters.items() if n != 'self']
    return f'{cls.__name__}(' + ', '.join(params) + ')'


def _first(cls):
    d = (inspect.getdoc(cls) or '').splitlines()
    return d[0] if d else ''


out = [
    '# Substrate & geometry', '',
    'The microstructural substrate is owned by **dmipy-sim** in two linked forms: explicit '
    '`Geometry` objects that the Monte-Carlo walkers diffuse inside, and the physical-'
    'parameter `Substrate` (plus the cited `biophysical_constants` catalogue). The same '
    'physical description feeds both engines — dmipy-sim walks an explicit geometry, '
    "dmipy-fit's analytical model takes the same parameters — and every physical constant "
    'is defined exactly once. **You describe the tissue once.**', '',
    '## One substrate, both engines', '',
    'A `Substrate` is the physical ground truth. Its derived accessors (volume fractions, '
    'tortuosity, mean radii, surface-relaxation rates) are the numbers the analytical model '
    'needs, computed in one place:', '',
    '```python', SUBSTRATE_SNIPPET.rstrip(), '```', '',
    'The geometry and the model are parametrised from the *same* `Substrate` fields, and '
    'the tissue constants come from a single catalogue: '
    '`dmipy_fit.audit.biophysical_constants` re-exports '
    '`dmipy_sim.substrate.biophysical_constants` verbatim, so there is exactly one '
    'definition (with citation provenance) of every physical constant. Derived geometric '
    'quantities — the exterior surface-to-volume ratio, the intra-pore ⟨4/d⟩ average, the '
    'tortuosity `lambda_perp_extra` — use the same closed forms on both sides.', '',
    '!!! note "Input parity, not output agreement"',
    '    One substrate feeding both engines lets you check the analytical model against the '
    'Monte-Carlo ground truth on matched tissue. Agreement is necessary evidence, not proof '
    '— the two engines are correlated and can be wrong the same way.', '',
    '## Geometries', '',
    'The forward substrate: closed pores, packed ensembles, and free diffusion the walkers '
    'sample. Each is a `dmipy_sim` `Geometry` accepted by `dmipy_sim.simulate(n_walkers, D, '
    'waveform, geometry)`.', '',
]
for g in _GEOMS:
    cls = getattr(dmipy_sim, g)
    out += [f'### `{g}`', '', _first(cls), '',
            '```python', _sig(cls), '```', '']

out += [
    '## Substrate parameters', '',
    'A `dmipy_sim.substrate.Substrate` carries the canonical white-matter physics — volume '
    'fractions (`f_axon`, `f_csf`), the axon-diameter Gamma law (`gamma_shape_diameter`, '
    '`gamma_scale_diameter`), `g_ratio`, the intrinsic diffusivities (`D_intra`, `D_extra`, '
    '`D_myelin_*`, `D_csf`), transverse relaxation (`T2_*`) and the transverse surface '
    'relaxivity `rho2` — and derives the model-facing quantities from them:', '',
    '| accessor | meaning |',
    '| --- | --- |',
    '| `f_intra`, `f_extra`, `f_myelin` | compartment volume fractions from `f_axon`, `g_ratio` |',
    '| `mean_inner_radius`, `mean_outer_radius` | Gamma-law radii (inner = `g_ratio`·outer) |',
    '| `lambda_perp_extra` | extra-axonal tortuosity (perpendicular diffusivity) |',
    '| `intra_surface_rate`, `extra_surface_rate` | surface-relaxation rates from `rho2` and S/V |',
    '',
    'Override any field (`Substrate(f_axon=0.6, g_ratio=0.65)`) to describe a different '
    'tissue; both the geometry you build and the model parameters follow.', '',
]

open('docs/substrate.md', 'w').write('\n'.join(out) + '\n')
print(f'wrote docs/substrate.md — {len(_GEOMS)} geometries: {", ".join(_GEOMS)}')
