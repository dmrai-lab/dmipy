# Install

`dmipy` is a thin umbrella that pulls both engines:

```bash
pip install dmipy                 # dmipy-sim + dmipy-fit
pip install "dmipy[cuda12]"       # + JAX CUDA-12 GPU (JAX, jaxopt)
pip install "dmipy[cpu]"          # + JAX CPU
```

!!! note "GPU (`[cuda12]`)"
    Needs a working CUDA-12 stack, and the environment must export `LD_LIBRARY_PATH` so the
    dynamic loader resolves the CUDA libraries — see the
    [dmipy-sim README](https://github.com/dmrai-lab/dmipy-sim#gpu) for the exact export.

!!! tip "CPU-only / shared machine"
    Set `JAX_PLATFORMS=cpu` to force JAX onto CPU regardless of what is installed.

There is no importable `dmipy` package — import the engines directly:

```python
import dmipy_sim          # forward Monte Carlo
import dmipy_fit          # analytical inverse
```

Or install an engine on its own:

```bash
pip install dmipy-sim
pip install "dmipy-fit[jax]"
```
