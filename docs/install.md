# Install

`dmipy` is a thin umbrella that pulls the packages of the ecosystem:

```bash
pip install dmipy                 # dmipy-sim + dmipy-replay + dmipy-fit + dmipy-design
pip install "dmipy[tract]"        # + dmipy-tract, tractography on FOD fields
pip install "dmipy[cuda12]"       # + JAX CUDA-12 GPU (JAX, jaxopt)
pip install "dmipy[cpu]"          # + JAX CPU
```

!!! note "GPU (`[cuda12]`)"
    Needs a working CUDA-12 stack, and the environment must export `LD_LIBRARY_PATH` so the
    dynamic loader resolves the CUDA libraries — see the
    [dmipy-sim README](https://github.com/dmrai-lab/dmipy-sim#gpu) for the exact export.

!!! tip "CPU-only / shared machine"
    Set `JAX_PLATFORMS=cpu` to force JAX onto CPU regardless of what is installed.

There is no importable `dmipy` package — import the packages directly:

```python
import dmipy_sim          # forward Monte Carlo: walks the substrates, produces the replay packs
import dmipy_replay       # the replay packs as a signal or an image; the acquisition object
import dmipy_fit          # analytical inverse
import dmipy_design       # sequence design
```

!!! warning "Upgrading from dmipy 1.x"
    dmipy 2.0 is a ground-up rewrite. The 1.x line (the original 2019 toolbox) was a single
    importable `dmipy` package; **2.x is a meta-package with no importable `dmipy` module**.
    Old `import dmipy` code will not run under 2.x. To stay on the original toolbox, pin
    `pip install "dmipy<2"` — it remains available on PyPI.

Or install a package on its own:

```bash
pip install dmipy-sim
pip install dmipy-replay
pip install "dmipy-fit[jax]"
pip install dmipy-design
pip install dmipy-tract
```
