# Principle #500 — Optimal Experimental Design

**Domain:** Optimization | **Carrier:** N/A (statistical) | **Difficulty:** Standard (δ=3)
**DAG:** [L.state] --> [S.observation] --> [O.bayesian] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state-->S.obs-->O.bayes  OED  sensor-placement  convex/greedy
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OPTIMAL EXPERIMENTAL DESIGN   P = (E,G,W,C)  Principle #500   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min_ξ Φ(M(ξ))   s.t. ξ ∈ Ξ  (design measure)        │
│        │ M(ξ) = Σ_i ξ_i f(x_i)f(x_i)ᵀ  (Fisher info matrix) │
│        │ A-optimal: Φ = tr(M⁻¹)   (minimize avg variance)     │
│        │ D-optimal: Φ = −log det(M)  (max info determinant)    │
│        │ Forward: given model + candidates → optimal design ξ*  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [S.obs] ──→ [O.bayes]                    │
│        │  FIM-build  sensor-select  design-opt                  │
│        │ V={L.state,S.obs,O.bayes}  A={L.state→S.obs,S.obs→O.bayes}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (compact Ξ → minimum exists)           │
│        │ Uniqueness: YES for D-optimal (log-concave)            │
│        │ Stability: Φ continuous in ξ; Kiefer-Wolfowitz theorem │
│        │ Mismatch: model misspecification, nonlinear models     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Φ(ξ)/Φ(ξ*)  (efficiency ratio)                    │
│        │ q = N/A (combinatorial / convex relaxation)           │
│        │ T = {efficiency, variance_reduction, design_points}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Fisher information M SPD when design has full support | PASS |
| S2 | D-optimality: log det concave → unique global optimum | PASS |
| S3 | Fedorov exchange / SDP relaxation converges | PASS |
| S4 | Efficiency > 95% of continuous D-optimal | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# oed/sensor_placement_s1.yaml
principle_ref: sha256:<p500_hash>
omega:
  candidates: 100
  domain: 2D_heat_source_localization
  parameters: 4   # (x_s, y_s, strength, background)
E:
  forward: "linear model y = F(x)θ + ε → Fisher info → criterion"
  model: steady_state_heat_equation
  criterion: D_optimal
B:
  sensors_to_place: [5, 10, 20]
  noise: {model: iid_Gaussian, sigma: 0.1}
I:
  scenario: sensor_placement_heat_source
  methods: [random, greedy, Fedorov_exchange, SDP_relaxation]
O: [D_efficiency, A_efficiency, parameter_variance]
epsilon:
  D_efficiency_min: 0.90
  variance_reduction_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 candidates, 4 parameters, sensors 5-20; well-defined | PASS |
| S2 | Linear model → FIM exact; D-optimal well-posed | PASS |
| S3 | Fedorov exchange converges within 100 swaps | PASS |
| S4 | D-efficiency > 90% with greedy + exchange | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# oed/benchmark_sensor.yaml
spec_ref: sha256:<spec500_hash>
principle_ref: sha256:<p500_hash>
dataset:
  name: Heat_source_sensor_placement
  reference: "Pukelsheim (2006) Optimal Design of Experiments"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Random placement
    params: {n_sensors: 10, trials: 1000}
    results: {D_efficiency: 0.65, A_efficiency: 0.58}
  - solver: Greedy (D-criterion)
    params: {n_sensors: 10}
    results: {D_efficiency: 0.88, A_efficiency: 0.82}
  - solver: Fedorov exchange
    params: {n_sensors: 10, max_exchanges: 100}
    results: {D_efficiency: 0.95, A_efficiency: 0.91}
quality_scoring:
  - {min_eff: 0.97, Q: 1.00}
  - {min_eff: 0.93, Q: 0.90}
  - {min_eff: 0.88, Q: 0.80}
  - {min_eff: 0.75, Q: 0.75}
```

**Baseline solver:** Greedy (D-criterion) — D-efficiency 88%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | D-Efficiency | A-Efficiency | Runtime | Q |
|--------|-------------|-------------|---------|---|
| Random (best of 1000) | 0.65 | 0.58 | 1 s | 0.75 |
| Greedy | 0.88 | 0.82 | 0.5 s | 0.80 |
| Fedorov exchange | 0.95 | 0.91 | 5 s | 0.90 |
| SDP relaxation + round | 0.98 | 0.96 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SDP): 300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p500_hash>",
  "h_s": "sha256:<spec500_hash>",
  "h_b": "sha256:<bench500_hash>",
  "r": {"D_efficiency": 0.98, "error_bound": 0.90, "ratio": 1.089},
  "c": {"A_efficiency": 0.96, "sensors": 10, "K": 3},
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
pwm-node benchmarks | grep oed
pwm-node verify oed/sensor_placement_s1.yaml
pwm-node mine oed/sensor_placement_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
