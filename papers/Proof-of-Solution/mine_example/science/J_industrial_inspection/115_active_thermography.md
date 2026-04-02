# Principle #115 — Active Thermography (IR)

**Domain:** Industrial Inspection & NDE | **Carrier:** Thermal (IR Photon) | **Difficulty:** Practitioner (δ=3)
**DAG:** G.thermal --> K.psf --> integral.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.thermal-->K.psf-->integral.temporal    IR-therm    CFRP-Delam-25      PPT
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ACTIVE THERMOGRAPHY (IR)   P = (E, G, W, C)   Principle #115   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T(x,y,t) = T₀ + Q/(e√(πt)) − ΔT_defect(x,y,t)      │
│        │ 1D heat diffusion: ∂T/∂t = α ∂²T/∂z²                 │
│        │ Defect delays thermal diffusion → contrast in IR video │
│        │ Inverse: recover defect depth/size from thermal decay  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.thermal] --> [K.psf] --> [integral.temporal]          │
│        │  HeatExcite  ThermalDiffuse  TemporalDecay             │
│        │ V={G.thermal, K.psf, integral.temporal}  A={G.thermal-->K.psf, K.psf-->integral.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (thermal diffusion always produces T(t))│
│        │ Uniqueness: YES for single-layer defects at known α    │
│        │ Stability: κ ≈ 12 (shallow), κ ≈ 60 (deep defects)   │
│        │ Mismatch: non-uniform heating, emissivity variation    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = defect detection F1 (primary), depth error (sec.)  │
│        │ q = 0.5 (diffusion: t* ∝ d²/α, slow convergence)     │
│        │ T = {detection_F1, depth_RMSE, contrast_ratio}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Camera frame rate and NETD match thermal contrast timescale | PASS |
| S2 | Thermal diffusivity known; flash energy produces measurable ΔT | PASS |
| S3 | PPT/TSR logarithmic derivative converges for diffusion model | PASS |
| S4 | F1 ≥ 0.85 for delaminations ≥ 10 mm diameter at depth ≤ 3 mm | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# active_thermography/cfrp_delam_s1.yaml
principle_ref: sha256:<p115_hash>
omega:
  camera_resolution: [640, 512]
  pixel_pitch_um: 15
  NETD_mK: 20
  frame_rate_Hz: 100
  flash_energy_J: 6000
  material: CFRP
  diffusivity_mm2s: 0.43
E:
  forward: "T(t) = T0 + Q/(e*sqrt(pi*t)) - DeltaT_defect"
  model: "1D semi-infinite solid with subsurface void"
I:
  dataset: CFRP_Delam_25
  samples: 25
  defect_types: [delamination, impact_damage, porosity_band]
  noise: {type: gaussian, NETD_mK: 20}
O: [F1, depth_RMSE_mm]
epsilon:
  F1_min: 0.85
  depth_RMSE_max: 0.3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 Hz frame rate captures t* ≈ d²/α ≈ 2 s for d=1 mm | PASS |
| S2 | κ ≈ 12 for shallow CFRP delaminations | PASS |
| S3 | PPT phase extraction converges for specified diffusivity | PASS |
| S4 | F1 ≥ 0.85 feasible for delaminations ≥ 10 mm at NETD=20 mK | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# active_thermography/benchmark_s1.yaml
spec_ref: sha256:<spec115_hash>
principle_ref: sha256:<p115_hash>
dataset:
  name: CFRP_Delam_25
  samples: 25
  sequence_shape: [640, 512, 500]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Max-Contrast
    params: {t_window: auto}
    results: {F1: 0.78, depth_RMSE: 0.45}
  - solver: PPT (Pulsed Phase)
    params: {n_freq: 64}
    results: {F1: 0.89, depth_RMSE: 0.25}
  - solver: TSR (Log-Polynomial)
    params: {order: 7}
    results: {F1: 0.92, depth_RMSE: 0.20}
quality_scoring:
  - {min_F1: 0.92, Q: 1.00}
  - {min_F1: 0.88, Q: 0.90}
  - {min_F1: 0.85, Q: 0.80}
  - {min_F1: 0.80, Q: 0.75}
```

**Baseline solver:** Max-Contrast — F1 0.78
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | F1 | Depth RMSE (mm) | Runtime | Q |
|--------|-----|-----------------|---------|---|
| Max-Contrast | 0.78 | 0.45 | 0.5 s | 0.75 |
| PPT | 0.89 | 0.25 | 3 s | 0.88 |
| TSR | 0.92 | 0.20 | 2 s | 0.98 |
| DL-Thermo (ResNet) | 0.94 | 0.18 | 1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DL-Thermo):  300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p115_hash>",
  "h_s": "sha256:<spec115_hash>",
  "h_b": "sha256:<bench115_hash>",
  "r": {"residual_norm": 0.18, "error_bound": 0.30, "ratio": 0.60},
  "c": {"fitted_rate": 0.48, "theoretical_rate": 0.5, "K": 3},
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
pwm-node benchmarks | grep active_thermography
pwm-node verify active_thermography/cfrp_delam_s1.yaml
pwm-node mine active_thermography/cfrp_delam_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
