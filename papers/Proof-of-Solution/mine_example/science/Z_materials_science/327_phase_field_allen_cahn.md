# Principle #327 — Phase-Field Modeling (Allen-Cahn)

**Domain:** Materials Science | **Carrier:** order parameter | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.double_well → ∂.space.laplacian |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          η→F→μ→∂η    Allen-Cahn  grain-growth-2D    FEM/FDM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE-FIELD (ALLEN-CAHN)       P = (E,G,W,C)   Principle #327 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂η/∂t = −L(δF/δη) = −L(f'(η) − κ∇²η)                │
│        │ F = ∫[f(η) + κ/2|∇η|²] dV  (Ginzburg-Landau free energy)│
│        │ f(η) = W η²(1−η)²  (double-well potential)           │
│        │ Forward: given η₀, L, κ, W → evolve η(x,t)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.double_well] ──→ [∂.space.laplacian]   │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.double_well, ∂.space.laplacian}  A={∂.time→N.double_well, N.double_well→∂.space.laplacian}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE, L²-theory)             │
│        │ Uniqueness: YES (Lipschitz f' ensures uniqueness)      │
│        │ Stability: free energy F monotonically decreasing      │
│        │ Mismatch: interface width vs physical width, mobility L│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖η_num − η_ref‖₂ / ‖η_ref‖₂ (primary)           │
│        │ q = 2.0 (FEM-linear), 1.0 (FDM-explicit)            │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Order parameter η ∈ [0,1]; free energy well-formed | PASS |
| S2 | Parabolic PDE with Lipschitz nonlinearity has unique solution | PASS |
| S3 | Semi-implicit time-stepping stable for stiff gradient term | PASS |
| S4 | Interface position error bounded by grid resolution vs κ | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# allen_cahn/planar_interface_s1_ideal.yaml
principle_ref: sha256:<p327_hash>
omega:
  grid: [256, 256]
  domain: [0, 10] x [0, 10]
  time: [0, 50.0]
  dt: 0.01
E:
  forward: "∂η/∂t = −L(f'(η) − κ∇²η)"
  mobility: 1.0
  gradient_coeff: 0.5
  well_height: 1.0
B:
  periodic: true
I:
  scenario: planar_interface_migration
  initial: {tanh_profile: true, width: 1.0}
O: [interface_position, interface_velocity, free_energy_decay]
epsilon:
  position_error_max: 0.01
  energy_monotonicity: strict
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 256² resolves interface of width ~√(κ/W); dt stable | PASS |
| S2 | Planar interface has analytic tanh steady-state profile | PASS |
| S3 | Semi-implicit scheme converges at O(dt + h²) | PASS |
| S4 | Interface position error < 0.01 achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# allen_cahn/benchmark_planar.yaml
spec_ref: sha256:<spec327_hash>
principle_ref: sha256:<p327_hash>
dataset:
  name: allen_cahn_planar_analytic
  reference: "Allen & Cahn (1979) analytic interface solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-explicit
    params: {N: 128, dt: 0.005}
    results: {position_error: 3.2e-2, energy_decay: monotonic}
  - solver: FEM-implicit
    params: {N: 256, dt: 0.01}
    results: {position_error: 4.1e-3, energy_decay: monotonic}
  - solver: Spectral (FFT)
    params: {N: 256, dt: 0.01}
    results: {position_error: 8.5e-5, energy_decay: monotonic}
quality_scoring:
  - {min_position_error: 1.0e-4, Q: 1.00}
  - {min_position_error: 1.0e-3, Q: 0.90}
  - {min_position_error: 1.0e-2, Q: 0.80}
  - {min_position_error: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-implicit — position error 4.1×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Position Error | Energy Decay | Runtime | Q |
|--------|---------------|--------------|---------|---|
| FDM-explicit | 3.2e-2 | monotonic | 5 s | 0.80 |
| FEM-implicit | 4.1e-3 | monotonic | 15 s | 0.90 |
| Spectral (FFT) | 8.5e-5 | monotonic | 8 s | 1.00 |

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
  "h_p": "sha256:<p327_hash>",
  "h_s": "sha256:<spec327_hash>",
  "h_b": "sha256:<bench327_hash>",
  "r": {"residual_norm": 8.5e-5, "error_bound": 1.0e-3, "ratio": 0.085},
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
pwm-node benchmarks | grep allen_cahn
pwm-node verify allen_cahn/planar_interface_s1_ideal.yaml
pwm-node mine allen_cahn/planar_interface_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
