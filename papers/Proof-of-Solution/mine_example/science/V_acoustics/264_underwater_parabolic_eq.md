# Principle #264 — Underwater Acoustics (Parabolic Equation)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** ∂.space → ∂.time → B.absorbing |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space→∂.time→B.absorbing    uw_pe        range_dep_wedge     RAM/PE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  UNDERWATER ACOUSTICS (PARABOLIC EQ) P = (E,G,W,C)   Principle #264 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂ψ/∂r = i/(2k₀)[∂²/∂z² + k₀²(n²−1)]ψ               │
│        │ One-way marching PE in range-dependent environments    │
│        │ Forward: given c(r,z), source → march field to range  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space] ──→ [∂.time] ──→ [B.absorbing]               │
│        │ derivative  derivative  boundary                       │
│        │ V={∂.space, ∂.time, B.absorbing}  A={∂.space→∂.time, ∂.time→B.absorbing}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic approximation well-posed)    │
│        │ Uniqueness: YES (marching problem with initial field)  │
│        │ Stability: Padé approximants stabilize wide-angle PE   │
│        │ Mismatch: backscatter neglected; narrow-angle error    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TL error |TL−TL_ref| in dB (primary)              │
│        │ q = 2.0 (standard PE), 4.0 (wide-angle Padé)         │
│        │ T = {TL_rms_error, phase_error, range_convergence}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Initial field and range-dependent c(r,z) well-defined | PASS |
| S2 | Parabolic approximation valid for small propagation angles | PASS |
| S3 | Split-step Fourier / Crank-Nicolson PE converge with Δr, Δz | PASS |
| S4 | TL error bounded by comparison with coupled-mode reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# uw_pe/range_dependent_wedge.yaml
principle_ref: sha256:<p264_hash>
omega:
  depth_start: 200  # meters
  depth_end: 0  # meters (wedge)
  range: 4000  # meters
  source_depth: 100
E:
  forward: "split-step Fourier parabolic equation"
  frequency: 25  # Hz
B:
  surface: pressure_release
  bottom: {type: fluid, c: 1700, rho: 1.5}
I:
  scenario: range_dependent_wedge
  dr: [10, 5, 2]  # range step in meters
  dz: [1.0, 0.5, 0.25]
O: [TL_rms_error_dB, phase_error]
epsilon:
  TL_rms_max: 1.0  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Wedge bathymetry smooth; PE grid adequate at 25 Hz | PASS |
| S2 | ASA benchmark wedge has coupled-mode reference solution | PASS |
| S3 | RAM PE converges with Δr=2 m, Δz=0.25 m | PASS |
| S4 | TL rms < 1 dB vs coupled-mode solution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# uw_pe/benchmark_wedge.yaml
spec_ref: sha256:<spec264_hash>
principle_ref: sha256:<p264_hash>
dataset:
  name: ASA_wedge_benchmark
  reference: "ASA benchmark coupled-mode solution (Jensen & Ferla)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RAM (standard PE, Δr=10)
    params: {dr: 10, dz: 1.0, pade_order: 1}
    results: {TL_rms: 3.5, phase_error: 0.15}
  - solver: RAM (wide-angle, Δr=5)
    params: {dr: 5, dz: 0.5, pade_order: 3}
    results: {TL_rms: 0.8, phase_error: 0.03}
  - solver: RAM (wide-angle, Δr=2)
    params: {dr: 2, dz: 0.25, pade_order: 4}
    results: {TL_rms: 0.2, phase_error: 0.005}
quality_scoring:
  - {min_TL_rms: 0.2, Q: 1.00}
  - {min_TL_rms: 1.0, Q: 0.90}
  - {min_TL_rms: 3.0, Q: 0.80}
  - {min_TL_rms: 5.0, Q: 0.75}
```

**Baseline solver:** RAM (wide-angle, Δr=5) — TL rms 0.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | TL rms (dB) | Phase Error | Runtime | Q |
|--------|-------------|-------------|---------|---|
| RAM (Padé-1, Δr=10) | 3.5 | 0.15 | 3 s | 0.75 |
| RAM (Padé-3, Δr=5) | 0.8 | 0.03 | 12 s | 0.90 |
| RAM (Padé-4, Δr=2) | 0.2 | 0.005 | 45 s | 1.00 |
| Split-step Fourier PE | 0.3 | 0.008 | 30 s | 1.00 |

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
  "h_p": "sha256:<p264_hash>",
  "h_s": "sha256:<spec264_hash>",
  "h_b": "sha256:<bench264_hash>",
  "r": {"residual_norm": 0.2, "error_bound": 1.0, "ratio": 0.20},
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
pwm-node benchmarks | grep uw_pe
pwm-node verify uw_pe/range_dependent_wedge.yaml
pwm-node mine uw_pe/range_dependent_wedge.yaml
pwm-node inspect sha256:<cert_hash>
```
