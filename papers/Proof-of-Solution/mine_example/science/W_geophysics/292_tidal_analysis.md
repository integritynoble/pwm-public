# Principle #292 — Tidal Analysis and Prediction

**Domain:** Geophysics | **Carrier:** N/A (harmonic analysis) | **Difficulty:** Standard (δ=3)
**DAG:** F.dft → ∫.temporal → O.l2 |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          F.dft→∫.temporal→O.l2      tidal-ha    tide-gauge         harmonic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIDAL ANALYSIS AND PREDICTION    P = (E,G,W,C)   Principle #292│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ h(t) = h₀ + Σ [A_n cos(ω_n t − φ_n)]  (harmonic sum) │
│        │ ω_n = known tidal constituent frequencies (M2,S2,K1…)  │
│        │ Forward: given {A_n, φ_n} → predict water level h(t)  │
│        │ Inverse: given h(t) observations → fit A_n, φ_n       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [F.dft] ──→ [∫.temporal] ──→ [O.l2]                    │
│        │ transform  integrate  optimize                         │
│        │ V={F.dft, ∫.temporal, O.l2}  A={F.dft→∫.temporal, ∫.temporal→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear LS for harmonic coefficients)   │
│        │ Uniqueness: YES with Rayleigh criterion for freq sep.  │
│        │ Stability: well-conditioned for year-long records      │
│        │ Mismatch: non-tidal residuals (surge, river, seiches)  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖h_pred − h_obs‖₂ / ‖h_obs‖₂ (water level misfit)│
│        │ q = 2.0 (linear least-squares, exact solution)        │
│        │ T = {amplitude_error, phase_error, prediction_skill}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Harmonic sum well-defined; constituent frequencies from astronomy | PASS |
| S2 | Linear LS with known frequencies has unique solution | PASS |
| S3 | UTide/T_TIDE converge for >29-day records with >35 constituents | PASS |
| S4 | Prediction skill >0.95 for tidally dominated ports | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tidal_ha/tide_gauge_s1_ideal.yaml
principle_ref: sha256:<p292_hash>
omega:
  sampling: 6_min
  domain: single_station
  record_length: 365  # days
  dt: 360  # seconds
E:
  forward: "h(t) = h₀ + Σ A_n cos(ω_n t − φ_n)"
  constituents: 67  # standard set
  nodal_corrections: true
B:
  datum: MSL
  time_zone: UTC
I:
  scenario: semidiurnal_port
  dominant: M2
  M2_amplitude: 1.5  # metres
  noise_std: 0.02  # metres
O: [amplitude_error, phase_error, prediction_RMS]
epsilon:
  amplitude_error_max: 0.01  # metres
  phase_error_max: 1.0  # degrees
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 365-day record at 6-min resolves 67 constituents (Rayleigh) | PASS |
| S2 | Linear LS with 67 constituents well-overdetermined | PASS |
| S3 | UTide converges; confidence intervals from bootstrap | PASS |
| S4 | M2 amplitude error < 1 cm with 2 cm noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tidal_ha/benchmark_port.yaml
spec_ref: sha256:<spec292_hash>
principle_ref: sha256:<p292_hash>
dataset:
  name: synthetic_semidiurnal_port
  reference: "365-day synthetic tide gauge, 67 constituents"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: T_TIDE
    params: {constituents: auto, conf: 0.95}
    results: {M2_amp_error: 0.008, pred_RMS: 0.035}
  - solver: UTide
    params: {constituents: 67, method: IRLS}
    results: {M2_amp_error: 0.005, pred_RMS: 0.028}
  - solver: Harmonic-OLS
    params: {constituents: 67}
    results: {M2_amp_error: 0.006, pred_RMS: 0.030}
quality_scoring:
  - {min_pred_RMS: 0.015, Q: 1.00}
  - {min_pred_RMS: 0.025, Q: 0.90}
  - {min_pred_RMS: 0.040, Q: 0.80}
  - {min_pred_RMS: 0.060, Q: 0.75}
```

**Baseline solver:** UTide — prediction RMS 0.028 m
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | M2 Amp Err (m) | Pred RMS (m) | Runtime | Q |
|--------|----------------|-------------|---------|---|
| T_TIDE | 0.008 | 0.035 | 1 s | 0.80 |
| Harmonic-OLS | 0.006 | 0.030 | 0.5 s | 0.90 |
| UTide | 0.005 | 0.028 | 2 s | 0.90 |
| UTide+response | 0.003 | 0.012 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (UTide+resp): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p292_hash>",
  "h_s": "sha256:<spec292_hash>",
  "h_b": "sha256:<bench292_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.04, "ratio": 0.30},
  "c": {"fitted_rate": 2.00, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep tidal_ha
pwm-node verify tidal_ha/tide_gauge_s1_ideal.yaml
pwm-node mine tidal_ha/tide_gauge_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
