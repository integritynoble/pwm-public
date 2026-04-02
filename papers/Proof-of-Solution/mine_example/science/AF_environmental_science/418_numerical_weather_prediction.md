# Principle #418 — Numerical Weather Prediction (NWP)

**Domain:** Environmental Science | **Carrier:** atmospheric state | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → N.bilinear.advection → ∂.space → B.periodic |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space→B.periodic   NWP          500hPa-forecast   semi-lag
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NUMERICAL WEATHER PREDICTION   P = (E,G,W,C)   Principle #418  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Primitive equations + data assimilation:               │
│        │ x_a = x_b + K(y − Hx_b)      (analysis update)       │
│        │ K = BH^T(HBH^T + R)^{-1}     (Kalman gain)           │
│        │ ∂x/∂t = M(x) + physics       (forecast model)        │
│        │ Forward: given obs y → analysis x_a → forecast x(t)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space] ──→ [B.periodic] │
│        │ derivative  nonlinear  derivative  boundary            │
│        │ V={∂.time, N.bilinear.advection, ∂.space, B.periodic}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space, ∂.space→B.periodic}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (well-posed for finite forecast horizon)│
│        │ Uniqueness: NO (chaotic; ensemble captures uncertainty)│
│        │ Stability: predictability limit ~2 weeks (Lorenz)     │
│        │ Mismatch: observation coverage, model error, resolution│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of 500 hPa geopotential height (m)           │
│        │ q = resolution-dependent                             │
│        │ T = {Z500_RMSE, ACC_score, forecast_day, K_leads}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Atmospheric state vector, observation operator dimensions consistent | PASS |
| S2 | 3D/4DVar or EnKF produce optimal analysis for Gaussian errors | PASS |
| S3 | Semi-implicit semi-Lagrangian time stepping stable at CFL > 1 | PASS |
| S4 | Z500 RMSE and ACC computable against ERA5 analysis | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nwp/global_forecast_s1_ideal.yaml
principle_ref: sha256:<p418_hash>
omega:
  grid: [0.25, 0.25]   # degrees
  levels: 60
  forecast_hours: 240   # 10 days
  dt: 720   # s
E:
  forward: "Primitive equations + parameterized physics"
  assimilation: 4DVar
  physics: [radiation, convection, boundary_layer, microphysics]
B:
  initial: {analysis: ERA5_like}
  lateral: {global: true}
I:
  scenario: medium_range_forecast
  lead_times: [24, 48, 72, 120, 240]   # hours
  resolutions: [1.0, 0.5, 0.25]   # degrees
O: [Z500_RMSE, T850_RMSE, ACC_Z500]
epsilon:
  Z500_RMSE_day5: 60.0   # m
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 0.25-deg global grid with 60 levels — operational NWP standard | PASS |
| S2 | 4DVar analysis well-posed; 10-day forecast within predictability | PASS |
| S3 | Semi-Lagrangian integrator stable at large dt | PASS |
| S4 | Z500 RMSE < 60 m at day 5 achievable at 0.25 deg | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# nwp/benchmark_forecast.yaml
spec_ref: sha256:<spec418_hash>
principle_ref: sha256:<p418_hash>
dataset:
  name: ERA5_verification
  reference: "ECMWF ERA5 reanalysis (Hersbach et al. 2020)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: GFS-like
    params: {res: 0.25, levels: 60}
    results: {Z500_RMSE_d5: 55, ACC_d5: 0.85}
  - solver: IFS-like
    params: {res: 0.1, levels: 90}
    results: {Z500_RMSE_d5: 42, ACC_d5: 0.90}
  - solver: ML-Pangu
    params: {model: transformer}
    results: {Z500_RMSE_d5: 45, ACC_d5: 0.88}
quality_scoring:
  - {max_Z500_d5: 40, Q: 1.00}
  - {max_Z500_d5: 55, Q: 0.90}
  - {max_Z500_d5: 70, Q: 0.80}
  - {max_Z500_d5: 100, Q: 0.75}
```

**Baseline solver:** GFS-like — Z500 RMSE 55 m at day 5
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Z500 RMSE (d5) | ACC (d5) | Runtime | Q |
|--------|---------------|---------|---------|---|
| GFS-like | 55 m | 0.85 | 2 hr | 0.90 |
| ML-Pangu | 45 m | 0.88 | 0.01 hr | 0.90 |
| IFS-like | 42 m | 0.90 | 8 hr | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p418_hash>",
  "h_s": "sha256:<spec418_hash>",
  "h_b": "sha256:<bench418_hash>",
  "r": {"Z500_RMSE_d5": 42, "ACC_d5": 0.90, "ratio": 0.76},
  "c": {"lead_times_tested": 5, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep nwp
pwm-node verify AF_environmental_science/nwp_forecast_s1_ideal.yaml
pwm-node mine AF_environmental_science/nwp_forecast_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
