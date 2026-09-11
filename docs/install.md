# Install

```bash
pip install dmipy                 # dmipy-design + dmipy-sim + dmipy-fit
pip install "dmipy[cuda12]"       # + JAX on a CUDA-12 GPU
pip install "dmipy[cpu]"          # + JAX on the CPU
```

There is no importable `dmipy` package; import the engines:

```python
import dmipy_design               # sequence design
import dmipy_sim                  # forward Monte Carlo
import dmipy_fit                  # analytical inverse
```

!!! note "GPU"
    The walk and the fits run on the GPU when JAX finds one. With `[cuda12]` the environment
    must export `LD_LIBRARY_PATH` so the loader finds the CUDA libraries; the
    [dmipy-sim README](https://github.com/dmrai-lab/dmipy-sim#gpu) has the exact line. Set
    `JAX_PLATFORMS=cpu` to force the CPU, for example in CI. Every example on this site runs on
    the CPU.

!!! warning "Coming from dmipy 1.x"
    The 2019 toolbox was a single importable `dmipy` package. It stays on PyPI:
    `pip install "dmipy<2"`. Everything else is in [Migrating](migrating.md).

Install one engine alone with `pip install dmipy-sim`, `pip install "dmipy-fit[jax]"` or
`pip install dmipy-design`; dmipy-fit and dmipy-design depend on dmipy-sim.
