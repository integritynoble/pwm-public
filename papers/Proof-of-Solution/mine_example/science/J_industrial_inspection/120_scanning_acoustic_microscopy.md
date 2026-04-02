# Principle #120 — Scanning Acoustic Microscopy (SAM)

**Domain:** Industrial Inspection & NDE | **Carrier:** Acoustic Wave | **Difficulty:** Practitioner (δ=3)
**DAG:** G.pulse.acoustic --> K.green.acoustic --> S.raster | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.acoustic-->K.green.acoustic-->S.raster    SAM         ICDelam-30         Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SCANNING ACOUSTIC MICROSCOPY (SAM)  P = (E, G, W, C)  #120    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V(x,y,z_f) = ∫ R(θ) P(θ, z_f) dθ                    │
│        │ R(θ) = Fresnel reflection; P = pupil function          │
│        │ V(z) curve encodes elastic properties and layer depths │
│        │ Inverse: reconstruct subsurface features from C-scans  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.acoustic] --> [K.green.acoustic] --> [S.raster] │
│        │  FocusedUS  AcousticReflect  RasterScan                │
│        │ V={G.pulse.acoustic, K.green.acoustic, S.raster}  A={G.pulse.acoustic-->K.green.acoustic, K.green.acoustic-->S.raster}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (acoustic reflection always present)    │
│        │ Uniqueness: YES for layer count ≤ 3 with known v_mat  │
│        │ Stability: κ ≈ 10 (bonded IC), κ ≈ 50 (multi-layer)  │
│        │ Mismatch: coupling variation, attenuation anisotropy   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = delamination detection F1 (primary), area RMSE     │
│        │ q = 1.0 (reflection-based, single-iteration)          │
│        │ T = {F1_detection, area_accuracy, depth_accuracy}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Transducer frequency (50–200 MHz) resolves features at target depth | PASS |
| S2 | Reflection coefficient contrast > noise floor for delamination detection | PASS |
| S3 | Gate-windowed C-scan converges for multi-interface package | PASS |
| S4 | F1 ≥ 0.90 for delaminations ≥ 100 μm in IC packages | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sam/icdelam_s1.yaml
principle_ref: sha256:<p120_hash>
omega:
  frequency_MHz: 100
  focal_length_mm: 8
  scan_step_um: 10
  coupling: water
  bandwidth_pct: 60
E:
  forward: "V(x,y) = integral(R(theta) * P(theta, z_f), dtheta)"
  scan_type: C-scan
I:
  dataset: ICDelam_30
  samples: 30
  defect_types: [die_delamination, void, cracked_solder]
  noise: {type: gaussian, SNR_dB: 35}
O: [F1, area_accuracy]
epsilon:
  F1_min: 0.90
  area_accuracy_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 MHz in water gives resolution ≈ 15 μm; 10 μm scan step adequate | PASS |
| S2 | κ ≈ 10 for die-attach delamination at specified frequency | PASS |
| S3 | Time-gated C-scan extraction is single-pass, convergent | PASS |
| S4 | F1 ≥ 0.90 feasible for defects ≥ 100 μm | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sam/benchmark_s1.yaml
spec_ref: sha256:<spec120_hash>
principle_ref: sha256:<p120_hash>
dataset:
  name: ICDelam_30
  samples: 30
  cscan_size: [1024, 1024]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Amplitude-Threshold
    params: {threshold: -6dB}
    results: {F1: 0.84, area_accuracy: 0.78}
  - solver: Hilbert-Envelope
    params: {gate_ns: 20}
    results: {F1: 0.91, area_accuracy: 0.87}
  - solver: U-Net-SAM
    params: {pretrained: true}
    results: {F1: 0.96, area_accuracy: 0.94}
quality_scoring:
  - {min_F1: 0.95, Q: 1.00}
  - {min_F1: 0.92, Q: 0.90}
  - {min_F1: 0.90, Q: 0.80}
  - {min_F1: 0.85, Q: 0.75}
```

**Baseline solver:** Amplitude-Threshold — F1 0.84
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | F1 | Area Accuracy | Runtime | Q |
|--------|-----|--------------|---------|---|
| Amplitude-Threshold | 0.84 | 0.78 | 0.1 s | 0.75 |
| Hilbert-Envelope | 0.91 | 0.87 | 0.5 s | 0.85 |
| U-Net-SAM | 0.96 | 0.94 | 1 s | 1.00 |
| SAFT (Synthetic Aperture) | 0.93 | 0.90 | 5 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (U-Net-SAM):  300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p120_hash>",
  "h_s": "sha256:<spec120_hash>",
  "h_b": "sha256:<bench120_hash>",
  "r": {"residual_norm": 0.06, "error_bound": 0.10, "ratio": 0.60},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep sam
pwm-node verify sam/icdelam_s1.yaml
pwm-node mine sam/icdelam_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
