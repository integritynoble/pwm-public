# Principle #473 — Radiometric Calibration

**Domain:** Geodesy / Remote Sensing | **Carrier:** N/A (model-based) | **Difficulty:** Basic (δ=2)
**DAG:** [L.dense] --> [O.l2] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.dense-->O.l2  RadCal  CEOS-PICS  regression
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RADIOMETRIC CALIBRATION       P = (E,G,W,C)   Principle #473   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ L = G · DN + B   (linear radiometric model)            │
│        │ L = spectral radiance (W/m²/sr/μm)                     │
│        │ DN = digital number (raw sensor output)                │
│        │ ρ = π L d² / (E_sun cos θ_s τ)  (reflectance)         │
│        │ Forward: given (G,B,DN) → L → ρ                       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.dense] ──→ [O.l2]                                   │
│        │  radiative-transfer  least-squares                     │
│        │ V={L.dense,O.l2}  A={L.dense→O.l2}  L_DAG=1.0                    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear model always invertible if G≠0) │
│        │ Uniqueness: YES for given gain/offset                  │
│        │ Stability: sensitive to G drift over mission lifetime  │
│        │ Mismatch: nonlinearity at extremes, stray light        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |L_cal − L_ref|/L_ref  (radiance error)           │
│        │ q = N/A (calibration uncertainty)                     │
│        │ T = {radiance_error, reflectance_error, stability}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gain G > 0; radiance units consistent (W/m²/sr/μm) | PASS |
| S2 | Linear model valid within dynamic range | PASS |
| S3 | Regression on calibration targets converges | PASS |
| S4 | Radiance error < 3% with vicarious calibration | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rad_cal/satellite_abs_s1.yaml
principle_ref: sha256:<p473_hash>
omega:
  bands: 11
  domain: multispectral_imager
  mission_years: 5
E:
  forward: "L = G·DN + B → ρ = πLd²/(E_sun cos θ τ)"
  calibration_sources: [onboard_lamp, solar_diffuser, vicarious]
B:
  reference_sites: [Libya4, Railroad_Valley, Dome_C]
  ground_truth: SI_traceable_radiometers
I:
  scenario: absolute_radiometric_calibration
  methods: [prelaunch, onboard, vicarious, cross_calibration]
O: [radiance_error_pct, reflectance_error_pct, temporal_stability]
epsilon:
  radiance_error_max: 3.0    # percent
  stability_max: 1.0          # percent/year
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 11 bands cover VNIR-SWIR; reference sites well-characterized | PASS |
| S2 | SI-traceable standards ensure calibration hierarchy | PASS |
| S3 | Regression on PICS data converges for G and B | PASS |
| S4 | Radiance error < 3% achievable with vicarious + cross-cal | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# rad_cal/benchmark_pics.yaml
spec_ref: sha256:<spec473_hash>
principle_ref: sha256:<p473_hash>
dataset:
  name: CEOS_PICS_Libya4
  reference: "Cosnefroy et al. (1996) PICS radiometric calibration"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Prelaunch only
    params: {source: lab_calibration}
    results: {radiance_error: 5.2, stability: 2.1}
  - solver: Onboard + vicarious
    params: {source: solar_diffuser + Libya4}
    results: {radiance_error: 2.8, stability: 0.8}
  - solver: Full cross-calibration
    params: {source: PICS + SNO + onboard}
    results: {radiance_error: 1.5, stability: 0.4}
quality_scoring:
  - {min_err: 1.0, Q: 1.00}
  - {min_err: 2.0, Q: 0.90}
  - {min_err: 3.0, Q: 0.80}
  - {min_err: 5.0, Q: 0.75}
```

**Baseline solver:** Onboard + vicarious — radiance error 2.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Rad Error (%) | Stability (%/yr) | Runtime | Q |
|--------|-------------|-------------------|---------|---|
| Prelaunch only | 5.2 | 2.1 | — | 0.75 |
| Onboard + vicarious | 2.8 | 0.8 | 10 s | 0.80 |
| Cross-calibration | 1.5 | 0.4 | 60 s | 0.90 |
| Full harmonization | 0.8 | 0.2 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (full): 200 × 1.00 = 200 PWM
Floor:            200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p473_hash>",
  "h_s": "sha256:<spec473_hash>",
  "h_b": "sha256:<bench473_hash>",
  "r": {"radiance_error_pct": 0.8, "error_bound": 3.0, "ratio": 0.267},
  "c": {"stability_pct_yr": 0.2, "bands": 11, "K": 4},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep rad_cal
pwm-node verify rad_cal/satellite_abs_s1.yaml
pwm-node mine rad_cal/satellite_abs_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
