# Principle #224 — Fatigue Life Prediction (Paris Law)

**Domain:** Structural Mechanics | **Carrier:** N/A (ODE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.pointwise.paris] --> [L.stiffness] --> [N.sif] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.pointwise.paris→L.stiffness→N.sif Paris-law   CT-specimen-fatigue FEM+ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FATIGUE LIFE PREDICTION (PARIS)   P = (E,G,W,C)  Principle #224│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ da/dN = C (ΔK)^m   (Paris-Erdogan law)                │
│        │ a = crack length, N = cycle count                      │
│        │ ΔK = K_max − K_min = stress intensity factor range     │
│        │ Forward: given a₀/σ/C/m → integrate for a(N), N_f     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.pointwise.paris] --> [L.stiffness] --> [N.sif]│
│        │ cycle-count  Paris-law-update  stiffness-solve  SIF-extract   │
│        │ V={∂.time,N.pointwise.paris,L.stiffness,N.sif}  L_DAG=3.0  │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE initial-value problem; Lipschitz)  │
│        │ Uniqueness: YES (da/dN is smooth function of ΔK)      │
│        │ Stability: sensitive to C, m, and initial crack size   │
│        │ Mismatch: Paris constants (C,m) calibration error      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error |N_f−N_ref|/N_ref (primary)        │
│        │ q = varies (ODE integration order; SIF accuracy)      │
│        │ T = {life_error, da/dN_fit, K_resolutions}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Paris law dimensions consistent [m/cycle vs Pa√m]; C, m positive | PASS |
| S2 | ODE well-posed with positive da/dN; unique a(N) trajectory | PASS |
| S3 | Adaptive RK integration + SIF from handbook converges | PASS |
| S4 | Life prediction error bounded by (C,m) uncertainty propagation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fatigue/ct_specimen_s1_ideal.yaml
principle_ref: sha256:<p224_hash>
omega:
  domain: compact_tension_specimen
  width: 0.05   # m
  thickness: 0.01
E:
  forward: "da/dN = C * (DeltaK)^m"
  C: 3.0e-12    # m/cycle / (Pa√m)^m
  m: 3.0
  K_Ic: 50.0e6   # Pa√m
B:
  loading: {P_max: 5000, R_ratio: 0.1}
  initial_crack: 0.01   # m
I:
  scenario: CT_constant_amplitude
  a0_over_W: [0.2, 0.3, 0.4]
  integration_methods: [RK45, Euler, midpoint]
O: [fatigue_life_N_f, a_vs_N_curve, da_dN_vs_DeltaK]
epsilon:
  life_error_max: 5.0e-2
  curve_L2_error: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | CT geometry SIF from ASTM E647; Paris constants from literature | PASS |
| S2 | ODE IVP well-posed; a monotonically increasing to a_crit | PASS |
| S3 | RK45 integration converges; SIF from polynomial fit | PASS |
| S4 | Life error < 5% with adaptive integration | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fatigue/benchmark_ct.yaml
spec_ref: sha256:<spec224_hash>
principle_ref: sha256:<p224_hash>
dataset:
  name: CT_fatigue_life
  reference: "ASTM E647 standard + analytical integration of Paris law"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Euler (N_steps=100)
    params: {method: Euler, steps: 100}
    results: {life_error: 8.5e-2}
  - solver: RK4 (N_steps=100)
    params: {method: RK4, steps: 100}
    results: {life_error: 2.0e-3}
  - solver: RK45-adaptive
    params: {method: RK45, tol: 1e-6}
    results: {life_error: 5.0e-5}
quality_scoring:
  - {min_err: 1.0e-4, Q: 1.00}
  - {min_err: 1.0e-3, Q: 0.95}
  - {min_err: 1.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
```

**Baseline solver:** RK4 — life error 2.0×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Life Error | a(N) L2 Err | Runtime | Q |
|--------|------------|-------------|---------|---|
| Euler (100 steps) | 8.5e-2 | 5.0e-2 | 0.01 s | 0.80 |
| RK4 (100 steps) | 2.0e-3 | 1.0e-3 | 0.01 s | 0.95 |
| RK45-adaptive | 5.0e-5 | 2.0e-5 | 0.02 s | 1.00 |
| Analytical (m=3) | 0.0 | 0.0 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (analytical): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.80 = 240 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p224_hash>",
  "h_s": "sha256:<spec224_hash>",
  "h_b": "sha256:<bench224_hash>",
  "r": {"residual_norm": 5.0e-5, "error_bound": 5.0e-2, "ratio": 0.001},
  "c": {"fitted_rate": 4.0, "theoretical_rate": 4.0, "K": 3},
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
| L4 Solution | — | 240–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep fatigue_paris
pwm-node verify fatigue/ct_specimen_s1_ideal.yaml
pwm-node mine fatigue/ct_specimen_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
