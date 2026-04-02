# Principle #400 — Hemodynamics (1D Arterial Network)

**Domain:** Computational Biology | **Carrier:** blood pressure/flow | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.bilinear.advection → ∂.space |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space      1D-arterial  aorta-network     FVM/DG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HEMODYNAMICS (1D ARTERIAL)     P = (E,G,W,C)   Principle #400  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂A/∂t + ∂(Au)/∂x = 0                    (mass)        │
│        │ ∂u/∂t + u ∂u/∂x + (1/ρ) ∂p/∂x = −f u/A (momentum)   │
│        │ p − p_ext = β(√A − √A₀)/A₀  (tube law)               │
│        │ A = cross-section area, u = velocity, p = pressure     │
│        │ Forward: given inlet Q(t), outlet BC → p(x,t), u(x,t) │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space]      │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.bilinear.advection, ∂.space}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic system with tube law)       │
│        │ Uniqueness: YES (Riemann problem well-posed)           │
│        │ Stability: CFL condition on wave speed c = √(β√A/(2ρA₀))│
│        │ Mismatch: wall stiffness β, outlet impedance           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative pressure error ‖p−p_ref‖/‖p_ref‖         │
│        │ q = 2.0 (FVM-MUSCL), 3.0 (DG-P2)                    │
│        │ T = {pressure_error, flow_error, wave_speed_error}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Area, velocity, pressure dimensions consistent with tube law | PASS |
| S2 | Hyperbolic system — characteristic analysis yields well-posed IVP | PASS |
| S3 | FVM with Riemann solver converges; DG achieves high-order | PASS |
| S4 | Pressure error computable against 3D FSI or in vivo data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hemodynamics/aorta_network_s1_ideal.yaml
principle_ref: sha256:<p400_hash>
omega:
  network: 55_artery_tree
  time: [0, 1.0]   # one cardiac cycle (s)
  dt: 1.0e-4   # s
E:
  forward: "1D blood flow: mass + momentum + tube law"
  rho: 1060   # kg/m³
  beta: vessel_dependent
B:
  inlet: {Q: cardiac_waveform}
  outlets: {windkessel_3element: true}
I:
  scenario: systemic_arterial_network
  mesh_sizes: [50, 100, 200]   # elements per vessel
O: [pressure_L2_error, flow_L2_error]
epsilon:
  pressure_error_max: 0.02   # 2% relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 55-artery network covers major systemic arteries; dt CFL-safe | PASS |
| S2 | Tube law and junction conditions well-defined | PASS |
| S3 | FVM-MUSCL converges at O(h²) per vessel | PASS |
| S4 | Pressure error < 2% achievable at 200 elements/vessel | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hemodynamics/benchmark_aorta.yaml
spec_ref: sha256:<spec400_hash>
principle_ref: sha256:<p400_hash>
dataset:
  name: ADAN_arterial_reference
  reference: "Blanco et al. (2015) ADAN model reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-Lax-Wendroff
    params: {N: 100}
    results: {p_error: 3.5e-2, Q_error: 4.0e-2}
  - solver: FVM-MUSCL
    params: {N: 100}
    results: {p_error: 1.8e-2, Q_error: 2.2e-2}
  - solver: DG-P2
    params: {N: 50}
    results: {p_error: 5.0e-3, Q_error: 6.5e-3}
quality_scoring:
  - {max_p_err: 0.005, Q: 1.00}
  - {max_p_err: 0.02, Q: 0.90}
  - {max_p_err: 0.05, Q: 0.80}
  - {max_p_err: 0.10, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL — pressure error 1.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pressure Error | Flow Error | Runtime | Q |
|--------|---------------|-----------|---------|---|
| FVM-Lax-Wendroff | 3.5e-2 | 4.0e-2 | 2 s | 0.80 |
| FVM-MUSCL | 1.8e-2 | 2.2e-2 | 5 s | 0.90 |
| DG-P2 | 5.0e-3 | 6.5e-3 | 8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DG-P2): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p400_hash>",
  "h_s": "sha256:<spec400_hash>",
  "h_b": "sha256:<bench400_hash>",
  "r": {"p_error": 5.0e-3, "Q_error": 6.5e-3, "ratio": 0.25},
  "c": {"fitted_rate": 2.95, "theoretical_rate": 3.0, "K": 3},
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
pwm-node benchmarks | grep hemodynamics
pwm-node verify AE_computational_biology/hemodynamics_s1_ideal.yaml
pwm-node mine AE_computational_biology/hemodynamics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
