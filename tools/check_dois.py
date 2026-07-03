"""Verify every catalog DOI is registered at doi.org (302 redirect), not a wrong reference.
Network, on-demand: python tools/check_dois.py  (needs dmipy-fit importable)."""
import inspect, re, sys, urllib.request
from dmipy_fit.custom_optimizers import reference_models as rm

DOI = re.compile(r'(?:doi:|https?://doi\.org/)\s*(10\.\d{4,}/\S+)')
fns = [n for n in dir(rm) if not n.startswith('_') and callable(getattr(rm, n))
       and getattr(getattr(rm, n), '__module__', '') == rm.__name__]
bad = []
for n in sorted(fns):
    m = DOI.search(inspect.getdoc(getattr(rm, n)) or '')
    if not m:
        print(f'  --  {n}: no DOI (abstract?)'); continue
    doi = m.group(1).rstrip('.,);')
    url = 'https://doi.org/' + doi.replace('(', '%28').replace(')', '%29')
    req = urllib.request.Request(url, method='HEAD')
    try:
        # do NOT follow: doi.org returns 3xx for a registered DOI, 404 for unknown
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        op = urllib.request.build_opener(NoRedirect)
        code = op.open(req, timeout=15).status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = f'ERR {e}'
    ok = isinstance(code, int) and 300 <= code < 400
    print(f'  {"OK" if ok else "!!"}  {n}: doi.org -> {code}  ({doi})')
    if not ok:
        bad.append((n, doi, code))
if bad:
    print(f'\n{len(bad)} DOI(s) did NOT resolve:', bad); sys.exit(1)
print('\nAll DOIs registered at doi.org.')
