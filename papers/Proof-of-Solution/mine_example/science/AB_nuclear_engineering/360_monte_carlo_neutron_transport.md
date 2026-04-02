# Principle #360 — Monte Carlo Neutron Transport (MCNP)

**Domain:** Nuclear Engineering | **Carrier:** neutron histories | **Difficulty:** Advanced (δ=5)
**DAG:** S.random → K.scatter.nuclear → ∫.path |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random→K.scatter.nuclear→∫.path      MC-transport shielding/keff    analog/VR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MONTE CARLO NEUTRON TRANSPORT  P = (E,G,W,C)   Principle #360  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ⟨f⟩ = ∫ f(r,Ω,E) ψ(r,Ω,E) dV dΩ dE                 │
│        │ Estimate tally ⟨f⟩ by random walk of N particle histories│
│        │ Each history: sample source → track → collide → repeat │
│        │ Variance: Var(⟨f⟩) ~ σ²/N  (CLT convergence)         │
│        │ Forward: given geometry/materials/source → tallies ± σ  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random] ──→ [K.scatter.nuclear] ──→ [∫.path]        │
│        │ sample  kernel  integrate                              │
│        │ V={S.random, K.scatter.nuclear, ∫.path}  A={S.random→K.scatter.nuclear, K.scatter.nuclear→∫.path}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (CLT guarantees estimator convergence)  │
│        │ Uniqueness: YES (expected value of tally is unique)    │
│        │ Stability: 1/√N convergence; FOM = 1/(σ²·T_cpu)       │
│        │ Mismatch: nuclear data, geometry simplification        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative tally error σ/⟨f⟩ (statistical)          │
│        │ q = 0.5 (1/√N convergence rate)                      │
│        │ T = {tally_RE, FOM, N_histories, K_batches}            │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Tallies well-defined; geometry/material cards consistent | PASS |
| S2 | CLT applies for finite-variance tallies | PASS |
| S3 | Analog MC converges at 1/√N; variance reduction improves FOM | PASS |
| S4 | Relative error σ/⟨f⟩ computable from batch statistics | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mc_transport/shielding_s1_ideal.yaml
principle_ref: sha256:<p360_hash>
omega:
  geometry: slab_shield
  materials: [iron, concrete, air]
  source: 14.1_MeV_point
  histories: [1e6, 1e7, 1e8]
E:
  forward: "Monte Carlo random walk with continuous-energy cross-sections"
  variance_reduction: [weight_windows, implicit_capture]
B:
  source: {type: point, energy: 14.1e6, position: [0,0,0]}
I:
  scenario: deep_penetration_shielding
  shield_thickness: 100   # cm
  mesh_sizes_N: [1e6, 1e7, 1e8]
O: [dose_rate_RE, transmission_factor, FOM]
epsilon:
  RE_max: 0.05   # 5% relative error
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Geometry/material definitions consistent; source well-defined | PASS |
| S2 | Deep penetration solvable with weight windows | PASS |
| S3 | 1/√N convergence verified across history counts | PASS |
| S4 | RE < 5% achievable with 10⁸ histories + weight windows | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mc_transport/benchmark_shielding.yaml
spec_ref: sha256:<spec360_hash>
principle_ref: sha256:<p360_hash>
dataset:
  name: SINBAD_iron_benchmark
  reference: "SINBAD shielding benchmark archive"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MCNP6-analog
    params: {N: 1e7}
    results: {RE: 0.12, FOM: 0.8}
  - solver: MCNP6-WW
    params: {N: 1e7, weight_windows: CADIS}
    results: {RE: 0.03, FOM: 25.0}
  - solver: Serpent2
    params: {N: 1e7, delta_tracking: true}
    results: {RE: 0.04, FOM: 18.0}
quality_scoring:
  - {max_RE: 0.02, Q: 1.00}
  - {max_RE: 0.05, Q: 0.90}
  - {max_RE: 0.10, Q: 0.80}
  - {max_RE: 0.15, Q: 0.75}
```

**Baseline solver:** MCNP6-WW — RE 3%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Relative Error | FOM | Runtime | Q |
|--------|---------------|-----|---------|---|
| MCNP6-analog | 0.12 | 0.8 | 600 s | 0.80 |
| Serpent2-DT | 0.04 | 18.0 | 300 s | 0.90 |
| MCNP6-WW(CADIS) | 0.03 | 25.0 | 250 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case:  500 × 0.90 = 450 PWM
Floor:      500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p360_hash>",
  "h_s": "sha256:<spec360_hash>",
  "h_b": "sha256:<bench360_hash>",
  "r": {"RE": 0.03, "FOM": 25.0, "N_histories": 1e7},
  "c": {"convergence_rate": 0.50, "N_batches": 100, "K": 3},
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep mc_transport
pwm-node verify AB_nuclear_engineering/mc_transport_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/mc_transport_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
