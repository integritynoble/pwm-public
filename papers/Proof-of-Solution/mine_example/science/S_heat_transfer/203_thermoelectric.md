# Principle #203 — Thermoelectric (Peltier/Seebeck)

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.space] --> [L.coupled.electromech] --> [B.electrode] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space→L.coupled.electromech→B.electrode      TE-device   TEC-1D            FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THERMOELECTRIC   P = (E,G,W,C)   Principle #203                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·(k∇T) + J²/σ − TJ·∇α = 0  (energy balance)        │
│        │ ∇·(σ∇V + σα∇T) = 0  (charge conservation)            │
│        │ α = Seebeck coeff, σ = electrical conductivity         │
│        │ Coupled thermal-electrical with Peltier/Thomson/Joule  │
│        │ Forward: BC/material(T) → T(x), V(x), COP/efficiency │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space] --> [L.coupled.electromech] --> [B.electrode]│
│        │ spatial-derivatives  coupled-Seebeck-solve  electrode-BC│
│        │ V={∂.space,L.coupled.electromech,B.electrode}  L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled elliptic, α(T) smooth)        │
│        │ Uniqueness: YES for bounded T range                    │
│        │ Stability: mild nonlinearity; Picard converges        │
│        │ Mismatch: α(T), k(T), σ(T) uncertainty               │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = COP error, temperature profile L2 error            │
│        │ q = 2.0 (FEM-P1)                                      │
│        │ T = {COP_error, T_profile_error, power_error}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled thermal-electrical consistent; Onsager reciprocity | PASS |
| S2 | Unique solution for bounded T; ZT figure of merit well-defined | PASS |
| S3 | Picard iteration on T-V coupling converges | PASS |
| S4 | COP error < 3% vs exact 1D thermoelectric solution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# thermoelectric/tec_1d_s1.yaml
principle_ref: sha256:<p203_hash>
omega:
  grid: [100]
  domain: [0, 0.002]   # 2 mm leg
E:
  forward: "coupled thermal-electrical with T-dependent properties"
  material: Bi2Te3
  alpha_300K: 200e-6    # V/K
  sigma_300K: 1.1e5     # S/m
  k_300K: 1.5           # W/(m·K)
B:
  cold: {T: 280}
  hot: {T: 320}
  current: 3.0   # A
I:
  scenario: thermoelectric_cooler_1D
  ZT: 0.8
  mesh_sizes: [25, 50, 100]
O: [COP_error, T_profile_L2, cooling_power_error]
epsilon:
  COP_error_max: 3.0e-2
  T_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D leg; Bi₂Te₃ properties within valid range | PASS |
| S2 | Exact 1D solution with constant properties exists | PASS |
| S3 | FEM + Picard converges in < 10 iterations | PASS |
| S4 | COP error < 3% at N=100 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# thermoelectric/benchmark_tec.yaml
spec_ref: sha256:<spec203_hash>
principle_ref: sha256:<p203_hash>
dataset:
  name: TEC_1D_exact
  reference: "Rowe (2006) thermoelectric handbook"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1 (constant props)
    params: {N: 50}
    results: {COP_error: 0.5%, T_error: 2.1e-3}
  - solver: FEM-P1 (T-dependent)
    params: {N: 50}
    results: {COP_error: 2.1%, T_error: 8.5e-3}
  - solver: COMSOL (multiphysics)
    params: {N: 100}
    results: {COP_error: 1.5%, T_error: 5.2e-3}
quality_scoring:
  - {min_COP_err: 0.5%, Q: 1.00}
  - {min_COP_err: 2.0%, Q: 0.90}
  - {min_COP_err: 3.0%, Q: 0.80}
  - {min_COP_err: 5.0%, Q: 0.75}
```

**Baseline solver:** COMSOL — COP error 1.5%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | COP Error | T Error | Runtime | Q |
|--------|----------|---------|---------|---|
| FEM-P1 (T-dep) | 2.1% | 8.5e-3 | 0.5 s | 0.90 |
| COMSOL | 1.5% | 5.2e-3 | 1.0 s | 0.90 |
| FEM-P2 (fine) | 0.3% | 1.1e-3 | 2.0 s | 1.00 |
| Spectral | 0.1% | 2.5e-4 | 0.5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p203_hash>",
  "h_s": "sha256:<spec203_hash>",
  "h_b": "sha256:<bench203_hash>",
  "r": {"residual_norm": 1.0e-3, "error_bound": 3.0e-2, "ratio": 0.033},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep thermoelectric
pwm-node verify thermoelectric/tec_1d_s1.yaml
pwm-node mine thermoelectric/tec_1d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
