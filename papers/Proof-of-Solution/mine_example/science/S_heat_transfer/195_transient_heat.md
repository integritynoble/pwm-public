# Principle #195 — Transient Heat Conduction

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [∂.time] --> [∂.space.laplacian] --> [B.robin] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→B.robin        TransHeat   slab-cooling      FEM/FDM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSIENT HEAT CONDUCTION   P = (E,G,W,C)   Principle #195     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρcₚ ∂T/∂t = ∇·(k∇T) + Q                             │
│        │ k = thermal conductivity, cₚ = specific heat          │
│        │ Parabolic PDE; admits separation-of-variables solution │
│        │ Forward: IC/BC/k/Q → solve T(x,t) on Ω×[0,T_f]      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space.laplacian] --> [B.robin]        │
│        │ time-step  thermal-diffusion  convective-BC           │
│        │ V={∂.time,∂.space.laplacian,B.robin}  L_DAG=1.0       │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic, Lax-Milgram)                │
│        │ Uniqueness: YES (maximum principle)                    │
│        │ Stability: unconditionally stable (implicit); CFL (exp)│
│        │ Mismatch: k(T) nonlinearity, contact resistance       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in temperature                    │
│        │ q = 2.0 (FEM-P1), 4.0 (FEM-P2 + CN time)            │
│        │ T = {L2_error, max_error, energy_balance}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Heat equation dimensionally consistent; k > 0 | PASS |
| S2 | Maximum principle ensures unique bounded solution | PASS |
| S3 | Crank-Nicolson FEM/FDM converges at O(h² + dt²) | PASS |
| S4 | Exact series solutions exist for simple geometries | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# transient_heat/slab_cooling_s1.yaml
principle_ref: sha256:<p195_hash>
omega:
  grid: [100]
  domain: [0, 0.1]   # 10 cm slab
  time: [0, 100]      # seconds
E:
  forward: "ρcₚ ∂T/∂t = k ∂²T/∂x²"
  k: 50.0       # W/(m·K), steel
  rho_cp: 3.5e6  # J/(m³·K)
B:
  left: {T: 0.0}       # sudden cooling
  right: {flux: 0.0}    # insulated
  IC: {T: 100.0}
I:
  scenario: slab_convective_cooling
  Bi: 0.0   # Dirichlet BC
  mesh_sizes: [25, 50, 100]
O: [L2_error, max_error, energy_balance]
epsilon:
  L2_error_max: 1.0e-4
  max_error_max: 5.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D slab; constant k; Dirichlet + Neumann BC valid | PASS |
| S2 | Fourier series exact solution exists | PASS |
| S3 | Crank-Nicolson converges at O(h²+dt²) | PASS |
| S4 | L2 error < 10⁻⁴ at N=100 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# transient_heat/benchmark_slab.yaml
spec_ref: sha256:<spec195_hash>
principle_ref: sha256:<p195_hash>
dataset:
  name: Fourier_series_exact
  reference: "Carslaw & Jaeger (1959) Ch. 3"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM (Euler explicit)
    params: {N: 100, dt: 0.001}
    results: {L2_error: 5.2e-4, max_error: 1.1e-3}
  - solver: FDM (Crank-Nicolson)
    params: {N: 100, dt: 0.1}
    results: {L2_error: 3.5e-5, max_error: 8.1e-5}
  - solver: FEM-P2 (BDF2)
    params: {N: 50, dt: 0.1}
    results: {L2_error: 8.2e-6, max_error: 2.1e-5}
quality_scoring:
  - {min_L2: 1.0e-6, Q: 1.00}
  - {min_L2: 1.0e-5, Q: 0.90}
  - {min_L2: 1.0e-4, Q: 0.80}
  - {min_L2: 1.0e-3, Q: 0.75}
```

**Baseline solver:** FDM Crank-Nicolson — L2 error 3.5×10⁻⁵
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FDM Euler explicit | 5.2e-4 | 1.1e-3 | 0.5 s | 0.80 |
| FDM Crank-Nicolson | 3.5e-5 | 8.1e-5 | 0.1 s | 0.90 |
| FEM-P2 (BDF2) | 8.2e-6 | 2.1e-5 | 0.2 s | 0.90 |
| Spectral (Chebyshev) | 5.5e-8 | 1.2e-7 | 0.05 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case (spectral): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p195_hash>",
  "h_s": "sha256:<spec195_hash>",
  "h_b": "sha256:<bench195_hash>",
  "r": {"residual_norm": 5.5e-8, "error_bound": 1.0e-4, "ratio": 5.5e-4},
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
pwm-node benchmarks | grep transient_heat
pwm-node verify transient_heat/slab_cooling_s1.yaml
pwm-node mine transient_heat/slab_cooling_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
