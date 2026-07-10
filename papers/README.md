# Papers

**Every paper here ships its own proof.** Each folder is a self-contained manuscript —
LaTeX source, the compiled PDF, and *one script per figure* — so nothing in the paper is a
black box you have to take on faith. The figures are rerunnable: each script carries cached
results (`*_data.npz`) so it replots in seconds without a GPU, and drops the cache to
recompute from scratch against the public [`dmipy-sim`](https://github.com/dmrai-lab/dmipy-sim)
(forward Monte Carlo) and [`dmipy-fit`](https://github.com/dmrai-lab/dmipy-fit) (analytical
inverse) engines. Clone a paper folder, `pip install dmipy-fit dmipy-sim`, and every number
and panel regenerates on your machine.

## Physics features

### Surface relaxivity

Water molecules pick up extra transverse relaxation every time they collide with a tissue
boundary — an axon wall, a myelin sheath. This adds a **surface term** `ρ·(S/V)` on top of the
bulk `1/T₂`, proportional to the compartment's surface-to-volume ratio and to the relaxivity
`ρ`. Because different compartments have different geometry, they relax at different rates —
which quietly biases any microstructure estimate that assumes they don't.

- **[`surface_relaxivity_bias/`](surface_relaxivity_bias/)** — *One `S/V` surface-relaxivity
  physics biases both diffusion and relaxometry microstructure estimates: it over-weights the
  intra-axonal signal fraction (first-order, packing-dependent) and nudges the myelin water
  fraction (small, structural).* Closed forms (Brownstein–Tarr interior, Novikov–Burcaw
  exterior) validated by wall-counting Monte Carlo, with a testable packing-dependent TE drift.
