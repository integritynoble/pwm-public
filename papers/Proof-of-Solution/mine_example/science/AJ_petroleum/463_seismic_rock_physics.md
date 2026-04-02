# Principle #463 — Seismic-to-Reservoir (Rock Physics)

**Domain:** Petroleum Engineering | **Carrier:** N/A (model-based) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [L.mix] --> [O.bayesian] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->L.mix-->O.bayes  RockPhys  Gassmann-bench  Bayesian-inv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEISMIC-TO-RESERVOIR (ROCK PHYSICS)  P = (E,G,W,C) Princ. #463│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ K_sat = K_dry + (1−K_dry/K_m)² /                      │
│        │        (φ/K_fl + (1−φ)/K_m − K_dry/K_m²)  (Gassmann)  │
│        │ V_p = √((K_sat + 4G/3)/ρ_b),  V_s = √(G/ρ_b)         │
│        │ ρ_b = (1−φ)ρ_m + φ(S_w ρ_w + S_o ρ_o)                │
│        │ Forward: given (φ,S,K_dry,K_m,K_fl) → (V_p,V_s,ρ)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [L.mix] ──→ [O.bayes]                       │
│        │  rock-model  mixing-law  inversion                     │
│        │ V={N.pw,L.mix,O.bayes}  A={N.pw→L.mix,L.mix→O.bayes}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Gassmann algebraic; well-defined)      │
│        │ Uniqueness: YES forward; inverse requires constraints  │
│        │ Stability: sensitive to K_dry/K_m ratio near 1         │
│        │ Mismatch: patchy vs uniform saturation, frequency      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |V_p − V_p_meas|/V_p_meas  (velocity error)       │
│        │ q = N/A (algebraic model)                             │
│        │ T = {velocity_error, impedance_error, AVO_fit}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Moduli positive; velocities real-valued for physical parameters | PASS |
| S2 | Gassmann well-defined when K_dry < K_m and φ > 0 | PASS |
| S3 | Direct evaluation + Bayesian inversion for reservoir properties | PASS |
| S4 | Velocity prediction within 2-5% of lab ultrasonic data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rock_phys/gassmann_s1_ideal.yaml
principle_ref: sha256:<p463_hash>
omega:
  samples: 200
  domain: sandstone_reservoir
E:
  forward: "Gassmann fluid substitution + Hertz-Mindlin dry frame"
  minerals: [quartz, feldspar, clay]
  fluids: [brine, oil, gas]
B:
  porosity_range: [0.05, 0.35]
  pressure_range: [10, 50]   # MPa
I:
  scenario: fluid_substitution_sandstone
  noise_levels: [0.0, 0.02, 0.05]
O: [Vp_error, Vs_error, impedance_error]
epsilon:
  Vp_error_max: 3.0e-2
  impedance_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 samples span porosity/saturation space; physical bounds | PASS |
| S2 | Gassmann well-posed for sandstone K_dry < K_quartz | PASS |
| S3 | Forward model evaluates in O(N) per sample | PASS |
| S4 | Vp error < 3% achievable with calibrated dry-frame model | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# rock_phys/benchmark_gassmann.yaml
spec_ref: sha256:<spec463_hash>
principle_ref: sha256:<p463_hash>
dataset:
  name: Han_sandstone_dataset
  reference: "Han et al. (1986) ultrasonic velocity measurements"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gassmann-direct
    params: {dry_frame: Hertz_Mindlin, coordination: 8}
    results: {Vp_error: 4.2e-2, Vs_error: 5.1e-2}
  - solver: Gassmann + pressure-dependent
    params: {dry_frame: modified_HM, coordination: fitted}
    results: {Vp_error: 2.5e-2, Vs_error: 3.1e-2}
  - solver: Bayesian calibrated
    params: {MCMC_samples: 10000}
    results: {Vp_error: 1.2e-2, Vs_error: 1.8e-2}
quality_scoring:
  - {min_err: 1.0e-2, Q: 1.00}
  - {min_err: 2.0e-2, Q: 0.90}
  - {min_err: 4.0e-2, Q: 0.80}
  - {min_err: 6.0e-2, Q: 0.75}
```

**Baseline solver:** Gassmann + pressure-dependent — Vp error 2.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Vp Error | Vs Error | Runtime | Q |
|--------|----------|----------|---------|---|
| Gassmann-direct | 4.2e-2 | 5.1e-2 | 0.1 s | 0.75 |
| Gassmann + pressure | 2.5e-2 | 3.1e-2 | 0.2 s | 0.80 |
| Bayesian calibrated | 1.2e-2 | 1.8e-2 | 60 s | 0.90 |
| Full Bayesian + patchy | 8.5e-3 | 1.2e-2 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p463_hash>",
  "h_s": "sha256:<spec463_hash>",
  "h_b": "sha256:<bench463_hash>",
  "r": {"Vp_error": 8.5e-3, "error_bound": 3.0e-2, "ratio": 0.283},
  "c": {"R2_fit": 0.96, "samples": 200, "K": 3},
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
pwm-node benchmarks | grep rock_phys
pwm-node verify rock_phys/gassmann_s1_ideal.yaml
pwm-node mine rock_phys/gassmann_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
