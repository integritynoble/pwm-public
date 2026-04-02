# Principle #456 — Rotor Dynamics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=3)
**DAG:** [L.dense] --> [E.hermitian] --> [∂.time] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.dense-->E.herm-->∂.t  RotDyn  RotBench-10  FEM/Campbell
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ROTOR DYNAMICS             P = (E, G, W, C)   Principle #456  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ M q̈ + (C + Ω G) q̇ + K q = F_unb(Ω,t) + F_bearing   │
│        │ G = gyroscopic matrix (skew-symmetric)                │
│        │ Campbell diagram: natural freq. vs spin speed Ω       │
│        │ Inverse: identify unbalance and bearing params        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.dense] ──→ [E.herm] ──→ [∂.t]                       │
│        │   mass/stiffness  eigenmodes  integration               │
│        │ V={L.dense,E.herm,∂.t}  A={L.dense→E.herm,E.herm→∂.t}  L_DAG=2.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE system)                     │
│        │ Uniqueness: YES (M SPD, unique eigenvalues)            │
│        │ Stability: critical speeds cause resonance             │
│        │ Mismatch: nonlinear bearings, cracks, thermal growth   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = vibration amplitude error (primary), freq. error   │
│        │ q = exact (eigenvalue problem)                        │
│        │ T = {amplitude_error, frequency_error, critical_speed} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | M, C, G, K matrix dimensions consistent; Ω range physical | PASS |
| S2 | M SPD; eigenvalue problem well-posed at each Ω | PASS |
| S3 | QZ algorithm converges for generalized eigenvalue problem | PASS |
| S4 | Vibration amplitude and critical speeds computable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/rotor_dynamics_s1_ideal.yaml
principle_ref: sha256:<p456_hash>
omega:
  description: "Jeffcott rotor, 2 bearings, Ω range 0-10000 RPM"
  nodes: 20
  dof: 80
E:
  forward: "M*q_ddot + (C+Omega*G)*q_dot + K*q = F"
  analysis: "Campbell diagram + unbalance response"
I:
  dataset: RotBench_10
  rotors: 10
  scenario: ideal
O: [critical_speed_error_pct, amplitude_error_pct]
epsilon:
  crit_speed_err_max: 2.0
  amplitude_err_max: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20-node FE model; 80 DOF consistent | PASS |
| S2 | Gyroscopic matrix properly skew-symmetric | PASS |
| S3 | Eigenvalue solver converges for all Ω | PASS |
| S4 | Critical speed error < 2% feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_rotor_s1.yaml
spec_ref: sha256:<spec456_hash>
principle_ref: sha256:<p456_hash>
dataset:
  name: RotBench_10
  rotors: 10
  data_hash: sha256:<dataset_456_hash>
baselines:
  - solver: FEM-Timoshenko
    params: {elements: 20}
    results: {crit_err: 0.5, amp_err: 2.0}
  - solver: Transfer-Matrix
    params: {}
    results: {crit_err: 0.8, amp_err: 3.5}
  - solver: Lumped-Mass
    params: {nodes: 5}
    results: {crit_err: 3.0, amp_err: 8.0}
quality_scoring:
  - {max_crit_err: 0.3, Q: 1.00}
  - {max_crit_err: 0.8, Q: 0.90}
  - {max_crit_err: 2.0, Q: 0.80}
  - {max_crit_err: 5.0, Q: 0.75}
```

**Baseline solver:** FEM-Timoshenko — critical speed error 0.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Crit Speed Err % | Amp Err % | Runtime | Q |
|--------|-----------------|----------|---------|---|
| FEM-Timoshenko | 0.5 | 2.0 | 1.0 s | 0.92 |
| Transfer Matrix | 0.8 | 3.5 | 0.1 s | 0.90 |
| Lumped Mass | 3.0 | 8.0 | 0.01 s | 0.78 |
| FEM-hp Refined | 0.2 | 0.8 | 5.0 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (hp):    300 × 0.98 = 294 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p456_hash>",
  "h_s": "sha256:<spec456_hash>",
  "h_b": "sha256:<bench456_hash>",
  "r": {"crit_speed_err": 0.2, "error_bound": 2.0, "ratio": 0.10},
  "c": {"method": "FEM-hp", "elements": 40, "K": 3},
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
| L4 Solution | — | 225–294 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep rotor_dynamics
pwm-node verify robotics/rotor_dynamics_s1_ideal.yaml
pwm-node mine robotics/rotor_dynamics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
