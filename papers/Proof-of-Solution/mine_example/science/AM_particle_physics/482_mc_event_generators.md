# Principle #482 — Monte Carlo Event Generators (Pythia/Herwig)

**Domain:** Particle Physics | **Carrier:** N/A (stochastic) | **Difficulty:** Advanced (δ=4)
**DAG:** [S.random] --> [N.splitting] --> [N.string] --> [∫.ensemble] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.rand-->N.split-->N.string-->∫.ens  MC-Event  LEP/LHC-data  Pythia/Herwig
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MC EVENT GENERATORS (PYTHIA/HERWIG) P=(E,G,W,C) Princ. #482   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dσ = Σ_ij f_i f_j dσ̂_ij × PS × Shower × Hadronize   │
│        │ Shower: dP/dt = (α_s/2π) P(z) dz dt  (Sudakov)       │
│        │ Hadronization: string (Lund) or cluster model          │
│        │ MPI: multiple parton interactions at low p_T            │
│        │ Forward: given (√s, process) → final-state particles   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.rand] ──→ [N.split] ──→ [N.string] ──→ [∫.ens]      │
│        │  MC-sample  parton-shower  hadronize  average          │
│        │ V={S.rand,N.split,N.string,∫.ens}  A={S.rand→N.split,N.split→N.string,N.string→∫.ens}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (well-defined MC algorithm)             │
│        │ Uniqueness: statistical (converges with N_events)      │
│        │ Stability: Sudakov form factor ensures unitarity        │
│        │ Mismatch: tuning parameters, missing higher orders     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = χ²/N_bins (data/MC agreement per distribution)     │
│        │ q = N/A (MC statistical: 1/√N convergence)           │
│        │ T = {chi2_distributions, multiplicity, p_T_spectrum}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Cross section positive; 4-momentum conservation per event | PASS |
| S2 | Sudakov unitarity ensures shower terminates; IR safe | PASS |
| S3 | Generator produces statistically convergent distributions | PASS |
| S4 | Tuned MC agrees with LEP/LHC data within systematics | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mc_event/ee_hadrons_s1.yaml
principle_ref: sha256:<p482_hash>
omega:
  events: 1000000
  domain: e+e-_annihilation
  sqrt_s: 91.2     # GeV (Z pole)
E:
  forward: "hard process + parton shower + hadronization"
  generators: [Pythia8, Herwig7, Sherpa]
  tune: Monash_2013
B:
  process: "e+e- → Z → hadrons"
  observables: [thrust, multiplicity, jet_rates]
I:
  scenario: LEP_ee_hadronic
  event_counts: [10000, 100000, 1000000]
O: [thrust_chi2, multiplicity_chi2, jet_rate_error]
epsilon:
  chi2_per_bin_max: 2.0
  multiplicity_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10⁶ events at Z pole; IR-safe observables selected | PASS |
| S2 | Z → hadrons well-understood; QED corrections small | PASS |
| S3 | All three generators produce convergent distributions | PASS |
| S4 | χ²/bin < 2 for tuned generators vs LEP data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mc_event/benchmark_lep.yaml
spec_ref: sha256:<spec482_hash>
principle_ref: sha256:<p482_hash>
dataset:
  name: LEP_event_shapes
  reference: "ALEPH/DELPHI/OPAL combined (2004)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Pythia8 (default tune)
    params: {events: 1M, tune: Monash2013}
    results: {thrust_chi2: 1.5, mult_error: 0.04}
  - solver: Herwig7 (default)
    params: {events: 1M, tune: default}
    results: {thrust_chi2: 1.8, mult_error: 0.06}
  - solver: Sherpa (MEPS@NLO)
    params: {events: 1M, merging: CKKW}
    results: {thrust_chi2: 1.2, mult_error: 0.03}
quality_scoring:
  - {min_chi2: 0.8, Q: 1.00}
  - {min_chi2: 1.2, Q: 0.90}
  - {min_chi2: 1.8, Q: 0.80}
  - {min_chi2: 2.5, Q: 0.75}
```

**Baseline solver:** Pythia8 (Monash) — thrust χ²/bin 1.5
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Thrust χ² | Mult Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| Herwig7 (default) | 1.8 | 0.06 | 300 s | 0.80 |
| Pythia8 (Monash) | 1.5 | 0.04 | 200 s | 0.80 |
| Sherpa (CKKW) | 1.2 | 0.03 | 600 s | 0.90 |
| Pythia8 (re-tuned) | 0.9 | 0.02 | 250 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (re-tuned): 400 × 1.00 = 400 PWM
Floor:                400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p482_hash>",
  "h_s": "sha256:<spec482_hash>",
  "h_b": "sha256:<bench482_hash>",
  "r": {"thrust_chi2": 0.9, "error_bound": 2.0, "ratio": 0.450},
  "c": {"events": 1000000, "observables": 15, "K": 3},
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
pwm-node benchmarks | grep mc_event
pwm-node verify mc_event/ee_hadrons_s1.yaml
pwm-node mine mc_event/ee_hadrons_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
