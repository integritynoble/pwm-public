# Principle #462 — Enhanced Oil Recovery (EOR) Modeling

**Domain:** Petroleum Engineering | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [N.darcy] --> [∂.space] --> [N.pointwise] --> [B.well] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.darcy-->∂.x-->N.pw-->B.well  EOR-model  polymer-flood  FIM+chemistry
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ENHANCED OIL RECOVERY MODELING P = (E,G,W,C) Principle #462    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂(φ S_α ρ_α C_{iα})/∂t + ∇·(ρ_α C_{iα} u_α) = R_i  │
│        │ u_α = −(k k_{rα}/μ_α(C))(∇p − ρ_α g∇D)              │
│        │ μ_w(C_p) = μ_w0(1 + a_p C_p + b_p C_p²) (polymer)    │
│        │ σ(C_s) → k_r(N_c) via CDC  (surfactant)               │
│        │ Forward: given injection strategy → recovery R_F(t)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.darcy] ──→ [∂.x] ──→ [N.pw] ──→ [B.well]  │
│        │  time-step  Darcy-flux  spatial  chemistry  well-BC    │
│        │ V={∂.t,N.darcy,∂.x,N.pw,B.well}  A={∂.t→N.darcy,N.darcy→∂.x,∂.x→N.pw,N.pw→B.well}  L_DAG=4.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (weak solutions for transport + reaction)│
│        │ Uniqueness: YES under monotone flux with bounded conc. │
│        │ Stability: CFL on transport; implicit for reactions    │
│        │ Mismatch: adsorption isotherm, viscosity model errors  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |R_F − R_F_ref|/R_F_ref  (recovery factor error)  │
│        │ q = 1.0 (upwind), 2.0 (TVD/MUSCL)                    │
│        │ T = {recovery_error, concentration_L2, mat_balance}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Species conservation + Darcy consistent; concentration bounded [0,1] | PASS |
| S2 | Monotone flux with bounded reaction terms ensures well-posedness | PASS |
| S3 | IMPES-transport + implicit chemistry converges for polymer flood | PASS |
| S4 | Recovery factor error bounded by grid refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# eor_model/polymer_flood_s1.yaml
principle_ref: sha256:<p462_hash>
omega:
  grid: [60, 60, 1]
  domain: quarter_five_spot
  time: [0, 3650.0]   # 10 years
  dt: 10.0
E:
  forward: "multiphase transport + polymer viscosity + adsorption"
  species: [polymer]
  viscosity_model: modified_Flory
  adsorption: Langmuir
B:
  injector: {rate: 500 STB/d, polymer_conc: 1500 ppm}
  producer: {type: BHP, value: 3000 psi}
I:
  scenario: polymer_flood_quarter_5spot
  grid_sizes: [30x30, 60x60, 120x120]
O: [recovery_factor, polymer_breakthrough_time, pressure_L2]
epsilon:
  recovery_error_max: 2.0e-2
  material_balance_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Quarter five-spot standard; dt=10 d with CFL check on transport | PASS |
| S2 | Polymer concentration bounded; adsorption isotherm monotone | PASS |
| S3 | Operator-split (transport then chemistry) converges | PASS |
| S4 | Recovery factor error < 2% on fine grid | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# eor_model/benchmark_polymer.yaml
spec_ref: sha256:<spec462_hash>
principle_ref: sha256:<p462_hash>
dataset:
  name: Polymer_flood_5spot_reference
  reference: "SPE 10th CSP polymer flood (Lake, 2014)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: IMPES-upwind
    params: {grid: 60x60, dt: 10d}
    results: {recovery_error: 3.5e-2, breakthrough_error: 8.1e-2}
  - solver: FIM-TVD
    params: {grid: 60x60, dt: 10d}
    results: {recovery_error: 1.8e-2, breakthrough_error: 4.2e-2}
  - solver: FIM-TVD (fine)
    params: {grid: 120x120, dt: 5d}
    results: {recovery_error: 5.5e-3, breakthrough_error: 1.1e-2}
quality_scoring:
  - {min_err: 3.0e-3, Q: 1.00}
  - {min_err: 1.0e-2, Q: 0.90}
  - {min_err: 2.0e-2, Q: 0.80}
  - {min_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FIM-TVD (60×60) — recovery error 1.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Recovery Error | BT Error | Runtime | Q |
|--------|---------------|----------|---------|---|
| IMPES-upwind | 3.5e-2 | 8.1e-2 | 15 s | 0.75 |
| FIM-TVD (60×60) | 1.8e-2 | 4.2e-2 | 55 s | 0.80 |
| FIM-TVD (120×120) | 5.5e-3 | 1.1e-2 | 380 s | 0.90 |
| FIM-TVD (240×240) | 1.8e-3 | 3.2e-3 | 2800 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (finest): 400 × 1.00 = 400 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p462_hash>",
  "h_s": "sha256:<spec462_hash>",
  "h_b": "sha256:<bench462_hash>",
  "r": {"residual_norm": 1.8e-3, "error_bound": 2.0e-2, "ratio": 0.090},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep eor_model
pwm-node verify eor_model/polymer_flood_s1.yaml
pwm-node mine eor_model/polymer_flood_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
