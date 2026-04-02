# Principle #71 — Digital Holographic Microscopy

**Domain:** Coherent Imaging | **Carrier:** Photon (coherent) | **Difficulty:** Advanced (δ=3)
**DAG:** K.green.fresnel --> L.mix --> N.pointwise.abs2 | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green.fresnel-->L.mix-->N.pointwise.abs2    DHM         HoloCell-15       PropRecon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DIGITAL HOLOGRAPHIC MICROSCOPY   P = (E, G, W, C)   #71       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H(x,y) = |R + O|² = |R|² + |O|² + R*O + RO*          │
│        │ R = reference wave; O = object wave                    │
│        │ Off-axis: spatial carrier separates terms in Fourier    │
│        │ Inverse: back-propagate O(x,y,z) from filtered hologram│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green.fresnel] --> [L.mix] --> [N.pointwise.abs2]     │
│        │  FresnelProp  Interfere  ModSq                         │
│        │ V={K.green.fresnel, L.mix, N.pointwise.abs2}  A={K.green.fresnel-->L.mix, L.mix-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (off-axis carrier encodes phase)        │
│        │ Uniqueness: YES (spatial filtering isolates +1 order)  │
│        │ Stability: κ ≈ 5 (off-axis), κ ≈ 30 (inline/twin img) │
│        │ Mismatch: aberrations, coherence noise, twin image     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = phase RMSE (primary), SSIM (secondary)             │
│        │ q = 2.0 (angular spectrum propagation exact)           │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Carrier frequency, pixel pitch, and NA satisfy off-axis sampling condition | PASS |
| S2 | Spatial filtering in Fourier domain isolates object term; bounded reconstruction | PASS |
| S3 | Angular spectrum propagation converges in single step for known distance | PASS |
| S4 | Phase RMSE ≤ 0.05 rad achievable for off-axis geometry at SNR > 25 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dhm/holocell_s1.yaml
principle_ref: sha256:<p071_hash>
omega:
  grid: [1024, 1024]
  pixel_um: 3.45
  wavelength_nm: 632.8
  NA: 0.65
  geometry: off_axis
  carrier_angle_deg: 3.0
E:
  forward: "H(x,y) = |R + O|^2; back-propagate via angular spectrum"
  propagation: "angular_spectrum"
I:
  dataset: HoloCell_15
  holograms: 15
  noise: {type: gaussian, sigma: 0.02}
  scenario: ideal
O: [phase_RMSE_rad, SSIM]
epsilon:
  phase_RMSE_max: 0.08
  SSIM_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3.45 µm pixel with 3° carrier angle satisfies Nyquist for off-axis | PASS |
| S2 | κ ≈ 5 for off-axis filtering at NA=0.65 | PASS |
| S3 | Angular spectrum method converges exactly for single-plane propagation | PASS |
| S4 | Phase RMSE ≤ 0.08 rad feasible at σ=0.02 noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dhm/benchmark_s1.yaml
spec_ref: sha256:<spec071_hash>
principle_ref: sha256:<p071_hash>
dataset:
  name: HoloCell_15
  holograms: 15
  size: [1024, 1024]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: AngularSpectrum
    params: {filter: spatial_bandpass}
    results: {phase_RMSE: 0.06, SSIM: 0.935}
  - solver: Fresnel-Conv
    params: {filter: butterworth}
    results: {phase_RMSE: 0.08, SSIM: 0.910}
  - solver: DeepHolo-UNet
    params: {pretrained: true}
    results: {phase_RMSE: 0.03, SSIM: 0.972}
quality_scoring:
  - {max_RMSE: 0.03, Q: 1.00}
  - {max_RMSE: 0.05, Q: 0.90}
  - {max_RMSE: 0.08, Q: 0.80}
  - {max_RMSE: 0.12, Q: 0.75}
```

**Baseline solver:** AngularSpectrum — phase RMSE 0.06 rad
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Phase RMSE | SSIM | Runtime | Q |
|--------|------------|------|---------|---|
| Fresnel-Conv | 0.08 | 0.910 | 0.2 s | 0.80 |
| AngularSpectrum | 0.06 | 0.935 | 0.3 s | 0.88 |
| Multi-height GS | 0.04 | 0.960 | 2 s | 0.95 |
| DeepHolo-UNet | 0.03 | 0.972 | 0.1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DeepHolo):  300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p071_hash>",
  "h_s": "sha256:<spec071_hash>",
  "h_b": "sha256:<bench071_hash>",
  "r": {"residual_norm": 0.003, "error_bound": 0.01, "ratio": 0.30},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep dhm
pwm-node verify dhm/holocell_s1.yaml
pwm-node mine dhm/holocell_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
