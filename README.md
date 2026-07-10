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

> **Upgrading from dmipy 1.x?** dmipy 2.0 is a ground-up rewrite with a different
> architecture and API. The 1.x line (the original 2019 toolbox, Fick–Wassermann–Deriche)
> was a single importable `dmipy` package; **2.x is a meta-package with no importable
> `dmipy` module** — you import `dmipy_sim` / `dmipy_fit`. Old `import dmipy` code will not
> run under 2.x. To stay on the original toolbox, pin `pip install "dmipy<2"` (it remains
> available on PyPI).

## This repo

- `pyproject.toml` — the thin `dmipy` meta-package (installs the two engines).
- `docs/` + `mkdocs.yml` — the [dmipy.org](https://dmipy.org) site (MkDocs Material; built and
  deployed by `.github/workflows/docs.yml`).
- `papers/` — reproducible manuscripts (source + PDF + rerunnable figures); currently
  `papers/surface_relaxivity_bias/` — *"Surface relaxivity biases diffusion and relaxometry
  microstructure estimates."* See [`papers/README.md`](papers/README.md).

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
