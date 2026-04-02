# Principle #276 — Seismic Reflection Processing

**Domain:** Geophysics | **Carrier:** N/A (signal processing) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.path → L.sparse |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.path→L.sparse      seis-refl   CMP-gather        NMO+stack
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEISMIC REFLECTION PROCESSING    P = (E,G,W,C)   Principle #276│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ t(x)² = t₀² + x²/v_rms²   (NMO hyperbola)            │
│        │ CMP stacking enhances S/N by √N (N = fold)            │
│        │ Forward: given v_rms(t₀) → predict travel-times        │
│        │ Inverse: given CMP gathers → velocity analysis + image │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.path] ──→ [L.sparse]                  │
│        │ kernel  integrate  linear-op                           │
│        │ V={K.green, ∫.path, L.sparse}  A={K.green→∫.path, ∫.path→L.sparse}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic moveout for flat layers)    │
│        │ Uniqueness: YES for 1-D; dip-dependent in 2-D/3-D     │
│        │ Stability: stacking improves SNR; sensitive to v_rms   │
│        │ Mismatch: NMO stretch, anisotropy, multiples           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖image − reflectivity_true‖₂ / ‖reflectivity‖₂    │
│        │ q = 1.0 (post-stack), 2.0 (pre-stack depth migration) │
│        │ T = {SNR_improvement, velocity_semblance, image_res}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | NMO equation dimensionally correct; CMP geometry well-defined | PASS |
| S2 | Flat-layer NMO exact; velocity semblance identifies v_rms | PASS |
| S3 | CMP stack converges; Kirchhoff migration images reflectors | PASS |
| S4 | Image quality bounded by fold, bandwidth, and velocity accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# seis_refl/cmp_s1_ideal.yaml
principle_ref: sha256:<p276_hash>
omega:
  traces_per_cmp: 48
  cmp_range: [0, 5000]  # metres
  time: [0, 3.0]  # seconds
  dt: 0.002
E:
  forward: "t² = t₀² + x²/v_rms²"
  source_wavelet: ricker_30Hz
B:
  surface: free
  reflectors: [500, 1200, 2000]  # metres depth
I:
  scenario: three_layer_flat
  fold: 48
  v_rms: [1500, 2000, 2800]
O: [SNR_stacked, reflector_depth_error, velocity_error]
epsilon:
  SNR_min: 20.0  # dB
  depth_error_max: 5.0  # metres
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 48-fold coverage adequate; dt=2ms satisfies Nyquist at 30 Hz | PASS |
| S2 | Three flat reflectors give unambiguous NMO velocities | PASS |
| S3 | Semblance velocity picking + CMP stack converge | PASS |
| S4 | Depth error < 5 m achievable with 48-fold stack | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# seis_refl/benchmark_cmp.yaml
spec_ref: sha256:<spec276_hash>
principle_ref: sha256:<p276_hash>
dataset:
  name: synthetic_3layer_cmp
  reference: "Three-layer flat reflector model"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: NMO-stack
    params: {fold: 48, mute: 30deg}
    results: {SNR: 22.0, depth_error: 3.5}
  - solver: Kirchhoff-poststack
    params: {aperture: 2000m}
    results: {SNR: 25.0, depth_error: 2.1}
  - solver: Kirchhoff-prestack
    params: {aperture: 3000m, angle_range: [0,40]}
    results: {SNR: 28.0, depth_error: 1.2}
quality_scoring:
  - {min_SNR: 30.0, Q: 1.00}
  - {min_SNR: 25.0, Q: 0.90}
  - {min_SNR: 20.0, Q: 0.80}
  - {min_SNR: 15.0, Q: 0.75}
```

**Baseline solver:** NMO-stack — SNR 22.0 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | SNR (dB) | Depth Error (m) | Runtime | Q |
|--------|----------|-----------------|---------|---|
| NMO-stack | 22.0 | 3.5 | 1 s | 0.80 |
| Kirchhoff-post | 25.0 | 2.1 | 5 s | 0.90 |
| Kirchhoff-pre | 28.0 | 1.2 | 30 s | 0.90 |
| RTM-prestack | 32.0 | 0.5 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RTM): 300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p276_hash>",
  "h_s": "sha256:<spec276_hash>",
  "h_b": "sha256:<bench276_hash>",
  "r": {"residual_norm": 0.5, "error_bound": 5.0, "ratio": 0.10},
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
pwm-node benchmarks | grep seis_refl
pwm-node verify seis_refl/cmp_s1_ideal.yaml
pwm-node mine seis_refl/cmp_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
