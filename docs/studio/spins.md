# Spin studio — watch the compartments

Watch individual water spins in the three white-matter compartments — **extra-axonal, intra-axonal, myelin water** — as their magnetization evolves through a pulse sequence, one Bloch sphere per compartment, with the chosen gradient waveform and RF pulses drawn on the player strip below.

Everything is a **live vector-Bloch replay** of a stored Monte-Carlo walk through canonical white matter: move any knob — sequence (PGSE / CPMG / PGSTE / GRE), b-value, δ, Δ/T<sub>M</sub>, TE, gradient angle to the fibre, excitation/refocus flip, **B1⁺ scale**, off-resonance — and the spins are re-evolved from scratch. Nothing is a pre-rendered video; the motion *is* the replay. Drop the B1⁺ scale and the excitation no longer tips the spins fully into the transverse plane; watch a spin echo refocus, and a stimulated echo store magnetization along **z** during the mixing time.

<iframe src="../bloch_pedagogy.html" style="width:100%;height:820px;border:1px solid #2a2f3a;border-radius:8px" title="Spin studio — watch the compartments"></iframe>

<p style="margin:.8em 0"><a href="../bloch_pedagogy.html" target="_blank" rel="noopener"><strong>Open full-screen ↗</strong></a> &nbsp;·&nbsp; runs entirely in your browser, best on a desktop.</p>

**What is real here.** The spins' positions are a dmipy-sim walk on the canonical white-matter
substrate (`tools/gen_spin_studio.py`: `Substrate.canonical()` packed and walked, stored as a
replay pack, a few dozen walkers per compartment decoded into the page); the compartments' T2 and
T1 are the substrate's. The page integrates the Bloch equation on those positions in the browser,
the one place on this site where physics runs in JavaScript, and CI checks that integration
against `dmipy_sim.replay_bloch` on the same positions and the same sequence
(`tools/check_spin_studio.py`, agreement to 10⁻³).
