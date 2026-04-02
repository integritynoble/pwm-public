# Fiber-Optic Mode Propagation — Four-Layer Walkthrough

**Principle #240 · Fiber-Optic Mode Solver**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: standard (δ=3) | DAG: [∂.space] --> [N.kerr] --> [F.dft]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Scalar/vector    │→│ Step-index or    │→│ Analytical LP    │→│ FEM / FDM /      │
│ wave eqn in      │ │ graded fiber,    │ │ modes, Sellmeier │ │ transfer matrix  │
│ cylindrical      │ │ S1-S4 scenarios  │ │ baselines        │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇²_t E_t + (n²(r)k₀² − β²)E_t = 0
Characteristic equation (step-index): J_ℓ(u)/[uJ_ℓ(u)] = K_ℓ(w)/[wK_ℓ(w)]
V-number: V = k₀a√(n₁² − n₂²), single-mode when V < 2.405

### DAG

```
[∂.space] --> [N.kerr] --> [F.dft]
spatial-propagation  Kerr-nonlinearity  spectral-transform
```

V={∂.space,N.kerr,F.dft}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Bounded refractive index → discrete guided modes |
| Uniqueness | YES | Each mode has unique n_eff |
| Stability | YES | n_eff depends continuously on profile |

Mismatch: core radius tolerance, refractive index error, wavelength drift

### Error Method

e = relative n_eff error |Δn_eff|/|n_eff|, mode-field diameter error
q = 2.0 (FDM), q = 4.0 (spectral method)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #240"
omega:
  fiber: step_index_SMF
  core_um: 4.1
  n_core: 1.4504
  n_clad: 1.4447
  wavelength_nm: 1550
E:
  forward: "nabla_t^2 E + (n^2*k0^2 - beta^2)*E = 0"
I:
  scenario: S1_ideal
  n_modes: 1  # single-mode
O: [n_eff_error, MFD_error_pct, cutoff_wavelength_error_nm]
epsilon:
  n_eff_error_max: 1e-6
  MFD_error_max_pct: 0.5
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact step-index | None | n_eff err ≤ 1e-6 |
| S2 Mismatch | Core radius ±0.1 μm | Δa | n_eff err ≤ 5e-5 |
| S3 Oracle | True radius given | Known Δa | n_eff err ≤ 5e-6 |
| S4 Blind Cal | Estimate a from n_eff meas | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: fiber_modes
  cases: 8  # SMF, MMF, graded-index, PCF
  analytical_ref: LP_mode_solutions, Gloge_approximations
baselines:
  - solver: FDM_cylindrical
    n_eff_err: 5e-7
    time_s: 2
  - solver: FEM_vectorial
    n_eff_err: 1e-7
    time_s: 8
quality_scoring:
  metric: n_eff_error
  thresholds:
    - {max: 1e-7, Q: 1.00}
    - {max: 5e-7, Q: 0.90}
    - {max: 1e-6, Q: 0.80}
    - {max: 1e-5, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | n_eff err | Time | Q | Reward |
|--------|----------|------|---|--------|
| FDM_cylindrical | 5e-7 | 2s | 0.90 | 270 PWM |
| FEM_vectorial | 1e-7 | 8s | 1.00 | 300 PWM |
| spectral_Galerkin | 5e-8 | 5s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 240,
  "r": {"residual_norm": 1e-7, "error_bound": 1e-6, "ratio": 0.10},
  "c": {"resolutions": [50,100,200], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 270–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep fiber_optic
pwm-node mine fiber/smf_s1_ideal.yaml
```
