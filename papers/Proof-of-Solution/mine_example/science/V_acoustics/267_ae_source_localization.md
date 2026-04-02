# Principle #267 — Acoustic Emission Source Localization

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** S.array → ∫.temporal → O.l2 |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.array→∫.temporal→O.l2    ae_loc       plate_AE_localize   TDOA/grid
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ACOUSTIC EMISSION SOURCE LOCALIZE   P = (E,G,W,C)   Principle #267 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Δtᵢⱼ = (|rᵢ−s| − |rⱼ−s|) / c_g                      │
│        │ TDOA-based localization from distributed sensors       │
│        │ Forward: given sensor positions, arrivals → source s   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.array] ──→ [∫.temporal] ──→ [O.l2]                  │
│        │ sample  integrate  optimize                            │
│        │ V={S.array, ∫.temporal, O.l2}  A={S.array→∫.temporal, ∫.temporal→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (overdetermined nonlinear system)       │
│        │ Uniqueness: YES with ≥4 sensors in 3D (non-degenerate)│
│        │ Stability: sensitive to arrival time picking and vel.  │
│        │ Mismatch: anisotropic wave speed, multipath, dispersion│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = source location error ‖ŝ−s_true‖ in mm (primary)  │
│        │ q = depends on picking accuracy and geometry          │
│        │ T = {location_error, residual_TDOA, confidence_ellipse}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sensor coordinates and wave speed model well-defined | PASS |
| S2 | Overdetermined TDOA system solvable with ≥4 sensors | PASS |
| S3 | Geiger's method / grid search converge for typical plate geometries | PASS |
| S4 | Location error bounded by TDOA uncertainty and GDOP | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ae_loc/plate_AE_localization.yaml
principle_ref: sha256:<p267_hash>
omega:
  plate: {Lx: 1.0, Ly: 1.0, thickness: 0.005}  # meters
  sensors: [[0,0],[1,0],[0,1],[1,1],[0.5,0.5],[0.5,0]]
  group_velocity: 5000  # m/s (S0 Lamb wave)
E:
  forward: "TDOA hyperbolic localization"
I:
  scenario: plate_AE_localization
  noise_std: [1e-7, 1e-6, 1e-5]  # seconds
O: [location_error_mm, TDOA_residual]
epsilon:
  location_error_max: 5.0  # mm
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 sensors on 1×1 m plate; good GDOP coverage | PASS |
| S2 | Isotropic plate with single S0 mode; well-posed TDOA | PASS |
| S3 | Grid search + Gauss-Newton converge for 1 μs noise | PASS |
| S4 | Location error < 5 mm for noise_std ≤ 1 μs | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ae_loc/benchmark_plate_AE.yaml
spec_ref: sha256:<spec267_hash>
principle_ref: sha256:<p267_hash>
dataset:
  name: plate_AE_reference
  reference: "Simulated pencil-lead break at known location"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Grid search
    params: {grid_res: 1mm, noise: 1e-6}
    results: {location_error: 3.2, TDOA_residual: 5e-7}
  - solver: Geiger's method
    params: {iterations: 20, noise: 1e-6}
    results: {location_error: 1.5, TDOA_residual: 2e-7}
  - solver: Bayesian MCMC
    params: {samples: 10000, noise: 1e-6}
    results: {location_error: 0.8, TDOA_residual: 1e-7}
quality_scoring:
  - {min_loc_err: 0.5, Q: 1.00}
  - {min_loc_err: 2.0, Q: 0.90}
  - {min_loc_err: 5.0, Q: 0.80}
  - {min_loc_err: 10.0, Q: 0.75}
```

**Baseline solver:** Geiger's method — location error 1.5 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Location Error (mm) | TDOA Residual (s) | Runtime | Q |
|--------|--------------------|--------------------|---------|---|
| Grid search (1 mm) | 3.2 | 5e-7 | 2 s | 0.80 |
| Geiger's method | 1.5 | 2e-7 | 0.1 s | 0.90 |
| Levenberg-Marquardt | 1.2 | 1.5e-7 | 0.05 s | 0.90 |
| Bayesian MCMC | 0.8 | 1e-7 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p267_hash>",
  "h_s": "sha256:<spec267_hash>",
  "h_b": "sha256:<bench267_hash>",
  "r": {"residual_norm": 0.8, "error_bound": 5.0, "ratio": 0.16},
  "c": {"fitted_rate": 1.0, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep ae_loc
pwm-node verify ae_loc/plate_AE_localization.yaml
pwm-node mine ae_loc/plate_AE_localization.yaml
pwm-node inspect sha256:<cert_hash>
```
