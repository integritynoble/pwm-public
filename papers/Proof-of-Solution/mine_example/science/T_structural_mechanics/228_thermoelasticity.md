# Principle #228 — Thermoelasticity

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [L.coupled.thermomech] --> [B.robin] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.coupled.thermomech→B.robin   thermoelast bimetal-strip      FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THERMOELASTICITY                  P = (E,G,W,C)  Principle #228│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇·σ = f,  σ = C:(ε − α ΔT I)                        │
│        │ ρcₚ ∂T/∂t = ∇·(k∇T) + Q  (optional coupling)        │
│        │ α = CTE, ΔT = T − T_ref, k = thermal conductivity    │
│        │ Forward: given T-field/BC → solve for (u, σ)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [L.coupled.thermomech] --> [B.robin]   │
│        │ time  coupled-thermo-mechanical  convective-BC         │
│        │ V={∂.time,L.coupled.thermomech,B.robin}  L_DAG=3.0    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sequential: heat eqn then elasticity) │
│        │ Uniqueness: YES (linear coupling; each sub-problem ok) │
│        │ Stability: κ depends on CTE mismatch and ΔT           │
│        │ Mismatch: CTE error, temperature field uncertainty     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-Q2 for both thermal and mechanical)     │
│        │ T = {displacement_error, stress_error, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Thermal strain consistent with CTE; stress-free at T_ref | PASS |
| S2 | Sequential solve well-posed; one-way coupling linearises problem | PASS |
| S3 | FEM for heat equation + elasticity converges independently | PASS |
| S4 | L2 error bounded by mesh-dependent estimates for both fields | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# thermoelasticity/bimetal_strip_s1_ideal.yaml
principle_ref: sha256:<p228_hash>
omega:
  grid: [128, 16]
  domain: bimetallic_strip
  length: 0.1
  thickness: [0.001, 0.001]   # two layers
E:
  forward: "sigma = C:(eps - alpha*DeltaT*I)"
  materials:
    - {E: 210e9, nu: 0.3, alpha: 12e-6, k: 50}   # steel
    - {E: 70e9, nu: 0.33, alpha: 23e-6, k: 200}   # aluminium
  T_ref: 293.15
B:
  left_end: {u: [0,0]}   # clamped
  thermal: {DeltaT: 100}   # uniform heating
I:
  scenario: bimetal_thermal_bending
  DeltaT_values: [50, 100, 200]
  mesh_sizes: [32x4, 64x8, 128x16]
O: [L2_displacement_error, tip_deflection_error, max_stress_error]
epsilon:
  L2_error_max: 1.0e-3
  tip_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh captures interface; both layers resolved | PASS |
| S2 | Timoshenko bimetal formula provides analytical tip deflection | PASS |
| S3 | FEM with interface elements converges for both materials | PASS |
| S4 | L2 error < 10⁻³ at 128×16 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# thermoelasticity/benchmark_bimetal.yaml
spec_ref: sha256:<spec228_hash>
principle_ref: sha256:<p228_hash>
dataset:
  name: bimetal_thermal_bending
  reference: "Timoshenko bimetal strip formula (1925)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4 (64×8)
    params: {h: 1/64}
    results: {L2_error: 3.2e-3, tip_error: 5.5e-3}
  - solver: FEM-Q8 (64×8)
    params: {h: 1/64}
    results: {L2_error: 4.5e-4, tip_error: 8.0e-4}
  - solver: FEM-Q8 (128×16)
    params: {h: 1/128}
    results: {L2_error: 1.1e-4, tip_error: 2.0e-4}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 5.0e-4, Q: 0.90}
  - {min_L2: 2.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 (64×8) — L2 error 4.5×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Tip Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q4 (64×8) | 3.2e-3 | 5.5e-3 | 3 s | 0.80 |
| FEM-Q8 (64×8) | 4.5e-4 | 8.0e-4 | 8 s | 0.90 |
| FEM-Q8 (128×16) | 1.1e-4 | 2.0e-4 | 30 s | 1.00 |
| Analytical (Timoshenko) | 0.0 | 0.0 | 0.01 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (analytical): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p228_hash>",
  "h_s": "sha256:<spec228_hash>",
  "h_b": "sha256:<bench228_hash>",
  "r": {"residual_norm": 1.1e-4, "error_bound": 1.0e-3, "ratio": 0.11},
  "c": {"fitted_rate": 2.00, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep thermoelasticity
pwm-node verify thermoelasticity/bimetal_strip_s1_ideal.yaml
pwm-node mine thermoelasticity/bimetal_strip_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
