# Principle #227 — Poroelasticity (Biot Theory)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [L.coupled] --> [∂.space] --> [B.drained] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.coupled→∂.space→B.drained   Biot        Terzaghi-consol    FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  POROELASTICITY (BIOT THEORY)      P = (E,G,W,C)  Principle #227│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇·σ' + α∇p = f   (momentum balance)                  │
│        │ ∂(αε_v + p/M)/∂t + ∇·(−k/μ ∇p) = Q  (fluid mass)    │
│        │ α = Biot coefficient, M = Biot modulus, k = permeability│
│        │ Forward: given BC/loads → solve for (u, p)(x,t)        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [L.coupled] --> [∂.space] --> [B.drained]│
│        │ time  coupled-Biot-solve  spatial-derivatives  drainage-BC│
│        │ V={∂.time,L.coupled,∂.space,B.drained}  L_DAG=3.0         │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (saddle-point system; inf-sup stable)   │
│        │ Uniqueness: YES (parabolic-elliptic coupling)          │
│        │ Stability: inf-sup for u-p pair; oscillation for Δt→0 │
│        │ Mismatch: permeability error, Biot coefficient calib.  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ + pore press │
│        │ q = 2.0 (Taylor-Hood / stabilised equal-order)        │
│        │ T = {displacement_error, pressure_error, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled u-p system consistent; Biot parameters well-defined | PASS |
| S2 | Inf-sup stable element pair; Terzaghi analytical solution exists | PASS |
| S3 | Implicit time stepping with monolithic solve converges | PASS |
| S4 | L2 error bounded by space-time discretisation estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# poroelasticity/terzaghi_consolidation_s1_ideal.yaml
principle_ref: sha256:<p227_hash>
omega:
  grid: [1, 64]
  domain: soil_column_1D
  height: 1.0
  time: [0, 100.0]
  dt: 0.1
E:
  forward: "Biot poroelasticity coupled system"
  E_drained: 1.0e7   # Pa
  poisson: 0.3
  alpha: 1.0   # Biot coefficient
  k_over_mu: 1.0e-8   # m²/(Pa·s)
  M: 1.0e10
B:
  top: {traction: -100.0e3, drainage: free}
  bottom: {u: 0, drainage: impermeable}
I:
  scenario: Terzaghi_1D_consolidation
  mesh_sizes: [16, 32, 64]
O: [L2_displacement_error, L2_pressure_error, settlement_vs_time]
epsilon:
  L2_error_max: 1.0e-3
  pressure_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D column mesh adequate; dt resolves consolidation time | PASS |
| S2 | Terzaghi 1D has exact analytical solution (Fourier series) | PASS |
| S3 | Implicit backward-Euler scheme stable; no pressure oscillation | PASS |
| S4 | L2 error < 10⁻³ at N=64 with dt=0.1 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# poroelasticity/benchmark_terzaghi.yaml
spec_ref: sha256:<spec227_hash>
principle_ref: sha256:<p227_hash>
dataset:
  name: Terzaghi_consolidation
  reference: "Terzaghi (1943) — analytical 1D consolidation solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q1Q1-stabilised (N=32)
    params: {N: 32, dt: 0.1}
    results: {L2_u_error: 2.5e-3, L2_p_error: 8.0e-3}
  - solver: FEM-Q2Q1 (N=32)
    params: {N: 32, dt: 0.1}
    results: {L2_u_error: 5.0e-4, L2_p_error: 2.0e-3}
  - solver: FEM-Q2Q1 (N=64, fine dt)
    params: {N: 64, dt: 0.01}
    results: {L2_u_error: 1.2e-4, L2_p_error: 5.0e-4}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 5.0e-4, Q: 0.90}
  - {min_L2: 2.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q2Q1 (N=32) — L2 displacement error 5.0×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 u Err | L2 p Err | Runtime | Q |
|--------|----------|----------|---------|---|
| FEM-Q1Q1-stab (N=32) | 2.5e-3 | 8.0e-3 | 5 s | 0.80 |
| FEM-Q2Q1 (N=32) | 5.0e-4 | 2.0e-3 | 15 s | 0.90 |
| FEM-Q2Q1 (N=64, fine) | 1.2e-4 | 5.0e-4 | 60 s | 1.00 |
| Spectral + Fourier | 1.0e-6 | 5.0e-6 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p227_hash>",
  "h_s": "sha256:<spec227_hash>",
  "h_b": "sha256:<bench227_hash>",
  "r": {"residual_norm": 1.0e-6, "error_bound": 1.0e-3, "ratio": 0.001},
  "c": {"fitted_rate": 2.02, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep poroelasticity
pwm-node verify poroelasticity/terzaghi_consolidation_s1_ideal.yaml
pwm-node mine poroelasticity/terzaghi_consolidation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
