# Principle #450 — Trajectory Optimization

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Research (δ=4)
**DAG:** [∂.time] --> [N.bilinear] --> [O.adjoint] --> [B.contact] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.bilin-->O.adj-->B.cont  TrajOpt  TrajBench-10  DIRCOL/iLQR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TRAJECTORY OPTIMIZATION    P = (E, G, W, C)   Principle #450  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min J = Σ l(x_k, u_k) + l_f(x_N)                     │
│        │ s.t. x_{k+1} = f(x_k, u_k), g(x,u) ≤ 0              │
│        │ Direct collocation or shooting methods                 │
│        │ Inverse: find optimal (x*,u*) satisfying constraints  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.bilin] ──→ [O.adj] ──→ [B.cont]           │
│        │   dynamics  Coriolis  optimal-ctrl  contact             │
│        │ V={∂.t,N.bilin,O.adj,B.cont}  A={∂.t→N.bilin,N.bilin→O.adj,O.adj→B.cont}  L_DAG=3.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (compact feasible set → minimum exists) │
│        │ Uniqueness: local (NLP generally non-convex)           │
│        │ Stability: depends on constraint qualification (LICQ)  │
│        │ Mismatch: model error, discretization, local minima    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = cost suboptimality (primary), constraint viol.     │
│        │ q = NLP-dependent (IPOPT quadratic convergence)       │
│        │ T = {cost, constraint_violation, KKT_residual}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | State, control, constraint dimensions consistent | PASS |
| S2 | Feasible trajectory exists (start/goal reachable) | PASS |
| S3 | IPOPT/SNOPT converges with warm-start | PASS |
| S4 | Cost and constraint residual computable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/trajopt_s1_ideal.yaml
principle_ref: sha256:<p450_hash>
omega:
  description: "6-DOF arm point-to-point, obstacle avoidance"
  states: 12
  controls: 6
  horizon: 100
E:
  forward: "x_{k+1} = f(x_k, u_k); min sum(u^2)"
  method: "direct collocation (Hermite-Simpson)"
I:
  dataset: TrajBench_10
  problems: 10
  obstacles: {count: 3, type: spheres}
  scenario: ideal
O: [cost, constraint_violation, solve_time]
epsilon:
  constraint_viol_max: 1e-6
  cost_ratio_max: 1.20
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 12 states (q,qdot), 6 controls, 100 knot points | PASS |
| S2 | All problems have feasible paths (verified) | PASS |
| S3 | IPOPT converges within 200 iterations | PASS |
| S4 | Constraint violation < 1e-6 achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_trajopt_s1.yaml
spec_ref: sha256:<spec450_hash>
principle_ref: sha256:<p450_hash>
dataset:
  name: TrajBench_10
  problems: 10
  data_hash: sha256:<dataset_450_hash>
baselines:
  - solver: DIRCOL-IPOPT
    params: {collocation: hermite_simpson}
    results: {cost: 12.5, viol: 1e-8}
  - solver: iLQR
    params: {iterations: 100}
    results: {cost: 13.2, viol: 1e-4}
  - solver: RRT-Shortcut
    params: {samples: 5000}
    results: {cost: 18.0, viol: 0}
quality_scoring:
  - {max_cost: 11.0, Q: 1.00}
  - {max_cost: 13.0, Q: 0.90}
  - {max_cost: 16.0, Q: 0.80}
  - {max_cost: 20.0, Q: 0.75}
```

**Baseline solver:** DIRCOL-IPOPT — cost 12.5
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Cost | Violation | Runtime | Q |
|--------|------|----------|---------|---|
| DIRCOL-IPOPT | 12.5 | 1e-8 | 2.0 s | 0.92 |
| iLQR | 13.2 | 1e-4 | 0.5 s | 0.88 |
| RRT-Shortcut | 18.0 | 0 | 1.0 s | 0.78 |
| DDP-AL | 11.8 | 1e-7 | 1.5 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (DDP-AL): 400 × 0.95 = 380 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p450_hash>",
  "h_s": "sha256:<spec450_hash>",
  "h_b": "sha256:<bench450_hash>",
  "r": {"cost": 11.8, "constraint_viol": 1e-7, "ratio": 0.93},
  "c": {"method": "DDP-AL", "iterations": 80, "K": 3},
  "Q": 0.95,
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
| L4 Solution | — | 300–380 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep trajectory_optimization
pwm-node verify robotics/trajopt_s1_ideal.yaml
pwm-node mine robotics/trajopt_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
