# Principle #185 — Eulerian-Lagrangian (Particle-Laden Flow)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [G.particle] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→G.particle→B.wall   EL-spray    particle-jet      FVM+DEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EULERIAN-LAGRANGIAN   P = (E,G,W,C)   Principle #185           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Fluid (Eulerian): ∂(ρu)/∂t + ∇·(ρu⊗u) = −∇p + ... + S_p│
│        │ Particle (Lagrangian): m_p du_p/dt = F_drag + F_grav   │
│        │ F_drag = ½CᴅρA|u−u_p|(u−u_p)                          │
│        │ Two-way coupling via source term S_p in Euler eqns    │
│        │ Forward: fluid IC/BC + particle injection → (u, x_p)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [G.particle] --> [B.wall]│
│        │ time  NS-solve  pressure  particle-track  BC                                     │
│        │ V={∂.time,N.bilinear.advection,L.poisson,G.particle,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled ODE-PDE system)                │
│        │ Uniqueness: YES for dilute regime (one-way coupling)   │
│        │ Stability: particle CFL + fluid CFL; Stokes number    │
│        │ Mismatch: drag model, particle size distribution      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = particle dispersion error, mean velocity error     │
│        │ q = 2.0 (2nd-order FVM + RK4 particle integration)   │
│        │ T = {dispersion_error, concentration_profile_error}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled Euler-Lagrange consistent; momentum exchange balanced | PASS |
| S2 | One-way coupling well-posed; two-way stable for low loading | PASS |
| S3 | RK4 particle + SIMPLE fluid converges | PASS |
| S4 | Dispersion matches Snyder & Lumley (1971) for isotropic turbulence | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# eulerian_lagrangian/particle_jet_s1.yaml
principle_ref: sha256:<p185_hash>
omega:
  grid: [128, 256]
  domain: [0.1, 0.5]   # m
  time: [0, 0.5]
E:
  forward: "Euler fluid + Lagrangian particle tracking"
  drag_model: Schiller_Naumann
B:
  inlet: {u: [0, 5.0], particles: {rate: 1000/s, d_p: 50e-6}}
  outlet: {zero_gradient: true}
  walls: {no_slip: true}
I:
  scenario: particle_laden_jet
  rho_p: 2500
  rho_f: 1.2
  N_particles: 10000
O: [dispersion_L2, mean_velocity_error, mass_loading_error]
epsilon:
  dispersion_error_max: 1.0e-1
  velocity_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves jet; particle count sufficient for statistics | PASS |
| S2 | Stokes number ~ O(1); drag correlation valid for Re_p < 800 | PASS |
| S3 | SIMPLE + RK4 converges; particle statistics converge with N | PASS |
| S4 | Dispersion error < 10% vs experimental data | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# eulerian_lagrangian/benchmark_jet.yaml
spec_ref: sha256:<spec185_hash>
principle_ref: sha256:<p185_hash>
dataset:
  name: Particle_jet_experiment
  reference: "Loth (2000) particle-laden jet data"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OpenFOAM-MPPICFoam
    params: {grid: 128x256, N_p: 10000}
    results: {dispersion_err: 8.5e-2, vel_error: 4.2e-2}
  - solver: ANSYS-Fluent (DPM)
    params: {grid: 128x256, N_p: 10000}
    results: {dispersion_err: 7.1e-2, vel_error: 3.8e-2}
  - solver: Custom FVM+RK4
    params: {grid: 128x256, N_p: 50000}
    results: {dispersion_err: 5.2e-2, vel_error: 2.5e-2}
quality_scoring:
  - {min_disp_err: 3.0e-2, Q: 1.00}
  - {min_disp_err: 6.0e-2, Q: 0.90}
  - {min_disp_err: 1.0e-1, Q: 0.80}
  - {min_disp_err: 1.5e-1, Q: 0.75}
```

**Baseline solver:** ANSYS DPM — dispersion error 7.1×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Dispersion Err | Vel Error | Runtime | Q |
|--------|---------------|-----------|---------|---|
| MPPICFoam | 8.5e-2 | 4.2e-2 | 120 s | 0.80 |
| Fluent DPM | 7.1e-2 | 3.8e-2 | 90 s | 0.80 |
| Custom FVM+RK4 (50k) | 5.2e-2 | 2.5e-2 | 300 s | 0.90 |
| LES + Lagrangian | 2.8e-2 | 1.5e-2 | 600 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (LES+Lag.): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p185_hash>",
  "h_s": "sha256:<spec185_hash>",
  "h_b": "sha256:<bench185_hash>",
  "r": {"residual_norm": 2.8e-2, "error_bound": 1.0e-1, "ratio": 0.28},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 2},
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
pwm-node benchmarks | grep euler_lagrange
pwm-node verify eulerian_lagrangian/particle_jet_s1.yaml
pwm-node mine eulerian_lagrangian/particle_jet_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
