# Principle #191 — Convection-Diffusion-Reaction Equation

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [N.pointwise.reaction] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian→N.pointwise.reaction→B.dirichlet   CDR         reactive-front    FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONVECTION-DIFFUSION-REACTION   P = (E,G,W,C)  Principle #191  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂c/∂t + u·∇c = D∇²c + R(c)                           │
│        │ R(c) = nonlinear reaction (e.g., −kc, kc(1−c))       │
│        │ Coupled species: ∂cᵢ/∂t + u·∇cᵢ = Dᵢ∇²cᵢ + Rᵢ(c)  │
│        │ Forward: IC/BC/u/D/R → solve c(x,t) on Ω×[0,T]      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [N.pointwise.reaction] --> [B.dirichlet]│
│        │ time  advect  diffuse  react  BC                                                                        │
│        │ V={∂.time,N.bilinear.advection,∂.space.laplacian,N.pointwise.reaction,B.dirichlet}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (semi-linear parabolic theory)          │
│        │ Uniqueness: YES for Lipschitz R(c)                     │
│        │ Stability: stiff reactions need implicit treatment     │
│        │ Mismatch: reaction rate k, Damkohler number error     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in concentration                  │
│        │ q = 2.0 (FEM-SUPG), operator splitting adds O(dt)    │
│        │ T = {L2_error, reaction_front_speed, mass_balance}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | CDR system consistent; species balance maintained | PASS |
| S2 | Lipschitz reaction guarantees unique solution; Damkohler finite | PASS |
| S3 | Operator splitting (Strang) or monolithic SUPG converge | PASS |
| S4 | L2 error bounded; front speed matches analytical traveling wave | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cdr/fisher_kpp_s1.yaml
principle_ref: sha256:<p191_hash>
omega:
  grid: [500]
  domain: [0, 50]
  time: [0, 20.0]
E:
  forward: "∂c/∂t = D∂²c/∂x² + kc(1−c)"
  D: 1.0
  k: 1.0
B:
  left: {c: 1.0}
  right: {c: 0.0}
  IC: {step: {x0: 5.0}}
I:
  scenario: Fisher_KPP_traveling_wave
  Da: 1.0
  mesh_sizes: [100, 250, 500]
O: [L2_error, front_speed_error, front_position_error]
epsilon:
  L2_error_max: 5.0e-3
  front_speed_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D grid; Fisher-KPP reaction well-formed; c ∈ [0,1] | PASS |
| S2 | Traveling wave solution exists with speed c* = 2√(Dk) | PASS |
| S3 | Crank-Nicolson + Newton converges; operator splitting works | PASS |
| S4 | L2 error < 5×10⁻³ at N=500; front speed within 1% | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# cdr/benchmark_fisher.yaml
spec_ref: sha256:<spec191_hash>
principle_ref: sha256:<p191_hash>
dataset:
  name: Fisher_KPP_traveling_wave
  reference: "Fisher (1937); exact front speed c* = 2"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM Crank-Nicolson
    params: {N: 500, dt: 0.01}
    results: {L2_error: 3.2e-3, front_speed_err: 0.5%}
  - solver: FEM-SUPG (P1)
    params: {N: 250}
    results: {L2_error: 5.1e-3, front_speed_err: 0.8%}
  - solver: Spectral (Fourier)
    params: {N: 128}
    results: {L2_error: 8.5e-5, front_speed_err: 0.01%}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 1.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FDM Crank-Nicolson — L2 error 3.2×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Front Speed Err | Runtime | Q |
|--------|----------|----------------|---------|---|
| FEM-SUPG (P1) | 5.1e-3 | 0.8% | 3 s | 0.80 |
| FDM-CN | 3.2e-3 | 0.5% | 2 s | 0.90 |
| Strang splitting | 2.5e-3 | 0.3% | 2 s | 0.90 |
| Spectral | 8.5e-5 | 0.01% | 1 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p191_hash>",
  "h_s": "sha256:<spec191_hash>",
  "h_b": "sha256:<bench191_hash>",
  "r": {"residual_norm": 8.5e-5, "error_bound": 5.0e-3, "ratio": 0.017},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep cdr
pwm-node verify cdr/fisher_kpp_s1.yaml
pwm-node mine cdr/fisher_kpp_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
