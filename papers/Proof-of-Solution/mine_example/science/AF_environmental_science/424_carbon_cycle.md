# Principle #424 — Carbon Cycle Modeling

**Domain:** Environmental Science | **Carrier:** carbon flux/stock | **Difficulty:** Advanced (δ=5)
**DAG:** N.reaction → ∂.time → ∫.volume |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time→∫.volume   carbon-cycle  global-C-budget   box-model
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CARBON CYCLE MODELING          P = (E,G,W,C)   Principle #424 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dC_a/dt = E_ff + E_luc − F_ocean − F_land             │
│        │ dC_o/dt = F_ocean − burial   (ocean carbon)            │
│        │ dC_l/dt = NPP − R_h − E_luc  (land carbon)            │
│        │ F_ocean = k_w (pCO2_atm − pCO2_ocean)  (air-sea flux) │
│        │ Forward: given emissions E(t) → C_a(t), pCO₂(t)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time] ──→ [∫.volume]               │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.reaction, ∂.time, ∫.volume}  A={N.reaction→∂.time, ∂.time→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled ODE system with bounded fluxes)│
│        │ Uniqueness: YES (for given emission scenario)          │
│        │ Stability: CO₂ buffering provides negative feedback    │
│        │ Mismatch: ocean CO₂ chemistry (Revelle factor), NPP   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |pCO₂ − pCO₂_obs| / pCO₂_obs (ppm error)        │
│        │ q = method-dependent (box model ODE)                  │
│        │ T = {pCO2_error, ocean_flux_error, land_flux_error}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Carbon stocks (PgC) and fluxes (PgC/yr) dimensionally consistent | PASS |
| S2 | Global carbon budget closes; ODE system well-posed | PASS |
| S3 | ODE solver converges; box model computationally inexpensive | PASS |
| S4 | pCO₂ error computable against Mauna Loa / ice core data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# carbon_cycle/global_budget_s1_ideal.yaml
principle_ref: sha256:<p424_hash>
omega:
  time: [1750, 2100]   # years
  dt: 1.0   # year
  boxes: [atmosphere, ocean_mixed, ocean_deep, land_veg, land_soil]
E:
  forward: "dC/dt = emissions − ocean_uptake − land_uptake (box model)"
  ocean_chemistry: Revelle_buffered
  land_model: Q10_respiration
B:
  initial: {C_atm: 589}   # PgC (pre-industrial)
I:
  scenario: historical_plus_RCP45
  emission_pathway: CDIAC_historical_1750_2020 + SSP2_4.5
O: [pCO2_error, airborne_fraction_error, ocean_uptake_error]
epsilon:
  pCO2_error_max: 5.0   # ppm
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 5 boxes cover major carbon reservoirs; 1-year dt adequate | PASS |
| S2 | Historical + SSP2-4.5 emissions well-documented | PASS |
| S3 | Annual timestep ODE solver converges trivially | PASS |
| S4 | pCO₂ error < 5 ppm vs Mauna Loa achievable with tuned model | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# carbon_cycle/benchmark_global.yaml
spec_ref: sha256:<spec424_hash>
principle_ref: sha256:<p424_hash>
dataset:
  name: GCP_global_carbon_budget
  reference: "Global Carbon Project (Friedlingstein et al. 2023)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Bern-SAR
    params: {boxes: 4, pulse_response: true}
    results: {pCO2_err: 8.0, AF_err: 0.05}
  - solver: HILDA
    params: {boxes: 7, ocean_diffusion: true}
    results: {pCO2_err: 4.0, AF_err: 0.03}
  - solver: FAIR-v2
    params: {boxes: 4, temperature_feedback: true}
    results: {pCO2_err: 3.0, AF_err: 0.02}
quality_scoring:
  - {max_pCO2_err: 2.0, Q: 1.00}
  - {max_pCO2_err: 5.0, Q: 0.90}
  - {max_pCO2_err: 10.0, Q: 0.80}
  - {max_pCO2_err: 20.0, Q: 0.75}
```

**Baseline solver:** FAIR-v2 — pCO₂ error 3.0 ppm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | pCO₂ Error (ppm) | AF Error | Runtime | Q |
|--------|-----------------|---------|---------|---|
| Bern-SAR | 8.0 | 0.05 | 0.01 s | 0.80 |
| HILDA | 4.0 | 0.03 | 0.05 s | 0.90 |
| FAIR-v2 | 3.0 | 0.02 | 0.1 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p424_hash>",
  "h_s": "sha256:<spec424_hash>",
  "h_b": "sha256:<bench424_hash>",
  "r": {"pCO2_err": 3.0, "AF_err": 0.02, "ratio": 0.60},
  "c": {"years_simulated": 350, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep carbon_cycle
pwm-node verify AF_environmental_science/carbon_cycle_s1_ideal.yaml
pwm-node mine AF_environmental_science/carbon_cycle_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
