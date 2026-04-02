# Principle #56 — CEST MRI

**Domain:** Medical Imaging | **Carrier:** Spin | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix.coil] --> [F.dft] --> [S.kspace] --> [N.pointwise]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix.coil --> F.dft --> S.kspace --> N.pointwise    CEST-map     BrainCEST-15      Lorentz
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CEST MRI   P = (E, G, W, C)   Principle #56                   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Z(Δω) = M_z(Δω)/M₀ = 1 − Σ_k L_k(Δω−Δω_k,Γ_k,A_k) │
│        │ L_k = Lorentzian pool (water, MT, amide, amine, etc.)  │
│        │ Inverse: fit CEST effect amplitudes {A_k} from the    │
│        │ Z-spectrum acquired at multiple saturation offsets      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix.coil] ──→ [F.dft] ──→ [S.kspace] ──→ [N.pointwise]│
│        │  Saturate Transform Encode  Sample   Detect            │
│        │ V={L.mix.coil,F.dft,S.kspace,N.pointwise}  A={L.mix.coil→F.dft, F.dft→S.kspace, S.kspace→N.pointwise}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Z-spectrum measurable with saturation) │
│        │ Uniqueness: CONDITIONAL (overlapping pools need multi- │
│        │   offset fitting or asymmetry analysis)                │
│        │ Stability: κ ≈ 15 (amide), κ ≈ 50 (amine, broad MT)   │
│        │ Mismatch: ΔB₀ (field inhomogeneity), ΔB₁ (sat. power)│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = CEST effect RMSE % (primary), CNR (secondary)     │
│        │ q = 2.0 (Lorentzian fitting convergence)              │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Saturation offsets span ±5 ppm with sufficient density | PASS |
| S2 | Multi-pool Lorentzian model separable with ≥30 offsets | PASS |
| S3 | NLLS Lorentzian fitting converges | PASS |
| S4 | APT effect ≥ 2% detectable at 3T with B₁=2 μT | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cest/brain_s1_ideal.yaml
principle_ref: sha256:<p056_hash>
omega:
  grid: [128, 128, 20]
  voxel_mm: [2, 2, 5]
  n_offsets: 53
  offset_range_ppm: [-6, 6]
  B1_uT: 2.0
  field_T: 3.0
E:
  forward: "Z(Δω) = 1 − Σ_k L_k(Δω−Δω_k)"
  model: "5-pool Lorentzian (water, MT, amide, amine, NOE)"
I:
  dataset: BrainCEST_15
  subjects: 15
  noise: {type: gaussian, SNR: 50}
  scenario: ideal
O: [APT_RMSE_pct, MT_RMSE_pct]
epsilon:
  APT_RMSE_max_pct: 0.5
  MT_RMSE_max_pct: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 53 offsets over ±6 ppm resolve 5 Lorentzian pools at 3T | PASS |
| S2 | κ ≈ 15 within well-posed regime for 5-pool fit | PASS |
| S3 | NLLS fitting converges at SNR=50 | PASS |
| S4 | APT RMSE ≤ 0.5% feasible for brain at 3T | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cest/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec056_hash>
principle_ref: sha256:<p056_hash>
dataset:
  name: BrainCEST_15
  subjects: 15
  size: [128, 128, 20]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MTR_Asymmetry
    params: {offset_ppm: 3.5}
    results: {APT_RMSE: 1.2, MT_RMSE: 5.0}
  - solver: Lorentzian_5Pool
    params: {n_iter: 200}
    results: {APT_RMSE: 0.45, MT_RMSE: 1.8}
  - solver: DeepCEST
    params: {pretrained: true}
    results: {APT_RMSE: 0.22, MT_RMSE: 0.9}
quality_scoring:
  - {max_APT_RMSE: 0.15, Q: 1.00}
  - {max_APT_RMSE: 0.30, Q: 0.90}
  - {max_APT_RMSE: 0.50, Q: 0.80}
  - {max_APT_RMSE: 1.00, Q: 0.75}
```

**Baseline solver:** MTR asymmetry — APT RMSE 1.2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | APT RMSE (%) | MT RMSE (%) | Runtime | Q |
|--------|-------------|-------------|---------|---|
| MTR Asymmetry | 1.20 | 5.0 | 0.1 s | 0.75 |
| Lorentzian 5-Pool | 0.45 | 1.8 | 30 s | 0.88 |
| DeepCEST (learned) | 0.22 | 0.9 | 1 s | 0.96 |
| BM-Sim-Net | 0.12 | 0.5 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (BM-Sim-Net):  300 × 1.00 = 300 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p056_hash>",
  "h_s": "sha256:<spec056_hash>",
  "h_b": "sha256:<bench056_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.035, "ratio": 0.43},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.96,
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
pwm-node benchmarks | grep cest
pwm-node verify cest/brain_s1_ideal.yaml
pwm-node mine cest/brain_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
