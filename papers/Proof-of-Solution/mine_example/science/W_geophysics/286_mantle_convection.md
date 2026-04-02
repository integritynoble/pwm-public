# Principle #286 — Mantle Convection Simulation

**Domain:** Geophysics | **Carrier:** N/A (PDE-based) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → N.bilinear.advection → ∂.space |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space      mantle-conv  Rayleigh-Benard  FEM-Stokes
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MANTLE CONVECTION SIMULATION     P = (E,G,W,C)   Principle #286│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇p + ∇·[η(∇u+∇uᵀ)] + ρgα(T−T₀)ẑ = 0 (Stokes)      │
│        │ ∇·u = 0  (incompressibility)                           │
│        │ ∂T/∂t + u·∇T = κ∇²T + H  (energy equation)            │
│        │ Ra = ρgαΔTd³/(ηκ)  (Rayleigh number)                  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space]      │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.bilinear.advection, ∂.space}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Boussinesq Stokes well-posed)         │
│        │ Uniqueness: YES for given Ra and initial conditions     │
│        │ Stability: depends on Ra; chaotic for Ra > 10⁶         │
│        │ Mismatch: Boussinesq approx, constant viscosity        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |Nu_computed − Nu_ref| / Nu_ref  (Nusselt number)  │
│        │ q = 2.0 (FEM), 1.0 (FDM)                             │
│        │ T = {Nusselt, Vrms, temperature_profile}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stokes + energy equations consistent; Boussinesq approximation valid | PASS |
| S2 | FEM with Taylor-Hood elements satisfies inf-sup for Stokes | PASS |
| S3 | ASPECT/CitcomS reproduce benchmark Nusselt numbers at Ra=10⁴–10⁶ | PASS |
| S4 | Nusselt error bounded by mesh resolution and time-stepping | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mantle_conv/rayleigh_benard_s1_ideal.yaml
principle_ref: sha256:<p286_hash>
omega:
  grid: [128, 128]
  domain: unit_square
  time: [0, 0.1]  # diffusion times
  dt: 1.0e-5
E:
  forward: "Boussinesq Stokes + energy equation"
  Ra: 1.0e5
  viscosity: isoviscous
  heating: basal
B:
  top: {T: 0, u: free_slip}
  bottom: {T: 1, u: free_slip}
  sides: reflecting
I:
  scenario: isoviscous_convection_Ra1e5
  initial_T: conductive_plus_perturbation
O: [Nusselt_number, Vrms, T_profile]
epsilon:
  Nu_error_max: 1.0e-2
  Vrms_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 128² grid adequate for Ra=10⁵; dt satisfies CFL | PASS |
| S2 | Isoviscous convection at Ra=10⁵ reaches steady state | PASS |
| S3 | FEM solver converges; Nusselt matches Blankenbach benchmark | PASS |
| S4 | Nu error < 1% achievable at 128² resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mantle_conv/benchmark_blankenbach.yaml
spec_ref: sha256:<spec286_hash>
principle_ref: sha256:<p286_hash>
dataset:
  name: Blankenbach_1989_case1a
  reference: "Blankenbach et al. (1989) benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-staggered
    params: {grid: 64x64, Ra: 1e5}
    results: {Nu_error: 2.5e-2, Vrms_error: 1.8e-2}
  - solver: FEM-Q2Q1
    params: {grid: 64x64, Ra: 1e5}
    results: {Nu_error: 8.5e-3, Vrms_error: 6.2e-3}
  - solver: FEM-Q2Q1 (fine)
    params: {grid: 128x128, Ra: 1e5}
    results: {Nu_error: 2.1e-3, Vrms_error: 1.5e-3}
quality_scoring:
  - {min_Nu_err: 1.0e-3, Q: 1.00}
  - {min_Nu_err: 5.0e-3, Q: 0.90}
  - {min_Nu_err: 1.0e-2, Q: 0.80}
  - {min_Nu_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q2Q1 (64²) — Nu error 8.5×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Nu Error | Vrms Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FDM-64² | 2.5e-2 | 1.8e-2 | 30 s | 0.80 |
| FEM-Q2Q1 64² | 8.5e-3 | 6.2e-3 | 60 s | 0.90 |
| FEM-Q2Q1 128² | 2.1e-3 | 1.5e-3 | 300 s | 0.90 |
| Spectral-Q2Q1 256² | 5.2e-4 | 3.8e-4 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (spectral): 500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p286_hash>",
  "h_s": "sha256:<spec286_hash>",
  "h_b": "sha256:<bench286_hash>",
  "r": {"residual_norm": 5.2e-4, "error_bound": 1.0e-2, "ratio": 0.052},
  "c": {"fitted_rate": 2.05, "theoretical_rate": 2.0, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep mantle_conv
pwm-node verify mantle_conv/rayleigh_benard_s1_ideal.yaml
pwm-node mine mantle_conv/rayleigh_benard_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
