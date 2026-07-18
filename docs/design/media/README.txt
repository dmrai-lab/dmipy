Figure-generation scripts for the dmipy-design docs
===================================================

Each GIF on the dmipy-design pages is produced by a self-contained script in this folder, so a
tweak (different scanner, frequency, protocol) is a one-line edit + re-run, not a rewrite.

  fig_mintte_vs_vanilla.py        -> mintte_vs_vanilla.gif
      Vanilla bang-bang PGSE (symmetric) vs optimized min-TE (asymmetric), same b, real
      Prisma limits, brain defaults (no motion nulling). Off-regions shaded (grey = scanner
      off-time; amber = the vanilla's extra symmetry dead-time).

  fig_ogse_pns_deliverability.py  -> ogse_pns_deliverability.gif
      Deliverability, not spectrum: the same 60 Hz OGSE designed with the PNS (SAFE-model)
      constraint off vs on. Max-b rides the slew limit and peaks at 123% PNS (scanner rejects
      it); the constrained design holds 80% for ~4% less b. Shows why PNS is a hard constraint.

  fig_ogse_frequency_sweep.py     -> ogse_frequency_sweep.gif
      OGSE spectral-targeting sweep: deliverable OGSE designed at 30 / 60 / 90 Hz (short readout,
      long TE -> many oscillation periods), with sharp, well-separated encoding-spectrum peaks at
      the targets and the b-value (SNR) dropping steeply with frequency. Demonstrates that
      spectral_freq controls the encoding band, and the spectral-resolution-vs-SNR trade.

Regenerate (needs the dmipy-design package on the path):

    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design \
        python fig_mintte_vs_vanilla.py
    OMP_NUM_THREADS=1 PYTHONPATH=/path/to/dmipy-design \
        python fig_ogse_vanilla_vs_optimized.py

Single-threaded BLAS matters: NOW is many tiny SciPy SLSQP solves, and on a high-core machine
un-pinned OpenBLAS oversubscribes threads and is ~100x slower. The scripts set OMP_NUM_THREADS=1
themselves; the env var above is belt-and-suspenders.
