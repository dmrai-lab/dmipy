# Changelog

`dmipy` is the umbrella install for the dmipy ecosystem. Its version follows dmipy-sim, dmipy-fit and
dmipy-design; dmipy-replay and dmipy-tract have version lines of their own.

## 3.0.0 - 2026-11-02

`pip install dmipy` installs the 3.0 line: dmipy-sim 3, dmipy-replay 0.2, dmipy-fit 3 and dmipy-design 3.
`pip install "dmipy[tract]"` adds dmipy-tract 0.1.

- **dmipy-sim** walks a tissue substrate once and keeps the walk as a replay pack.
- **dmipy-replay** turns a pack into a signal or an image: any acquisition, orientation distributions, replay phantoms.
- **dmipy-fit** fits multi-compartment models to data, and the replay compartments fit through a pack.
- **dmipy-design** designs deliverable waveforms and refocusing RF under a scanner's limits.
- **dmipy-tract** tracks streamlines on FOD fields (the `tract` extra).
- **Requires** `dmipy-sim>=3,<4`, `dmipy-replay>=0.2,<0.3`, `dmipy-fit>=3,<4` and `dmipy-design>=3,<4`; the `tract`
  extra requires `dmipy-tract>=0.1,<0.2`. The extras `cuda12` and `cpu` add JAX with jaxopt, and `docs` builds the
  dmipy.org site.

## 2.1.0

Tracks **dmipy-sim 2.1.0** and **dmipy-fit 2.1.0**. The dependency ranges (`>=2.0,<3`) already
admit the 2.1 engines; this bump keeps the umbrella version aligned.

### Added
- **dmipy.org "Mesh substrates" page** — loading a PLY into `dmipy_sim.Mesh`, the resolution
  guard, per-compartment properties, and the visualisation gallery (with the rotating GIF).

### Changed
- **docs/papers**: cataloged the T2-factor note, de-special-cased NEXI, added result-figure PNGs.

## 2.0.0

First coordinated public release of the dmipy ecosystem (sim + fit).
