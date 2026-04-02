# Principle #121 — Magnetic Flux Leakage (MFL)

**Domain:** Industrial Inspection & NDE | **Carrier:** Magnetic Field | **Difficulty:** Practitioner (δ=3)
**DAG:** G.cw --> K.green.em --> S.raster | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.cw-->K.green.em-->S.raster    MFL         PipeCorr-40        Invert
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MAGNETIC FLUX LEAKAGE (MFL)   P = (E, G, W, C)   #121         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ B_leak(x,y) = f(ΔB, geometry, μ(x,y), wall_loss)     │
│        │ ∇·B = 0; flux leaks where wall thins or has defects   │
│        │ Hall sensor array measures radial + axial components   │
│        │ Inverse: estimate wall loss depth/width from B_leak   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.cw] --> [K.green.em] --> [S.raster]                   │
│        │  Magnetize  FluxLeak  ScanDetect                       │
│        │ V={G.cw, K.green.em, S.raster}  A={G.cw-->K.green.em, K.green.em-->S.raster}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (any wall loss produces leakage field)  │
│        │ Uniqueness: LIMITED (depth-width ambiguity for pits)   │
│        │ Stability: κ ≈ 15 (large corrosion), κ ≈ 80 (pits)  │
│        │ Mismatch: remanence variation, velocity effects        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = depth sizing RMSE %wt (primary), POD (secondary)  │
│        │ q = 1.5 (FEM-based inversion convergence)             │
│        │ T = {depth_RMSE, POD, false_call_rate}                 │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Magnetization saturates pipe wall; Hall sensor spacing resolves defect width | PASS |
| S2 | Leakage field amplitude exceeds sensor noise for ≥ 10% wall loss | PASS |
| S3 | FEM inversion converges for axisymmetric corrosion profiles | PASS |
| S4 | Depth RMSE ≤ 10% wall thickness for corrosion ≥ 20% depth | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mfl/pipecorr_s1.yaml
principle_ref: sha256:<p121_hash>
omega:
  pipe_OD_mm: 610
  wall_thickness_mm: 9.5
  magnetization: saturated
  sensor_spacing_mm: 6
  velocity_ms: 2.0
E:
  forward: "B_leak = f(Delta_B, defect_geometry, mu)"
  model: "3D FEM magnetic field with wall-loss perturbation"
I:
  dataset: PipeCorr_40
  samples: 40
  defect_types: [general_corrosion, pitting, gouge]
  noise: {type: gaussian, SNR_dB: 30}
O: [depth_RMSE_pct, POD]
epsilon:
  depth_RMSE_max: 10.0
  POD_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 mm sensor pitch resolves 20 mm wide corrosion; wall saturated | PASS |
| S2 | κ ≈ 15 for general corrosion at 30 dB SNR | PASS |
| S3 | FEM inversion converges within 20 iterations | PASS |
| S4 | Depth RMSE ≤ 10% feasible for corrosion ≥ 20% wall loss | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mfl/benchmark_s1.yaml
spec_ref: sha256:<spec121_hash>
principle_ref: sha256:<p121_hash>
dataset:
  name: PipeCorr_40
  samples: 40
  signal_shape: [128, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Amplitude
    params: {calibration: linear}
    results: {depth_RMSE: 12.5, POD: 0.85}
  - solver: Neural-Sizing
    params: {features: [peak, width, area]}
    results: {depth_RMSE: 8.2, POD: 0.92}
  - solver: FEM-Inversion
    params: {iterations: 20}
    results: {depth_RMSE: 6.1, POD: 0.95}
quality_scoring:
  - {max_RMSE: 6.0, Q: 1.00}
  - {max_RMSE: 8.0, Q: 0.90}
  - {max_RMSE: 10.0, Q: 0.80}
  - {max_RMSE: 15.0, Q: 0.75}
```

**Baseline solver:** Peak-Amplitude — RMSE 12.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Depth RMSE (%wt) | POD | Runtime | Q |
|--------|-------------------|-----|---------|---|
| Peak-Amplitude | 12.5 | 0.85 | 0.01 s | 0.75 |
| Neural-Sizing | 8.2 | 0.92 | 0.1 s | 0.88 |
| FEM-Inversion | 6.1 | 0.95 | 30 s | 0.98 |
| Hybrid-DL-FEM | 5.8 | 0.96 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Hybrid):  300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p121_hash>",
  "h_s": "sha256:<spec121_hash>",
  "h_b": "sha256:<bench121_hash>",
  "r": {"residual_norm": 5.8, "error_bound": 10.0, "ratio": 0.58},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep mfl
pwm-node verify mfl/pipecorr_s1.yaml
pwm-node mine mfl/pipecorr_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
