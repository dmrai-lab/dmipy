# Gaussian-Phase cylinder for arbitrary waveforms

Derivation note for `C4CylinderGaussianPhaseApproximation`
(`dmipy_fit.signal_models.cylinder_models`) — the Gaussian-Phase-Approximation (GPA) cylinder
generalised from fixed-direction PGSE (Van Gelderen) to **arbitrary rotating / tensor-valued
gradient waveforms** (OGSE, LTE / PTE / STE, free `G(t)`).

**The useful result.** In the fast-eigenmode limit, the perpendicular attenuation of a
*dispersed* cylinder population depends on the waveform only through the **l ≤ 2 angular power
spectrum** of `G(t)` (six numbers `Γ_lm`) plus the **b-tensor** — a compact, differentiable,
`O(n_t)` closed form evaluated as a spherical-harmonic inner product against the ODF. That is
what makes it cheap enough to sit inside a waveform-design loop.

**Scope & honesty.** This is the *fast-eigenmode* (long-time) approximation: accurate for radii
`R ≲ 3 µm` and gradient spectra below the first cylinder eigenmode; large radii and
high-frequency OGSE need the full spectral GPA. The *exact* result for an arbitrary waveform is
Grebenkov's multiple-correlation-function matrix formalism — this note is a fast approximation
for the restricted regime it targets, not a replacement for that. It is validated against
`dmipy-sim` Monte-Carlo (§6); that agreement is a consistency check between the two engines, not
an independent proof.

---

## 1. Problem Statement

The classic Gaussian Phase Approximation (GPA) for a cylinder was derived for Pulsed
Gradient Spin Echo (PGSE) with a fixed gradient direction.  We extend it to arbitrary
free-gradient waveforms G(t) ∈ ℝ³, including rotating and tensor-valued encodings
(STE, OPTICUBE21, NOW-STE, arbitrary OGSE) while preserving exact equivalence with
the PGSE formula in the fixed-direction limit.

---

## 2. Physics

### 2.1 Accumulated phase for a single water molecule

    φ = γ ∫₀ᵀ G(t)·r(t) dt

where γ = 2.675 × 10⁸ rad/(s·T) is the water gyromagnetic ratio, G(t) is the
gradient waveform (T/m), r(t) is the molecule position (m), and T is the total
waveform duration.

### 2.2 GPA signal for a cylinder with axis n̂

Under the Gaussian Phase Approximation the signal is:

    E(n̂) = exp(−⟨φ²⟩/2)

The phase variance decomposes:

    ⟨φ²⟩ = φ_par(n̂) + φ_perp(n̂)

### 2.3 Parallel contribution (Gaussian, exact for any waveform)

    φ_par(n̂) = λ_par · n̂ᵀ B n̂

