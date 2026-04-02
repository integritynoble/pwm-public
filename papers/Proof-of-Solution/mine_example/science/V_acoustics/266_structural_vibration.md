# Principle #266 — Structural Vibration (Forced Response)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Textbook (δ=1)
**DAG:** L.sparse → ∂.time → E.hermitian |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.sparse→∂.time→E.hermitian    struct_vib   cantilever_impulse  Newmark/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STRUCTURAL VIBRATION (FORCED RESP)  P = (E,G,W,C)   Principle #266 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ M ü + C u̇ + K u = f(t)                                │
│        │ Mass-damping-stiffness system under dynamic loads      │
│        │ Forward: given M, C, K, f(t) → solve u(t) or U(ω)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.sparse] ──→ [∂.time] ──→ [E.hermitian]              │
│        │ linear-op  derivative  eigensolve                      │
│        │ V={L.sparse, ∂.time, E.hermitian}  A={L.sparse→∂.time, ∂.time→E.hermitian}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE system theory)              │
│        │ Uniqueness: YES (given IC and forcing)                 │
│        │ Stability: modal damping ratios control transient decay│
│        │ Mismatch: damping model errors, joint nonlinearities   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (Newmark-β), exact (modal superposition)     │
│        │ T = {displacement_error, frequency_response_match}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | M, C, K matrices symmetric positive (semi-)definite; f(t) defined | PASS |
| S2 | Linear ODE theory guarantees unique solution for all t | PASS |
| S3 | Newmark-β unconditionally stable; modal superposition exact | PASS |
| S4 | Relative L2 error bounded by time-integration accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# struct_vib/cantilever_impulse.yaml
principle_ref: sha256:<p266_hash>
omega:
  structure: cantilever_beam
  length: 1.0  # meters
  elements: 20
  time: [0, 1.0]
  dt: 1.0e-4
E:
  forward: "M ü + C u̇ + K u = f(t)"
  material: {E: 200e9, rho: 7800, I: 1e-6}
  damping: {zeta: 0.02}
I:
  scenario: cantilever_impulse_response
  force: {type: impulse, location: tip, magnitude: 100}
O: [L2_displacement_error, natural_frequency_error]
epsilon:
  L2_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 beam elements resolve first 5 modes; Δt adequate | PASS |
| S2 | Cantilever beam has exact Euler-Bernoulli mode shapes | PASS |
| S3 | Newmark-β (γ=0.5, β=0.25) unconditionally stable | PASS |
| S4 | L2 error < 10⁻⁴ achievable with 20 elements | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# struct_vib/benchmark_cantilever.yaml
spec_ref: sha256:<spec266_hash>
principle_ref: sha256:<p266_hash>
dataset:
  name: cantilever_impulse_reference
  reference: "Analytic Euler-Bernoulli modal solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Newmark-β (20 elements)
    params: {N: 20, dt: 1e-4, gamma: 0.5, beta: 0.25}
    results: {L2_error: 5.2e-3, freq_error: 0.1}
  - solver: Modal superposition (5 modes)
    params: {N_modes: 5}
    results: {L2_error: 8.5e-5, freq_error: 0.01}
  - solver: Modal superposition (20 modes)
    params: {N_modes: 20}
    results: {L2_error: 3.1e-7, freq_error: 1e-4}
quality_scoring:
  - {min_L2: 1.0e-6, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** Modal superposition (5 modes) — L2 error 8.5×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Freq Error (%) | Runtime | Q |
|--------|----------|----------------|---------|---|
| Newmark-β (20 elem) | 5.2e-3 | 0.1 | 1 s | 0.75 |
| Modal (5 modes) | 8.5e-5 | 0.01 | 0.1 s | 0.90 |
| Newmark-β (100 elem) | 2.1e-5 | 0.002 | 5 s | 1.00 |
| Modal (20 modes) | 3.1e-7 | 1e-4 | 0.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case: 100 × 1.00 = 100 PWM
Floor:     100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p266_hash>",
  "h_s": "sha256:<spec266_hash>",
  "h_b": "sha256:<bench266_hash>",
  "r": {"residual_norm": 3.1e-7, "error_bound": 1.0e-4, "ratio": 0.0031},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 4},
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
pwm-node benchmarks | grep struct_vib
pwm-node verify struct_vib/cantilever_impulse.yaml
pwm-node mine struct_vib/cantilever_impulse.yaml
pwm-node inspect sha256:<cert_hash>
```
