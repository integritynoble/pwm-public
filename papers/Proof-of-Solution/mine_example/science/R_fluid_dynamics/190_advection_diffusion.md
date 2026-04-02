# Principle #190 — Advection-Diffusion Equation

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian→B.dirichlet      AdvDiff     Gaussian-plume    FEM/FDM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ADVECTION-DIFFUSION   P = (E,G,W,C)   Principle #190           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂c/∂t + u·∇c = D∇²c + S                              │
│        │ c = concentration, u = velocity (given), D = diffusivity│
│        │ Peclet number Pe = UL/D governs character              │
│        │ Forward: IC/BC/u/D/S → solve for c(x,t) on Ω×[0,T]  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.dirichlet]│
│        │ time  advection  diffusion  BC                                               │
│        │ V={∂.time,N.bilinear.advection,∂.space.laplacian,B.dirichlet}  L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE, well-posed)             │
│        │ Uniqueness: YES (maximum principle holds)              │
│        │ Stability: κ ~ 1 (diffusion-dominated); upwinding for │
│        │   high Pe to avoid oscillations                        │
│        │ Mismatch: D uncertainty, velocity field error          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in concentration                  │
│        │ q = 2.0 (FEM-P1 SUPG), 4.0 (spectral)               │
│        │ T = {L2_error, max_error, mass_conservation}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Linear PDE; c non-negative with max principle; mass conserved | PASS |
| S2 | Parabolic well-posedness; unique smooth solution | PASS |
| S3 | SUPG/FEM, FVM-upwind, spectral all converge | PASS |
| S4 | Analytical solutions exist (Gaussian plume) for verification | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# advdiff/gaussian_plume_s1.yaml
principle_ref: sha256:<p190_hash>
omega:
  grid: [256, 256]
  domain: [0, 10]²
  time: [0, 5.0]
E:
  forward: "∂c/∂t + u·∇c = D∇²c"
  u: [1.0, 0.0]   # uniform advection
  D: 0.01
B:
  inlet: {c: 0}
  outlet: {zero_gradient: true}
  IC: {Gaussian: {center: [2,5], sigma: 0.5, amplitude: 1.0}}
I:
  scenario: advecting_diffusing_plume
  Pe: 100
  mesh_sizes: [64, 128, 256]
O: [L2_error, max_error, mass_conservation]
epsilon:
  L2_error_max: 1.0e-3
  mass_error_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves Pe=100 boundary layer with SUPG | PASS |
| S2 | Gaussian plume analytical solution exists | PASS |
| S3 | SUPG FEM / Crank-Nicolson converges at O(h² + dt²) | PASS |
| S4 | L2 error < 10⁻³ at 256² | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# advdiff/benchmark_plume.yaml
spec_ref: sha256:<spec190_hash>
principle_ref: sha256:<p190_hash>
dataset:
  name: Gaussian_plume_analytical
  reference: "Analytical Gaussian diffusion solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-upwind (1st)
    params: {N: 256}
    results: {L2_error: 8.5e-3, max_error: 1.2e-2}
  - solver: FEM-SUPG (P1)
    params: {N: 128}
    results: {L2_error: 1.5e-3, max_error: 3.2e-3}
  - solver: Spectral (Fourier)
    params: {N: 64}
    results: {L2_error: 2.1e-5, max_error: 5.5e-5}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-SUPG — L2 error 1.5×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FDM-upwind | 8.5e-3 | 1.2e-2 | 1 s | 0.75 |
| FEM-SUPG (P1) | 1.5e-3 | 3.2e-3 | 5 s | 0.80 |
| FEM-SUPG (P2) | 1.2e-4 | 2.8e-4 | 10 s | 0.90 |
| Spectral (N=64) | 2.1e-5 | 5.5e-5 | 2 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case (spectral): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p190_hash>",
  "h_s": "sha256:<spec190_hash>",
  "h_b": "sha256:<bench190_hash>",
  "r": {"residual_norm": 2.1e-5, "error_bound": 1.0e-3, "ratio": 0.021},
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
pwm-node benchmarks | grep advdiff
pwm-node verify advdiff/gaussian_plume_s1.yaml
pwm-node mine advdiff/gaussian_plume_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
