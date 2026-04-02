# Maxwell Full-Wave Solver — Four-Layer Walkthrough

**Principle #232 · Maxwell Full-Wave Electromagnetic Simulation**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: hard (δ=5) | DAG: [∂.time] --> [∂.space.curl] --> [B.absorbing]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Maxwell eqns,    │→│ 3D cavity or     │→│ Analytical modes │→│ FDTD / FEM /     │
│ curl-curl form,  │ │ scatterer spec,  │ │ + ref solutions, │ │ spectral solver,  │
│ BCs, materials   │ │ S1-S4 scenarios  │ │ baselines, grids │ │ certificate       │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle (The Physics)

### Governing Equation

∇×(∇×E) − k₀²ε_r E = −jωμ₀ J_src

Full-wave Maxwell's equations in frequency domain:
- E, H ∈ C³ vector fields
- ε_r(x) complex permittivity (dispersive media)
- Boundary: PEC, PMC, impedance, or absorbing (PML)

### DAG Decomposition

```
[Src] → [Mat] → [Curl²] → [BC] → [Detect]
 J_src   ε_r(x)  ∇×∇×E    PML    E,H fields
```

V={∂.time,∂.space.curl,B.absorbing}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Lax-Milgram for lossy media; Fredholm alternative for lossless |
| Uniqueness | YES | Unique at non-resonant frequencies; lossy media always unique |
| Stability | CONDITIONAL | κ grows near resonance; PML reflection < 10⁻⁶ required |

Mismatch parameters: mesh size h, PML thickness, material ε_r error, source positioning

### Error Method

e = relative L² error ‖E_num − E_ref‖/‖E_ref‖
q = 2.0 (second-order edge elements), q = 4.0 (high-order)
Convergence verified via h-refinement at K ≥ 3 resolutions

---

## Layer 2 — spec.md (Task Design)

```yaml
principle_ref: "Principle #232"

omega:
  domain: [1.0, 1.0, 1.0]  # 1m³ cavity
  freq_GHz: 3.0
  grid: [64, 64, 64]

E:
  forward: "curl(curl(E)) - k0^2 * eps_r * E = -j*omega*mu0*J"
  material: {eps_r: 2.2, sigma: 0.01}
  boundary: PML_8_layers

I:
  scenario: S1_ideal
  source: {type: electric_dipole, pos: [0.5, 0.5, 0.5]}
  mismatch: null

O: [relative_L2_error, field_energy_conservation, S_parameter_error]

epsilon:
  rel_L2_max: 0.02
  energy_conservation: 0.999
```

### S1-S4 Scenario Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | True ε_r, exact BCs | None | rel_err ≤ 0.02 |
| S2 Mismatch | Nominal ε_r ± 5% | Δε_r, mesh shift | rel_err ≤ 0.05 |
| S3 Oracle | True ε_r given | Known perturbation | rel_err ≤ 0.03 |
| S4 Blind Cal | Estimate ε_r from fields | Self-calibrate | recovery ≥ 80% |

Layer 2 reward: 150 × φ(t) PWM per spec

---

## Layer 3 — Benchmark (Data + Baselines)

```yaml
spec_ref: "spec #232-S1"
dataset:
  name: maxwell_cavity_3D
  cases: 8
  analytical_modes: TE101, TM110, TE111
  mesh_sizes: [h/4, h/2, h]

baselines:
  - solver: FDTD_Yee
    rel_L2: 0.018
    time_s: 120
  - solver: FEM_Nedelec_p2
    rel_L2: 0.005
    time_s: 300
  - solver: FDFD_direct
    rel_L2: 0.012
    time_s: 180

quality_scoring:
  metric: relative_L2_error
  thresholds:
    - {max: 0.005, Q: 1.00}
    - {max: 0.010, Q: 0.90}
    - {max: 0.020, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

Layer 3 reward: 100 × φ(t) PWM per benchmark

---

## Layer 4 — Solution (Mining)

### Solver Table

| Solver | rel_L2 | Time | Q | Reward (≈) |
|--------|--------|------|---|------------|
| FDTD_Yee | 0.018 | 120s | 0.80 | 400 PWM |
| FEM_Nedelec_p2 | 0.005 | 300s | 1.00 | 500 PWM |
| FDFD_direct | 0.012 | 180s | 0.90 | 450 PWM |
| Spectral_hp | 0.002 | 600s | 1.00 | 500 PWM |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
  = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 232,
  "r": {"residual_norm": 0.005, "error_bound": 0.02, "ratio": 0.25},
  "c": {"resolutions": [32,64,128], "fitted_rate": 2.04, "theoretical_rate": 2.0},
  "Q": 1.00,
  "gates": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | One-time | Ongoing |
|-------|----------|---------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec | 150 PWM × 4 | 10% of L4 mints |
| L3 Benchmark | 100 PWM × 4 | 15% of L4 mints |
| L4 Solution | — | 400–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep maxwell_fullwave
pwm-node verify maxwell/cavity_s1_ideal.yaml
pwm-node mine maxwell/cavity_s1_ideal.yaml
```
