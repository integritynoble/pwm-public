# Principle #193 — Stefan Problem (Solidification/Melting)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [∂.space.laplacian] --> [N.stefan] --> [B.interface] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.stefan→B.interface      Stefan      freezing-1D       FEM/enthalpy
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STEFAN PROBLEM   P = (E,G,W,C)   Principle #193                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂T/∂t = α∇²T  in each phase (solid/liquid)           │
│        │ T = T_m on interface Γ(t)  (melting temperature)       │
│        │ ρL ds/dt = k_l ∂T_l/∂n − k_s ∂T_s/∂n  (Stefan cond.)│
│        │ s(t) = interface position (free boundary)              │
│        │ Forward: IC/BC/L/k → solve T(x,t) + s(t)             │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space.laplacian] --> [N.stefan] --> [B.interface]│
│        │ time  heat-diffusion  interface-track  phase-BC                  │
│        │ V={∂.time,∂.space.laplacian,N.stefan,B.interface}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Neumann similarity solution in 1D)    │
│        │ Uniqueness: YES for one-phase; conditions for two-phase│
│        │ Stability: interface velocity bounded by heat flux     │
│        │ Mismatch: latent heat L error, thermal conductivity   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = interface position error, temperature L2 error     │
│        │ q = 1.0 (enthalpy method), 2.0 (front-tracking FEM) │
│        │ T = {interface_error, T_profile_error, energy_balance}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stefan condition couples heat flux to interface speed; energy conserved | PASS |
| S2 | Neumann similarity solution provides analytical benchmark | PASS |
| S3 | Enthalpy method / front-tracking converges with mesh refinement | PASS |
| S4 | Interface position error bounded by h (enthalpy) or h² (FEM) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# stefan/freezing_1d_s1.yaml
principle_ref: sha256:<p193_hash>
omega:
  grid: [200]
  domain: [0, 1]
  time: [0, 1.0]
E:
  forward: "∂T/∂t = α∇²T + Stefan interface condition"
  T_melt: 0.0
  L: 334000   # J/kg (water)
  k: {solid: 2.22, liquid: 0.6}
  alpha: {solid: 1.17e-6, liquid: 1.43e-7}
B:
  left: {T: -10.0}   # cold wall
  right: {T: 5.0}     # warm liquid
  IC: {T: 5.0, interface: 0.0}
I:
  scenario: one_phase_freezing
  Stefan_number: 0.15
  mesh_sizes: [50, 100, 200]
O: [interface_position_error, T_L2_error, energy_balance]
epsilon:
  interface_error_max: 5.0e-3
  T_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D grid; Stefan number 0.15 physically reasonable | PASS |
| S2 | Neumann exact similarity solution exists for one-phase | PASS |
| S3 | Enthalpy method converges; interface captured within 1-2 cells | PASS |
| S4 | Interface error < 5×10⁻³ at N=200 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# stefan/benchmark_freezing.yaml
spec_ref: sha256:<spec193_hash>
principle_ref: sha256:<p193_hash>
dataset:
  name: Neumann_exact_solution
  reference: "Carslaw & Jaeger (1959) similarity solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Enthalpy method (explicit)
    params: {N: 200, dt: 1e-4}
    results: {interface_err: 3.8e-3, T_error: 8.2e-3}
  - solver: Front-tracking FEM
    params: {N: 100}
    results: {interface_err: 1.5e-3, T_error: 3.1e-3}
  - solver: Level-set Stefan
    params: {N: 200}
    results: {interface_err: 1.2e-3, T_error: 2.5e-3}
quality_scoring:
  - {min_intf_err: 5.0e-4, Q: 1.00}
  - {min_intf_err: 2.0e-3, Q: 0.90}
  - {min_intf_err: 5.0e-3, Q: 0.80}
  - {min_intf_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Front-tracking FEM — interface error 1.5×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Interface Err | T Error | Runtime | Q |
|--------|-------------|---------|---------|---|
| Enthalpy (explicit) | 3.8e-3 | 8.2e-3 | 5 s | 0.80 |
| Front-tracking FEM | 1.5e-3 | 3.1e-3 | 8 s | 0.90 |
| Level-set Stefan | 1.2e-3 | 2.5e-3 | 10 s | 0.90 |
| Adaptive FEM | 4.2e-4 | 8.5e-4 | 15 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (adaptive): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p193_hash>",
  "h_s": "sha256:<spec193_hash>",
  "h_b": "sha256:<bench193_hash>",
  "r": {"residual_norm": 4.2e-4, "error_bound": 5.0e-3, "ratio": 0.084},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep stefan
pwm-node verify stefan/freezing_1d_s1.yaml
pwm-node mine stefan/freezing_1d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
