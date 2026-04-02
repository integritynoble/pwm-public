# Principle #119 — Shearography

**Domain:** Industrial Inspection & NDE | **Carrier:** Coherent Photon (Laser) | **Difficulty:** Practitioner (δ=3)
**DAG:** K.green --> L.shear.spatial --> N.pointwise.abs2 | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green-->L.shear.spatial-->N.pointwise.abs2    Shear       CompPanel-20       Unwrap
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SHEAROGRAPHY   P = (E, G, W, C)   Principle #119               │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔΦ(x,y) = (4π/λ) × ∂w/∂x × Δx                       │
│        │ Sheared speckle interferogram; w = out-of-plane disp.  │
│        │ Δx = shear amount; phase ∝ strain derivative           │
│        │ Inverse: extract ∂w/∂x from phase-shifted interferograms│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] --> [L.shear.spatial] --> [N.pointwise.abs2]   │
│        │  Propagate  LateralShear  SpeckleIntensity             │
│        │ V={K.green, L.shear.spatial, N.pointwise.abs2}  A={K.green-->L.shear.spatial, L.shear.spatial-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (speckle always present on rough surface)│
│        │ Uniqueness: YES (phase uniquely maps to ∂w/∂x)        │
│        │ Stability: κ ≈ 6 (lab), κ ≈ 30 (field, vibration)    │
│        │ Mismatch: rigid-body motion, decorrelation, air turb.  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = defect detection POD (primary), phase noise (sec.) │
│        │ q = 2.0 (phase unwrapping convergence)                │
│        │ T = {POD, phase_noise_rad, false_indication_rate}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Shear amount Δx matches expected strain gradient wavelength | PASS |
| S2 | Phase sensitivity > noise floor for thermal/vacuum loading | PASS |
| S3 | Phase unwrapping converges for ≤ 2π fringe density | PASS |
| S4 | POD ≥ 0.90 for disbonds ≥ 15 mm under vacuum loading | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# shearography/comppanel_s1.yaml
principle_ref: sha256:<p119_hash>
omega:
  wavelength_nm: 532
  shear_mm: 10
  camera: [1024, 1024]
  loading: vacuum
  pressure_kPa: -20
E:
  forward: "DeltaPhi = (4*pi/lambda) * dw/dx * Delta_x"
  phase_steps: 4
I:
  dataset: CompPanel_20
  samples: 20
  defect_types: [disbond, delamination, impact_damage]
  noise: {type: speckle, decorrelation: 0.05}
O: [POD, phase_noise_rad]
epsilon:
  POD_min: 0.90
  phase_noise_max: 0.3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 mm shear resolves strain anomaly from 15 mm disbond | PASS |
| S2 | κ ≈ 6 in controlled lab with vacuum loading | PASS |
| S3 | 4-step phase shifting recovers ΔΦ with ≤ 0.2 rad noise | PASS |
| S4 | POD ≥ 0.90 feasible for specified defect sizes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# shearography/benchmark_s1.yaml
spec_ref: sha256:<spec119_hash>
principle_ref: sha256:<p119_hash>
dataset:
  name: CompPanel_20
  samples: 20
  phase_maps: [1024, 1024]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Threshold-Phase
    params: {sigma: 3}
    results: {POD: 0.82, phase_noise: 0.35}
  - solver: Gabor-Filter
    params: {scales: 5}
    results: {POD: 0.91, phase_noise: 0.22}
  - solver: CNN-Shear
    params: {pretrained: true}
    results: {POD: 0.96, phase_noise: 0.15}
quality_scoring:
  - {min_POD: 0.95, Q: 1.00}
  - {min_POD: 0.92, Q: 0.90}
  - {min_POD: 0.90, Q: 0.80}
  - {min_POD: 0.85, Q: 0.75}
```

**Baseline solver:** Threshold-Phase — POD 0.82
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | POD | Phase Noise (rad) | Runtime | Q |
|--------|-----|--------------------|---------|---|
| Threshold-Phase | 0.82 | 0.35 | 0.1 s | 0.75 |
| Gabor-Filter | 0.91 | 0.22 | 1 s | 0.85 |
| CNN-Shear | 0.96 | 0.15 | 0.5 s | 1.00 |
| Wavelet-Denoise | 0.93 | 0.18 | 2 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (CNN-Shear):  300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p119_hash>",
  "h_s": "sha256:<spec119_hash>",
  "h_b": "sha256:<bench119_hash>",
  "r": {"residual_norm": 0.15, "error_bound": 0.30, "ratio": 0.50},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep shearography
pwm-node verify shearography/comppanel_s1.yaml
pwm-node mine shearography/comppanel_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
