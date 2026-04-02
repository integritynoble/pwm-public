# Principle #475 — Self-Consistent Field Theory (SCFT)

**Domain:** Polymer Physics | **Carrier:** N/A (mean-field) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [L.dense] --> [N.pointwise] --> [∫.volume] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->L.dense-->N.pw-->∫.vol  SCFT  diblock-melt  spectral/RealSp
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SELF-CONSISTENT FIELD THEORY (SCFT) P=(E,G,W,C) Princ. #475   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂q/∂s = (b²/6)∇²q − w(r)q   (modified diffusion eq.) │
│        │ q(r,0) = 1  (initial condition for propagator)         │
│        │ φ_A(r) = (1/Q)∫₀ᶠ q(r,s)q†(r,s) ds  (density)       │
│        │ w_A(r) = χN φ_B(r) + ξ(r)   (field equation)          │
│        │ φ_A + φ_B = 1  (incompressibility)                    │
│        │ Forward: given (χN,f,N) → equilibrium morphology φ(r) │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [L.dense] ──→ [N.pw] ──→ [∫.vol]             │
│        │  time-step  Rouse-matrix  nonlinear  volume-avg        │
│        │ V={∂.t,L.dense,N.pw,∫.vol}  A={∂.t→L.dense,L.dense→N.pw,N.pw→∫.vol}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (saddle point of free energy functional)│
│        │ Uniqueness: NO (multiple morphologies; free energy min)│
│        │ Stability: Anderson mixing accelerates convergence     │
│        │ Mismatch: mean-field ignores fluctuations (Fredrickson)│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |F − F_ref|/|F_ref|  (free energy error)          │
│        │ q = spectral (exponential for smooth fields)          │
│        │ T = {free_energy_error, field_residual, symmetry_check}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Propagator equation well-posed; incompressibility enforced | PASS |
| S2 | Saddle point exists for χN above ODT; Leibler theory validates | PASS |
| S3 | Pseudo-spectral + Anderson mixing converges within 10³ iterations | PASS |
| S4 | Free energy converged to 10⁻⁸ per chain | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# scft/diblock_s1_ideal.yaml
principle_ref: sha256:<p475_hash>
omega:
  grid: [64, 64, 64]
  domain: periodic_box
  contour_steps: 100
E:
  forward: "modified diffusion equation + self-consistency"
  chi_N: 20.0
  f: 0.35      # minority block fraction
  N: 100
B:
  periodic: [x, y, z]
  incompressibility: enforced
I:
  scenario: AB_diblock_gyroid_vs_cylinder
  chi_N_values: [12, 15, 20, 30, 50]
O: [free_energy, density_profile, morphology_type]
epsilon:
  free_energy_tol: 1.0e-8
  field_residual_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 64³ resolves interfaces at χN=20; 100 contour steps | PASS |
| S2 | χN=20, f=0.35 near gyroid/cylinder boundary; well-studied | PASS |
| S3 | Pseudo-spectral + Anderson converges for all morphologies | PASS |
| S4 | Free energy to 10⁻⁸ distinguishes competing phases | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# scft/benchmark_diblock.yaml
spec_ref: sha256:<spec475_hash>
principle_ref: sha256:<p475_hash>
dataset:
  name: Diblock_phase_diagram_SCFT
  reference: "Matsen & Schick (1994) SCFT phase diagram"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Real-space (Crank-Nicolson)
    params: {grid: 64^3, ds: 0.01, mixing: simple}
    results: {free_energy_error: 2.1e-5, iterations: 5000}
  - solver: Pseudo-spectral (Anderson)
    params: {grid: 64^3, ds: 0.01, anderson_depth: 10}
    results: {free_energy_error: 3.2e-7, iterations: 800}
  - solver: Pseudo-spectral (fine)
    params: {grid: 128^3, ds: 0.005, anderson_depth: 20}
    results: {free_energy_error: 8.5e-9, iterations: 600}
quality_scoring:
  - {min_err: 1.0e-8, Q: 1.00}
  - {min_err: 1.0e-6, Q: 0.90}
  - {min_err: 1.0e-4, Q: 0.80}
  - {min_err: 1.0e-3, Q: 0.75}
```

**Baseline solver:** Pseudo-spectral (Anderson) — free energy error 3.2×10⁻⁷
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | F Error | Iterations | Runtime | Q |
|--------|---------|-----------|---------|---|
| Real-space (simple) | 2.1e-5 | 5000 | 600 s | 0.80 |
| Pseudo-spectral (64³) | 3.2e-7 | 800 | 120 s | 0.90 |
| Pseudo-spectral (128³) | 8.5e-9 | 600 | 900 s | 1.00 |
| GPU pseudo-spectral | 1.2e-8 | 600 | 45 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (fine spectral): 400 × 1.00 = 400 PWM
Floor:                     400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p475_hash>",
  "h_s": "sha256:<spec475_hash>",
  "h_b": "sha256:<bench475_hash>",
  "r": {"free_energy_error": 8.5e-9, "error_bound": 1.0e-6, "ratio": 0.0085},
  "c": {"iterations": 600, "grid": "128^3", "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep scft
pwm-node verify scft/diblock_s1_ideal.yaml
pwm-node mine scft/diblock_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
