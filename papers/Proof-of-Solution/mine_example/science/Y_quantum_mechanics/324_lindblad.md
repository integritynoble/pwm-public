# Principle #324 — Quantum Master Equation (Lindblad)

**Domain:** Quantum Mechanics | **Carrier:** density matrix | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → L.hamiltonian → N.pointwise |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ρ→L→ρ'→Tr   Lindblad    2-level-decay       RK4/MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM MASTER EQ. (LINDBLAD)  P = (E,G,W,C)   Principle #324 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dρ/dt = −i[H,ρ] + Σₖ γₖ(LₖρLₖ† − ½{Lₖ†Lₖ,ρ})       │
│        │ Lₖ = Lindblad (jump) operators, γₖ = decay rates       │
│        │ Tr(ρ) = 1, ρ ≥ 0 preserved (CPTP map)                │
│        │ Forward: given H, {Lₖ,γₖ}, ρ₀ → evolve ρ(t)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.hamiltonian] ──→ [N.pointwise]         │
│        │ derivative  linear-op  nonlinear                       │
│        │ V={∂.time, L.hamiltonian, N.pointwise}  A={∂.time→L.hamiltonian, L.hamiltonian→N.pointwise}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (CPTP semigroup always well-defined)    │
│        │ Uniqueness: YES (unique steady state for ergodic L)    │
│        │ Stability: exponential approach to steady state        │
│        │ Mismatch: Markov approximation, secular approximation  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖ρ_num − ρ_exact‖_F / ‖ρ_exact‖_F (primary)      │
│        │ q = 4.0 (RK4), 2.0 (Euler)                           │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Density matrix Hermitian, positive, trace-1 preserved | PASS |
| S2 | Lindblad form guarantees completely positive evolution | PASS |
| S3 | RK4 and quantum-jump MC methods converge | PASS |
| S4 | Frobenius-norm error bounded by time-step estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lindblad/two_level_decay_s1_ideal.yaml
principle_ref: sha256:<p324_hash>
omega:
  dim: 2
  time: [0, 20.0]
  dt: 0.01
E:
  forward: "dρ/dt = −i[H,ρ] + γ(σ₋ρσ₊ − ½{σ₊σ₋,ρ})"
  model: damped_Rabi
B:
  initial: {rho: excited_state}
I:
  scenario: spontaneous_emission
  omega_R: 5.0  # Rabi frequency
  gamma: 1.0    # decay rate
  delta: 0.0    # detuning
O: [populations, coherences, purity]
epsilon:
  rho_error_max: 1.0e-6
  trace_drift_max: 1.0e-12
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2×2 density matrix; dt=0.01 resolves Rabi oscillations | PASS |
| S2 | Analytic solution exists for damped two-level system | PASS |
| S3 | RK4 converges at O(dt⁴) for smooth Lindblad evolution | PASS |
| S4 | ρ error < 10⁻⁶ achievable with dt=0.01, RK4 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lindblad/benchmark_two_level.yaml
spec_ref: sha256:<spec324_hash>
principle_ref: sha256:<p324_hash>
dataset:
  name: damped_rabi_analytic
  reference: "Analytic solution of optical Bloch equations"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Euler
    params: {dt: 0.01}
    results: {rho_error: 1.5e-3, trace_drift: 2.1e-5}
  - solver: RK4
    params: {dt: 0.01}
    results: {rho_error: 2.3e-7, trace_drift: 1.0e-14}
  - solver: Quantum-jump MC
    params: {N_traj: 10000, dt: 0.01}
    results: {rho_error: 8.5e-3, trace_drift: 0.0}
quality_scoring:
  - {min_rho_error: 1.0e-8, Q: 1.00}
  - {min_rho_error: 1.0e-6, Q: 0.90}
  - {min_rho_error: 1.0e-4, Q: 0.80}
  - {min_rho_error: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — ρ error 2.3×10⁻⁷
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | ρ Error | Trace Drift | Runtime | Q |
|--------|---------|-------------|---------|---|
| Quantum-jump MC | 8.5e-3 | 0.0 | 10 s | 0.75 |
| Euler | 1.5e-3 | 2.1e-5 | 0.01 s | 0.80 |
| RK4 | 2.3e-7 | 1.0e-14 | 0.02 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RK4): 300 × 0.90 = 270 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p324_hash>",
  "h_s": "sha256:<spec324_hash>",
  "h_b": "sha256:<bench324_hash>",
  "r": {"residual_norm": 2.3e-7, "error_bound": 1.0e-4, "ratio": 0.0023},
  "c": {"fitted_rate": 4.0, "theoretical_rate": 4.0, "K": 3},
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
pwm-node benchmarks | grep lindblad
pwm-node verify lindblad/two_level_decay_s1_ideal.yaml
pwm-node mine lindblad/two_level_decay_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
