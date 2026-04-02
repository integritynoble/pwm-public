# Principle #465 — Well Productivity Index

**Domain:** Petroleum Engineering | **Carrier:** N/A (analytical/numerical) | **Difficulty:** Basic (δ=2)
**DAG:** [∂.space] --> [L.sparse] --> [B.well] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.x-->L.sparse-->B.well  WellPI  Peaceman-bench  analytical+FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WELL PRODUCTIVITY INDEX   P = (E,G,W,C)   Principle #465       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ q = J (p̄_R − p_wf)   (PI definition)                  │
│        │ J = 2πkh / (μB ln(r_e/r_w) + S)   (radial steady)     │
│        │ Peaceman: r_0 = 0.28√(Δx² + Δy²) · (k_y/k_x)^¼ …    │
│        │   (equivalent well-block radius for numerical grids)    │
│        │ Forward: given (k,h,μ,r_w,S,grid) → J, q               │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.x] ──→ [L.sparse] ──→ [B.well]                      │
│        │  radial-flow  FD-disc  well-BC                         │
│        │ V={∂.x,L.sparse,B.well}  A={∂.x→L.sparse,L.sparse→B.well}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytical for radial flow)            │
│        │ Uniqueness: YES for given reservoir/well parameters    │
│        │ Stability: sensitive to skin factor S and r_w           │
│        │ Mismatch: non-Darcy near wellbore, partial penetration │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |J_num − J_exact|/J_exact  (PI error)              │
│        │ q = 2.0 (grid refinement → Peaceman limit)            │
│        │ T = {PI_error, rate_error, pressure_drawdown_error}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PI J > 0 for physical parameters; units consistent | PASS |
| S2 | Radial solution exact; Peaceman correction well-defined | PASS |
| S3 | Numerical PI converges to analytical with grid refinement | PASS |
| S4 | PI error bounded by O(h²) with Peaceman well model | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# well_pi/peaceman_s1_ideal.yaml
principle_ref: sha256:<p465_hash>
omega:
  grid: [21, 21, 1]
  domain: single_well_radial
  well_location: center
E:
  forward: "Darcy radial flow + Peaceman well model"
  permeability: 100.0    # mD
  thickness: 10.0        # m
  viscosity: 1.0         # cP
  r_w: 0.1               # m
B:
  outer: {type: constant_pressure, value: 300 bar}
  well: {type: BHP, value: 250 bar}
I:
  scenario: steady_radial_flow
  grid_sizes: [11x11, 21x21, 41x41, 81x81]
O: [PI_error, rate_error, pressure_profile_L2]
epsilon:
  PI_error_max: 2.0e-2
  rate_error_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 21×21 with well at center; r_w well-resolved | PASS |
| S2 | Steady radial flow has unique analytical solution | PASS |
| S3 | TPFA + Peaceman converges with grid refinement | PASS |
| S4 | PI error < 2% on 41×41 grid | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# well_pi/benchmark_peaceman.yaml
spec_ref: sha256:<spec465_hash>
principle_ref: sha256:<p465_hash>
dataset:
  name: Peaceman_well_model_validation
  reference: "Peaceman (1978, 1983) equivalent radius"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TPFA (no Peaceman)
    params: {grid: 21x21}
    results: {PI_error: 0.35, rate_error: 0.35}
  - solver: TPFA + Peaceman
    params: {grid: 21x21}
    results: {PI_error: 1.8e-2, rate_error: 1.9e-2}
  - solver: TPFA + Peaceman (fine)
    params: {grid: 81x81}
    results: {PI_error: 4.2e-3, rate_error: 4.5e-3}
quality_scoring:
  - {min_err: 2.0e-3, Q: 1.00}
  - {min_err: 1.0e-2, Q: 0.90}
  - {min_err: 2.0e-2, Q: 0.80}
  - {min_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** TPFA + Peaceman (21×21) — PI error 1.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PI Error | Rate Error | Runtime | Q |
|--------|----------|------------|---------|---|
| TPFA (no Peaceman) | 0.35 | 0.35 | 0.1 s | 0.75 |
| TPFA + Peaceman (21²) | 1.8e-2 | 1.9e-2 | 0.2 s | 0.80 |
| TPFA + Peaceman (41²) | 8.5e-3 | 9.0e-3 | 0.5 s | 0.90 |
| TPFA + Peaceman (81²) | 4.2e-3 | 4.5e-3 | 2.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (fine): 200 × 1.00 = 200 PWM
Floor:            200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p465_hash>",
  "h_s": "sha256:<spec465_hash>",
  "h_b": "sha256:<bench465_hash>",
  "r": {"PI_error": 4.2e-3, "error_bound": 2.0e-2, "ratio": 0.210},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 4},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep well_pi
pwm-node verify well_pi/peaceman_s1_ideal.yaml
pwm-node mine well_pi/peaceman_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
