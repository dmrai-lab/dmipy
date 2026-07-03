"""Generate docs/sequences.md — the acquisition-sequence parity page.

Single source of truth: introspects the ``from_*`` constructors that dmipy-sim's
``Sequence`` and dmipy-fit's ``AcquisitionScheme`` share, so the page lists exactly the
constructors that round-trip through *both* engines.  The parity example is exec'd at
build time so it is guaranteed to run against the real API.

Run: python tools/gen_sequences.py   (needs dmipy-sim + dmipy-fit importable)
"""
import inspect
from dmipy_sim.sequences import Sequence
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme

# --- the parity example, shown verbatim and exec'd to prove it runs -----------------
PARITY_SNIPPET = '''\
import numpy as np
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.custom_optimizers import reference_models as models
import dmipy_sim

# --- specify the acquisition ONCE (physical PGSE parameters) ---
bvals = np.array([0.0, 1e9, 2e9])          # s/m^2
dirs  = np.tile([1.0, 0.0, 0.0], (3, 1))   # gradient directions
delta, Delta = 0.01, 0.03                  # pulse duration / separation (s)

# one constructor, one object -- accepted by both engines
scheme = AcquisitionScheme.from_pgse(bvals, dirs, delta, Delta)

# analytical inverse (dmipy-fit): forward-simulate / fit the scheme directly
E_analytic = models.ball_and_stick()(scheme, **{
    'C1Stick_1_mu': [0.0, 0.0], 'C1Stick_1_lambda_par': 1.7e-9,
    'G1Ball_1_lambda_iso': 3e-9, 'partial_volume_0': 0.6, 'partial_volume_1': 0.4})

# forward truth (dmipy-sim): the SAME scheme drives the Monte-Carlo walk
E_mc = dmipy_sim.simulate(20_000, 1.7e-9, scheme.waveform, dmipy_sim.FreeDiffusion())
'''

SIM_NATIVE_SNIPPET = '''\
from dmipy_sim.sequences import Sequence

# identical signature on the sim side -- the fit scheme just wraps this
seq = Sequence.from_pgse(bvals, dirs, delta, Delta)
seq.bvalues            # == scheme.bvalues, exactly
'''

# fail generation if the shown example no longer runs against the real API
_ns = {}
exec(PARITY_SNIPPET, _ns)
assert _ns['scheme'].number_of_measurements == 3, 'parity example changed shape'

# --- the parity constructor set: from_* present on BOTH classes ---------------------
_ORDER = ['from_pgse', 'from_ogse', 'from_cpmg', 'from_btensor_ste',
          'from_btensor_pte', 'from_btensor_waveform', 'from_waveform']
sim_from = {n for n in dir(Sequence) if n.startswith('from_')}
fit_from = {n for n in dir(AcquisitionScheme) if n.startswith('from_')}
parity = [n for n in _ORDER if n in sim_from and n in fit_from and n != 'from_pulseq']
parity += [n for n in sorted(sim_from & fit_from) if n not in parity and n != 'from_pulseq']

out = [
    '# Acquisition sequences', '',
    'The physical sequence is owned by **dmipy-sim**, and the free gradient waveform '
    '`G(t)` is the base representation — `PGSE`, `OGSE`, `CPMG` and the b-tensor '
    'encodings are *factory constructors*, not separate types. The same constructor, '
    'called with the same physical parameters, builds the object in either engine, and a '
    'single object drives both the analytical inverse (dmipy-fit) and the Monte-Carlo '
    'forward truth (dmipy-sim). **You specify the acquisition once.**', '',
    '## One acquisition, both engines', '',
    'Build the scheme from PGSE parameters, then hand the *same* object to the analytical '
    'model and to the Monte-Carlo simulator:', '',
    '```python', PARITY_SNIPPET.rstrip(), '```', '',
    'The b-values the analytical model sees are the ones dmipy-sim integrated from `G(t)` '
    '— the scheme carries the waveform, and `scheme.waveform` is what `dmipy_sim.simulate` '
    'consumes. Starting from the sim side gives the identical object:', '',
    '```python', SIM_NATIVE_SNIPPET.rstrip(), '```', '',
    'This is by construction, not coincidence: `AcquisitionScheme.from_X` delegates to '
    '`dmipy_sim.sequences.Sequence.from_X` with the **identical signature** — dmipy-sim '
    'owns the physical sequence, and the fit scheme only adds the analytical shell / '
    'spherical-harmonics layer on top. So the parameters you pass are the same whichever '
    'engine you start from.', '',
    '!!! note "Input parity, not output agreement"',
    '    Feeding one acquisition to both engines lets you cross-check the analytical model '
    'against the Monte-Carlo ground truth on a matched substrate. Agreement is necessary '
    'evidence, not proof — the two engines are correlated and can be wrong the same way.', '',
    '## Constructors', '',
    'Each constructor below exists with the identical signature on both '
    '`dmipy_sim.sequences.Sequence` and `dmipy_fit.core.acquisition_scheme.AcquisitionScheme`. '
    '(The fit side adds `min_b_shell_distance` / `b0_threshold` for analytical shell '
    'clustering; the physical parameters are the same.)', '',
]
for n in parity:
    fn = getattr(Sequence, n)
    first = (inspect.getdoc(fn) or '').splitlines()
    first = first[0] if first else ''
    sig = str(inspect.signature(fn))
    out += [f'### `{n}()`', '', first, '',
            '```python', f'{n}{sig}', '```', '']

open('docs/sequences.md', 'w').write('\n'.join(out) + '\n')
print(f'wrote docs/sequences.md — {len(parity)} parity constructors: {", ".join(parity)}')
