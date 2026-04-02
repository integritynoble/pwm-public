# Principle #359 — Thermal-Hydraulics (Two-Phase Reactor)

**Domain:** Nuclear Engineering | **Carrier:** coolant enthalpy/void | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → N.bilinear.advection → ∂.space → B.dirichlet |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space→B.dirichlet   two-phase    BWR-channel       drift-flux
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THERMAL-HYDRAULICS (TWO-PHASE) P = (E,G,W,C)   Principle #359 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂(ρ_m)/∂t + ∂(ρ_m u_m)/∂z = 0          (mass)        │
│        │ ∂(ρ_m u_m)/∂t + ∂(ρ_m u_m²)/∂z = −∂p/∂z − ρ_m g     │
│        │    − f/(2D_h) ρ_m |u_m| u_m              (momentum)   │
│        │ ∂(ρ_m h_m)/∂t + ∂(ρ_m u_m h_m)/∂z = q'''(z)  (energy)│
│        │ Drift-flux: u_g = C_0 j + V_gj            (closure)   │
│        │ Forward: given q'''(z), inlet BC → void, T, p profiles │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space] ──→ [B.dirichlet] │
│        │ derivative  nonlinear  derivative  boundary            │
│        │ V={∂.time, N.bilinear.advection, ∂.space, B.dirichlet}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space, ∂.space→B.dirichlet}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic system with drift-flux)     │
│        │ Uniqueness: YES for subcooled/saturated; conditional 2φ│
│        │ Stability: CFL-limited; Ledinegg instability possible  │
│        │ Mismatch: heat transfer correlations, drift-flux params │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error in void fraction |α−α_ref|/α_ref   │
│        │ q = 1.0 (upwind FVM), 2.0 (MUSCL)                    │
│        │ T = {void_error, T_clad_error, pressure_drop_error}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass/momentum/energy equations dimensionally consistent | PASS |
| S2 | Drift-flux model well-posed for vertical channel flow | PASS |
| S3 | Semi-implicit FVM converges with drift-flux closure | PASS |
| S4 | Void fraction error measurable against NUPEC/BFBT data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# thermal_hydraulics/bwr_channel_s1_ideal.yaml
principle_ref: sha256:<p359_hash>
omega:
  grid: [100]
  domain: vertical_channel_1D
  length: 3.66   # m (active fuel length)
  time: [0, 30.0]
  dt: 0.01
E:
  forward: "1D two-phase drift-flux model"
  closure: Chexal-Lellouche
B:
  inlet: {mass_flux: 1500, T_in: 550, p_in: 7.0e6}  # kg/m²s, K, Pa
  outlet: {p_out: 7.0e6}
I:
  scenario: BWR_heated_channel
  q_linear: 20.0   # kW/m
  mesh_sizes: [25, 50, 100]
O: [void_fraction_error, T_clad_error, pressure_drop_error]
epsilon:
  void_error_max: 0.02
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 cells over 3.66 m resolves axial profiles; dt CFL-safe | PASS |
| S2 | Subcooled inlet, boiling above saturation — well-posed with drift-flux | PASS |
| S3 | Semi-implicit scheme converges; drift-flux closure validated | PASS |
| S4 | Void error < 2% achievable against BFBT data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# thermal_hydraulics/benchmark_bwr.yaml
spec_ref: sha256:<spec359_hash>
principle_ref: sha256:<p359_hash>
dataset:
  name: NUPEC_BFBT_void
  reference: "NUPEC BWR Full-size Fine-mesh Bundle Tests"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RELAP5-upwind
    params: {N: 50, dt: 0.01}
    results: {void_err: 0.035, T_clad_err: 3.2}
  - solver: TRACE-SETS
    params: {N: 50, dt: 0.005}
    results: {void_err: 0.025, T_clad_err: 2.1}
  - solver: CTF-subchannel
    params: {N: 100, dt: 0.005}
    results: {void_err: 0.015, T_clad_err: 1.5}
quality_scoring:
  - {max_void_err: 0.01, Q: 1.00}
  - {max_void_err: 0.02, Q: 0.90}
  - {max_void_err: 0.04, Q: 0.80}
  - {max_void_err: 0.06, Q: 0.75}
```

**Baseline solver:** TRACE-SETS — void error 2.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Void Error | T_clad Error (K) | Runtime | Q |
|--------|-----------|-------------------|---------|---|
| RELAP5-upwind | 0.035 | 3.2 | 5 s | 0.80 |
| TRACE-SETS | 0.025 | 2.1 | 12 s | 0.90 |
| CTF-subchannel | 0.015 | 1.5 | 30 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (CTF):  500 × 0.90 = 450 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p359_hash>",
  "h_s": "sha256:<spec359_hash>",
  "h_b": "sha256:<bench359_hash>",
  "r": {"void_err": 0.015, "T_clad_err": 1.5, "dp_err": 0.02},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep thermal_hydraulics
pwm-node verify AB_nuclear_engineering/thermal_hydraulics_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/thermal_hydraulics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
