# dmipy — umbrella + docs (dmipy.org)

This repo is the **dmipy** brand umbrella: a thin meta-package (`pip install dmipy` → the two
engines) and the source of the documentation site at dmipy.org. It holds **no engine code** —
the engines are the sibling repos.

## Layout
- `pyproject.toml` — `dmipy` meta-package: deps = `dmipy-sim` + `dmipy-fit` (pinned git tags);
  `[docs]`/`[cuda12]`/`[cpu]` extras. No importable `dmipy` package.
- `mkdocs.yml`, `docs/` — MkDocs Material site → dmipy.org. API pages use `mkdocstrings` to
  autodoc the *installed* `dmipy_sim` / `dmipy_fit`, so the reference is sourced from the real
  engine docstrings (can't drift).
- `.github/workflows/docs.yml` — build + deploy to GitHub Pages (CNAME → dmipy.org).
- `papers/` — reproducible manuscripts (PDF + LaTeX + rerunnable figures); index at
  `papers/README.md`. Currently `papers/surface_relaxivity_bias/` (canonical working copy
  kept privately).

## Relationships (don't conflate)
- **dmipy** (this repo) = the public computational-engine brand + docs + paper.
- **dmipy-sim / dmipy-fit** = the engines (source of truth for the API docs).
- **dmrai-lab** = the organisation (dmrai-lab.org); the `dmrai` provenance/record/agent layer
  is private. dmipy.org is the tool; dmrai-lab.org is the lab.

## Editing docs
Prose-first. Keep engine READMEs compact and let dmipy.org carry the tutorials + API. Do not
duplicate the dmrai-lab.org manifesto here — echo one line and link back.
