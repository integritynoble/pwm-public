# Principle #111 — Industrial Computed Tomography

**Domain:** Industrial Inspection | **Carrier:** X-ray | **Difficulty:** Hard (δ=5)
**DAG:** Pi.radon.cone --> S.angular.full | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.radon.cone-->S.angular.full    IndCT      CT-Castings         FBP/Iter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INDUSTRIAL CT   P = (E, G, W, C)   Principle #111             │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_θ(s) = -ln[∫ I_0·exp(-∫ μ(r) dl) dE / I_0] + n    │
│        │ Polychromatic X-ray: beam-hardening + scatter          │
│        │ Cone-beam geometry with flat-panel detector             │
│        │ Inverse: recover 3D attenuation μ(r) from projections │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon.cone] --> [S.angular.full]                     │
│        │ ConeBeamProj  FullRotation                              │
│        │ V={Pi.radon.cone, S.angular.full}  A={Pi.radon.cone-->S.angular.full}   L_DAG=3.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Radon transform invertible)            │
│        │ Uniqueness: YES for sufficient angular sampling         │
│        │ Stability: κ ≈ 12 (full-angle), κ ≈ 60 (limited)      │
│        │ Mismatch: beam hardening, scatter, geometric cal error  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), defect detection rate (secondary)  │
│        │ q = 2.0 (FDK/SIRT convergence)                       │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Cone-beam geometry consistent with detector size and SDD | PASS |
| S2 | Full 360° rotation → well-posed; beam-hardening correctable | PASS |
| S3 | FDK converges for cone-beam; SIRT for limited-angle | PASS |
| S4 | PSNR ≥ 30 dB achievable for metallic castings | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# industrial_ct/castings_s1_ideal.yaml
principle_ref: sha256:<p111_hash>
omega:
  grid: [512, 512, 512]
  voxel_um: 50
  voltage_kV: 225
  projections: 720
E:
  forward: "y_θ = -ln(∫ I_0·exp(-∫ μ dl) dE / I_0) + n"
  geometry: cone_beam
I:
  dataset: CT_Castings
  volumes: 20
  noise: {type: poisson, flux: 1e6}
  scenario: ideal
O: [PSNR, SSIM, defect_detection_pct]
epsilon:
  PSNR_min: 30.0
  defect_detection_min_pct: 95.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 720 projections over 360°; 512³ at 50 μm | PASS |
| S2 | Full rotation + high flux → κ ≈ 12 | PASS |
| S3 | FDK converges for 720-view cone-beam | PASS |
| S4 | PSNR ≥ 30 dB and detection > 95% feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# industrial_ct/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec111_hash>
principle_ref: sha256:<p111_hash>
dataset:
  name: CT_Castings
  volumes: 20
  size: [512, 512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDK
    results: {PSNR: 31.5, SSIM: 0.901, detect_pct: 96.2}
  - solver: SIRT
    params: {n_iter: 100}
    results: {PSNR: 33.8, SSIM: 0.935, detect_pct: 97.8}
  - solver: DL-CT
    results: {PSNR: 37.2, SSIM: 0.968, detect_pct: 99.1}
quality_scoring:
  - {min: 38.0, Q: 1.00}
  - {min: 34.0, Q: 0.90}
  - {min: 31.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline:** FDK — PSNR 31.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | Detection (%) | Q |
|--------|-----------|---------------|---|
| FDK | 31.5 | 96.2 | 0.82 |
| SIRT | 33.8 | 97.8 | 0.90 |
| DL-CT | 37.2 | 99.1 | 0.97 |
| CT-Former | 38.5 | 99.5 | 1.00 |

### Reward: `R = 100 × 5 × q` → Best: 500 PWM | Floor: 375 PWM

```json
{
  "h_p": "sha256:<p111_hash>", "Q": 0.97,
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
| L4 Solution | — | 375–500 PWM per solve |

## Quick-Start

```bash
pwm-node benchmarks | grep industrial_ct
pwm-node mine industrial_ct/castings_s1_ideal.yaml
```
