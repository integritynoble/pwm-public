# Principle #98 — Photometric Stereo

**Domain:** Depth Imaging | **Carrier:** Photon (visible) | **Difficulty:** Standard (δ=3)
**DAG:** G.beam --> K.psf --> integral.angular | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.psf-->integral.angular    PS-normal  DiLiGenT             NormalEst
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHOTOMETRIC STEREO   P = (E, G, W, C)   Principle #98         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_j(r) = ρ(r)·max(n(r)·l_j, 0) + n_j(r)             │
│        │ Lambertian: intensity = albedo × (normal · light_dir) │
│        │ j = 1..K lighting directions; K ≥ 3 for solvability   │
│        │ Inverse: recover surface normal n(r) per pixel         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.psf] --> [integral.angular]              │
│        │ DirIllum  BRDF  MultiLight                              │
│        │ V={G.beam, K.psf, integral.angular}  A={G.beam-->K.psf, K.psf-->integral.angular}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (K≥3 non-coplanar lights → solvable)   │
│        │ Uniqueness: YES for Lambertian; non-unique for specular│
│        │ Stability: κ ≈ 5 (Lambertian), κ ≈ 50 (non-Lambert.)  │
│        │ Mismatch: cast shadows, inter-reflections, non-Lambert.│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = normal MAE degrees (primary), depth RMSE (second.) │
│        │ q = 2.0 (least-squares normal estimation)             │
│        │ T = {normal_MAE_deg, albedo_error, K_resolutions}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | K≥3 lighting directions; non-coplanar configuration | PASS |
| S2 | LS normal estimation well-conditioned for K≥6 lights | PASS |
| S3 | LS / robust estimation converges for Lambertian model | PASS |
| S4 | Normal MAE < 5° achievable for near-Lambertian surfaces | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# photometric_stereo/diligent_s1_ideal.yaml
principle_ref: sha256:<p098_hash>
omega:
  grid: [612, 512]
  n_lights: 96
  light_config: hemisphere
E:
  forward: "y_j = ρ·max(n·l_j, 0) + noise"
  BRDF: Lambertian
I:
  dataset: DiLiGenT
  objects: 10
  noise: {type: gaussian, sigma_DN: 2}
  scenario: ideal
O: [normal_MAE_deg]
epsilon:
  normal_MAE_max_deg: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 96 lights on hemisphere; non-degenerate configuration | PASS |
| S2 | κ ≈ 5 for 96-light Lambertian case | PASS |
| S3 | LS normal estimation converges with 96 observations | PASS |
| S4 | Normal MAE < 5° feasible for DiLiGenT Lambertian subset | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# photometric_stereo/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec098_hash>
principle_ref: sha256:<p098_hash>
dataset:
  name: DiLiGenT
  objects: 10
  size: [612, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Least-Squares
    params: {robust: false}
    results: {normal_MAE_deg: 4.2}
  - solver: Robust-PS
    params: {outlier_model: sparse}
    results: {normal_MAE_deg: 2.8}
  - solver: PS-FCN
    params: {pretrained: true}
    results: {normal_MAE_deg: 1.5}
quality_scoring:
  - {max_MAE_deg: 1.5, Q: 1.00}
  - {max_MAE_deg: 3.0, Q: 0.90}
  - {max_MAE_deg: 5.0, Q: 0.80}
  - {max_MAE_deg: 8.0, Q: 0.75}
```

**Baseline solver:** Least-Squares — MAE 4.2°
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Normal MAE (°) | Runtime | Q |
|--------|-----------------|---------|---|
| Least-Squares | 4.2 | 0.5 s | 0.80 |
| Robust-PS | 2.8 | 5 s | 0.90 |
| PS-FCN | 1.5 | 1 s | 1.00 |
| UniPS | 1.2 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (UniPS):  300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p098_hash>",
  "h_s": "sha256:<spec098_hash>",
  "h_b": "sha256:<bench098_hash>",
  "r": {"normal_MAE_deg": 1.5, "albedo_err": 0.02},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep photometric_stereo
pwm-node verify photometric_stereo/diligent_s1_ideal.yaml
pwm-node mine photometric_stereo/diligent_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
