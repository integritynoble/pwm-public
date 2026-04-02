# Principle #86 — Electron Tomography

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Hard (δ=5)
**DAG:** Pi.radon --> K.psf.ctf --> S.tilt | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.radon-->K.psf.ctf-->S.tilt    ET-recon   ET-CellOrganelle   Tomo-recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ELECTRON TOMOGRAPHY   P = (E, G, W, C)   Principle #86         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_θ(s) = ∫ f(r)·δ(s − r·n_θ) dr + n(s)              │
│        │ Radon transform: projection at tilt angle θ            │
│        │ Missing wedge: θ ∈ [−70°,+70°] (not full 180°)        │
│        │ Inverse: recover 3D volume f from tilt series {y_θ}    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon] --> [K.psf.ctf] --> [S.tilt]                  │
│        │  RadonProj  CTF  TiltSeries                             │
│        │ V={Pi.radon, K.psf.ctf, S.tilt}  A={Pi.radon-->K.psf.ctf, K.psf.ctf-->S.tilt}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Radon transform invertible)            │
│        │ Uniqueness: NO — missing wedge creates null space       │
│        │ Stability: κ ≈ 50 (±70°), κ ≈ 200 (±50° limited)      │
│        │ Mismatch: tilt-axis offset, magnification drift         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), FSC (secondary)                    │
│        │ q = 1.0 (SIRT convergence rate)                       │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Projection geometry matches tilt angles; detector size consistent | PASS |
| S2 | Missing-wedge regularizable via TV/sparsity prior | PASS |
| S3 | SIRT / CGLS converge monotonically for limited-angle data | PASS |
| S4 | PSNR ≥ 22 dB achievable with ±70° tilt range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# electron_tomo/cell_s1_ideal.yaml
principle_ref: sha256:<p086_hash>
omega:
  grid: [512, 512, 512]
  pixel_nm: 1.0
  tilt_range_deg: [-70, 70]
  tilt_step_deg: 2
E:
  forward: "y_θ = Radon(f, θ) + n"
  projections: 71
I:
  dataset: ET_CellOrganelle
  volumes: 10
  noise: {type: poisson, dose_e_per_A2: 5}
  scenario: ideal
O: [PSNR, FSC_resolution_nm]
epsilon:
  PSNR_min: 22.0
  FSC_resolution_max_nm: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 71 projections over ±70° at 2° steps; 512³ grid at 1 nm | PASS |
| S2 | Missing-wedge regularizable; κ ≈ 50 at ±70° | PASS |
| S3 | SIRT converges for 71 projections with Poisson noise | PASS |
| S4 | PSNR ≥ 22 dB feasible at 5 e⁻/Å² per projection | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# electron_tomo/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec086_hash>
principle_ref: sha256:<p086_hash>
dataset:
  name: ET_CellOrganelle
  volumes: 10
  size: [512, 512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: WBP
    params: {filter: ram-lak}
    results: {PSNR: 22.8, FSC_res_nm: 4.5}
  - solver: SIRT
    params: {n_iter: 200}
    results: {PSNR: 24.5, FSC_res_nm: 3.8}
  - solver: IsoNet
    params: {pretrained: true}
    results: {PSNR: 27.2, FSC_res_nm: 2.5}
quality_scoring:
  - {min: 28.0, Q: 1.00}
  - {min: 25.0, Q: 0.90}
  - {min: 23.0, Q: 0.80}
  - {min: 21.0, Q: 0.75}
```

**Baseline solver:** WBP — PSNR 22.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | FSC (nm) | Runtime | Q |
|--------|-----------|----------|---------|---|
| WBP | 22.8 | 4.5 | 10 s | 0.80 |
| SIRT | 24.5 | 3.8 | 120 s | 0.87 |
| IsoNet | 27.2 | 2.5 | 60 s | 0.95 |
| CryoET-Transformer | 28.5 | 2.0 | 90 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (CryoET-TF):  500 × 1.00 = 500 PWM
Floor:                   500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p086_hash>",
  "h_s": "sha256:<spec086_hash>",
  "h_b": "sha256:<bench086_hash>",
  "r": {"residual_norm": 0.018, "error_bound": 0.04, "ratio": 0.45},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.95,
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

---

## Quick-Start

```bash
pwm-node benchmarks | grep electron_tomo
pwm-node verify electron_tomo/cell_s1_ideal.yaml
pwm-node mine electron_tomo/cell_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
