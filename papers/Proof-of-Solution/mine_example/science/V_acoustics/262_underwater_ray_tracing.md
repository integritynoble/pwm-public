# Principle #262 — Underwater Acoustic Propagation (Ray Tracing)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** G.point → K.green → ∫.path |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.green→∫.path    uw_ray       munk_profile        Bellhop
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  UNDERWATER ACOUSTIC PROPAGATION (RAY)  P = (E,G,W,C) Principle #262│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ d²r/ds² = ∇(1/c(z)) / (1/c(z))                       │
│        │ Ray equations in depth-dependent sound speed profile   │
│        │ Forward: given c(z), source depth → ray paths and TL  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.green] ──→ [∫.path]                   │
│        │ source  kernel  integrate                              │
│        │ V={G.point, K.green, ∫.path}  A={G.point→K.green, K.green→∫.path}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE theory for smooth c(z))            │
│        │ Uniqueness: YES (given initial angle and c(z))         │
│        │ Stability: caustic formation causes amplitude issues   │
│        │ Mismatch: sound speed profile errors, bottom loss      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TL error |TL−TL_ref| in dB (primary)              │
│        │ q = depends on ray density and caustic corrections    │
│        │ T = {TL_rms_error, ray_arrival_time_error}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sound speed profile smooth and positive; source depth valid | PASS |
| S2 | ODE theory guarantees unique ray paths for C¹ profiles | PASS |
| S3 | Bellhop/ray codes converge with angular density of launch rays | PASS |
| S4 | TL error bounded by comparison with normal-mode reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# uw_ray/munk_profile_propagation.yaml
principle_ref: sha256:<p262_hash>
omega:
  depth: 5000  # meters
  range: 100000  # meters (100 km)
  source_depth: 1000
E:
  forward: "ray tracing in Munk canonical sound speed profile"
  c_profile: munk_canonical
B:
  surface: pressure_release
  bottom: {type: absorbing, loss: 0.5_dB_per_wavelength}
I:
  scenario: munk_profile_propagation
  launch_angles: [-20, 20]  # degrees
  num_rays: [100, 500, 2000]
O: [TL_rms_error_dB, arrival_time_error]
epsilon:
  TL_rms_max: 2.0  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Munk profile smooth; 100 km range within ray-theory validity | PASS |
| S2 | Deep-water channel guides rays; well-posed ODE | PASS |
| S3 | 2000 rays produce converged TL at 100 km | PASS |
| S4 | TL rms error < 2 dB vs normal-mode benchmark | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# uw_ray/benchmark_munk_profile.yaml
spec_ref: sha256:<spec262_hash>
principle_ref: sha256:<p262_hash>
dataset:
  name: munk_profile_reference
  reference: "KRAKEN normal-mode solution (converged)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Bellhop (100 rays)
    params: {num_rays: 100, launch_angles: [-20, 20]}
    results: {TL_rms: 4.5, arrival_error: 0.08}
  - solver: Bellhop (500 rays)
    params: {num_rays: 500, launch_angles: [-20, 20]}
    results: {TL_rms: 1.8, arrival_error: 0.02}
  - solver: Bellhop (2000 rays, Gaussian beams)
    params: {num_rays: 2000, beam: gaussian}
    results: {TL_rms: 0.6, arrival_error: 0.005}
quality_scoring:
  - {min_TL_rms: 0.5, Q: 1.00}
  - {min_TL_rms: 2.0, Q: 0.90}
  - {min_TL_rms: 5.0, Q: 0.80}
  - {min_TL_rms: 10.0, Q: 0.75}
```

**Baseline solver:** Bellhop (500 rays) — TL rms 1.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | TL rms (dB) | Arrival Error (s) | Runtime | Q |
|--------|-------------|---------------------|---------|---|
| Bellhop (100 rays) | 4.5 | 0.08 | 2 s | 0.75 |
| Bellhop (500 rays) | 1.8 | 0.02 | 8 s | 0.90 |
| Bellhop (2000 rays) | 0.6 | 0.005 | 30 s | 1.00 |
| Bellhop (Gaussian beams) | 0.4 | 0.003 | 35 s | 1.00 |

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
  "h_p": "sha256:<p262_hash>",
  "h_s": "sha256:<spec262_hash>",
  "h_b": "sha256:<bench262_hash>",
  "r": {"residual_norm": 0.4, "error_bound": 2.0, "ratio": 0.20},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep uw_ray
pwm-node verify uw_ray/munk_profile_propagation.yaml
pwm-node mine uw_ray/munk_profile_propagation.yaml
pwm-node inspect sha256:<cert_hash>
```
