# Principle #398 — Cable Equation (Neural)

**Domain:** Computational Biology | **Carrier:** membrane potential | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → ∂.space.laplacian → L.circuit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→L.circuit      cable-eq     passive-dendrite  CN/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CABLE EQUATION (NEURAL)        P = (E,G,W,C)   Principle #398  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ τ_m ∂V/∂t = λ² ∂²V/∂x² − V + R_m I_ext(x,t)        │
│        │ τ_m = R_m C_m (membrane time constant)                 │
│        │ λ = √(R_m d / 4R_i) (electrotonic length constant)    │
│        │ V = membrane potential deviation from rest              │
│        │ Forward: given I_ext(x,t), geometry → V(x,t)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [L.circuit]       │
│        │ derivative  derivative  linear-op                      │
│        │ V={∂.time, ∂.space.laplacian, L.circuit}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→L.circuit}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear parabolic PDE)                  │
│        │ Uniqueness: YES (unique for given IC/BC)               │
│        │ Stability: YES (dissipative; exponential decay)        │
│        │ Mismatch: membrane resistance, dendritic diameter       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖V−V_ref‖/‖V_ref‖              │
│        │ q = 2.0 (Crank-Nicolson), 2.0 (FEM-linear)           │
│        │ T = {V_error, decay_time_error, K_resolutions}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Voltage and cable parameters dimensionally consistent | PASS |
| S2 | Linear parabolic PDE — unique solution by standard theory | PASS |
| S3 | Crank-Nicolson unconditionally stable; O(h² + dt²) convergence | PASS |
| S4 | L2 error computable against analytic Green's function solution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cable_equation/passive_dendrite_s1_ideal.yaml
principle_ref: sha256:<p398_hash>
omega:
  grid: [200]
  domain: dendrite_1D
  length: 1000   # um
  time: [0, 50.0]   # ms
  dt: 0.025   # ms
E:
  forward: "τ_m ∂V/∂t = λ² ∂²V/∂x² − V + R_m I_ext"
  tau_m: 10.0   # ms
  lambda_: 200.0   # um
B:
  ends: {sealed: true}   # dV/dx = 0
  initial: {V0: 0.0}
I:
  scenario: current_pulse_injection
  I_ext: {location: center, amplitude: 1.0, duration: 1.0}
  mesh_sizes: [50, 100, 200]
O: [V_L2_error, peak_attenuation_error]
epsilon:
  V_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 nodes over 1 mm; dt=0.025 ms stable for CN | PASS |
| S2 | Passive cable with sealed ends — analytic solution exists | PASS |
| S3 | CN scheme converges at O(h² + dt²) | PASS |
| S4 | V error < 10⁻⁴ achievable at h=5 um, dt=0.025 ms | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cable_equation/benchmark_passive.yaml
spec_ref: sha256:<spec398_hash>
principle_ref: sha256:<p398_hash>
dataset:
  name: Rall_cable_analytic
  reference: "Rall (1969) analytical cable solutions"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {N: 100, dt: 0.01}
    results: {V_error: 1.5e-3, attenuation_err: 3.0e-3}
  - solver: Crank-Nicolson
    params: {N: 100, dt: 0.025}
    results: {V_error: 2.8e-4, attenuation_err: 5.5e-4}
  - solver: FEM-quadratic
    params: {N: 50, dt: 0.025}
    results: {V_error: 1.2e-5, attenuation_err: 2.0e-5}
quality_scoring:
  - {min_V_err: 1.0e-5, Q: 1.00}
  - {min_V_err: 1.0e-4, Q: 0.90}
  - {min_V_err: 1.0e-3, Q: 0.80}
  - {min_V_err: 5.0e-3, Q: 0.75}
```

**Baseline solver:** Crank-Nicolson — V error 2.8×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | V L2 Error | Attenuation Error | Runtime | Q |
|--------|-----------|-------------------|---------|---|
| Forward-Euler | 1.5e-3 | 3.0e-3 | 0.1 s | 0.80 |
| Crank-Nicolson | 2.8e-4 | 5.5e-4 | 0.2 s | 0.90 |
| FEM-quadratic | 1.2e-5 | 2.0e-5 | 0.3 s | 1.00 |

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
  "h_p": "sha256:<p398_hash>",
  "h_s": "sha256:<spec398_hash>",
  "h_b": "sha256:<bench398_hash>",
  "r": {"V_error": 1.2e-5, "attenuation_err": 2.0e-5, "ratio": 0.12},
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
pwm-node benchmarks | grep cable_equation
pwm-node verify AE_computational_biology/cable_equation_s1_ideal.yaml
pwm-node mine AE_computational_biology/cable_equation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
