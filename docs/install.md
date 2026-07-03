# Install

`dmipy` is a thin umbrella that pulls both engines:

```bash
pip install dmipy                 # dmipy-sim + dmipy-fit
pip install "dmipy[cuda12]"       # + JAX CUDA-12 GPU (JAX, jaxopt, osqp)
pip install "dmipy[cpu]"          # + JAX CPU
```

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
