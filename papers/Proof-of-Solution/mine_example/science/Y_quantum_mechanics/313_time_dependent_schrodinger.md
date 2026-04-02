# Principle #313 — Time-Dependent Schrodinger Equation

**Domain:** Quantum Mechanics | **Carrier:** wavefunction | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → L.hamiltonian |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.hamiltonian     TDSE-1D     wavepacket-scatter  split-op
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIME-DEPENDENT SCHRODINGER     P = (E,G,W,C)   Principle #313  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ iℏ ∂ψ/∂t = Hψ = [−(ℏ²/2m)∇² + V(r,t)]ψ              │
│        │ ψ(r,0) = ψ₀(r)  (initial condition)                   │
│        │ |ψ|² = probability density, norm conserved             │
│        │ Forward: given V(r,t), ψ₀ → evolve ψ(r,t) over [0,T] │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.hamiltonian]                           │
│        │ derivative  linear-op                                  │
│        │ V={∂.time, L.hamiltonian}  A={∂.time→L.hamiltonian}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Stone's theorem, unitary group)        │
│        │ Uniqueness: YES (unitary evolution is unique)          │
│        │ Stability: norm-preserving; κ depends on V smoothness  │
│        │ Mismatch: potential error, time-step truncation        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖ψ_num − ψ_exact‖₂ / ‖ψ_exact‖₂ (primary)       │
│        │ q = 2.0 (Crank-Nicolson), spectral (split-operator)  │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wavefunction dimensions consistent; norm conservation well-formed | PASS |
| S2 | Unitary evolution guaranteed by Stone's theorem | PASS |
| S3 | Split-operator, Crank-Nicolson, Chebyshev propagators converge | PASS |
| S4 | L2 error bounded by time-step and spatial discretization estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tdse/wavepacket_s1_ideal.yaml
principle_ref: sha256:<p313_hash>
omega:
  grid: [1024]
  domain: [-50, 50]
  time: [0, 20.0]
  dt: 0.005
E:
  forward: "iℏ ∂ψ/∂t = [−(1/2)d²/dx² + V(x)]ψ"
  potential: gaussian_barrier
B:
  absorbing_bc: {type: mask_function}
I:
  scenario: wavepacket_scattering
  k0: 5.0
  sigma: 2.0
  barrier_height: 3.0
O: [transmission_coeff, reflection_coeff, norm_conservation]
epsilon:
  T_R_error_max: 1.0e-4
  norm_drift_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 1024 pts resolves wavepacket; dt satisfies stability | PASS |
| S2 | Free-particle + barrier has known T/R from transfer matrix | PASS |
| S3 | Split-operator converges at O(dt²) for smooth V | PASS |
| S4 | T+R error < 10⁻⁴ achievable with given resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tdse/benchmark_wavepacket.yaml
spec_ref: sha256:<spec313_hash>
principle_ref: sha256:<p313_hash>
dataset:
  name: gaussian_barrier_scattering
  reference: "Transfer-matrix analytic T/R coefficients"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Crank-Nicolson
    params: {N: 512, dt: 0.01}
    results: {T_R_error: 2.5e-3, norm_drift: 1.2e-8}
  - solver: Split-Operator (Strang)
    params: {N: 1024, dt: 0.005}
    results: {T_R_error: 8.1e-5, norm_drift: 3.1e-14}
  - solver: Chebyshev propagator
    params: {N: 1024, poly_order: 30}
    results: {T_R_error: 1.2e-6, norm_drift: 2.0e-15}
quality_scoring:
  - {min_T_R_error: 1.0e-6, Q: 1.00}
  - {min_T_R_error: 1.0e-4, Q: 0.90}
  - {min_T_R_error: 1.0e-3, Q: 0.80}
  - {min_T_R_error: 5.0e-3, Q: 0.75}
```

**Baseline solver:** Split-Operator — T/R error 8.1×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T/R Error | Norm Drift | Runtime | Q |
|--------|-----------|------------|---------|---|
| Crank-Nicolson | 2.5e-3 | 1.2e-8 | 2 s | 0.80 |
| Split-Operator | 8.1e-5 | 3.1e-14 | 3 s | 0.90 |
| Chebyshev | 1.2e-6 | 2.0e-15 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Chebyshev): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p313_hash>",
  "h_s": "sha256:<spec313_hash>",
  "h_b": "sha256:<bench313_hash>",
  "r": {"residual_norm": 1.2e-6, "error_bound": 1.0e-4, "ratio": 0.012},
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
pwm-node benchmarks | grep tdse
pwm-node verify tdse/wavepacket_s1_ideal.yaml
pwm-node mine tdse/wavepacket_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
