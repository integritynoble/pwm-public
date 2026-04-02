# Principle #328 — Phase-Field (Cahn-Hilliard)

**Domain:** Materials Science | **Carrier:** composition field | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.chemical → ∂.space.biharmonic |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          c→F→μ→J      Cahn-Hill   spinodal-2D        FEM/spectral
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE-FIELD (CAHN-HILLIARD)    P = (E,G,W,C)   Principle #328 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂c/∂t = ∇·(M∇μ),  μ = δF/δc = f'(c) − κ∇²c          │
│        │ F = ∫[f(c) + κ/2|∇c|²] dV                            │
│        │ f(c) = c²(1−c)²  (double-well); M = mobility          │
│        │ Forward: given c₀, M, κ → evolve c(x,t) (conserved)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.chemical] ──→ [∂.space.biharmonic]     │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.chemical, ∂.space.biharmonic}  A={∂.time→N.chemical, N.chemical→∂.space.biharmonic}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (fourth-order parabolic PDE)            │
│        │ Uniqueness: YES (energy dissipation implies uniqueness)│
│        │ Stability: F decreasing; mass conserved exactly        │
│        │ Mismatch: interface width, mobility model, mesh        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖c_num − c_ref‖₂ / ‖c_ref‖₂ (primary)           │
│        │ q = 2.0 (FEM-C¹), spectral (FFT-based)              │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Composition c conserved; fourth-order PDE well-posed | PASS |
| S2 | Energy dissipation guarantees unique long-time behavior | PASS |
| S3 | Semi-implicit Fourier-spectral method stable for stiff terms | PASS |
| S4 | Composition error bounded by mesh resolution vs interface width | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cahn_hilliard/spinodal_s1_ideal.yaml
principle_ref: sha256:<p328_hash>
omega:
  grid: [256, 256]
  domain: unit_square
  time: [0, 100.0]
  dt: 0.05
E:
  forward: "∂c/∂t = M∇²(f'(c) − κ∇²c)"
  mobility: 1.0
  gradient_coeff: 0.5
B:
  periodic: true
I:
  scenario: spinodal_decomposition
  c0_mean: 0.5
  noise_amplitude: 0.05
O: [structure_factor, coarsening_exponent, free_energy_decay]
epsilon:
  coarsening_exp_error: 0.05  # expect n≈1/3 (Lifshitz-Slyozov)
  mass_conservation: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 256² resolves spinodal wavelength; dt stable | PASS |
| S2 | Spinodal decomposition yields t^{1/3} coarsening law | PASS |
| S3 | FFT-based semi-implicit scheme handles biharmonic operator | PASS |
| S4 | Coarsening exponent measurable from structure factor | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cahn_hilliard/benchmark_spinodal.yaml
spec_ref: sha256:<spec328_hash>
principle_ref: sha256:<p328_hash>
dataset:
  name: spinodal_coarsening_reference
  reference: "Lifshitz-Slyozov t^{1/3} coarsening law"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-explicit
    params: {N: 128, dt: 0.01}
    results: {coarsening_exp: 0.28, energy_monotonic: true}
  - solver: FFT semi-implicit
    params: {N: 256, dt: 0.05}
    results: {coarsening_exp: 0.32, energy_monotonic: true}
  - solver: FEM-C1 (Hermite)
    params: {N: 128, dt: 0.05}
    results: {coarsening_exp: 0.31, energy_monotonic: true}
quality_scoring:
  - {min_exp_error: 0.01, Q: 1.00}
  - {min_exp_error: 0.03, Q: 0.90}
  - {min_exp_error: 0.05, Q: 0.80}
  - {min_exp_error: 0.10, Q: 0.75}
```

**Baseline solver:** FFT semi-implicit — coarsening exponent 0.32
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Coarsening Exp | Mass Drift | Runtime | Q |
|--------|---------------|------------|---------|---|
| FDM-explicit | 0.28 | 1.2e-6 | 30 s | 0.75 |
| FEM-C1 | 0.31 | 5.1e-10 | 60 s | 0.90 |
| FFT semi-implicit | 0.32 | 1.0e-14 | 20 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FFT): 300 × 0.90 = 270 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p328_hash>",
  "h_s": "sha256:<spec328_hash>",
  "h_b": "sha256:<bench328_hash>",
  "r": {"residual_norm": 0.01, "error_bound": 0.05, "ratio": 0.20},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep cahn_hilliard
pwm-node verify cahn_hilliard/spinodal_s1_ideal.yaml
pwm-node mine cahn_hilliard/spinodal_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
