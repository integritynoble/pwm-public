# Principle #17 — Phase Contrast Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Textbook (δ=1)
**DAG:** K.psf --> N.phase --> L.diag | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf-->N.phase-->L.diag  PhaseC  PhaseCell-10  QPI-Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE CONTRAST   P = (E, G, W, C)   Principle #17            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = |U_bg + U_scat · exp(iφ(r))|² ≈ I_bg[1 -    │
│        │   2·Δn·t(r)·2π/λ]  (weak-phase approx)               │
│        │ Phase ring retards unscattered light by π/2           │
│        │ Inverse: recover optical path length Δn·t(r)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf] ──→ [N.phase] ──→ [L.diag]                    │
│        │  PSF-filter   Phase-shift(ring)  Modulate(attenuation) │
│        │ V={K,N,L}  A={K-->N, N-->L}   L_DAG=1.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear in φ for weak phase objects)   │
│        │ Uniqueness: YES within weak-phase approximation       │
│        │ Stability: κ ≈ 8 (weak phase); κ ≈ 50 (strong)      │
│        │ Mismatch: phase-ring attenuation, halo artifacts      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = phase_RMSE (rad), SSIM                            │
│        │ q = 2.0 (TIE solver, direct inversion)             │
│        │ T = {residual_norm, phase_error, halo_metric}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Phase-ring geometry consistent with condenser annulus and NA | PASS |
| S2 | Weak phase (φ < 0.5 rad) → linear model, κ ≈ 8 | PASS |
| S3 | Direct division/TIE gives closed-form phase recovery | PASS |
| S4 | Phase RMSE ≤ 0.1 rad achievable for weak objects | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# phase_contrast/cells_s1_ideal.yaml
principle_ref: sha256:<p017_hash>
omega:
  grid: [512, 512]
  pixel_nm: 200
  wavelength_nm: 546
  NA: 0.75
  phase_ring_attenuation: 0.25
E:
  forward: "y ≈ I_bg[1 - 2·φ(r)] (weak phase)"
I:
  dataset: PhaseCell_10
  images: 10
  noise: {type: gaussian, sigma: 0.01}
  scenario: ideal
O: [phase_RMSE_rad, SSIM]
epsilon:
  phase_RMSE_max: 0.10
  SSIM_min: 0.88
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 nm pixel at NA=0.75: Nyquist satisfied | PASS |
| S2 | Weak phase objects: κ ≈ 8 | PASS |
| S3 | Direct inversion converges in 1 step | PASS |
| S4 | Phase RMSE ≤ 0.10 rad at σ=0.01 | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# phase_contrast/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec017_hash>
dataset:
  name: PhaseCell_10
  images: 10
  size: [512, 512]
baselines:
  - solver: Direct-Inversion
    params: {method: linearize}
    results: {phase_RMSE: 0.085, SSIM: 0.901}
  - solver: TIE-Solver
    params: {defocus_um: 1.0}
    results: {phase_RMSE: 0.062, SSIM: 0.932}
  - solver: PhaseNet
    params: {arch: UNet}
    results: {phase_RMSE: 0.028, SSIM: 0.971}
quality_scoring:
  metric: phase_RMSE_rad
  thresholds:
    - {max: 0.025, Q: 1.00}
    - {max: 0.050, Q: 0.90}
    - {max: 0.100, Q: 0.80}
    - {max: 0.150, Q: 0.75}
```

**Baseline:** Direct-Inversion — RMSE 0.085 rad | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | Phase RMSE | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Direct-Inversion | 0.085 rad | 0.901 | 0.01 s | 0.80 |
| TIE-Solver | 0.062 rad | 0.932 | 0.1 s | 0.88 |
| PhaseNet | 0.028 rad | 0.971 | 0.2 s | 0.98 |
| Iterative-Phase | 0.045 rad | 0.945 | 0.5 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q = 100 × Q
Best (PhaseNet):  100 × 0.98 = 98 PWM
Floor:            100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p017_hash>",
  "r": {"residual_norm": 0.028, "error_bound": 0.10, "ratio": 0.28},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.92,
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
| L4 Solution | — | 75–98 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep phase_contrast
pwm-node verify phase_contrast/cells_s1_ideal.yaml
pwm-node mine phase_contrast/cells_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
