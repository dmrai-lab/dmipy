# The packages

dmipy is six packages and an umbrella install. Each is one thing, and each depends only on the packages above it:

```text
dmipy-analytic           the closed forms of the signal
      │
dmipy-replay             the reader: a replay pack becomes a signal or an image; the acquisition object
      │
dmipy-sim                the producer: a Monte-Carlo walk of a substrate becomes a replay pack
      │
      ├── dmipy-fit      analytical models, fitted on the same acquisition object
      ├── dmipy-design   deliverable waveforms under a scanner's limits
      └── dmipy-tract    tractography on FOD fields
            │
dmipy                    the umbrella: one install of the four above it, dmipy-tract as an extra
```

| package | what it is | import | install |
|---|---|---|---|
| [dmipy-analytic](https://github.com/dmrai-lab/dmipy-analytic) | closed and semi-closed forms of the diffusion-MRI signal for special cases (free and restricted diffusion, exchange, relaxation, coherence pathways, orientation distributions, the fields of simple shapes), each with its assumptions and its source; NumPy definitions with JAX twins. The one copy the other packages import. [Closed forms](analytic/index.md) | `dmipy_analytic` | `pip install dmipy-analytic` |
| [dmipy-replay](https://github.com/dmrai-lab/dmipy-replay) | the reader of replay packs: a pack becomes a signal or an image under any acquisition, tissue, scanner and pose, from a file or by range from the Hub, with no walk and no GPU. It owns what every package shares: the acquisition object (`ScannerSequence`) and its builders, the scanner catalogue, the substrate spec and the tissue. Its core is NumPy only. [The replay guide](replay/index.md) | `dmipy_replay` | `pip install dmipy-replay` |
| [dmipy-sim](https://github.com/dmrai-lab/dmipy-sim) | the producer: a substrate walked once by Monte Carlo and encoded as it runs (`walk`), stored as a certified replay pack (`build_replay_pack`); `simulate` is the walk and the replay in one call. JAX, on a CPU or a GPU. [Simulate](sim.md) | `dmipy_sim` | `pip install dmipy-sim` |
| [dmipy-fit](https://github.com/dmrai-lab/dmipy-fit) | analytical multi-compartment models, relaxation and surface relaxivity as factors, CSD, and their fits, batched in JAX; replay models fit against a pack. [Fit](fit.md) | `dmipy_fit` | `pip install "dmipy-fit[jax]"` |
| [dmipy-design](https://github.com/dmrai-lab/dmipy-design) | gradient waveforms optimised under a named scanner's limits and a timing budget, returned as a `ScannerSequence`; refocusing RF; Pulseq export; a pack's certificate against a deliverable set. [Design](design.md) | `dmipy_design` | `pip install dmipy-design` |
| [dmipy-tract](https://github.com/dmrai-lab/dmipy-tract) | streamline tractography on FOD fields, batched on the JAX device: one field (`FODField`), one tracker (`track`), one output (`Tractogram`) | `dmipy_tract` | `pip install dmipy-tract` |
| [dmipy](https://github.com/dmrai-lab/dmipy) | the umbrella: `pip install dmipy` installs dmipy-sim, dmipy-replay, dmipy-fit and dmipy-design (dmipy-analytic comes with them), `dmipy[tract]` adds dmipy-tract. It has no importable module; it holds this site. | — | `pip install dmipy` |

The [install page](install.md) has the extras. Every package imports under its own name:

```python
import dmipy_analytic    # the closed forms
import dmipy_replay      # the reader and the acquisition object
import dmipy_sim         # the producer
import dmipy_fit         # the analytical inverse
import dmipy_design      # sequence design
import dmipy_tract       # tractography (pip install "dmipy[tract]")
```

## What crosses between them

- **The acquisition** is one object, dmipy-replay's `ScannerSequence`: the sequence dmipy-design returns is the one
  dmipy-sim walks for, dmipy-replay replays and dmipy-fit reads ([Acquisition](acquisition.md)).
- **The substrate** is one spec, dmipy-replay's `SubstrateSpec`: a geometry writes it (`geometry.spec`), dmipy-sim
  walks it, and every pack embeds the spec it was walked from.
- **The pack** is the `.rpk` file of the open [replay-pack format](https://github.com/dmrai-lab/replay-pack-spec):
  dmipy-sim writes it, dmipy-replay reads it, and the public ones are on the Hub under
  [SubstrateCommons](https://huggingface.co/SubstrateCommons).
- **The forms** are dmipy-analytic's alone: a constant (`GAMMA`), a closed form or an eigenmode solution is
  defined there once, and the packages that need it import it.

The code of dmipy-analytic and dmipy-replay is Apache-2.0; dmipy-sim, dmipy-fit, dmipy-design, dmipy-tract and the
umbrella are dual-licensed, AGPL-3.0 or a commercial licence.
