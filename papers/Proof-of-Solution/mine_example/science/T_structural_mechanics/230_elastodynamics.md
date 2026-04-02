# Principle #230 — Elastodynamics (Wave Propagation in Solids)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [∂.space] --> [L.elastic] --> [B.absorbing] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space→L.elastic→B.absorbing   elastodyn   Lamb-wave-plate    FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ELASTODYNAMICS (WAVE PROPAGATION) P = (E,G,W,C)  Principle #230│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρ ∂²u/∂t² = ∇·σ + f,  σ = C:ε                       │
│        │ P-wave: c_p = √((λ+2μ)/ρ)                             │
│        │ S-wave: c_s = √(μ/ρ)                                   │
│        │ Forward: given IC/BC/source → solve for u(x,t)        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space] --> [L.elastic] --> [B.absorbing]│
│        │ time-integration  spatial-derivatives  elastic-solve  absorbing-BC│
│        │ V={∂.time,∂.space,L.elastic,B.absorbing}  L_DAG=3.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic PDE; well-posed with IC/BC)│
│        │ Uniqueness: YES (energy conservation; finite speed)    │
│        │ Stability: CFL condition for explicit; Δt ≤ h/c_p     │
│        │ Mismatch: wave speed error, numerical dispersion       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-Q2); dispersion limits long-time accuracy│
│        │ T = {waveform_error, arrival_time_error, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wave speeds consistent with material; CFL condition met | PASS |
| S2 | Hyperbolic PDE well-posed; unique solution by energy methods | PASS |
| S3 | Explicit Newmark-β (β=0) with lumped mass converges under CFL | PASS |
| S4 | L2 error bounded by dispersion analysis + mesh refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# elastodynamics/lamb_wave_s1_ideal.yaml
principle_ref: sha256:<p230_hash>
omega:
  grid: [512, 16]
  domain: aluminium_plate
  length: 0.5
  thickness: 0.002
  time: [0, 0.0001]
  dt: 1.0e-8   # CFL-compliant
E:
  forward: "rho * d2u/dt2 = div(sigma)"
  density: 2700
  E_modulus: 70.0e9
  poisson: 0.33
B:
  source: {type: tone_burst, freq: 200e3, cycles: 5, pos: [0.0, 0.001]}
  edges: {absorbing: true}
I:
  scenario: Lamb_wave_S0_A0
  freq_thickness: [0.2, 0.4]   # MHz·mm
  mesh_sizes: [128x4, 256x8, 512x16]
O: [L2_waveform_error, group_velocity_error, mode_separation]
epsilon:
  L2_error_max: 5.0e-3
  velocity_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Elements per wavelength ≥ 20 at 200 kHz; CFL satisfied | PASS |
| S2 | Lamb wave dispersion curves provide reference group velocities | PASS |
| S3 | Explicit time integration converges under CFL constraint | PASS |
| S4 | L2 error < 5×10⁻³ at 512×16 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# elastodynamics/benchmark_lamb.yaml
spec_ref: sha256:<spec230_hash>
principle_ref: sha256:<p230_hash>
dataset:
  name: Lamb_wave_aluminium
  reference: "Dispersion curves from Rayleigh-Lamb frequency equation"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-explicit-Q4 (256×8)
    params: {h: 1/256, dt: 1e-8, Newmark: true}
    results: {L2_error: 1.2e-2, velocity_error: 2.0e-2}
  - solver: FEM-explicit-Q8 (256×8)
    params: {h: 1/256, dt: 5e-9}
    results: {L2_error: 3.0e-3, velocity_error: 5.0e-3}
  - solver: Spectral-element (p=8, 64×2)
    params: {p: 8, GLL: true}
    results: {L2_error: 5.0e-4, velocity_error: 1.0e-3}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 2.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-explicit-Q8 — L2 error 3.0×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Vel. Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FEM-Q4 explicit (256×8) | 1.2e-2 | 2.0e-2 | 30 s | 0.75 |
| FEM-Q8 explicit (256×8) | 3.0e-3 | 5.0e-3 | 120 s | 0.80 |
| SEM (p=8, 64×2) | 5.0e-4 | 1.0e-3 | 60 s | 1.00 |
| SEM (p=12, 32×2) | 8.0e-5 | 2.0e-4 | 40 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SEM p=12): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p230_hash>",
  "h_s": "sha256:<spec230_hash>",
  "h_b": "sha256:<bench230_hash>",
  "r": {"residual_norm": 8.0e-5, "error_bound": 5.0e-3, "ratio": 0.016},
  "c": {"fitted_rate": 2.05, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep elastodynamics
pwm-node verify elastodynamics/lamb_wave_s1_ideal.yaml
pwm-node mine elastodynamics/lamb_wave_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
