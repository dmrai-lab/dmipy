# Changelog

`dmipy` is the umbrella install for the two engines — `dmipy-sim` (forward Monte Carlo) and
`dmipy-fit` (analytical inverse). It versions in lockstep with them.

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
