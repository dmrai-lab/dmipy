# Contributing to dmipy

This is the **umbrella** repo: the thin `dmipy` meta-package (installs the two engines), the
[dmipy.org](https://dmipy.org) documentation site, and the licensing templates. The code that
does the physics lives in the engines — contribute there:

- **dmipy-sim** (forward Monte-Carlo): https://github.com/dmrai-lab/dmipy-sim
- **dmipy-fit** (analytical inverse): https://github.com/dmrai-lab/dmipy-fit

## What belongs here

- Packaging / dependency changes to the umbrella `pyproject.toml`.
- Documentation on [dmipy.org](https://dmipy.org):

  ```bash
  pip install ".[docs]"
  mkdocs serve
  ```

- Licensing (`licensing/`, `LICENSING.md`).

Keep the umbrella thin — no importable `dmipy` package; it only pins and installs the engines.

## Contributor License Agreement

dmipy is **dual-licensed** (AGPL-3.0 OR commercial), so we need an explicit relicensing grant
from contributors — see the [CLA](licensing/CLA.md). For now, add this line to your first
pull request:

> I have read the CLA and I agree to it on behalf of myself (and my employer if applicable).
> Signed, [your name] <[your email]>

You keep the copyright to your work. Please open an issue before starting anything large.
