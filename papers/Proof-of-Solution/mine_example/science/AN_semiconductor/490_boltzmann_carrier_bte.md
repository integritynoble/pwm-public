# Principle #490 — Boltzmann Transport (Carrier BTE)

**Domain:** Semiconductor Physics | **Carrier:** N/A (kinetic) | **Difficulty:** Expert (δ=5)
**DAG:** [∂.time] --> [K.scatter] --> [∫.angular] --> [N.pointwise] | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->K.scat-->∫.ang-->N.pw  BTE-carrier bulk-Si-mobility  MC/SH-expand
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BOLTZMANN TRANSPORT (CARRIER BTE) P=(E,G,W,C) Principle #490  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂f/∂t + v·∇_r f + (qE/ℏ)·∇_k f = C[f]               │
│        │ f(r,k,t) = distribution function                       │
│        │ C[f] = Σ_s ∫ [S_s(k'→k)f(k') − S_s(k→k')f(k)] dk'  │
│        │ Scattering: acoustic, optical, ionized impurity, etc.  │
│        │ Forward: given (E-field, T, doping) → mobility, f(k)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [K.scat] ──→ [∫.ang] ──→ [N.pw]              │
│        │  time-step  scattering  angle-integ  field-couple      │
│        │ V={∂.t,K.scat,∫.ang,N.pw}  A={∂.t→K.scat,K.scat→∫.ang,∫.ang→N.pw}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (BTE well-posed with bounded C[f])     │
│        │ Uniqueness: YES (H-theorem → unique steady state)     │
│        │ Stability: MC convergence ~ 1/√N_particles            │
│        │ Mismatch: band structure approx, quantum corrections   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |μ_sim − μ_expt|/μ_expt  (mobility error)        │
│        │ q = N/A (MC statistical)                              │
│        │ T = {mobility_error, velocity_field, energy_dist}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Distribution f ≥ 0; scattering rates satisfy detailed balance | PASS |
| S2 | H-theorem guarantees equilibrium; BTE well-posed | PASS |
| S3 | Ensemble MC converges with 10⁵ particles | PASS |
| S4 | Mobility matches experiment within 10% for bulk Si | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# bte_carrier/si_mobility_s1.yaml
principle_ref: sha256:<p490_hash>
omega:
  particles: 100000
  domain: bulk_silicon
  temperature: 300   # K
  fields: [0.1, 1, 10, 100]   # kV/cm
E:
  forward: "ensemble Monte Carlo BTE solver"
  band_structure: non_parabolic_3_valley
  scattering: [acoustic_deformation, optical_deformation, ionized_impurity]
B:
  doping: [1e14, 1e16, 1e18]   # cm⁻³
  temperature_range: [77, 300, 500]   # K
I:
  scenario: bulk_Si_electron_mobility
  methods: [ensemble_MC, SH_expansion, direct_BTE]
O: [low_field_mobility, velocity_field_curve, energy_distribution]
epsilon:
  mobility_error_max: 0.10
  velocity_error_max: 0.08
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10⁵ particles provide < 1% statistical noise; fields physical | PASS |
| S2 | Si band structure + 3 scattering mechanisms well-characterized | PASS |
| S3 | Ensemble MC converges within 10 ps simulation time | PASS |
| S4 | Low-field mobility within 10% of Jacoboni data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# bte_carrier/benchmark_si.yaml
spec_ref: sha256:<spec490_hash>
principle_ref: sha256:<p490_hash>
dataset:
  name: Silicon_mobility_experimental
  reference: "Jacoboni & Reggiani (1983) bulk Si transport"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Ensemble MC (parabolic)
    params: {particles: 50000, bands: parabolic}
    results: {mobility_error: 0.15, velocity_error: 0.12}
  - solver: Ensemble MC (non-parabolic)
    params: {particles: 100000, bands: non_parabolic}
    results: {mobility_error: 0.08, velocity_error: 0.06}
  - solver: SH expansion (deterministic)
    params: {harmonics: 7, k_grid: 200}
    results: {mobility_error: 0.05, velocity_error: 0.04}
quality_scoring:
  - {min_err: 0.03, Q: 1.00}
  - {min_err: 0.08, Q: 0.90}
  - {min_err: 0.12, Q: 0.80}
  - {min_err: 0.20, Q: 0.75}
```

**Baseline solver:** MC non-parabolic — mobility error 8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Mobility Error | Velocity Error | Runtime | Q |
|--------|---------------|---------------|---------|---|
| MC parabolic | 0.15 | 0.12 | 60 s | 0.75 |
| MC non-parabolic | 0.08 | 0.06 | 300 s | 0.90 |
| SH expansion | 0.05 | 0.04 | 30 s | 0.90 |
| Full-band MC | 0.03 | 0.02 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (full-band): 500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p490_hash>",
  "h_s": "sha256:<spec490_hash>",
  "h_b": "sha256:<bench490_hash>",
  "r": {"mobility_error": 0.03, "error_bound": 0.10, "ratio": 0.300},
  "c": {"velocity_error": 0.02, "dopings": 3, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep bte_carrier
pwm-node verify bte_carrier/si_mobility_s1.yaml
pwm-node mine bte_carrier/si_mobility_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
