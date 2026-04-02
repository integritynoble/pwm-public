# Principle #213 — Modal Analysis (Eigenfrequency)

**Domain:** Structural Mechanics | **Carrier:** N/A (eigenvalue problem) | **Difficulty:** Textbook (δ=1)
**DAG:** [E.generalized] --> [L.stiffness] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.generalized→L.stiffness      modal       cantilever-modes   FEM+eig
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MODAL ANALYSIS (EIGENFREQUENCY)   P = (E,G,W,C)  Principle #213│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Kφ = ω²Mφ  (generalized eigenvalue problem)            │
│        │ K = stiffness matrix, M = mass matrix                  │
│        │ ω = natural frequency, φ = mode shape                  │
│        │ Forward: given K,M → solve for (ω_i, φ_i), i=1..N     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.generalized] --> [L.stiffness]                    │
│        │ eigenvalue-solve  stiffness+mass-assemble               │
│        │ V={E.generalized,L.stiffness}  L_DAG=1.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (symmetric positive-definite M, K)      │
│        │ Uniqueness: YES (eigenvalues real & positive; modes     │
│        │   orthogonal up to multiplicity)                        │
│        │ Stability: κ depends on eigenvalue separation           │
│        │ Mismatch: mass/stiffness modelling error                │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative freq error |ω_num−ω_ref|/ω_ref (primary) │
│        │ q = 2p (eigenvalue superconvergence for FEM order p)  │
│        │ T = {freq_errors, MAC_values, K_resolutions}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | K, M symmetric positive-(semi)definite; dimensions consistent | PASS |
| S2 | Spectral theorem guarantees real eigenvalues and orthogonal modes | PASS |
| S3 | Lanczos/subspace iteration converges for lowest N modes | PASS |
| S4 | Frequency error bounded by eigenvalue approximation theory | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# modal_analysis/cantilever_modes_s1_ideal.yaml
principle_ref: sha256:<p213_hash>
omega:
  grid: [64, 16]
  domain: cantilever_beam_2D
  length: 1.0
  height: 0.05
E:
  forward: "K*phi = omega^2 * M * phi"
  youngs_modulus: 210.0e9
  density: 7800
  poisson: 0.3
B:
  left_end: {u: [0,0]}   # clamped
I:
  scenario: cantilever_first_10_modes
  num_modes: 10
  mesh_sizes: [16x4, 32x8, 64x16]
O: [frequency_errors, MAC_values, mode_shape_L2_errors]
epsilon:
  freq_error_max: 1.0e-3
  MAC_min: 0.999
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh adequate for first 10 modes; element aspect ratio ok | PASS |
| S2 | Cantilever eigenvalues known analytically for beam; 2D FEM converges | PASS |
| S3 | Lanczos solver converges for well-separated eigenvalues | PASS |
| S4 | Frequency error < 0.1% at 64×16 for first 10 modes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# modal_analysis/benchmark_cantilever_modes.yaml
spec_ref: sha256:<spec213_hash>
principle_ref: sha256:<p213_hash>
dataset:
  name: cantilever_eigenfrequencies
  reference: "Analytical beam frequencies ω_n = β_n² √(EI/ρA)/L²"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4 (32×8)
    params: {mesh: 32x8, Lanczos: true}
    results: {freq_error_mode1: 1.2e-3, freq_error_mode10: 8.5e-3}
  - solver: FEM-Q8 (16×4)
    params: {mesh: 16x4, Lanczos: true}
    results: {freq_error_mode1: 3.0e-4, freq_error_mode10: 2.1e-3}
  - solver: FEM-Q8 (32×8)
    params: {mesh: 32x8, Lanczos: true}
    results: {freq_error_mode1: 7.5e-5, freq_error_mode10: 5.3e-4}
quality_scoring:
  - {min_freq_err: 1.0e-4, Q: 1.00}
  - {min_freq_err: 1.0e-3, Q: 0.90}
  - {min_freq_err: 5.0e-3, Q: 0.80}
  - {min_freq_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 (16×4) — mode-1 freq error 3.0×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Mode-1 Err | Mode-10 Err | Runtime | Q |
|--------|------------|-------------|---------|---|
| FEM-Q4 (32×8) | 1.2e-3 | 8.5e-3 | 2 s | 0.80 |
| FEM-Q8 (16×4) | 3.0e-4 | 2.1e-3 | 3 s | 0.90 |
| FEM-Q8 (32×8) | 7.5e-5 | 5.3e-4 | 10 s | 1.00 |
| hp-FEM (p=4) | 1.0e-6 | 8.0e-5 | 8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (hp-FEM): 100 × 1.00 = 100 PWM
Floor:              100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p213_hash>",
  "h_s": "sha256:<spec213_hash>",
  "h_b": "sha256:<bench213_hash>",
  "r": {"residual_norm": 1.0e-6, "error_bound": 1.0e-3, "ratio": 0.001},
  "c": {"fitted_rate": 4.02, "theoretical_rate": 4.0, "K": 3},
  "Q": 1.00,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep modal_analysis
pwm-node verify modal_analysis/cantilever_modes_s1_ideal.yaml
pwm-node mine modal_analysis/cantilever_modes_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
