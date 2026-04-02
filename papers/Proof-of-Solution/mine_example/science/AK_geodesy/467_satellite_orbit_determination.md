# Principle #467 — Satellite Orbit Determination

**Domain:** Geodesy | **Carrier:** N/A (ODE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [N.bilinear.pair] --> [∂.time.symplectic] --> [O.l2] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin.pair-->∂.t.symp-->O.l2  SatOrbit  LEO-tracking  batch-LSQ/filter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SATELLITE ORBIT DETERMINATION  P = (E,G,W,C)  Principle #467   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r̈ = −(GM/r³)r + a_J2 + a_drag + a_SRP + a_3body + …  │
│        │ a_J2 = perturbation from Earth's oblateness (J2,J3,…)  │
│        │ Observation: ρ = h(r,v,params) + ε  (range/Doppler)    │
│        │ Forward: given force model + obs → estimate (r₀,v₀)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin.pair] ──→ [∂.t.symp] ──→ [O.l2]               │
│        │  gravity-pair  symplectic-step  orbit-fit              │
│        │ V={N.bilin.pair,∂.t.symp,O.l2}  A={N.bilin.pair→∂.t.symp,∂.t.symp→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Keplerian + perturbations smooth)      │
│        │ Uniqueness: YES with sufficient tracking data          │
│        │ Stability: Lyapunov exponents bounded for LEO/MEO      │
│        │ Mismatch: atmospheric drag uncertainty, SRP modeling   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖r_est − r_truth‖₂  (orbit position error, m)    │
│        │ q = varies by integrator order (RK7/8 → ~8)          │
│        │ T = {position_RMS, velocity_RMS, residual_RMS}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Force model terms dimensionally consistent (m/s²); state vector 6D | PASS |
| S2 | Sufficient tracking arcs ensure observability of all 6 elements | PASS |
| S3 | Batch LSQ and sequential filter converge with cm-level residuals | PASS |
| S4 | Orbit error bounded by observation noise × geometry factor | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sat_orbit/leo_pod_s1.yaml
principle_ref: sha256:<p467_hash>
omega:
  satellite: LEO_600km
  domain: full_orbit
  time: [0, 86400.0]     # 1 day arc
  integrator_step: 30.0   # seconds
E:
  forward: "Newtonian gravity + J2-J20 + drag + SRP + 3rd body"
  gravity_model: EGM2008_degree70
  drag_model: NRLMSISE-00
  SRP: cannonball
B:
  tracking: {SLR: 10_stations, GNSS: onboard_receiver}
  observations_per_day: 2000
I:
  scenario: LEO_precise_orbit_determination
  force_models: [gravity_only, gravity+drag, full]
O: [position_RMS, velocity_RMS, SLR_residual_RMS]
epsilon:
  position_RMS_max: 0.05    # meters
  SLR_residual_max: 0.02    # meters
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | LEO at 600 km; 2000 obs/day provides good coverage | PASS |
| S2 | Force model complete for cm-level POD | PASS |
| S3 | Batch LSQ converges within 5 iterations | PASS |
| S4 | Position RMS < 5 cm with full force model + SLR+GNSS | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sat_orbit/benchmark_leo_pod.yaml
spec_ref: sha256:<spec467_hash>
principle_ref: sha256:<p467_hash>
dataset:
  name: GRACE_POD_validation
  reference: "GFZ GRACE precise orbit (Kang et al., 2006)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Batch LSQ (gravity only)
    params: {gravity: J2-J6, drag: none}
    results: {position_RMS: 15.0, SLR_residual: 8.2}
  - solver: Batch LSQ (full model)
    params: {gravity: EGM2008_70, drag: NRLMSISE, SRP: cannonball}
    results: {position_RMS: 0.035, SLR_residual: 0.018}
  - solver: Reduced-dynamic (GNSS)
    params: {empirical_accel: piecewise_constant_15min}
    results: {position_RMS: 0.022, SLR_residual: 0.012}
quality_scoring:
  - {min_RMS: 0.02, Q: 1.00}
  - {min_RMS: 0.05, Q: 0.90}
  - {min_RMS: 0.10, Q: 0.80}
  - {min_RMS: 1.0, Q: 0.75}
```

**Baseline solver:** Batch LSQ (full) — position RMS 3.5 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pos RMS (m) | SLR Resid (m) | Runtime | Q |
|--------|-------------|---------------|---------|---|
| Batch (gravity only) | 15.0 | 8.2 | 10 s | 0.75 |
| Batch (full model) | 0.035 | 0.018 | 120 s | 0.90 |
| Reduced-dynamic | 0.022 | 0.012 | 180 s | 1.00 |
| Kinematic GNSS | 0.045 | 0.025 | 60 s | 0.80 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (reduced-dynamic): 400 × 1.00 = 400 PWM
Floor:                       400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p467_hash>",
  "h_s": "sha256:<spec467_hash>",
  "h_b": "sha256:<bench467_hash>",
  "r": {"position_RMS": 0.022, "error_bound": 0.05, "ratio": 0.440},
  "c": {"SLR_residual": 0.012, "arc_length": 86400, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep sat_orbit
pwm-node verify sat_orbit/leo_pod_s1.yaml
pwm-node mine sat_orbit/leo_pod_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
