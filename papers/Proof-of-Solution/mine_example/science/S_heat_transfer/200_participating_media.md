# Principle #200 — Participating Media Radiation

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.angular] --> [K.scatter] --> [∫.angular] --> [N.absorption] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.angular→K.scatter→∫.angular→N.absorption   PartMedia   combustion-slab   DOM/P1
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PARTICIPATING MEDIA   P = (E,G,W,C)   Principle #200           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ RTE + energy: coupled radiation-conduction             │
│        │ ρcₚ ∂T/∂t = ∇·(k∇T) − ∇·q_rad + Q                  │
│        │ ∇·q_rad = κ(4σT⁴ − G);  G = ∫₄π I dΩ               │
│        │ Emission, absorption, scattering all present           │
│        │ Forward: T field + κ(λ,T) → coupled (T, I)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.angular] --> [K.scatter] --> [∫.angular] --> [N.absorption]│
│        │ angular-transport  scattering-kernel  angular-integral  absorption│
│        │ V={∂.angular,K.scatter,∫.angular,N.absorption}  L_DAG=3.0         │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled system well-posed for T > 0)  │
│        │ Uniqueness: YES (contraction mapping for moderate τ)  │
│        │ Stability: T⁴ nonlinearity; requires iteration        │
│        │ Mismatch: spectral κ(λ), WSGGM model parameters     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = temperature L2 error, radiative flux error         │
│        │ q = 2.0 (FVM + DOM)                                   │
│        │ T = {T_error, flux_error, energy_balance}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled RTE + energy consistent; T⁴ emission well-formed | PASS |
| S2 | Fixed-point iteration on T-I coupling converges | PASS |
| S3 | P1/DOM + FVM energy equation converge together | PASS |
| S4 | Temperature error < 2% vs benchmark for τ ∈ [0.1, 10] | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# participating_media/comb_slab_s1.yaml
principle_ref: sha256:<p200_hash>
omega:
  grid: [100]
  domain: [0, 1]
  time: steady_state
E:
  forward: "∇·(k∇T) = ∇·q_rad;  DOM for RTE"
  k: 0.1
  kappa: 1.0    # absorption coefficient
  sigma_s: 0.0
B:
  left: {T: 1500, emissivity: 0.8}
  right: {T: 500, emissivity: 0.8}
I:
  scenario: radiation_conduction_slab
  conduction_radiation_param: [0.01, 0.1, 1.0]
  N_directions: [4, 8, 16]
O: [T_L2_error, heat_flux_error, energy_balance]
epsilon:
  T_error_max: 2.0e-2
  flux_error_max: 3.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D slab; conduction-radiation parameter well-defined | PASS |
| S2 | Coupled system converges via Picard iteration | PASS |
| S3 | DOM-S8 + FDM converges within 20 outer iterations | PASS |
| S4 | T error < 2% vs Modest benchmark | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# participating_media/benchmark_slab.yaml
spec_ref: sha256:<spec200_hash>
principle_ref: sha256:<p200_hash>
dataset:
  name: Modest_radiation_conduction
  reference: "Modest (2013) Ch. 22 benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: P1 + FDM
    params: {N: 100}
    results: {T_error: 3.5e-2, flux_error: 5.2e-2}
  - solver: DOM-S8 + FDM
    params: {N: 100}
    results: {T_error: 1.2e-2, flux_error: 1.8e-2}
  - solver: Monte Carlo + FDM
    params: {N: 100, photons: 1e6}
    results: {T_error: 8.5e-3, flux_error: 1.5e-2}
quality_scoring:
  - {min_T_err: 5.0e-3, Q: 1.00}
  - {min_T_err: 1.5e-2, Q: 0.90}
  - {min_T_err: 3.0e-2, Q: 0.80}
  - {min_T_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** DOM-S8 + FDM — T error 1.2×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Error | Flux Error | Runtime | Q |
|--------|---------|-----------|---------|---|
| P1 approx | 3.5e-2 | 5.2e-2 | 0.5 s | 0.80 |
| DOM-S8 | 1.2e-2 | 1.8e-2 | 2 s | 0.90 |
| Monte Carlo | 8.5e-3 | 1.5e-2 | 30 s | 0.90 |
| DOM-S16 (fine) | 4.2e-3 | 6.1e-3 | 5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (DOM-S16): 300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p200_hash>",
  "h_s": "sha256:<spec200_hash>",
  "h_b": "sha256:<bench200_hash>",
  "r": {"residual_norm": 4.2e-3, "error_bound": 2.0e-2, "ratio": 0.21},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep participating
pwm-node verify participating_media/comb_slab_s1.yaml
pwm-node mine participating_media/comb_slab_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
