# Principle #478 — Colloidal Interactions (DLVO Theory)

**Domain:** Polymer Physics / Colloid Science | **Carrier:** N/A (model-based) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [L.dense] --> [∫.volume] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->L.dense-->∫.vol  DLVO  colloid-stability  PB+vdW
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COLLOIDAL INTERACTIONS (DLVO)  P = (E,G,W,C)  Principle #478  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V_DLVO(h) = V_vdW(h) + V_EDL(h)                       │
│        │ V_vdW = −A_H R/(12h)  (van der Waals, sphere-flat)    │
│        │ V_EDL = 64πRn_∞k_BT/κ² · γ² exp(−κh)  (double-layer) │
│        │ κ = √(2n_∞e²/(ε₀ε_r k_BT))  (Debye length⁻¹)        │
│        │ Forward: given (A_H,R,ψ₀,κ) → V(h), stability ratio  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [L.dense] ──→ [∫.vol]                       │
│        │  DLVO-force  pair-sum  volume-integ                    │
│        │ V={N.pw,L.dense,∫.vol}  A={N.pw→L.dense,L.dense→∫.vol}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (algebraic for linearized PB)           │
│        │ Uniqueness: YES for given Hamaker + surface potential  │
│        │ Stability: barrier height determines CCC               │
│        │ Mismatch: non-DLVO forces (hydration, steric, depletion)│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |CCC_pred − CCC_expt|/CCC_expt  (CCC error)      │
│        │ q = N/A (analytical + numerical PB)                   │
│        │ T = {barrier_height, CCC_error, W_stability_ratio}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Potential V(h) → 0 as h → ∞; units consistent (J) | PASS |
| S2 | Linearized PB valid for ψ₀ < 25 mV; exact for Derjaguin approx | PASS |
| S3 | Direct evaluation + nonlinear PB solver converge | PASS |
| S4 | CCC prediction within factor of 2 for monovalent salts | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dlvo/colloid_stability_s1.yaml
principle_ref: sha256:<p478_hash>
omega:
  separations: 1000
  domain: sphere_sphere
  h_range: [0.1e-9, 100e-9]
E:
  forward: "DLVO: V_vdW + V_EDL (nonlinear PB)"
  A_H: 1.0e-20       # J (Hamaker constant)
  radius: 100e-9      # m
  psi_0: 25e-3        # V (surface potential)
B:
  electrolyte: [NaCl, CaCl2]
  concentrations: [1e-4, 1e-3, 1e-2, 0.1, 1.0]   # M
I:
  scenario: CCC_determination
  models: [linearized_PB, nonlinear_PB, constant_charge]
O: [barrier_height, CCC, stability_ratio_W]
epsilon:
  CCC_error_max: 0.50    # factor
  barrier_error_max: 0.30  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1000 separations log-spaced; R=100 nm standard | PASS |
| S2 | ψ₀=25 mV within linearized PB validity for check | PASS |
| S3 | Nonlinear PB + vdW evaluate for all concentrations | PASS |
| S4 | CCC within factor 2 of Schulze-Hardy rule | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dlvo/benchmark_ccc.yaml
spec_ref: sha256:<spec478_hash>
principle_ref: sha256:<p478_hash>
dataset:
  name: CCC_experimental_data
  reference: "Elimelech et al. (1995) colloid stability measurements"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linearized PB + non-retarded vdW
    params: {PB: linearized, retardation: none}
    results: {CCC_error: 0.45, barrier_error: 0.30}
  - solver: Nonlinear PB + retarded vdW
    params: {PB: nonlinear, retardation: Casimir_Polder}
    results: {CCC_error: 0.25, barrier_error: 0.15}
  - solver: Full numerical (charge regulation)
    params: {PB: nonlinear, surface: charge_regulation}
    results: {CCC_error: 0.12, barrier_error: 0.08}
quality_scoring:
  - {min_err: 0.10, Q: 1.00}
  - {min_err: 0.20, Q: 0.90}
  - {min_err: 0.35, Q: 0.80}
  - {min_err: 0.50, Q: 0.75}
```

**Baseline solver:** Nonlinear PB + retarded vdW — CCC error 25%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | CCC Error | Barrier Error | Runtime | Q |
|--------|----------|--------------|---------|---|
| Linearized PB | 0.45 | 0.30 | 0.01 s | 0.75 |
| Nonlinear PB | 0.25 | 0.15 | 0.1 s | 0.80 |
| Charge regulation | 0.12 | 0.08 | 1.0 s | 0.90 |
| Extended DLVO (+ hydration) | 0.06 | 0.04 | 5.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (extended): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p478_hash>",
  "h_s": "sha256:<spec478_hash>",
  "h_b": "sha256:<bench478_hash>",
  "r": {"CCC_error": 0.06, "error_bound": 0.50, "ratio": 0.120},
  "c": {"barrier_error": 0.04, "electrolytes": 2, "K": 5},
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
pwm-node benchmarks | grep dlvo
pwm-node verify dlvo/colloid_stability_s1.yaml
pwm-node mine dlvo/colloid_stability_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
