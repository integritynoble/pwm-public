# Principle #70 — Ptychographic Imaging

**Domain:** Coherent Imaging | **Carrier:** Photon (coherent) | **Difficulty:** Research (δ=5)
**DAG:** L.diag.complex --> K.green.fresnel --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.complex-->K.green.fresnel-->N.pointwise.abs2    Ptycho      PtychoSim-20      PIE/ePIE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PTYCHOGRAPHIC IMAGING   P = (E, G, W, C)   Principle #70       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_j(q) = |F{P(r - r_j) · O(r)}|²                     │
│        │ P = probe function; O = complex object transmittance   │
│        │ Scanning overlap ≥ 60%; far-field diffraction patterns │
│        │ Inverse: recover O(r) and P(r) from {I_j} set         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.complex] --> [K.green.fresnel] --> [N.pointwise.abs2]│
│        │  DiagMask  FresnelProp  ModSq                          │
│        │ V={L.diag.complex, K.green.fresnel, N.pointwise.abs2}  A={L.diag.complex-->K.green.fresnel, K.green.fresnel-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sufficient overlap guarantees coverage)│
│        │ Uniqueness: YES (redundant overlap removes phase amb.) │
│        │ Stability: κ ≈ 8 (high overlap), κ ≈ 60 (low overlap) │
│        │ Mismatch: partial coherence, position errors, vibr.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), phase RMSE (secondary)             │
│        │ q = 1.5 (ePIE geometric convergence)                  │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Scan positions, overlap ratio, and detector geometry yield consistent reciprocal sampling | PASS |
| S2 | Overlap ≥ 60% ensures redundancy; phase ambiguity resolved up to global offset | PASS |
| S3 | ePIE/PIE converges monotonically with sufficient overlap and coherent illumination | PASS |
| S4 | Phase RMSE ≤ 0.1 rad achievable at high SNR with ≥ 70% overlap | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ptychography/ptychosim_s1.yaml
principle_ref: sha256:<p070_hash>
omega:
  grid: [256, 256]
  pixel_nm: 10
  wavelength_nm: 0.15
  probe_diameter_nm: 400
  overlap_pct: 70
E:
  forward: "I_j(q) = |F{P(r-r_j) * O(r)}|^2"
  probe: "Gaussian, FWHM=400 nm"
I:
  dataset: PtychoSim_20
  patterns: 200
  noise: {type: poisson, peak: 5000}
  scenario: ideal
O: [PSNR, phase_RMSE_rad]
epsilon:
  PSNR_min: 28.0
  phase_RMSE_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 nm pixel with 0.15 nm wavelength satisfies sampling for 400 nm probe | PASS |
| S2 | 70% overlap provides ~4× redundancy per pixel | PASS |
| S3 | ePIE converges within 200 iterations for Poisson noise at peak 5000 | PASS |
| S4 | PSNR ≥ 28 dB and phase RMSE ≤ 0.15 rad feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ptychography/benchmark_s1.yaml
spec_ref: sha256:<spec070_hash>
principle_ref: sha256:<p070_hash>
dataset:
  name: PtychoSim_20
  objects: 20
  scan_positions: 200
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: PIE
    params: {n_iter: 300}
    results: {PSNR: 26.5, phase_RMSE: 0.18}
  - solver: ePIE
    params: {n_iter: 200, alpha: 1.0, beta: 1.0}
    results: {PSNR: 30.2, phase_RMSE: 0.10}
  - solver: rPIE
    params: {n_iter: 200}
    results: {PSNR: 31.5, phase_RMSE: 0.08}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline solver:** ePIE — PSNR 30.2 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | Phase RMSE | Runtime | Q |
|--------|-----------|------------|---------|---|
| PIE | 26.5 | 0.18 | 5 min | 0.75 |
| ePIE | 30.2 | 0.10 | 3 min | 0.90 |
| rPIE | 31.5 | 0.08 | 4 min | 0.95 |
| PtychoNN (DL) | 33.0 | 0.06 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (PtychoNN):  500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p070_hash>",
  "h_s": "sha256:<spec070_hash>",
  "h_b": "sha256:<bench070_hash>",
  "r": {"residual_norm": 0.006, "error_bound": 0.02, "ratio": 0.30},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep ptychography
pwm-node verify ptychography/ptychosim_s1.yaml
pwm-node mine ptychography/ptychosim_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
