# Principle #79 — High Dynamic Range (HDR) Imaging

**Domain:** Computational Photography | **Carrier:** Photon | **Difficulty:** Moderate (δ=3)
**DAG:** L.diag.gray --> integral.temporal --> N.pointwise.log | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         L.diag.gray-->integral.temporal-->N.pointwise.log    HDR-Fuse    HDR-Bracket-20    Debevec
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HDR IMAGING   P = (E, G, W, C)   Principle #79                 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_k(r) = f(x(r) · Δt_k) + n_k(r),  k = 1..K          │
│        │ f = camera response function (CRF); Δt_k = exposure k  │
│        │ x = scene radiance; y_k = LDR capture at exposure k    │
│        │ Inverse: recover x and f from bracket set {y_k, Δt_k}  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.gray] --> [integral.temporal] --> [N.pointwise.log]│
│        │  Exposure  Integrate  CRF                               │
│        │ V={L.diag.gray, integral.temporal, N.pointwise.log}  A={L.diag.gray-->integral.temporal, integral.temporal-->N.pointwise.log}   L_DAG=3.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (overlapping exposures cover full DR)    │
│        │ Uniqueness: YES if CRF monotonic and exposures overlap  │
│        │ Stability: κ ≈ 4 (well-spaced brackets), κ ≈ 25 (poor) │
│        │ Mismatch: camera motion, CRF estimation error           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = HDR-VDP-3 Q-score (primary), PU-PSNR (secondary)   │
│        │ q = 2.0 (Debevec-Malik merging convergence)            │
│        │ T = {residual_norm, DR_recovered_stops, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Exposure brackets span target DR; CRF samples cover [0,255] | PASS |
| S2 | Overlapping exposures → unique radiance per pixel region | PASS |
| S3 | Debevec-Malik weighted merge converges; CRF recovery stable | PASS |
| S4 | PU-PSNR ≥ 35 dB achievable for 5-bracket HDR | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hdr/bracket_s1_ideal.yaml
principle_ref: sha256:<p079_hash>
omega:
  grid: [1024, 768]
  pixel_um: 4.0
  exposures: 5
  EV_range: [-2, +2]
  bit_depth: 8
E:
  forward: "y_k = f(x · Δt_k) + n_k"
  CRF: "Monotonic, estimated via Debevec-Malik"
I:
  dataset: HDR_Bracket_20
  scenes: 20
  noise: {type: heteroscedastic, read_sigma: 3.0, gain: 0.5}
  scenario: ideal
O: [PU_PSNR, HDR_VDP_Q]
epsilon:
  PU_PSNR_min: 35.0
  HDR_VDP_Q_min: 70.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 5 exposures spanning ±2 EV at 8-bit depth | PASS |
| S2 | κ ≈ 4 for 5-bracket well-spaced set | PASS |
| S3 | Debevec-Malik CRF recovery and merge converge | PASS |
| S4 | PU-PSNR ≥ 35 dB feasible for 5-bracket indoor scenes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hdr/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec079_hash>
principle_ref: sha256:<p079_hash>
dataset:
  name: HDR_Bracket_20
  scenes: 20
  size: [1024, 768]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Debevec-Malik
    params: {lambda_smooth: 50}
    results: {PU_PSNR: 36.2, HDR_VDP_Q: 72.5}
  - solver: Mertens-Exposure-Fusion
    params: {weights: [1,1,1]}
    results: {PU_PSNR: 34.8, HDR_VDP_Q: 68.0}
  - solver: DeepHDR
    params: {pretrained: true}
    results: {PU_PSNR: 41.5, HDR_VDP_Q: 82.3}
quality_scoring:
  - {min: 41.0, Q: 1.00}
  - {min: 38.0, Q: 0.90}
  - {min: 35.0, Q: 0.80}
  - {min: 32.0, Q: 0.75}
```

**Baseline solver:** Debevec-Malik — PU-PSNR 36.2 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PU-PSNR (dB) | HDR-VDP Q | Runtime | Q |
|--------|--------------|-----------|---------|---|
| Mertens-Fusion | 34.8 | 68.0 | 0.3 s | 0.78 |
| Debevec-Malik | 36.2 | 72.5 | 0.5 s | 0.82 |
| DeepHDR | 41.5 | 82.3 | 1.5 s | 0.98 |
| HDR-Transformer | 39.8 | 78.1 | 2.0 s | 0.93 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DeepHDR):  300 × 0.98 = 294 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p079_hash>",
  "h_s": "sha256:<spec079_hash>",
  "h_b": "sha256:<bench079_hash>",
  "r": {"residual_norm": 0.005, "error_bound": 0.015, "ratio": 0.33},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.98,
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
| L4 Solution | — | 225–294 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep hdr
pwm-node verify hdr/bracket_s1_ideal.yaml
pwm-node mine hdr/bracket_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
