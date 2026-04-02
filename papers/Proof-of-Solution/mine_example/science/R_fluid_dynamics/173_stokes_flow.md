# Principle #173 — Stokes Flow

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [L.stokes] --> [B.wall] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stokes→B.wall          Stokes      sphere-drag       FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STOKES FLOW   P = (E,G,W,C)   Principle #173                  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −μ∇²u + ∇p = f                                        │
│        │ ∇·u = 0                                                │
│        │ Linear saddle-point system (Re → 0 limit of NS)       │
│        │ Forward: given f,BC,μ → solve for (u,p) on Ω          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stokes] --> [B.wall]                                │
│        │ saddle-point-solve  wall-BC                             │
│        │ V={L.stokes,B.wall}  A={L→B}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lax-Milgram on H¹₀ × L²₀)            │
│        │ Uniqueness: YES (elliptic, inf-sup stable)             │
│        │ Stability: κ depends on domain aspect ratio            │
│        │ Mismatch: viscosity μ error, boundary geometry         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in velocity                      │
│        │ q = 2.0 (P2/P1 FEM), 3.0 (P3/P2 FEM)               │
│        │ T = {residual_norm, inf-sup_constant, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Saddle-point structure well-formed; divergence-free constraint consistent | PASS |
| S2 | Lax-Milgram + inf-sup (LBB) condition → unique solution | PASS |
| S3 | Taylor-Hood FEM, MINI element, spectral methods converge | PASS |
| S4 | A priori FEM error estimate: ‖u−uₕ‖ ≤ Ch^(k+1) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# stokes/sphere_drag_s1.yaml
principle_ref: sha256:<p173_hash>
omega:
  grid: [64, 64, 64]
  domain: sphere_in_box
  sphere_radius: 0.5
E:
  forward: "−μ∇²u + ∇p = 0, ∇·u = 0"
  mu: 1.0
B:
  sphere: {u: [0,0,0]}   # no-slip
  inlet: {u: [1,0,0]}     # uniform inflow
  outlet: {stress_free: true}
I:
  scenario: stokes_sphere_drag
  mesh_sizes: [16, 32, 64]
O: [L2_velocity_error, drag_coefficient_error, pressure_L2]
epsilon:
  L2_error_max: 1.0e-3
  drag_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3D mesh around sphere; BC types consistent with Stokes | PASS |
| S2 | Analytic Stokes solution exists (F_D = 6πμRU) | PASS |
| S3 | Taylor-Hood P2/P1 converges at O(h²) on tetrahedral mesh | PASS |
| S4 | L2 error < 10⁻³ achievable at h ~ 1/64 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# stokes/benchmark_sphere.yaml
spec_ref: sha256:<spec173_hash>
principle_ref: sha256:<p173_hash>
dataset:
  name: Stokes_sphere_analytic
  reference: "Stokes drag: F = 6πμRU"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P2P1
    params: {h: 1/32}
    results: {L2_error: 2.8e-3, drag_error: 0.8%}
  - solver: FEM-P2P1
    params: {h: 1/64}
    results: {L2_error: 7.1e-4, drag_error: 0.2%}
  - solver: Spectral-BEM
    params: {N: 32}
    results: {L2_error: 3.2e-5, drag_error: 0.001%}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-P2P1 (h=1/64) — L2 error 7.1×10⁻⁴
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Drag Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FEM-P2P1 (h=1/32) | 2.8e-3 | 0.8% | 5 s | 0.80 |
| FEM-P2P1 (h=1/64) | 7.1e-4 | 0.2% | 40 s | 0.90 |
| FEM-P3P2 (h=1/32) | 1.2e-4 | 0.03% | 20 s | 0.90 |
| Spectral-BEM | 3.2e-5 | 0.001% | 8 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case (BEM):  100 × 1.00 = 100 PWM
Floor:            100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p173_hash>",
  "h_s": "sha256:<spec173_hash>",
  "h_b": "sha256:<bench173_hash>",
  "r": {"residual_norm": 3.2e-5, "error_bound": 1.0e-3, "ratio": 0.032},
  "c": {"fitted_rate": 2.98, "theoretical_rate": 3.0, "K": 3},
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
pwm-node benchmarks | grep stokes
pwm-node verify stokes/sphere_drag_s1.yaml
pwm-node mine stokes/sphere_drag_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
