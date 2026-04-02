# Principle #277 — Ambient Noise Tomography

**Domain:** Geophysics | **Carrier:** N/A (correlation-based) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.temporal → ∫.path |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.temporal→∫.path      ant-tomo    regional-Vs       FTAN+tomo
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  AMBIENT NOISE TOMOGRAPHY         P = (E,G,W,C)   Principle #277│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ G(r₁,r₂,t) ≈ −dC(r₁,r₂,t)/dt  (Green's function)    │
│        │ C(τ) = ∫ u(r₁,t) u(r₂,t+τ) dt  (cross-correlation)   │
│        │ Forward: given Vs(x) → predict inter-station dispersion│
│        │ Inverse: given dispersion maps → 3-D Vs model          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.temporal] ──→ [∫.path]                │
│        │ kernel  integrate  integrate                           │
│        │ V={K.green, ∫.temporal, ∫.path}  A={K.green→∫.temporal, ∫.temporal→∫.path}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (stationary noise → Green's function)   │
│        │ Uniqueness: conditional on station density and azimuth  │
│        │ Stability: improves with longer correlation windows     │
│        │ Mismatch: non-uniform noise sources, seasonal variation │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖Vs_rec − Vs_true‖₂ / ‖Vs_true‖₂ (relative L2)   │
│        │ q = 1.0 (ray-based), 2.0 (finite-freq kernel)        │
│        │ T = {misfit, checkerboard_recovery, resolution_length} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Cross-correlation → Green's function relation well-established | PASS |
| S2 | FTAN extracts group velocities for periods 5–50 s reliably | PASS |
| S3 | Ray-based tomography converges for >200 paths on 1°×1° grid | PASS |
| S4 | Relative L2 error bounded by path density and period range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ant_tomo/regional_s1_ideal.yaml
principle_ref: sha256:<p277_hash>
omega:
  grid: [50, 50]
  domain: regional_500km
  periods: [5, 8, 12, 20, 30, 50]
E:
  forward: "ray-based group velocity prediction"
  correlation_length: 30_days
  stations: 80
B:
  boundary: ray_path_coverage > 5 per cell
I:
  scenario: regional_checkerboard
  anomaly_size: 50_km
  Vs_perturbation: 5%
O: [L2_Vs_error, checkerboard_recovery, path_density]
epsilon:
  L2_error_max: 5.0e-2
  recovery_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 80 stations yield >3000 paths; 50×50 grid well-sampled | PASS |
| S2 | Checkerboard anomalies ≥50 km resolved by 5–50 s periods | PASS |
| S3 | LSQR inversion converges in <100 iterations | PASS |
| S4 | L2 error < 5% with >70% checkerboard recovery | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ant_tomo/benchmark_regional.yaml
spec_ref: sha256:<spec277_hash>
principle_ref: sha256:<p277_hash>
dataset:
  name: synthetic_regional_checkerboard
  reference: "80-station network, 6 periods"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Ray-LSQR
    params: {iterations: 100, smoothing: 50km}
    results: {L2_error: 4.5e-2, recovery: 0.72}
  - solver: Ray-LSQR-TV
    params: {iterations: 100, TV_weight: 0.01}
    results: {L2_error: 3.2e-2, recovery: 0.81}
  - solver: Eikonal-Tomo
    params: {grid: 0.5deg}
    results: {L2_error: 2.8e-2, recovery: 0.85}
quality_scoring:
  - {min_L2: 1.0e-2, Q: 1.00}
  - {min_L2: 3.0e-2, Q: 0.90}
  - {min_L2: 5.0e-2, Q: 0.80}
  - {min_L2: 1.0e-1, Q: 0.75}
```

**Baseline solver:** Ray-LSQR — L2 error 4.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Recovery | Runtime | Q |
|--------|----------|----------|---------|---|
| Ray-LSQR | 4.5e-2 | 0.72 | 5 s | 0.80 |
| Ray-LSQR-TV | 3.2e-2 | 0.81 | 8 s | 0.90 |
| Eikonal-Tomo | 2.8e-2 | 0.85 | 15 s | 0.90 |
| Finite-freq kernel | 9.8e-3 | 0.92 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (finite-freq): 300 × 1.00 = 300 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p277_hash>",
  "h_s": "sha256:<spec277_hash>",
  "h_b": "sha256:<bench277_hash>",
  "r": {"residual_norm": 9.8e-3, "error_bound": 5.0e-2, "ratio": 0.196},
  "c": {"fitted_rate": 1.08, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep ant_tomo
pwm-node verify ant_tomo/regional_s1_ideal.yaml
pwm-node mine ant_tomo/regional_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
