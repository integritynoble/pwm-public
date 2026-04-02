# Principle #199 — Radiation Heat Transfer (RTE)

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.angular] --> [K.scatter] --> [∫.angular] --> [N.emission] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.angular→K.scatter→∫.angular→N.emission      RTE         gray-slab-1D      DOM/MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RADIATIVE TRANSFER (RTE)   P = (E,G,W,C)   Principle #199      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ŝ·∇I(r,ŝ) = κ(Ib−I) + σs/(4π)∫I(ŝ')Φ(ŝ'→ŝ)dΩ'   │
│        │ I = radiative intensity, κ = absorption, σs = scatter  │
│        │ Ib = σT⁴/π (blackbody), Φ = scattering phase function│
│        │ Integro-differential in space × direction (5D)        │
│        │ Forward: T(x)/κ/σs → solve I(r,ŝ) → compute q_rad   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.angular] --> [K.scatter] --> [∫.angular] --> [N.emission]│
│        │ angular-derivative  scattering-kernel  angular-integration  emission-source│
│        │ V={∂.angular,K.scatter,∫.angular,N.emission}  L_DAG=3.0                    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear integro-DE for given T)         │
│        │ Uniqueness: YES (integral operator contraction)        │
│        │ Stability: well-conditioned for finite optical depth   │
│        │ Mismatch: κ wavelength dependence, scattering approx  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = radiative heat flux error, intensity L2 error      │
│        │ q = 2.0 (DOM S4/S8), MC: O(1/√N)                    │
│        │ T = {heat_flux_error, intensity_error, K_directions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | RTE dimensionally consistent; energy conservation with emission | PASS |
| S2 | Linear RTE for fixed T; unique solution via integral formulation | PASS |
| S3 | DOM (discrete ordinates), P_N, Monte Carlo all converge | PASS |
| S4 | Heat flux error bounded; exact solutions for gray slab | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rte/gray_slab_s1.yaml
principle_ref: sha256:<p199_hash>
omega:
  grid: [100]
  domain: [0, 1]   # optical thickness τ = κL
E:
  forward: "μ dI/dτ + I = (1−ω)Ib + ω/(2)∫I dμ'"
  optical_thickness: 1.0
  scattering_albedo: 0.0   # pure absorption
B:
  left: {emissivity: 1.0, T: 1000}
  right: {emissivity: 1.0, T: 500}
I:
  scenario: gray_slab_1D
  tau_values: [0.1, 1.0, 10.0]
  N_directions: [4, 8, 16]   # S_N quadrature
O: [heat_flux_error, intensity_L2, emissive_power_error]
epsilon:
  flux_error_max: 1.0e-2
  intensity_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D slab; gray medium; angular quadrature adequate | PASS |
| S2 | Exact analytical solution for pure absorption gray slab | PASS |
| S3 | DOM-S8 converges; sweeping method stable | PASS |
| S4 | Heat flux error < 1% at N=100, S8 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# rte/benchmark_gray_slab.yaml
spec_ref: sha256:<spec199_hash>
principle_ref: sha256:<p199_hash>
dataset:
  name: Gray_slab_exact
  reference: "Modest (2013) Ch. 14 exact solutions"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DOM-S4
    params: {N: 100}
    results: {flux_error: 2.5e-2, intensity_err: 1.2e-2}
  - solver: DOM-S8
    params: {N: 100}
    results: {flux_error: 5.1e-3, intensity_err: 2.8e-3}
  - solver: Monte Carlo
    params: {N_photons: 1e6}
    results: {flux_error: 3.2e-3, intensity_err: 5.1e-3}
quality_scoring:
  - {min_flux_err: 1.0e-3, Q: 1.00}
  - {min_flux_err: 5.0e-3, Q: 0.90}
  - {min_flux_err: 1.0e-2, Q: 0.80}
  - {min_flux_err: 3.0e-2, Q: 0.75}
```

**Baseline solver:** DOM-S8 — flux error 5.1×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Flux Error | Intensity Err | Runtime | Q |
|--------|-----------|--------------|---------|---|
| DOM-S4 | 2.5e-2 | 1.2e-2 | 0.1 s | 0.80 |
| DOM-S8 | 5.1e-3 | 2.8e-3 | 0.3 s | 0.90 |
| DOM-S16 | 8.2e-4 | 4.5e-4 | 1.0 s | 1.00 |
| Monte Carlo (10⁶) | 3.2e-3 | 5.1e-3 | 10 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (DOM-S16): 300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p199_hash>",
  "h_s": "sha256:<spec199_hash>",
  "h_b": "sha256:<bench199_hash>",
  "r": {"residual_norm": 8.2e-4, "error_bound": 1.0e-2, "ratio": 0.082},
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
pwm-node benchmarks | grep rte
pwm-node verify rte/gray_slab_s1.yaml
pwm-node mine rte/gray_slab_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
