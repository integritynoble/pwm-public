# Principle #355 — Neutron Diffusion

**Domain:** Nuclear Engineering | **Carrier:** neutron | **Difficulty:** Standard (δ=3)
**DAG:** ∂.space.laplacian → N.reaction.fission → B.neumann |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space.laplacian→N.reaction.fission→B.neumann   diffusion    slab/sphere       FDM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NEUTRON DIFFUSION              P = (E,G,W,C)   Principle #355  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂φ/∂t = ∇·(D∇φ) − Σ_a φ + S                          │
│        │ D = 1/(3Σ_tr)  diffusion coefficient                   │
│        │ φ = scalar neutron flux, Σ_a = absorption cross-section│
│        │ Forward: given geometry/D/Σ_a/S/BC → solve φ(r,t)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.laplacian] ──→ [N.reaction.fission] ──→ [B.neumann] │
│        │ derivative  nonlinear  boundary                        │
│        │ V={∂.space.laplacian, N.reaction.fission, B.neumann}  A={∂.space.laplacian→N.reaction.fission, N.reaction.fission→B.neumann}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear elliptic/parabolic PDE)         │
│        │ Uniqueness: YES (unique for given source & BC)         │
│        │ Stability: YES (diffusion operator is dissipative)     │
│        │ Mismatch: cross-section errors, geometric simplification│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖φ−φ_ref‖/‖φ_ref‖              │
│        │ q = 2.0 (FDM central), 2.0 (FEM linear)              │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Flux dimensions consistent; diffusion coefficient well-defined | PASS |
| S2 | Linear elliptic PDE — existence/uniqueness via Lax-Milgram | PASS |
| S3 | FDM and FEM converge at O(h²) for smooth solutions | PASS |
| S4 | L2 error computable against analytic or transport reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# neutron_diffusion/slab_s1_ideal.yaml
principle_ref: sha256:<p355_hash>
omega:
  grid: [200]
  domain: slab_1D
  time: [0, 5.0]
  dt: 0.005
E:
  forward: "∂φ/∂t = D ∂²φ/∂x² − Σ_a φ + S"
  D: 1.0
  Sigma_a: 0.1
B:
  left: {phi: 0.0}    # vacuum
  right: {phi: 0.0}
I:
  scenario: fixed_source_slab
  source_strength: 1.0
  mesh_sizes: [50, 100, 200]
O: [L2_flux_error, max_error]
epsilon:
  L2_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200-cell mesh adequate for 1D slab; dt stable | PASS |
| S2 | Fixed-source subcritical system has unique solution | PASS |
| S3 | Central-difference FDM converges at O(h²) | PASS |
| S4 | L2 error < 10⁻⁴ achievable with 200 cells | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# neutron_diffusion/benchmark_slab.yaml
spec_ref: sha256:<spec355_hash>
principle_ref: sha256:<p355_hash>
dataset:
  name: analytic_slab_diffusion
  reference: "Analytic Green's function solution for 1D slab"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-central
    params: {N: 100, dt: 0.005}
    results: {L2_error: 3.2e-4, max_error: 8.1e-4}
  - solver: FEM-linear
    params: {N: 100, dt: 0.005}
    results: {L2_error: 2.8e-4, max_error: 7.0e-4}
  - solver: FEM-quadratic
    params: {N: 50, dt: 0.005}
    results: {L2_error: 1.5e-5, max_error: 4.2e-5}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 5.0e-4, Q: 0.80}
  - {min_L2: 1.0e-3, Q: 0.75}
```

**Baseline solver:** FDM-central — L2 error 3.2×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FDM-central | 3.2e-4 | 8.1e-4 | 0.5 s | 0.90 |
| FEM-linear | 2.8e-4 | 7.0e-4 | 0.8 s | 0.90 |
| FEM-quadratic | 1.5e-5 | 4.2e-5 | 1.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FEM-quad): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p355_hash>",
  "h_s": "sha256:<spec355_hash>",
  "h_b": "sha256:<bench355_hash>",
  "r": {"residual_norm": 1.5e-5, "error_bound": 1.0e-4, "ratio": 0.15},
  "c": {"fitted_rate": 2.01, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep neutron_diffusion
pwm-node verify AB_nuclear_engineering/neutron_diffusion_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/neutron_diffusion_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
