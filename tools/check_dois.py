"""Verify every catalog DOI points to the *intended* paper — not just that it resolves.

A DOI can resolve (302) yet reference a completely different work (fabricated DOIs
often land on a real-but-wrong paper in the same journal/year).  So this checks two
things per model:
  1. the DOI is registered at doi.org, and
  2. the registered first-author surname matches the surname cited in the docstring.

Network, on-demand:  python tools/check_dois.py   (needs dmipy-fit importable)
Exits non-zero if any DOI is unregistered OR points to a mismatched author.
"""
import inspect, json, re, sys, urllib.request
from dmipy_fit.custom_optimizers import reference_models as rm

DOI = re.compile(r'(?:doi:|https?://doi\.org/)\s*(10\.\d{4,}/\S+)')
CITE = re.compile(r'\b(19|20)\d{2}\b')          # a year marks a citation line
UA = {'User-Agent': 'dmipy-doi-check/1.1 (mailto:rutger.fick@carcutter.com)'}


def cited_surname(doc, doi):
    """First-author surname the docstring intends for this DOI (line above the doi:)."""
    lines = doc.splitlines()
    for i, ln in enumerate(lines):
        if doi in ln:
            for j in (i, i - 1, i - 2):          # doi line, then the lines just above
                if 0 <= j < len(lines) and CITE.search(lines[j]) and 'doi' not in lines[j].lower():
                    m = re.match(r'\s*(?:[A-Za-z]+:\s*)?([A-Za-zÀ-ÿ]+)', lines[j])
                    if m:
                        return m.group(1)
    return None


def registered(doi):
    url = 'https://doi.org/' + doi.replace('(', '%28').replace(')', '%29')
    req = urllib.request.Request(url, headers={**UA, 'Accept': 'application/vnd.citationstyles.csl+json'})
    j = json.load(urllib.request.urlopen(req, timeout=25))
    fam = (j.get('author') or [{}])[0].get('family', '?')
    yr = j.get('issued', {}).get('date-parts', [['?']])[0][0]
    ti = (j.get('title') or ['?']); ti = ti[0] if isinstance(ti, list) else ti
    return fam, yr, (ti or '')[:52]


fns = [n for n in dir(rm) if not n.startswith('_') and callable(getattr(rm, n))
       and getattr(getattr(rm, n), '__module__', '') == rm.__name__]
bad = []
for n in sorted(fns):
    doc = inspect.getdoc(getattr(rm, n)) or ''
    m = DOI.search(doc)
    if not m:
        print(f'  --  {n}: no DOI (abstract?)'); continue
    doi = m.group(1).rstrip('.,);')
    want = cited_surname(doc, doi)
    try:
        fam, yr, ti = registered(doi)
    except Exception as e:
        print(f'  !!  {n}: UNRESOLVED {doi} -> {e}'); bad.append((n, doi, 'unresolved')); continue
    match = want is None or want.lower()[:5] in fam.lower() or fam.lower()[:5] in want.lower()
    flag = 'OK' if match else '!!'
    note = '' if match else f'  <-- cited "{want}" but DOI is "{fam}"'
    print(f'  {flag}  {n}: {fam} {yr} :: {ti}{note}')
    if not match:
        bad.append((n, doi, f'author mismatch: cited {want}, DOI {fam}'))

if bad:
    print(f'\n{len(bad)} DOI(s) FAILED (unresolved or wrong paper):')
    for n, doi, why in bad:
        print(f'   {n}: {doi} — {why}')
    sys.exit(1)
print('\nAll DOIs registered AND point to the cited author.')
