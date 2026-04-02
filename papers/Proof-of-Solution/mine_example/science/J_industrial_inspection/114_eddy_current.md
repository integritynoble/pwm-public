# Principle #114 — Eddy Current Testing (ECT)

**Domain:** Industrial Inspection | **Carrier:** EM (AC field) | **Difficulty:** Standard (δ=3)
**DAG:** G.cw --> K.green.em --> S.raster | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.cw-->K.green.em-->S.raster    ECT        ECT-TubeDefect      Inversion
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ECT   P = (E, G, W, C)   Principle #114                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔZ(x) = ∫ Δσ(r)·E_inc(r)·E_scat(r) dr               │
│        │ Impedance change ΔZ due to conductivity perturbation   │
│        │ E_inc = excitation field; Δσ = defect conductivity     │
│        │ Inverse: recover defect profile from impedance scan    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.cw] --> [K.green.em] --> [S.raster]                   │
│        │ ACExcite  EMResponse  RasterScan                        │
│        │ V={G.cw, K.green.em, S.raster}  A={G.cw-->K.green.em, K.green.em-->S.raster}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (impedance responds to conductivity)    │
│        │ Uniqueness: CONDITIONAL (depth-size ambiguity)         │
│        │ Stability: κ ≈ 15 (surface), κ ≈ 60 (subsurface)      │
│        │ Mismatch: lift-off variation, permeability changes      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = defect depth RMSE (primary), sizing error (sec.)   │
│        │ q = 2.0 (Born-approximation inversion convergence)    │
│        │ T = {depth_RMSE_mm, sizing_error_mm}                   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Excitation frequency and coil size match skin depth | PASS |
| S2 | Born approximation valid for small defects; κ ≈ 15 | PASS |
| S3 | Iterative Born inversion converges for calibrated probe | PASS |
| S4 | Depth RMSE < 0.5 mm achievable for surface cracks | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ect/tube_s1_ideal.yaml
principle_ref: sha256:<p114_hash>
omega:
  scan_length_mm: 500
  scan_points: 256
  frequencies_kHz: [100, 300, 500]
E:
  forward: "ΔZ = ∫ Δσ·E_inc·E_scat dr"
I:
  dataset: ECT_TubeDefect
  scans: 60
  noise: {type: gaussian, SNR_dB: 30}
  scenario: ideal
O: [depth_RMSE_mm, detection_pct]
epsilon:
  depth_RMSE_max_mm: 0.5
  detection_min_pct: 95.0
```

### S1-S4 Table (Layer 2) — All gates PASS

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
baselines:
  - solver: Impedance-Plane
    results: {depth_RMSE_mm: 0.42, detection_pct: 96.1}
  - solver: Born-Inversion
    results: {depth_RMSE_mm: 0.28, detection_pct: 97.8}
  - solver: ECT-Net
    results: {depth_RMSE_mm: 0.15, detection_pct: 99.2}
quality_scoring:
  - {max_RMSE: 0.15, Q: 1.00}
  - {max_RMSE: 0.30, Q: 0.90}
  - {max_RMSE: 0.50, Q: 0.80}
  - {max_RMSE: 0.80, Q: 0.75}
```

**Baseline:** Impedance-Plane — RMSE 0.42 mm | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (mm) | Detection (%) | Q |
|--------|-----------|---------------|---|
| Impedance-Plane | 0.42 | 96.1 | 0.80 |
| Born-Inversion | 0.28 | 97.8 | 0.90 |
| ECT-Net | 0.15 | 99.2 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p114_hash>", "Q": 0.90,
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

## Quick-Start

```bash
pwm-node benchmarks | grep ect
pwm-node mine ect/tube_s1_ideal.yaml
```
