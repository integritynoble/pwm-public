# Principle #57 — Arterial Spin Labeling (ASL) MRI

**Domain:** Medical Imaging | **Carrier:** Spin | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix.coil] --> [F.dft] --> [S.kspace] --> [∫.temporal]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix.coil --> F.dft --> S.kspace --> ∫.temporal    ASL-CBF      BrainASL-20       Buxton
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ARTERIAL SPIN LABELING (ASL)   P = (E, G, W, C)  Principle #57│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔM = M_control − M_label = 2·M₀·f·T₁·α·exp(−TI/T₁)  │
│        │ CBF = f = ΔM/(2·M₀·T₁·α·exp(−TI/T₁))               │
│        │ Inverse: quantify cerebral blood flow (CBF) from      │
│        │ control−label difference images using Buxton model     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix.coil] ──→ [F.dft] ──→ [S.kspace] ──→ [∫.temporal]│
│        │  Label   Propagate Encode  Sample   Detect             │
│        │ V={L.mix.coil,F.dft,S.kspace,∫.temporal}  A={L.mix.coil→F.dft, F.dft→S.kspace, S.kspace→∫.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (label/control difference measurable)   │
│        │ Uniqueness: YES (CBF uniquely determined by Buxton eqn)│
│        │ Stability: κ ≈ 12 (multi-average), κ ≈ 40 (single rep)│
│        │ Mismatch: Δ_T₁ (tissue), Δ_ATT (arrival time), Δ_α   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = CBF RMSE mL/100g/min (primary), CoV % (secondary) │
│        │ q = 2.0 (Buxton model fitting convergence)            │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TI, labeling duration, and voxel size match perfusion territory | PASS |
| S2 | Multi-PLD data allows bounded ATT and CBF estimation | PASS |
| S3 | Buxton kinetic model fitting converges | PASS |
| S4 | CBF RMSE ≤ 8 mL/100g/min achievable with 30 averages at 3T | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# asl/brain_s1_ideal.yaml
principle_ref: sha256:<p057_hash>
omega:
  grid: [64, 64, 20]
  voxel_mm: [3.5, 3.5, 6]
  n_PLDs: 6
  PLD_ms: [200, 500, 1000, 1500, 2000, 2500]
  label_duration_ms: 1800
  field_T: 3.0
E:
  forward: "ΔM = 2·M₀·f·T₁·α·exp(−PLD/T₁)"
  model: "Buxton general kinetic model"
I:
  dataset: BrainASL_20
  subjects: 20
  noise: {type: gaussian, tSNR: 5}
  scenario: ideal
O: [CBF_RMSE, CoV_pct]
epsilon:
  CBF_RMSE_max: 8.0
  CoV_max_pct: 15.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 PLDs from 200–2500 ms cover arterial transit time range | PASS |
| S2 | κ ≈ 12 within well-posed regime for multi-PLD | PASS |
| S3 | Buxton model fitting converges for Gaussian noise | PASS |
| S4 | CBF RMSE ≤ 8 feasible for tSNR=5 with averaging | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# asl/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec057_hash>
principle_ref: sha256:<p057_hash>
dataset:
  name: BrainASL_20
  subjects: 20
  size: [64, 64, 20]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Single_PLD_Buxton
    params: {PLD_ms: 1500}
    results: {CBF_RMSE: 10.5, CoV_pct: 18}
  - solver: Multi_PLD_NLLS
    params: {n_PLDs: 6}
    results: {CBF_RMSE: 6.5, CoV_pct: 12}
  - solver: DeepASL
    params: {pretrained: true}
    results: {CBF_RMSE: 4.0, CoV_pct: 7}
quality_scoring:
  - {max_RMSE: 3.0, Q: 1.00}
  - {max_RMSE: 5.0, Q: 0.90}
  - {max_RMSE: 7.0, Q: 0.80}
  - {max_RMSE: 8.0, Q: 0.75}
```

**Baseline solver:** Single-PLD Buxton — CBF RMSE 10.5
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | CBF RMSE | CoV (%) | Runtime | Q |
|--------|---------|---------|---------|---|
| Single-PLD Buxton | 10.5 | 18 | 0.5 s | 0.75 |
| Multi-PLD NLLS | 6.5 | 12 | 5 s | 0.83 |
| DeepASL (learned) | 4.0 | 7 | 1 s | 0.93 |
| Bayesian-ASL | 2.5 | 5 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian-ASL):  300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p057_hash>",
  "h_s": "sha256:<spec057_hash>",
  "h_b": "sha256:<bench057_hash>",
  "r": {"residual_norm": 0.030, "error_bound": 0.06, "ratio": 0.50},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.93,
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
pwm-node benchmarks | grep asl
pwm-node verify asl/brain_s1_ideal.yaml
pwm-node mine asl/brain_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
