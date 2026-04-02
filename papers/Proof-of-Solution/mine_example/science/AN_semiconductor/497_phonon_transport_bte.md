# Principle #497 — Phonon Transport (BTE for Heat)

**Domain:** Semiconductor Physics | **Carrier:** N/A (kinetic) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [K.scatter] --> [∫.angular] --> [B.interface] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->K.scat-->∫.ang-->B.iface  PhononBTE  Si-thermal  MC/DOM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHONON TRANSPORT (BTE FOR HEAT) P=(E,G,W,C) Principle #497    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂f/∂t + v_g·∇f = (f₀−f)/τ(ω,T) + Q̇/(ℏω D(ω))      │
│        │ f(r,ω,ŝ,t) = phonon distribution function             │
│        │ q = Σ_p ∫ ℏω v_g(ω) [f−f₀] D(ω) dω  (heat flux)     │
│        │ Fourier limit: q = −κ∇T when L >> Λ_mfp               │
│        │ Forward: given (geometry, T_boundary) → T(r), q(r)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [K.scat] ──→ [∫.ang] ──→ [B.iface]           │
│        │  time-step  scattering  angle-integ  boundary          │
│        │ V={∂.t,K.scat,∫.ang,B.iface}  A={∂.t→K.scat,K.scat→∫.ang,∫.ang→B.iface}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (BTE well-posed with RTA)               │
│        │ Uniqueness: YES (H-theorem for phonons)                │
│        │ Stability: MC convergence 1/√N; DOM stable with upwind│
│        │ Mismatch: RTA vs full scattering, anharmonic effects   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |κ_eff − κ_ref|/κ_ref  (thermal conductivity err) │
│        │ q = N/A (MC) or 2.0 (DOM with spatial refinement)    │
│        │ T = {kappa_error, temperature_profile, ballistic_limit}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Distribution f ≥ 0; energy conservation with source term | PASS |
| S2 | RTA well-posed; dispersion from first principles available | PASS |
| S3 | MC and DOM converge for thin-film and bulk limits | PASS |
| S4 | κ_eff matches experiment for Si thin films within 15% | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# phonon_bte/si_thin_film_s1.yaml
principle_ref: sha256:<p497_hash>
omega:
  grid: 200
  domain: 1D_Si_thin_film
  thickness_range: [10e-9, 10e-6]   # m
E:
  forward: "phonon BTE with relaxation time approximation"
  dispersion: Si_first_principles
  branches: [LA, TA1, TA2, LO, TO1, TO2]
  scattering: [Umklapp, isotope, boundary]
B:
  hot_side: 310   # K
  cold_side: 290
  boundaries: diffuse_Casimir
I:
  scenario: Si_cross_plane_thermal_conductivity
  thicknesses: [10nm, 100nm, 1um, 10um]
O: [kappa_effective, temperature_profile, ballistic_fraction]
epsilon:
  kappa_error_max: 0.15
  temperature_profile_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 spatial points; full Si phonon dispersion; 6 branches | PASS |
| S2 | Thin film 10 nm → 10 μm spans ballistic to diffusive | PASS |
| S3 | MC and DOM converge for all thicknesses | PASS |
| S4 | κ_eff within 15% of measured values for Si thin films | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# phonon_bte/benchmark_si_film.yaml
spec_ref: sha256:<spec497_hash>
principle_ref: sha256:<p497_hash>
dataset:
  name: Si_thin_film_thermal_conductivity
  reference: "Ju & Goodson (1999); Esfarjani et al. (2011)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gray BTE (single MFP)
    params: {model: gray, tau: single_effective}
    results: {kappa_error: 0.30, profile_error: 0.15}
  - solver: Frequency-dependent BTE (DOM)
    params: {frequencies: 100, angles: 32, grid: 200}
    results: {kappa_error: 0.10, profile_error: 0.04}
  - solver: MC phonon transport
    params: {particles: 1M, frequencies: full_BZ}
    results: {kappa_error: 0.08, profile_error: 0.03}
quality_scoring:
  - {min_err: 0.05, Q: 1.00}
  - {min_err: 0.10, Q: 0.90}
  - {min_err: 0.15, Q: 0.80}
  - {min_err: 0.30, Q: 0.75}
```

**Baseline solver:** Frequency-dependent DOM — κ error 10%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | κ Error | Profile Error | Runtime | Q |
|--------|---------|-------------|---------|---|
| Gray BTE | 0.30 | 0.15 | 1 s | 0.75 |
| Freq-dep DOM | 0.10 | 0.04 | 60 s | 0.90 |
| MC (1M) | 0.08 | 0.03 | 300 s | 0.90 |
| Ab initio + MC | 0.04 | 0.015 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (ab initio): 400 × 1.00 = 400 PWM
Floor:                 400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p497_hash>",
  "h_s": "sha256:<spec497_hash>",
  "h_b": "sha256:<bench497_hash>",
  "r": {"kappa_error": 0.04, "error_bound": 0.15, "ratio": 0.267},
  "c": {"profile_error": 0.015, "thicknesses": 4, "K": 4},
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
pwm-node benchmarks | grep phonon_bte
pwm-node verify phonon_bte/si_thin_film_s1.yaml
pwm-node mine phonon_bte/si_thin_film_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
