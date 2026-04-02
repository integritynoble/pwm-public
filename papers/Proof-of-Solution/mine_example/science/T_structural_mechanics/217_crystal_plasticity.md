# Principle #217 — Crystal Plasticity (CPFEM)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Frontier (δ=5)
**DAG:** [N.pointwise.crystal] --> [L.tangent] --> [∂.time] --> [B.dirichlet] |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise.crystal→L.tangent→∂.time→B.dirichlet   CPFEM       polycrystal-tens   FEM-NR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CRYSTAL PLASTICITY (CPFEM)        P = (E,G,W,C)  Principle #217│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ F = Fᵉ Fᵖ  (multiplicative decomposition)             │
│        │ Lᵖ = Σα γ̇α sα⊗mα  (slip on crystallographic systems) │
│        │ γ̇α = γ̇₀ |τα/gα|^n sign(τα) (power-law flow rule)     │
│        │ Forward: given texture/BC/loads → (u, σ, Fᵖ, γα)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise.crystal] --> [L.tangent] --> [∂.time] --> [B.dirichlet]│
│        │ slip-system-eval  tangent-solve  load-step  displacement-BC         │
│        │ V={N.pointwise.crystal,L.tangent,∂.time,B.dirichlet}  L_DAG=5.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (implicit integration of flow rule)     │
│        │ Uniqueness: CONDITIONAL (multiple active slip ambiguity)│
│        │ Stability: rate sensitivity n regularises; Δt-dependent│
│        │ Mismatch: texture error, slip system misidentification │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 stress error ‖σ−σ_ref‖/‖σ_ref‖       │
│        │ q = 1.0 (nonlinear; limited by grain boundaries)     │
│        │ T = {stress_error, texture_evolution, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Multiplicative decomposition and slip systems consistent | PASS |
| S2 | Rate-dependent flow rule regularises; implicit integration stable | PASS |
| S3 | CPFEM with implicit integration converges for moderate strains | PASS |
| S4 | Stress error bounded; texture evolution verified against EBSD | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# crystal_plasticity/polycrystal_tension_s1_ideal.yaml
principle_ref: sha256:<p217_hash>
omega:
  grid: [32, 32, 32]
  domain: RVE_cube
  num_grains: 100
E:
  forward: "F = Fe*Fp, slip-rate power law"
  crystal_structure: FCC
  slip_systems: 12   # {111}<110>
  n_rate: 20
  gamma0_dot: 0.001
B:
  bottom: {u_z: 0}
  top: {u_z: 0.1}   # 10% tensile strain
I:
  scenario: uniaxial_tension_polycrystal
  strain_levels: [0.02, 0.05, 0.10]
  mesh_sizes: [16³, 24³, 32³]
O: [stress_strain_curve, texture_ODF_error, grain_avg_stress_error]
epsilon:
  stress_error_max: 5.0e-2
  ODF_error_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | RVE with 100 grains statistically representative; mesh/grain ok | PASS |
| S2 | Rate-dependent formulation ensures solvability | PASS |
| S3 | Implicit CPFEM with sub-stepping converges to 10% strain | PASS |
| S4 | Stress-strain curve within 5% of experimental polycrystal data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# crystal_plasticity/benchmark_polycrystal.yaml
spec_ref: sha256:<spec217_hash>
principle_ref: sha256:<p217_hash>
dataset:
  name: FCC_polycrystal_tension
  reference: "Roters et al. (2010) — DAMASK reference simulations"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CPFEM-implicit (16³)
    params: {grains: 100, steps: 50}
    results: {stress_error: 4.8e-2, ODF_error: 0.12}
  - solver: CPFEM-implicit (24³)
    params: {grains: 100, steps: 50}
    results: {stress_error: 2.5e-2, ODF_error: 0.08}
  - solver: spectral-CPFEM (32³)
    params: {grains: 100, steps: 100}
    results: {stress_error: 1.2e-2, ODF_error: 0.05}
quality_scoring:
  - {min_err: 1.0e-2, Q: 1.00}
  - {min_err: 3.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** CPFEM-implicit (24³) — stress error 2.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Stress Err | ODF Err | Runtime | Q |
|--------|------------|---------|---------|---|
| CPFEM-implicit (16³) | 4.8e-2 | 0.12 | 600 s | 0.80 |
| CPFEM-implicit (24³) | 2.5e-2 | 0.08 | 2400 s | 0.90 |
| spectral-CPFEM (32³) | 1.2e-2 | 0.05 | 3600 s | 1.00 |
| FFT-CPFEM (64³) | 8.0e-3 | 0.03 | 7200 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (FFT):  500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p217_hash>",
  "h_s": "sha256:<spec217_hash>",
  "h_b": "sha256:<bench217_hash>",
  "r": {"residual_norm": 8.0e-3, "error_bound": 5.0e-2, "ratio": 0.16},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep crystal_plasticity
pwm-node verify crystal_plasticity/polycrystal_tension_s1_ideal.yaml
pwm-node mine crystal_plasticity/polycrystal_tension_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