where B is the **b-tensor**:

    B_ij = γ² ∫₀ᵀ q_i(t) q_j(t) dt,    q(t) = γ ∫₀ᵗ G(t') dt'

For PGSE: B = b · n⊗n (rank-1), so φ_par = b·(n̂·n)²·λ_par.
For spherical b-tensor (STE): B = (b/3)·I, so φ_par = (b/3)·λ_par (orientation-independent).

### 2.4 Perpendicular contribution: fast-eigenmode GPA

For a cylinder of radius R with impermeable wall, diffusivity D perpendicular to the
axis, the perpendicular phase variance in the **fast-eigenmode limit** is:

    φ_perp(n̂) = C_geom · ∫₀ᵀ |G_⊥(t, n̂)|² dt

where G_⊥(t, n̂) = G(t) − (G(t)·n̂) n̂ is the gradient component perpendicular to
the cylinder axis, and

    C_geom = γ² Σₖ Bₖ / αₖ

with:
- μₖ = k-th zero of J₁'(x)  (μ₁ = 1.84118, μ₂ = 5.33144, ...)
- Bₖ = 2(R/μₖ)² / (μₖ² − 1)   (eigenmode amplitude weights)
- αₖ = (μₖ/R)² · D             (eigenmode decay rates, s⁻¹)

**Validity condition:** αₖ · T >> 1, i.e., the waveform duration T must greatly exceed
the eigenmode decay time τ₁ = R²/(μ₁²·D).

  | R (µm) | D (m²/s) | τ₁ (ms) | Clinical T=75 ms → α₁T |
  |--------|----------|---------|------------------------|
  | 1      | 1.7×10⁻⁹ | 0.17    | 440  (error < 0.1 %)   |
  | 2      | 1.7×10⁻⁹ | 0.69    | 109  (error < 0.1 %)   |
  | 5      | 1.7×10⁻⁹ | 4.3     | 17   (error ~ 3 %)     |

### 2.5 Factorisation via angular power spectrum

Using |G_⊥|² = |G|² − (G·n̂)² = |G|² · (1 − (Ĝ·n̂)²), where Ĝ = G/|G|:

    ∫|G_⊥|² dt = ∫|G|² dt − ∫|G|² (Ĝ·n̂)² dt

The second integral is the **l=2 projection** of the angular power spectrum
Γ_lm = ∫|G(t)|² Y_lm(Ĝ(t)) dt onto n̂.  Using the SH addition theorem:

    ∫|G|² (Ĝ·n̂)² dt = (8π/15) Σₘ Γ₂ₘ Y₂ₘ(n̂) + (2/3) ∫|G|² dt

Therefore:

    φ_perp(n̂) = C_geom · [2/3 · ∫|G|² dt − (8π/15) · Σₘ Γ₂ₘ Y₂ₘ(n̂)]

where Γ₂ₘ are the five l=2 (m = −2,−1,0,1,2) real SH components of the
gradient angular power spectrum:

    Γ₂ₘ = ∫₀ᵀ |G(t)|² Y₂ₘ(Ĝ(t)) dt

and Γ₀₀ = ∫|G|² dt / √(4π).

### 2.6 Complete single-fiber signal

    E(n̂) = exp(
        − C_geom · [2/3 · Γ₀₀√(4π) − (8π/15) · Γ₂ₘ · Y₂ₘ(n̂)]
        − λ_par · n̂ᵀ B n̂
    )

This formula uses **only two waveform-derived objects** (Γ_lm and B) and the
cylinder geometry factor C_geom.  Both objects can be precomputed once per
measurement at O(n_t) cost.

---

## 3. Implementation Algorithm

### Step 1 — Precompute C_geom (once per (R, D) pair)

```
Input: R (m), D (m²/s), roots μₖ = zeros of J₁'(x) (at least 100 terms)
C_geom = γ² · Σₖ  2(R/μₖ)² / (μₖ²−1)  /  ((μₖ/R)²·D)
```

### Step 2 — Compute Γ_lm from G(t)  (shape: (n_m, 6))

```
Input: G[m, t, 3] in T/m, dt (s)
For each measurement m:
    Ĝ[t] = G[m,t] / |G[m,t]|        (unit direction; skip t where G=0)
    G2[t] = |G[m,t]|²

    Γ₀₀[m]   = Σ_t G2[t] · Y₀₀(Ĝ[t]) · dt     Y₀₀ = 1/√(4π)
    Γ₂,₋₂[m] = Σ_t G2[t] · Y₂,₋₂(Ĝ[t]) · dt   Y₂,₋₂ = √(15/4π) · x·y
    Γ₂,₋₁[m] = Σ_t G2[t] · Y₂,₋₁(Ĝ[t]) · dt   Y₂,₋₁ = √(15/4π) · y·z
    Γ₂, ₀[m] = Σ_t G2[t] · Y₂, ₀(Ĝ[t]) · dt   Y₂, ₀ = √(5/16π) · (2z²−x²−y²)
    Γ₂, ₁[m] = Σ_t G2[t] · Y₂, ₁(Ĝ[t]) · dt   Y₂, ₁ = √(15/4π) · x·z
    Γ₂, ₂[m] = Σ_t G2[t] · Y₂, ₂(Ĝ[t]) · dt   Y₂, ₂ = √(15/16π) · (x²−y²)
```

where (x, y, z) = Ĝ[t].

### Step 3 — Compute b-tensor B (shape: (n_m, 3, 3))

```
q[m, t] = γ · Σ_{t'≤t} G[m, t'] · dt    (cumulative sum, shape (n_m, n_t, 3))
B[m, i, j] = Σ_t q[m, t, i] · q[m, t, j] · dt
```

For PGSE: B[m] = b[m] · n[m] ⊗ n[m]  (reconstruct analytically, avoid discretisation).

### Step 4 — Evaluate E(n̂) for a specific fiber direction

```
φ_perp = C_geom · (2/3 · Γ₀₀[m] · √(4π)  −  8π/15 · Γ₂ₘ[m] · Y₂ₘ(n̂))
φ_par  = λ_par · (n̂ᵀ B[m] n̂)
E[m]   = exp(−φ_perp − φ_par)
```

### Step 5 — Dispersed signal via SH inner product

For an orientation distribution ODF(n̂) with SH coefficients f_lm (Tournier/MRtrix
real SH, even l only):

```
a. Evaluate E_m(n̂_q) at N_q = 724 quadrature points on the sphere (uniform weights w_q = 1/724)
b. Project to SH: E_lm[m] = 4π · Σ_q w_q · E_m(n̂_q) · Y_lm(n̂_q)
c. Dispersed signal: S[m] = E_lm[m] · f_lm  (inner product)
```

The quadrature is over the full sphere (antipodally symmetric for any axis).
l_max = 8 is required: the exponent exp(−φ) generates harmonic content up to
l=8 for physically relevant parameters (C_geom × b ~ 0.1–10).

---

## 4. SH Convention

Real symmetric SH (Tournier/MRtrix convention):

    Y_l^0(θ,φ) = √((2l+1)/(4π)) · P_l(cos θ)
    Y_0^0 = 1 / (2√π)

Array layout: even orders l=0,2,4,...,l_max; all m in [−l, l] per order.
Total coefficients for l_max=8: 1+5+9+13+17 = 45.
m=0 indices: l=0→0, l=2→3, l=4→10, l=6→21, l=8→36.

**Normalisation of ODF:** For any properly normalised ODF, f_00 = 1/(2√π).
This means the dispersed signal at b=0 equals 1: S = E_lm · f_lm = 1.

**Watson ODF:** Use GL quadrature (not sphere-grid fitting) for accuracy at κ≥20.
The function `dmipy_sim.sh_convolution.watson_odf_sh(kappa, lmax=8)` provides accurate coefficients.

---

## 5. Key Identities

**PGSE limit:** For a fixed-direction PGSE along n with pulse parameters (δ, Δ):

    Γ₀₀ = G² · 2δ / √(4π)
    Γ₂₀ = G² · 2δ · √(5/(16π)) · (2(n·ẑ)² − 1 + ... ) [depends on n vs z-axis]
    B = b · n ⊗ n   where b = γ² G² δ² (Δ − δ/3)

→ E(n̂) reduces to the Van Gelderen PGSE formula when δ >> τ₁ = R²/(μ₁²D).

**STE (spherical b-tensor):** B = (b_trace/3) · I₃.
The dispersed signal becomes ODF-independent (orientation-independent) for any
anisotropic ODF, because u^T B u = b_trace/3 for all n̂.

**Zero b-value:** B = 0 → φ_perp = 0, φ_par = 0 → E(n̂) = 1 for all n̂ → S = 1. ✓

---

## 6. Monte Carlo Validation

Validated at atol ≤ 0.02 (b < 3000 s/mm²) and atol ≤ 0.05 (b ≥ 3000 s/mm²) against
500 000-walker MC trajectories for:

| Waveform    | Type  | Duration | G_max levels (T/m)    |
|-------------|-------|----------|-----------------------|
| OPTICUBE21  | STE   | 100 ms   | 0.05, 0.08, 0.10, 0.20, 0.30 |
| NOW-STE     | STE   | 75.6 ms  | 0.05, 0.08, 0.10, 0.20, 0.30 |
| PGSE        | linear| δ=20ms Δ=40ms | 0.05, 0.08, 0.10, 0.20, 0.30 |

Radii: R ∈ {1.0, 2.0, 3.0, 5.0} µm.  Watson κ ∈ {1, 5, 20, 100}.
Tests (public): `dmipy_fit/signal_models/tests/test_gaussian_phase.py`, `test_gamma_lm_cylinder.py`, `test_cylinder_fixture_ogse_dispersed.py`.
MC fixtures are generated and checked within that test suite.

MC uses the same SH convolution as dmipy-sim: GL fiber-response fit → `apply_odf`.

---

## 7. Known Limitations

1. **Fast-eigenmode condition** — Error grows as τ₁/T increases.  For R=5µm, T=40ms:
   τ₁/T = 0.11 → error ~12% at moderate b.  R > ~3µm requires the full spectral GPA.

2. **High-frequency OGSE** — When f > α₁/(2π) ~ D·μ₁²/(2πR²), the fast-eigenmode
   approximation breaks.  For R=2µm, D=1.7×10⁻⁹: f_max ≈ 230 Hz.

3. **Exchange / permeability** — Assumes impermeable membrane.

4. **l_max = 4 for Γ_lm** — The angular power spectrum only needs l=0 and l=2 because
   the cylinder GPA involves only ∫|G_⊥|² dt, which projects onto l≤2.  Higher orders
   of Γ_lm (l=4,6,...) contribute only through waveform self-products, which are zero
   under the fast-eigenmode limit.  The SH projection of exp(−φ) to E_lm uses l_max=8.
