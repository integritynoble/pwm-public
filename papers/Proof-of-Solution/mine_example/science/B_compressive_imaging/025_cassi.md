# Principle #25 — Coded Aperture Snapshot Spectral Imaging (CASSI)

**Domain:** Compressive Imaging | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** L.diag.binary → L.shear.spectral → ∫.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag→L.shear→∫  CASSI   KAIST-TSA-10       CS-Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CASSI  P = (E, G, W, C)   Principle #25                      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(x,y) = Σ_λ C(x,y) · f(x, y+a·λ) + n              │
│        │ C ∈ {0,1}^{H×W} binary coded aperture mask           │
│        │ a = dispersion slope (px/band); 28:1 compression      │
│        │ Inverse: recover f ∈ R^{H×W×N_λ} from 2D snapshot y │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.binary] --> [L.shear.spectral] --> [∫.spectral]│
│        │   coded mask          prism shear          sum over λ  │
│        │   C(x,y)∈{0,1}       shift by a·λ px     onto detector│
│        │ V={L.diag.binary, L.shear.spectral, ∫.spectral}      │
│        │ A={L.diag.binary->L.shear.spectral,                   │
│        │    L.shear.spectral->∫.spectral}  L_DAG=3.0           │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (underdetermined but regularizable)    │
│        │ Uniqueness: YES under sparsity (RIP condition)        │
│        │ Stability: κ ≈ 50 (calibrated); κ ≈ 200 (mismatch)  │
│        │ Mismatch: dx, dy, θ, a₁ (slope), α (angle)          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = per-channel PSNR, SSIM, SAM (deg)                │
│        │ q = 2.0 (iterative CS solvers O(h²))               │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mask C matches spatial grid; dispersion a·N_λ fits detector | PASS |
| S2 | Binary random mask (50% fill) satisfies RIP; κ ≈ 50 | PASS |
| S3 | GAP-TV, ADMM, PnP all converge for CASSI | PASS |
| S4 | Per-channel PSNR ≥ 24 dB; convergence rate q=2.0 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cassi/kaist_s1_ideal.yaml
principle_ref: sha256:<p025_hash>
omega:
  grid: [256, 256, 28]
  spectral_range_nm: [450, 650]
  dispersion_slope: 2.0
E:
  forward: "y = Σ_λ C·f(x,y+a·λ) + n"
  mask: "C ∈ {0,1}^{256×256}, fill=0.5"
I:
  dataset: KAIST_TSA_10
  scenes: 10
  noise: {type: poisson_gaussian, alpha: 1e5, sigma: 0.01}
  scenario: ideal
O: [per_channel_PSNR, SSIM, SAM_deg]
epsilon:
  PSNR_min: 24.0
  SSIM_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid [256,256,28] with slope 2.0 px/band: detector width consistent | PASS |
| S2 | Fill 0.5, 28 bands: RIP satisfied, κ ≈ 50 | PASS |
| S3 | GAP-TV converges at O(1/k) for these parameters | PASS |
| S4 | PSNR ≥ 24 dB feasible per CS theory bounds | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# cassi/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec025_hash>
dataset:
  name: KAIST_TSA_10
  scenes: 10
  size: [256, 256, 28]
baselines:
  - solver: GAP-TV
    params: {lambda_tv: 0.01, n_iter: 50}
    results: {PSNR: 24.34, SSIM: 0.723, SAM: 22.3}
  - solver: TwIST
    params: {lambda: 0.005, n_iter: 100}
    results: {PSNR: 25.1, SSIM: 0.741, SAM: 20.8}
  - solver: PnP-HSICNN
    params: {denoiser: HSICNN, rho: 0.5, n_iter: 40}
    results: {PSNR: 28.2, SSIM: 0.812, SAM: 16.5}
quality_scoring:
  - {min: 30.0, Q: 1.00}
  - {min: 26.0, Q: 0.90}
  - {min: 24.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** GAP-TV — PSNR 24.34 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | SAM | Runtime | Q |
|--------|-----------|------|-----|---------|---|
| GAP-TV | 24.34 | 0.723 | 22.3 | 3 min | 0.80 |
| TwIST | 25.1 | 0.741 | 20.8 | 4 min | 0.82 |
| PnP-HSICNN | 28.2 | 0.812 | 16.5 | 6 min | 0.90 |
| MST-L | 31.2 | 0.891 | 12.1 | 2 min | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.1 × Q = 330 × Q   (ν_c=1.1 under-covered)
Best (MST-L):  330 × 1.00 = 330 PWM
Floor:         330 × 0.75 = 247 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p025_hash>",
  "h_s": "sha256:<spec025_hash>",
  "h_b": "sha256:<bench025_hash>",
  "r": {"residual_norm": 0.024, "error_bound": 0.05, "ratio": 0.48},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.89,
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
| L4 Solution | — | 247–330 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep cassi
pwm-node verify cassi/kaist_s1_ideal.yaml
pwm-node mine cassi/kaist_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
