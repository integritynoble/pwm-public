# Principle #176 — RANS k-epsilon Model

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→N.pointwise.turbmodel→B.wall   RANS-kε     channel-Re395     FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RANS k-ε MODEL   P = (E,G,W,C)   Principle #176               │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂ū/∂t + (ū·∇)ū = −∇p̄/ρ + ∇·[(ν+νₜ)∇ū] + f         │
│        │ ∇·ū = 0                                                │
│        │ ∂k/∂t + ū·∇k = ∇·[(ν+νₜ/σₖ)∇k] + Pₖ − ε            │
│        │ ∂ε/∂t + ū·∇ε = ∇·[(ν+νₜ/σε)∇ε] + C₁εPₖ/k − C₂ε²/k │
│        │ νₜ = Cμk²/ε; Cμ=0.09, C₁=1.44, C₂=1.92              │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall]│
│        │ time  momentum  pressure  k-ε-model  wall-fn                                                │
│        │ V={∂.time,N.bilinear.advection,L.poisson,N.pointwise.turbmodel,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (RANS is well-posed for attached flows) │
│        │ Uniqueness: YES for converged steady state             │
│        │ Stability: depends on y⁺ and wall treatment           │
│        │ Mismatch: model constants, wall function choice        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in mean velocity vs DNS/expt     │
│        │ q = 2.0 (2nd-order FVM)                               │
│        │ T = {velocity_profile_error, Cf_error, k_profile_err} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | RANS + k-ε system dimensionally consistent; closure complete | PASS |
| S2 | Standard constants yield convergent solutions for channel/pipe flows | PASS |
| S3 | SIMPLE/PISO with under-relaxation converges; residuals drop 5+ orders | PASS |
| S4 | Mean velocity error < 5% vs DNS for Re_τ < 1000 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rans_ke/channel_Re395_s1.yaml
principle_ref: sha256:<p176_hash>
omega:
  grid: [100, 80]
  domain: channel_2D
  half_height: 1.0
E:
  forward: "RANS + standard k-ε with wall functions"
  constants: {C_mu: 0.09, C1: 1.44, C2: 1.92, sigma_k: 1.0, sigma_e: 1.3}
B:
  walls: {type: wall_function, y_plus_target: 30}
  streamwise: periodic
I:
  scenario: channel_flow
  Re_tau: 395
  mesh_sizes: [50x40, 100x80]
O: [L2_velocity_error, Cf_error, k_profile_error]
epsilon:
  L2_error_max: 5.0e-2
  Cf_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | y⁺ ≈ 30 at first cell; mesh adequate for wall functions | PASS |
| S2 | Channel flow at Re_τ=395 well within k-ε validity range | PASS |
| S3 | SIMPLE converges in < 5000 iterations | PASS |
| S4 | L2 velocity error < 5% vs MKM DNS data | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# rans_ke/benchmark_channel395.yaml
spec_ref: sha256:<spec176_hash>
principle_ref: sha256:<p176_hash>
dataset:
  name: MKM_DNS_Re395
  reference: "Moser, Kim & Mansour (1999) DNS channel Re_τ=395"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OpenFOAM-simpleFoam (k-ε std)
    params: {mesh: 100x80, wall_fn: standard}
    results: {L2_vel_error: 3.8e-2, Cf_error: 4.1%}
  - solver: OpenFOAM-simpleFoam (k-ε RNG)
    params: {mesh: 100x80, wall_fn: standard}
    results: {L2_vel_error: 3.2e-2, Cf_error: 3.5%}
  - solver: Custom FVM (k-ε low-Re)
    params: {mesh: 100x200, y_plus_1: 1}
    results: {L2_vel_error: 2.1e-2, Cf_error: 2.2%}
quality_scoring:
  - {min_L2: 1.0e-2, Q: 1.00}
  - {min_L2: 3.0e-2, Q: 0.90}
  - {min_L2: 5.0e-2, Q: 0.80}
  - {min_L2: 8.0e-2, Q: 0.75}
```

**Baseline solver:** OpenFOAM k-ε std — L2 error 3.8×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Vel Error | Cf Error | Runtime | Q |
|--------|-------------|----------|---------|---|
| k-ε std (wall fn) | 3.8e-2 | 4.1% | 30 s | 0.90 |
| k-ε RNG | 3.2e-2 | 3.5% | 35 s | 0.90 |
| k-ε low-Re | 2.1e-2 | 2.2% | 120 s | 0.90 |
| k-ε realizable | 1.5e-2 | 1.8% | 40 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 0.90 = 270 PWM (model error floor)
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p176_hash>",
  "h_s": "sha256:<spec176_hash>",
  "h_b": "sha256:<bench176_hash>",
  "r": {"residual_norm": 1.5e-2, "error_bound": 5.0e-2, "ratio": 0.30},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 2},
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
pwm-node benchmarks | grep rans_ke
pwm-node verify rans_ke/channel_Re395_s1.yaml
pwm-node mine rans_ke/channel_Re395_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
