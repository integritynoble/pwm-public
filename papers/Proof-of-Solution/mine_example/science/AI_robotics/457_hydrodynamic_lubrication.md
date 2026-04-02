# Principle #457 — Hydrodynamic Lubrication (Reynolds Equation)

**Domain:** Robotics & Mechanical Systems | **Carrier:** fluid | **Difficulty:** Standard (δ=2)
**DAG:** [∂.space] --> [L.sparse] --> [B.wall] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.x-->L.sparse-->B.wall  Reynolds  LubBench-10  FDM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HYDRODYNAMIC LUBRICATION   P = (E, G, W, C)   Principle #457  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂/∂x(h³/12μ ∂p/∂x) + ∂/∂z(h³/12μ ∂p/∂z)             │
│        │   = U/2 ∂h/∂x + ∂h/∂t   (Reynolds equation)          │
│        │ h(x,z) = film thickness; p = pressure distribution    │
│        │ Inverse: determine h or viscosity from pressure data   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.x] ──→ [L.sparse] ──→ [B.wall]                      │
│        │   Reynolds-eq  FEM-disc  boundary                       │
│        │ V={∂.x,L.sparse,B.wall}  A={∂.x→L.sparse,L.sparse→B.wall}  L_DAG=2.0                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (elliptic PDE with proper BC)           │
│        │ Uniqueness: YES (with Reynolds/Swift-Stieber cavit.)   │
│        │ Stability: well-posed; smooth solution for smooth h    │
│        │ Mismatch: cavitation model, thermal effects, roughness │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = pressure error (primary), load capacity error      │
│        │ q = 2.0 (FDM second-order central differences)       │
│        │ T = {pressure_error, load_error, convergence_rate}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Film thickness h > 0; viscosity μ > 0; grid covers bearing | PASS |
| S2 | Elliptic PDE with Dirichlet/cavitation BC well-posed | PASS |
| S3 | SOR / direct solver converges for discretized system | PASS |
| S4 | Pressure error < 1% vs analytic (short/long bearing) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/reynolds_s1_ideal.yaml
principle_ref: sha256:<p457_hash>
omega:
  description: "Journal bearing, L/D=1, clearance ratio 0.001"
  grid: [100, 50]
  eccentricity: 0.5
E:
  forward: "Reynolds equation, isothermal, incompressible"
  cavitation: "Reynolds (half-Sommerfeld)"
I:
  dataset: LubBench_10
  bearings: 10
  scenario: ideal
O: [pressure_error_pct, load_error_pct]
epsilon:
  pressure_err_max: 1.0
  load_err_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100×50 grid adequate for L/D=1 bearing | PASS |
| S2 | Reynolds BC with cavitation boundary well-defined | PASS |
| S3 | SOR converges in < 500 iterations | PASS |
| S4 | Pressure error < 1% vs Sommerfeld analytic | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_reynolds_s1.yaml
spec_ref: sha256:<spec457_hash>
principle_ref: sha256:<p457_hash>
dataset:
  name: LubBench_10
  bearings: 10
  data_hash: sha256:<dataset_457_hash>
baselines:
  - solver: FDM-SOR
    params: {grid: [100, 50], omega: 1.7}
    results: {pressure_err: 0.5, load_err: 1.0}
  - solver: FEM-Q4
    params: {elements: 2000}
    results: {pressure_err: 0.3, load_err: 0.6}
  - solver: Short-Bearing-Analytic
    params: {}
    results: {pressure_err: 5.0, load_err: 8.0}
quality_scoring:
  - {max_pressure_err: 0.1, Q: 1.00}
  - {max_pressure_err: 0.5, Q: 0.90}
  - {max_pressure_err: 1.5, Q: 0.80}
  - {max_pressure_err: 3.0, Q: 0.75}
```

**Baseline solver:** FDM-SOR — pressure error 0.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pressure Err % | Load Err % | Runtime | Q |
|--------|---------------|-----------|---------|---|
| FDM-SOR | 0.5 | 1.0 | 0.2 s | 0.90 |
| FEM-Q4 | 0.3 | 0.6 | 0.5 s | 0.94 |
| Short-Bearing | 5.0 | 8.0 | 0.001 s | 0.72 |
| FEM-hp | 0.08 | 0.15 | 2.0 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (FEM-hp): 200 × 0.98 = 196 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p457_hash>",
  "h_s": "sha256:<spec457_hash>",
  "h_b": "sha256:<bench457_hash>",
  "r": {"pressure_err": 0.08, "error_bound": 1.0, "ratio": 0.08},
  "c": {"method": "FEM-hp", "elements": 5000, "K": 3},
  "Q": 0.98,
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
| L4 Solution | — | 150–196 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep hydrodynamic_lubrication
pwm-node verify robotics/reynolds_s1_ideal.yaml
pwm-node mine robotics/reynolds_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
