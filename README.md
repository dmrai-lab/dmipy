# dmipy

**Diffusion Microstructure Imaging in Python** — the umbrella over the two engines, and the
home of the documentation at **[dmipy.org](https://dmipy.org)**.

- **[dmipy-sim](https://github.com/dmrai-lab/dmipy-sim)** — JAX Monte-Carlo forward simulator
  (arbitrary `G(t)`, restricted diffusion, surface relaxivity, permeability, T2).
- **[dmipy-fit](https://github.com/dmrai-lab/dmipy-fit)** — analytical multi-compartment
  fitting + JAX GPU (T2 + surface-relaxivity factors, CSD, NNLS myelin-water fraction).

One free-waveform substrate interface, `fit → sim`.

```bash
pip install dmipy            # dmipy-sim + dmipy-fit
pip install "dmipy[cuda12]"  # + JAX GPU
```

```python
import dmipy_sim, dmipy_fit   # no importable `dmipy`; import the engines directly
```

## This repo

- `pyproject.toml` — the thin `dmipy` meta-package (installs the two engines).
- `docs/` + `mkdocs.yml` — the [dmipy.org](https://dmipy.org) site (MkDocs Material; built and
  deployed by `.github/workflows/docs.yml`).
- (on release) `papers/surface_relaxivity_mwf/` — *"Surface relaxivity and bulk T2 are
  inseparable in multi-echo MRI"* (added when the preprint is posted).

Build the docs locally:

```bash
pip install ".[docs]"
mkdocs serve
```

## License

Dual-licensed: **GNU AGPL-3.0** for open-source use, or a **commercial license** for
proprietary/closed use — the same terms apply to both engines. See [LICENSE](LICENSE) and
[LICENSING.md](LICENSING.md) (commercial: rutger.fick@dmrai-lab.org).

The lab and its philosophy: **[dmrai-lab.org](https://dmrai-lab.org)**.
