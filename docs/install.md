# Install

```bash
pip install dmipy                 # dmipy-sim + dmipy-replay + dmipy-fit + dmipy-design (and dmipy-analytic under them)
pip install "dmipy[tract]"        # + dmipy-tract, tractography on FOD fields
pip install "dmipy[cpu]"          # + JAX on the CPU, with jaxopt
pip install "dmipy[cuda12]"       # + JAX on a CUDA-12 GPU, with jaxopt
```

Extras combine: `pip install "dmipy[tract,cuda12]"`. There is no importable `dmipy` package; import the
packages ([what each one is](packages.md)):

```python
import dmipy_analytic             # the closed forms
import dmipy_replay               # the reader and the acquisition object
import dmipy_sim                  # the producer: walks and replay packs
import dmipy_fit                  # the analytical inverse
import dmipy_design               # sequence design
```

## One package alone

Each package installs on its own, with the packages it depends on:

```bash
pip install dmipy-analytic                # NumPy only
pip install "dmipy-analytic[special]"     # + the forms that need scipy's special functions
pip install "dmipy-analytic[jax]"         # + dmipy_analytic.jax, the JAX twins
pip install dmipy-replay                  # read and replay packs: NumPy only
pip install "dmipy-replay[pose]"          # + the pose expansion (scipy)
pip install dmipy-sim                     # walk substrates, write packs (JAX)
pip install "dmipy-sim[mesh]"             # + .ply meshes (trimesh)
pip install "dmipy-fit[jax]"              # the batched fits (JAX, jaxopt)
pip install "dmipy-design[pulseq]"        # + the Pulseq export (pypulseq)
pip install dmipy-tract                   # tractography (JAX)
```

!!! note "GPU"
    The walk, the fits and the tracker run on the GPU when JAX finds one. With `[cuda12]` the environment
    exports `LD_LIBRARY_PATH` so the loader finds the CUDA libraries; the
    [dmipy-sim install notes](https://github.com/dmrai-lab/dmipy-sim#install) have the exact line. Set
    `JAX_PLATFORMS=cpu` to force the CPU, for example in CI. Every example on this site runs on the CPU, and
    dmipy-replay needs no GPU at all.

!!! warning "Coming from dmipy 1.x"
    The 2019 toolbox was a single importable `dmipy` package. It stays on PyPI:
    `pip install "dmipy<2"`. Everything else is in [Migrating](migrating.md).
