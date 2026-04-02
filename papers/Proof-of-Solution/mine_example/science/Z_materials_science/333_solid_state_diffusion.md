# Principle #333 — Solid-State Diffusion (Fick's Laws)

**Domain:** Materials Science | **Carrier:** concentration field | **Difficulty:** Textbook (δ=1)
**DAG:** ∂.time → ∂.space.laplacian → B.dirichlet |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          c→J→∂c→D    Fick-diff   carburization-1D   FEM/analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SOLID-STATE DIFFUSION (FICK)   P = (E,G,W,C)   Principle #333 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂c/∂t = ∇·(D∇c)  (Fick's second law)                 │
│        │ J = −D∇c  (Fick's first law)                          │
│        │ D = D₀ exp(−Q/RT)  (Arrhenius temperature dependence) │
│        │ Forward: given c₀, D(T), BC → evolve c(x,t)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [B.dirichlet]     │
│        │ derivative  derivative  boundary                       │
│        │ V={∂.time, ∂.space.laplacian, B.dirichlet}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→B.dirichlet}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE, classical theory)       │
│        │ Uniqueness: YES (maximum principle for D>0)            │
│        │ Stability: unconditionally stable (implicit schemes)   │
│        │ Mismatch: concentration-dependent D, grain boundaries  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖c_num − c_exact‖₂ / ‖c_exact‖₂ (primary)       │
│        │ q = 2.0 (FEM-linear), erf-based analytic             │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Concentration and flux dimensions consistent; D > 0 | PASS |
| S2 | Constant-D yields error-function analytic solution | PASS |
| S3 | FEM and FDM converge for smooth initial/boundary data | PASS |
| S4 | Concentration error bounded by mesh-dependent estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fick/carburization_s1_ideal.yaml
principle_ref: sha256:<p333_hash>
omega:
  grid: [256]
  domain: [0, 5.0e-3]  # meters
  time: [0, 3600]  # 1 hour
  dt: 1.0
E:
  forward: "∂c/∂t = D ∂²c/∂x²"
  D: 1.0e-10  # m²/s (carbon in austenite at 900°C)
B:
  x0: {c: 0.008}  # surface concentration (wt fraction)
  x_end: {dc/dx: 0}  # no-flux
I:
  scenario: carburization_1D
  c_initial: 0.002  # wt fraction
  T: 1173  # K
O: [concentration_profile, case_depth, mass_uptake]
epsilon:
  profile_L2_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 256 on 5 mm resolves diffusion front; dt=1s stable | PASS |
| S2 | Semi-infinite solution c = c_s erfc(x/2√Dt) available | PASS |
| S3 | Crank-Nicolson converges at O(dt + h²) | PASS |
| S4 | Profile L2 error < 10⁻⁴ achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fick/benchmark_carburization.yaml
spec_ref: sha256:<spec333_hash>
principle_ref: sha256:<p333_hash>
dataset:
  name: carburization_erfc_analytic
  reference: "Analytic: c(x,t) = c_s erfc(x/(2√Dt))"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-explicit
    params: {N: 128, dt: 0.5}
    results: {profile_L2: 2.1e-3}
  - solver: Crank-Nicolson
    params: {N: 256, dt: 1.0}
    results: {profile_L2: 3.5e-5}
  - solver: Analytic (erfc)
    params: {}
    results: {profile_L2: 0.0}
quality_scoring:
  - {min_L2: 1.0e-6, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Crank-Nicolson — profile L2 3.5×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Profile L2 | Runtime | Q |
|--------|-----------|---------|---|
| FDM-explicit | 2.1e-3 | 0.5 s | 0.80 |
| Crank-Nicolson | 3.5e-5 | 0.2 s | 0.90 |
| Analytic (erfc) | 0.0 | 0.01 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (analytic): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p333_hash>",
  "h_s": "sha256:<spec333_hash>",
  "h_b": "sha256:<bench333_hash>",
  "r": {"residual_norm": 0.0, "error_bound": 1.0e-4, "ratio": 0.0},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep fick
pwm-node verify fick/carburization_s1_ideal.yaml
pwm-node mine fick/carburization_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
