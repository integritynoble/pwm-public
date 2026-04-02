# Principle #486 — Dark Matter Direct Detection

**Domain:** Particle Physics | **Carrier:** N/A (statistical) | **Difficulty:** Advanced (δ=4)
**DAG:** [N.pointwise] --> [∫.volume] --> [O.bayesian] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->∫.vol-->O.bayes  DM-Direct  Xe-experiment  likelihood
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DARK MATTER DIRECT DETECTION  P = (E,G,W,C)  Principle #486   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dR/dE_R = (ρ_χ σ₀)/(2 m_χ μ²) F²(E_R) ∫ f(v)/v dv  │
│        │ ρ_χ = 0.3 GeV/cm³  (local DM density)                 │
│        │ F(E_R) = nuclear form factor (Helm)                    │
│        │ f(v) = Maxwell-Boltzmann in galactic frame             │
│        │ Forward: given (m_χ, σ₀, v_esc) → recoil spectrum     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [∫.vol] ──→ [O.bayes]                       │
│        │  cross-section  halo-integ  posterior                  │
│        │ V={N.pw,∫.vol,O.bayes}  A={N.pw→∫.vol,∫.vol→O.bayes}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (rate integral well-defined for v<v_esc)│
│        │ Uniqueness: YES for given (m_χ, σ₀, halo model)       │
│        │ Stability: sensitive to halo model and v_esc           │
│        │ Mismatch: halo uncertainties, nuclear form factor      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = upper limit on σ₀ or discovery significance        │
│        │ q = N/A (Poisson statistics)                          │
│        │ T = {exclusion_limit, background_model, exposure}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Rate dR/dE > 0; recoil energy in physical range; units consistent | PASS |
| S2 | Velocity integral well-defined for v_esc = 544 km/s | PASS |
| S3 | Profile likelihood / CLs method converges | PASS |
| S4 | Exclusion limits reproducible across experiments | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dm_direct/xenon_s1.yaml
principle_ref: sha256:<p486_hash>
omega:
  exposure: 1.0        # tonne-year
  domain: liquid_xenon_TPC
  energy_range: [1, 100]   # keV_NR
E:
  forward: "WIMP-nucleus scattering rate + detector response"
  target: Xe_131
  form_factor: Helm
  halo: standard_halo_model
B:
  backgrounds: [ER_from_Rn, neutrons, neutrino_floor]
  discrimination: S1_S2_ratio
I:
  scenario: spin_independent_WIMP_search
  masses_GeV: [6, 10, 30, 100, 300, 1000]
O: [exclusion_90CL, sensitivity_median, background_rate]
epsilon:
  limit_precision: 0.20    # factor on σ₀
  background_control: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1 tonne-year exposure; 1-100 keV NR range covers WIMP signal | PASS |
| S2 | Standard halo model well-defined; Helm form factor standard | PASS |
| S3 | Profile likelihood with background model converges | PASS |
| S4 | 90% CL exclusion reproduces published LZ/XENONnT limits | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dm_direct/benchmark_xenon.yaml
spec_ref: sha256:<spec486_hash>
principle_ref: sha256:<p486_hash>
dataset:
  name: XENONnT_SR1
  reference: "XENON Collaboration (2023) first science results"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Optimum interval (Yellin)
    params: {method: Yellin, exposure: 1 ty}
    results: {limit_ratio: 1.5, computation: simple}
  - solver: Profile likelihood (background model)
    params: {method: PLR, backgrounds: full}
    results: {limit_ratio: 1.0, computation: moderate}
  - solver: Full Bayesian (posterior)
    params: {method: MCMC, priors: astrophysical}
    results: {limit_ratio: 0.9, computation: expensive}
quality_scoring:
  - {min_ratio: 0.8, Q: 1.00}
  - {min_ratio: 1.0, Q: 0.90}
  - {min_ratio: 1.3, Q: 0.80}
  - {min_ratio: 2.0, Q: 0.75}
```

**Baseline solver:** Profile likelihood — limit ratio 1.0
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Limit Ratio | Background | Runtime | Q |
|--------|------------|-----------|---------|---|
| Yellin interval | 1.5 | none | 1 s | 0.75 |
| Profile likelihood | 1.0 | full | 60 s | 0.90 |
| Bayesian (MCMC) | 0.9 | full | 3600 s | 1.00 |
| ML-accelerated PLR | 1.0 | full | 10 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (Bayesian): 400 × 1.00 = 400 PWM
Floor:                400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p486_hash>",
  "h_s": "sha256:<spec486_hash>",
  "h_b": "sha256:<bench486_hash>",
  "r": {"limit_ratio": 0.9, "error_bound": 1.3, "ratio": 0.692},
  "c": {"exposure_ty": 1.0, "masses_tested": 6, "K": 3},
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
pwm-node benchmarks | grep dm_direct
pwm-node verify dm_direct/xenon_s1.yaml
pwm-node mine dm_direct/xenon_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
