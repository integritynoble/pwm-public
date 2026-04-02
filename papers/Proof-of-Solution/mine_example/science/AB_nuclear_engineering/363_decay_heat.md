# Principle #363 — Decay Heat Calculation

**Domain:** Nuclear Engineering | **Carrier:** decay energy | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction → ∂.time.implicit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit   decay-heat   PWR-shutdown      summation
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DECAY HEAT CALCULATION         P = (E,G,W,C)   Principle #363  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ P_decay(t) = Σ_i λ_i N_i(t) · E_i                    │
│        │ N_i(t) from Bateman equations (post-shutdown inventory)│
│        │ E_i = average decay energy (β + γ + α)                 │
│        │ Or: P/P₀ = Σ_k a_k [t^{−α_k} − (t+T_op)^{−α_k}]    │
│        │ Forward: given irradiation history → P_decay(t_cool)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit]                     │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction, ∂.time.implicit}  A={N.reaction→∂.time.implicit}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (post-shutdown inventory uniquely decays)│
│        │ Uniqueness: YES (deterministic decay chains)           │
│        │ Stability: YES (monotone decrease after peak)          │
│        │ Mismatch: fission yield uncertainty, decay data errors  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |P_calc − P_meas| / P_meas (relative power error) │
│        │ q = N/A (summation method; accuracy limited by data)  │
│        │ T = {power_error, total_energy_error, K_cooling_times} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Decay power dimensions [W]; inventory consistent with irradiation | PASS |
| S2 | Bateman + summation uniquely determines decay heat curve | PASS |
| S3 | Summation codes (ORIGEN, FISPACT) converge with validated data | PASS |
| S4 | Power error computable against ANS-5.1 / calorimetric data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# decay_heat/pwr_shutdown_s1_ideal.yaml
principle_ref: sha256:<p363_hash>
omega:
  cooling_times: [1, 10, 100, 1000, 1e4, 1e5, 1e6, 1e7]   # seconds
  burnup: 33.0   # GWd/tHM
  operating_time: 3.15e7   # 1 year
E:
  forward: "P(t) = Σ_i λ_i N_i(t) E_i (summation method)"
  nuclide_library: ENDF-VIII.0_decay
  fission_yields: ENDF-VIII.0_FY
B:
  initial: {fuel: UO2, enrichment: 3.5}
I:
  scenario: PWR_post_shutdown
  fissile: U235
  cooling_range: [1, 1e7]   # seconds
O: [decay_heat_fraction, total_energy_error]
epsilon:
  power_error_max: 0.05   # 5%
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Cooling times span 1 s to 115 days — covers safety-relevant range | PASS |
| S2 | 33 GWd/tHM standard PWR burnup; well-characterized | PASS |
| S3 | ORIGEN summation validated against ANS-5.1 standard | PASS |
| S4 | Power error < 5% achievable with ENDF-VIII.0 data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# decay_heat/benchmark_pwr.yaml
spec_ref: sha256:<spec363_hash>
principle_ref: sha256:<p363_hash>
dataset:
  name: ANS_5_1_2014
  reference: "ANS-5.1-2014 decay heat standard for LWRs"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ANS-5.1-fit
    params: {groups: 23}
    results: {power_err: 0.04, total_E_err: 0.03}
  - solver: ORIGEN-ARP
    params: {nuclides: 1600}
    results: {power_err: 0.02, total_E_err: 0.015}
  - solver: FISPACT-II
    params: {nuclides: 2500}
    results: {power_err: 0.015, total_E_err: 0.01}
quality_scoring:
  - {max_power_err: 0.01, Q: 1.00}
  - {max_power_err: 0.03, Q: 0.90}
  - {max_power_err: 0.05, Q: 0.80}
  - {max_power_err: 0.10, Q: 0.75}
```

**Baseline solver:** ORIGEN-ARP — power error 2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Power Error | Total E Error | Runtime | Q |
|--------|-----------|---------------|---------|---|
| ANS-5.1-fit | 0.04 | 0.03 | 0.01 s | 0.80 |
| ORIGEN-ARP | 0.02 | 0.015 | 3 s | 0.90 |
| FISPACT-II | 0.015 | 0.01 | 8 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FISPACT): 300 × 0.90 = 270 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p363_hash>",
  "h_s": "sha256:<spec363_hash>",
  "h_b": "sha256:<bench363_hash>",
  "r": {"power_err": 0.015, "total_E_err": 0.01, "ratio": 0.30},
  "c": {"cooling_times_tested": 8, "K": 3},
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep decay_heat
pwm-node verify AB_nuclear_engineering/decay_heat_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/decay_heat_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
