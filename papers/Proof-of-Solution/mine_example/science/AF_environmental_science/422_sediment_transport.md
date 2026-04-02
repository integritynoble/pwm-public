# Principle #422 — Sediment Transport (Exner Equation)

**Domain:** Environmental Science | **Carrier:** bed elevation | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.bilinear.advection → ∂.space |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space      Exner-eq     bed-evolution      FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEDIMENT TRANSPORT (EXNER)     P = (E,G,W,C)   Principle #422 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ (1−λ_p) ∂η/∂t + ∂q_s/∂x = 0           (Exner)       │
│        │ q_s = α (τ_b − τ_cr)^{3/2}   (Meyer-Peter-Mueller)   │
│        │ η = bed elevation, q_s = bedload flux                  │
│        │ τ_b = bed shear stress, τ_cr = critical shear          │
│        │ Forward: given flow field → η(x,t) bed evolution       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space]      │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.bilinear.advection, ∂.space}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic conservation law)           │
│        │ Uniqueness: YES (entropy solution for given flux)      │
│        │ Stability: morphological CFL constraint                │
│        │ Mismatch: transport formula choice, grain size dist.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖η−η_ref‖/‖η_ref‖                  │
│        │ q = 1.0 (upwind), 2.0 (MUSCL)                       │
│        │ T = {bed_error, sediment_conservation, K_timesteps}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Bed elevation, sediment flux, shear stress dimensionally consistent | PASS |
| S2 | Exner equation is hyperbolic — entropy solution exists | PASS |
| S3 | FVM-upwind converges; morphological acceleration (MORFAC) stable | PASS |
| S4 | Bed elevation error computable against flume experiment data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sediment_transport/bed_evolution_s1_ideal.yaml
principle_ref: sha256:<p422_hash>
omega:
  grid: [200]
  domain: channel_1D
  length: 1000   # m
  time: [0, 3600.0]   # s (1 hour)
  dt: 0.5
E:
  forward: "(1−λ_p)∂η/∂t + ∂q_s/∂x = 0 (Exner + MPM)"
  porosity: 0.4
  d50: 0.001   # m (1 mm sand)
B:
  upstream: {Q: 1.0, q_s: equilibrium}
  downstream: {h: normal_depth}
I:
  scenario: aggradation_degradation
  mesh_sizes: [50, 100, 200]
O: [eta_L2_error, sediment_mass_error]
epsilon:
  eta_error_max: 0.01   # m
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 cells over 1 km; dt=0.5 s satisfies morphological CFL | PASS |
| S2 | Steady flow + Exner — quasi-steady analytical comparison | PASS |
| S3 | FVM-upwind converges for bedload-dominated transport | PASS |
| S4 | Bed error < 1 cm achievable at 200 cells | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sediment_transport/benchmark_bed.yaml
spec_ref: sha256:<spec422_hash>
principle_ref: sha256:<p422_hash>
dataset:
  name: flume_aggradation
  reference: "Seal et al. (1997) aggradation experiments"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-upwind
    params: {N: 100, dt: 0.5}
    results: {eta_err: 0.025, mass_err: 1.0e-8}
  - solver: FVM-MUSCL
    params: {N: 100, dt: 0.5}
    results: {eta_err: 0.008, mass_err: 1.0e-8}
  - solver: FVM-MUSCL-fine
    params: {N: 400, dt: 0.1}
    results: {eta_err: 0.002, mass_err: 1.0e-10}
quality_scoring:
  - {min_eta_err: 0.002, Q: 1.00}
  - {min_eta_err: 0.01, Q: 0.90}
  - {min_eta_err: 0.03, Q: 0.80}
  - {min_eta_err: 0.05, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL — eta error 0.8 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | eta L2 Error (m) | Mass Error | Runtime | Q |
|--------|-----------------|-----------|---------|---|
| FVM-upwind | 0.025 | 1e-8 | 0.5 s | 0.80 |
| FVM-MUSCL | 0.008 | 1e-8 | 1 s | 0.90 |
| FVM-MUSCL-fine | 0.002 | 1e-10 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (fine): 300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p422_hash>",
  "h_s": "sha256:<spec422_hash>",
  "h_b": "sha256:<bench422_hash>",
  "r": {"eta_err": 0.002, "mass_err": 1.0e-10, "ratio": 0.20},
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
pwm-node benchmarks | grep sediment_transport
pwm-node verify AF_environmental_science/sediment_transport_s1_ideal.yaml
pwm-node mine AF_environmental_science/sediment_transport_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
