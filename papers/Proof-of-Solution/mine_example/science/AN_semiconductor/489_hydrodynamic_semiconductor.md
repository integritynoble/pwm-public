# Principle #489 — Hydrodynamic Semiconductor Transport

**Domain:** Semiconductor Physics | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [N.bilinear] --> [∂.space] --> [L.poisson] --> [B.contact] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.bilin-->∂.x-->L.poisson-->B.cont  HD-Semi  MOSFET-hot-carrier FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HYDRODYNAMIC SEMICONDUCTOR TRANSPORT P=(E,G,W,C) Princ. #489  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂n/∂t + ∇·(nv) = 0   (density)                        │
│        │ ∂(nv)/∂t + ∇·(nvv) + ∇(nk_BT_n/m*) = −nqE/m* − nv/τ_p│
│        │ ∂W/∂t + ∇·(Wv) + ∇·(nk_BT_n v) = −nqE·v − (W−W₀)/τ_w│
│        │ W = ½m*v² + 3/2 nk_BT_n  (total energy density)       │
│        │ Forward: given doping/BC → (n, v, T_n) in device       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.bilin] ──→ [∂.x] ──→ [L.poisson] ──→ [B.cont]  │
│        │  time-step  advection  spatial  Poisson  contact-BC    │
│        │ V={∂.t,N.bilin,∂.x,L.poisson,B.cont}  A={∂.t→N.bilin,N.bilin→∂.x,∂.x→L.poisson,L.poisson→B.cont}  L_DAG=4.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic system with relaxation)     │
│        │ Uniqueness: YES for subsonic flow                      │
│        │ Stability: relaxation terms ensure convergence         │
│        │ Mismatch: closure approximation, non-parabolic bands   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |v_peak − v_ref|/v_ref  (velocity overshoot error)│
│        │ q = 2.0 (ENO/WENO for shocks), 1.0 (upwind)         │
│        │ T = {velocity_error, temperature_error, current_error} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Conservation of mass, momentum, energy consistent; T_n > 0 | PASS |
| S2 | Relaxation ensures hyperbolicity; subsonic steady states exist | PASS |
| S3 | ENO scheme + Gummel outer loop converges for n+ - n - n+ | PASS |
| S4 | Velocity overshoot matches Monte Carlo within 10% | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hd_semi/n_n_n_diode_s1.yaml
principle_ref: sha256:<p489_hash>
omega:
  mesh: 400
  domain: 1D_Si_n+nn+_diode
  length: 0.6e-6   # μm
E:
  forward: "hydrodynamic equations + Poisson"
  material: Si
  doping: {n_plus: 5e17, channel: 2e15}   # cm⁻³
  tau_p: 0.4e-12    # momentum relaxation (s)
  tau_w: 0.3e-12    # energy relaxation (s)
B:
  contacts: ohmic
  voltage: [0, 0.5, 1.0, 1.5, 2.0]   # V
I:
  scenario: hot_carrier_velocity_overshoot
  models: [drift_diffusion, hydrodynamic, Monte_Carlo_ref]
O: [peak_velocity, electron_temperature, IV_curve]
epsilon:
  velocity_error_max: 0.10
  temperature_error_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 400 mesh points resolve n+ - n transition; τ_p, τ_w physical | PASS |
| S2 | n+ - n - n+ standard benchmark for hot carriers | PASS |
| S3 | ENO + Newton converges for V up to 2V | PASS |
| S4 | Peak velocity within 10% of MC reference | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hd_semi/benchmark_nnn.yaml
spec_ref: sha256:<spec489_hash>
principle_ref: sha256:<p489_hash>
dataset:
  name: Si_n_n_n_diode_MC_reference
  reference: "Rudan & Odeh (1986); Grasser et al. (2003)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Drift-diffusion
    params: {mesh: 400}
    results: {velocity_error: 0.35, no_overshoot: true}
  - solver: Hydrodynamic (upwind)
    params: {mesh: 400, scheme: upwind}
    results: {velocity_error: 0.12, temp_error: 0.18}
  - solver: Hydrodynamic (ENO)
    params: {mesh: 400, scheme: ENO}
    results: {velocity_error: 0.08, temp_error: 0.12}
quality_scoring:
  - {min_err: 0.05, Q: 1.00}
  - {min_err: 0.10, Q: 0.90}
  - {min_err: 0.15, Q: 0.80}
  - {min_err: 0.30, Q: 0.75}
```

**Baseline solver:** Hydrodynamic (ENO) — velocity error 8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Velocity Error | Temp Error | Runtime | Q |
|--------|---------------|-----------|---------|---|
| Drift-diffusion | 0.35 | N/A | 0.1 s | 0.75 |
| HD upwind | 0.12 | 0.18 | 0.5 s | 0.80 |
| HD ENO | 0.08 | 0.12 | 1.0 s | 0.90 |
| HD WENO (fine) | 0.04 | 0.06 | 5.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (WENO): 400 × 1.00 = 400 PWM
Floor:            400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p489_hash>",
  "h_s": "sha256:<spec489_hash>",
  "h_b": "sha256:<bench489_hash>",
  "r": {"velocity_error": 0.04, "error_bound": 0.10, "ratio": 0.400},
  "c": {"temp_error": 0.06, "voltages": 5, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep hd_semi
pwm-node verify hd_semi/n_n_n_diode_s1.yaml
pwm-node mine hd_semi/n_n_n_diode_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
