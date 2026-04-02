# Principle #177 — RANS k-omega SST Model

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→N.pointwise.turbmodel→B.wall   RANS-SST    bump-channel      FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RANS k-ω SST   P = (E,G,W,C)   Principle #177                 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂ū/∂t + (ū·∇)ū = −∇p̄/ρ + ∇·[(ν+νₜ)∇ū]              │
│        │ ∂k/∂t + ū·∇k = P̃ₖ − β*kω + ∇·[(ν+σₖνₜ)∇k]          │
│        │ ∂ω/∂t + ū·∇ω = αS² − βω² + ∇·[(ν+σωνₜ)∇ω] + CDₖω  │
│        │ νₜ = a₁k/max(a₁ω, SF₂); blending F₁,F₂ functions    │
│        │ Menter (1994) blends k-ω (wall) ↔ k-ε (freestream)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall]│
│        │ time  momentum  pressure  k-ω-SST  wall-resolve                                             │
│        │ V={∂.time,N.bilinear.advection,L.poisson,N.pointwise.turbmodel,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (SST well-posed for attached/mild sep.) │
│        │ Uniqueness: YES for converged steady state             │
│        │ Stability: requires y⁺ < 1 for full resolution        │
│        │ Mismatch: blending function tuning, separation onset   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in mean velocity vs DNS/expt     │
│        │ q = 2.0 (2nd-order FVM)                               │
│        │ T = {velocity_error, Cf_error, separation_point_err}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SST closure complete; blending functions well-defined | PASS |
| S2 | SST resolves BL without wall functions at y⁺<1 | PASS |
| S3 | SIMPLE/PISO converges; SST more robust than k-ε near walls | PASS |
| S4 | Mean velocity error < 3% vs DNS for adverse-pressure-gradient flows | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rans_sst/bump_channel_s1.yaml
principle_ref: sha256:<p177_hash>
omega:
  grid: [200, 100]
  domain: channel_with_bump
  bump_height: 0.05
E:
  forward: "RANS + k-ω SST"
B:
  walls: {type: no_slip, y_plus: 1}
  inlet: {velocity_profile: parabolic}
  outlet: {zero_gradient: true}
I:
  scenario: bump_in_channel
  Re: 10000
  mesh_sizes: [100x50, 200x100]
O: [L2_velocity_error, Cf_error, separation_length_error]
epsilon:
  L2_error_max: 3.0e-2
  sep_length_error_max: 10%
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh resolves y⁺<1; bump geometry well-defined | PASS |
| S2 | SST appropriate for mild adverse pressure gradient | PASS |
| S3 | SIMPLE converges; separation bubble captured | PASS |
| S4 | L2 error < 3% achievable with fine mesh | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# rans_sst/benchmark_bump.yaml
spec_ref: sha256:<spec177_hash>
principle_ref: sha256:<p177_hash>
dataset:
  name: NASA_bump_DNS
  reference: "NASA Turbulence Modeling Resource"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OpenFOAM (k-ω SST)
    params: {mesh: 200x100, y_plus: 0.8}
    results: {L2_error: 2.5e-2, Cf_error: 2.8%}
  - solver: OpenFOAM (k-ε realizable)
    params: {mesh: 200x100, wall_fn: true}
    results: {L2_error: 4.2e-2, Cf_error: 5.1%}
  - solver: SU2 (k-ω SST)
    params: {mesh: 200x100}
    results: {L2_error: 2.6e-2, Cf_error: 2.9%}
quality_scoring:
  - {min_L2: 1.0e-2, Q: 1.00}
  - {min_L2: 2.5e-2, Q: 0.90}
  - {min_L2: 4.0e-2, Q: 0.80}
  - {min_L2: 6.0e-2, Q: 0.75}
```

**Baseline solver:** OpenFOAM k-ω SST — L2 error 2.5×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Cf Error | Runtime | Q |
|--------|----------|----------|---------|---|
| k-ε realizable | 4.2e-2 | 5.1% | 30 s | 0.80 |
| k-ω SST (coarse) | 3.5e-2 | 3.8% | 45 s | 0.80 |
| k-ω SST (fine) | 2.5e-2 | 2.8% | 120 s | 0.90 |
| k-ω SST + transition | 1.8e-2 | 2.0% | 180 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 0.90 = 270 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p177_hash>",
  "h_s": "sha256:<spec177_hash>",
  "h_b": "sha256:<bench177_hash>",
  "r": {"residual_norm": 1.8e-2, "error_bound": 3.0e-2, "ratio": 0.60},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 2},
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep rans_sst
pwm-node verify rans_sst/bump_channel_s1.yaml
pwm-node mine rans_sst/bump_channel_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
