# Principle #116 — Terahertz Imaging (THz)

**Domain:** Industrial Inspection & NDE | **Carrier:** THz Photon | **Difficulty:** Research (δ=5)
**DAG:** G.pulse --> K.green --> F.dft | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse-->K.green-->F.dft    THz-img     CoatLayer-20       Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TERAHERTZ IMAGING (THz)   P = (E, G, W, C)   Principle #116    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E_ref(t) → E_sam(t); ñ(ω) = −(c/ωd) ln(E_sam/E_ref) │
│        │ THz-TDS: pulsed THz reflects at each dielectric layer  │
│        │ Inverse: extract layer thickness d and ñ(ω) from TDS  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [K.green] --> [F.dft]                      │
│        │  THzPulse  Propagate  TDS-FFT                          │
│        │ V={G.pulse, K.green, F.dft}  A={G.pulse-->K.green, K.green-->F.dft}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Fresnel reflections always present)    │
│        │ Uniqueness: YES for ≤ 5 layers with sufficient BW      │
│        │ Stability: κ ≈ 10 (thick coats), κ ≈ 80 (thin films) │
│        │ Mismatch: water absorption, scattering in granular mat.│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = thickness RMSE μm (primary), ñ error (secondary)  │
│        │ q = 2.0 (deconvolution convergence rate)              │
│        │ T = {thickness_RMSE, refractive_index_error, BW_GHz}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | THz bandwidth ≥ 2 THz resolves layers ≥ 30 μm; pixel pitch matches focus | PASS |
| S2 | Fresnel coefficients non-degenerate for distinct layer ñ values | PASS |
| S3 | Time-domain deconvolution converges with Wiener regularization | PASS |
| S4 | Thickness RMSE ≤ 5 μm achievable for paint coatings ≥ 50 μm | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# thz_imaging/coatlayer_s1.yaml
principle_ref: sha256:<p116_hash>
omega:
  bandwidth_THz: 3.0
  pixel_mm: 0.5
  scan_area_mm: [50, 50]
  time_window_ps: 100
  samples_per_trace: 4096
E:
  forward: "E_sam(t) = sum_layers(r_i * E_ref(t - 2*n_i*d_i/c))"
  model: "transfer-matrix, Fresnel at each interface"
I:
  dataset: CoatLayer_20
  samples: 20
  layer_types: [primer, basecoat, clearcoat]
  noise: {type: gaussian, SNR_dB: 40}
O: [thickness_RMSE_um, n_error]
epsilon:
  thickness_RMSE_max: 5.0
  n_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3 THz bandwidth gives axial resolution ≈ 50 μm in paint (n≈1.6) | PASS |
| S2 | κ ≈ 10 for 3-layer automotive paint stack | PASS |
| S3 | Transfer-matrix inversion converges for SNR=40 dB | PASS |
| S4 | Thickness RMSE ≤ 5 μm feasible for layers ≥ 30 μm | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# thz_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec116_hash>
principle_ref: sha256:<p116_hash>
dataset:
  name: CoatLayer_20
  samples: 20
  trace_length: 4096
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Picking
    params: {min_separation_ps: 2}
    results: {thickness_RMSE: 8.2, n_error: 0.08}
  - solver: Sparse-Deconv
    params: {lambda: 0.01}
    results: {thickness_RMSE: 4.1, n_error: 0.04}
  - solver: Transfer-Matrix-Fit
    params: {optimizer: LM}
    results: {thickness_RMSE: 2.8, n_error: 0.02}
quality_scoring:
  - {max_RMSE: 3.0, Q: 1.00}
  - {max_RMSE: 5.0, Q: 0.90}
  - {max_RMSE: 8.0, Q: 0.80}
  - {max_RMSE: 12.0, Q: 0.75}
```

**Baseline solver:** Peak-Picking — RMSE 8.2 μm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Thickness RMSE (μm) | ñ Error | Runtime | Q |
|--------|---------------------|---------|---------|---|
| Peak-Picking | 8.2 | 0.08 | 0.1 s | 0.78 |
| Sparse-Deconv | 4.1 | 0.04 | 2 s | 0.90 |
| Transfer-Matrix-Fit | 2.8 | 0.02 | 10 s | 1.00 |
| DNN-THz | 3.5 | 0.03 | 0.3 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (TMF):  500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p116_hash>",
  "h_s": "sha256:<spec116_hash>",
  "h_b": "sha256:<bench116_hash>",
  "r": {"residual_norm": 2.8, "error_bound": 5.0, "ratio": 0.56},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep thz_imaging
pwm-node verify thz_imaging/coatlayer_s1.yaml
pwm-node mine thz_imaging/coatlayer_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
