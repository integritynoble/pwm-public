# Principle #314 — Quantum Scattering (Partial Wave Analysis)

**Domain:** Quantum Mechanics | **Carrier:** scattering amplitude | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → L.hamiltonian → B.absorbing |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.hamiltonian→B.absorbing    scatter-PW  hard-sphere/LJ     Numerov
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM SCATTERING (PARTIAL WAVE)  P = (E,G,W,C) Principle #314│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [−d²/dr² + l(l+1)/r² + 2mV(r)/ℏ²]uₗ(r) = k²uₗ(r)   │
│        │ σ_total = (4π/k²) Σₗ (2l+1) sin²δₗ                    │
│        │ Phase shifts δₗ from asymptotic matching               │
│        │ Forward: given V(r), E → compute {δₗ} → σ(θ), σ_total │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.hamiltonian] ──→ [B.absorbing]         │
│        │ derivative  linear-op  boundary                        │
│        │ V={∂.time, L.hamiltonian, B.absorbing}  A={∂.time→L.hamiltonian, L.hamiltonian→B.absorbing}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lippmann-Schwinger for short-range V)  │
│        │ Uniqueness: YES (phase shifts unique for given E, V)   │
│        │ Stability: κ ~ l_max; more partial waves at higher E   │
│        │ Mismatch: potential truncation, angular momentum cutoff│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |σ_num − σ_exact|/|σ_exact| (primary)             │
│        │ q = 4.0 (Numerov), 2.0 (RK4)                         │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Radial equation and phase-shift extraction well-defined | PASS |
| S2 | Short-range V guarantees finite number of significant δₗ | PASS |
| S3 | Numerov integrator converges at O(h⁴) for radial equation | PASS |
| S4 | Cross-section error bounded by partial-wave truncation + grid error | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# scattering/hard_sphere_s1_ideal.yaml
principle_ref: sha256:<p314_hash>
omega:
  grid: [2048]
  domain: radial_0_to_30
  r_max: 30.0
E:
  forward: "radial Schrodinger + asymptotic matching for δₗ"
  potential: hard_sphere
B:
  r0: {u_l: 0}
  r_max: {asymptotic_match: true}
I:
  scenario: hard_sphere
  radius: 1.0
  k: 2.0
  l_max: 10
O: [phase_shifts, total_cross_section, differential_cross_section]
epsilon:
  sigma_rel_max: 1.0e-6
  phase_shift_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 2048 pts resolves rapid oscillations at k=2.0 | PASS |
| S2 | Hard-sphere phase shifts have exact analytic form | PASS |
| S3 | Numerov integrator converges rapidly for step potential | PASS |
| S4 | σ_total error < 10⁻⁶ achievable at given resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# scattering/benchmark_hard_sphere.yaml
spec_ref: sha256:<spec314_hash>
principle_ref: sha256:<p314_hash>
dataset:
  name: hard_sphere_phase_shifts
  reference: "Analytic: δₗ = −arctan(jₗ(ka)/nₗ(ka))"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Numerov
    params: {N: 1024, l_max: 10}
    results: {sigma_error: 4.5e-5, phase_error: 2.1e-7}
  - solver: RK4
    params: {N: 2048, l_max: 10}
    results: {sigma_error: 1.2e-4, phase_error: 8.3e-6}
  - solver: Variable-phase (Calogero)
    params: {N: 512}
    results: {sigma_error: 9.8e-7, phase_error: 5.1e-9}
quality_scoring:
  - {min_sigma_error: 1.0e-6, Q: 1.00}
  - {min_sigma_error: 1.0e-4, Q: 0.90}
  - {min_sigma_error: 1.0e-3, Q: 0.80}
  - {min_sigma_error: 5.0e-3, Q: 0.75}
```

**Baseline solver:** Numerov — σ error 4.5×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | σ Error | Phase Error | Runtime | Q |
|--------|---------|-------------|---------|---|
| RK4 | 1.2e-4 | 8.3e-6 | 0.8 s | 0.90 |
| Numerov | 4.5e-5 | 2.1e-7 | 0.3 s | 0.90 |
| Variable-phase | 9.8e-7 | 5.1e-9 | 0.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (variable-phase): 300 × 1.00 = 300 PWM
Floor:                      300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p314_hash>",
  "h_s": "sha256:<spec314_hash>",
  "h_b": "sha256:<bench314_hash>",
  "r": {"residual_norm": 9.8e-7, "error_bound": 1.0e-4, "ratio": 0.0098},
  "c": {"fitted_rate": 4.0, "theoretical_rate": 4.0, "K": 3},
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
pwm-node benchmarks | grep scattering
pwm-node verify scattering/hard_sphere_s1_ideal.yaml
pwm-node mine scattering/hard_sphere_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
