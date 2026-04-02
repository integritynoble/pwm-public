# Principle #332 — Classical Nucleation Theory

**Domain:** Materials Science | **Carrier:** nucleus | **Difficulty:** Textbook (δ=1)
**DAG:** N.exponential → ∫.temporal → O.l2 |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ΔG→r*→ΔG*→J CNT         water-nucleation   analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CLASSICAL NUCLEATION THEORY    P = (E,G,W,C)   Principle #332 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔG(r) = −(4π/3)r³ΔG_v + 4πr²γ                       │
│        │ r* = 2γ/ΔG_v  (critical radius)                       │
│        │ ΔG* = (16πγ³)/(3ΔG_v²)  (nucleation barrier)         │
│        │ J = J₀ exp(−ΔG*/kT)  (nucleation rate)               │
│        │ Forward: given γ, ΔG_v, T → compute r*, ΔG*, J       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [ΔG] ──→ [r*] ──→ [ΔG*] ──→ [J] ──→ [ΔG]            │
│        │ free-energy  crit-radius  barrier  rate  repeat        │
│        │ V={ΔG,r*,ΔG*,J}  A={ΔG→r*,r*→ΔG*,ΔG*→J,J→ΔG}        │
│        │ L_DAG=2.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytic closed-form expressions)      │
│        │ Uniqueness: YES (unique r*, ΔG*, J for given params)   │
│        │ Stability: exponential sensitivity of J to γ and T    │
│        │ Mismatch: capillarity approximation, curvature effects │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |log J_calc − log J_expt| (primary, decades)      │
│        │ q = exact (analytic formula)                          │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Free-energy balance dimensionally consistent | PASS |
| S2 | Analytic expressions always yield unique r*, ΔG*, J | PASS |
| S3 | Closed-form solution; no numerical convergence needed | PASS |
| S4 | Nucleation rate comparable to experimental measurements | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cnt/water_nucleation_s1_ideal.yaml
principle_ref: sha256:<p332_hash>
omega:
  T_range: [220, 260]  # K
  supersaturation_range: [2, 20]
E:
  forward: "r* = 2γ/ΔG_v, ΔG* = 16πγ³/(3ΔG_v²), J = J₀exp(−ΔG*/kT)"
  model: classical_capillarity
B:
  phase: {parent: vapor, daughter: liquid}
I:
  scenario: water_vapor_nucleation
  gamma: 0.072  # N/m
  molecular_volume: 3.0e-29  # m³
O: [critical_radius, barrier_height, nucleation_rate]
epsilon:
  log_J_error_max: 2.0  # decades
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | T and supersaturation ranges physical for water | PASS |
| S2 | CNT formulas valid; water surface tension known | PASS |
| S3 | Analytic evaluation exact | PASS |
| S4 | log J within 2 decades of experiment for CNT | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cnt/benchmark_water.yaml
spec_ref: sha256:<spec332_hash>
principle_ref: sha256:<p332_hash>
dataset:
  name: water_nucleation_experimental
  reference: "Wolk & Strey (2001) expansion chamber data"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CNT (classical)
    params: {gamma: bulk_value}
    results: {log_J_error: 3.5}
  - solver: CNT (Tolman-corrected)
    params: {gamma: Tolman_correction, delta: 0.1e-9}
    results: {log_J_error: 1.8}
  - solver: DFT-nucleation
    params: {functional: SAFT}
    results: {log_J_error: 0.8}
quality_scoring:
  - {min_log_J_error: 0.5, Q: 1.00}
  - {min_log_J_error: 1.0, Q: 0.90}
  - {min_log_J_error: 2.0, Q: 0.80}
  - {min_log_J_error: 4.0, Q: 0.75}
```

**Baseline solver:** CNT (Tolman-corrected) — log J error 1.8 decades
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | log J Error | Runtime | Q |
|--------|------------|---------|---|
| CNT (classical) | 3.5 | 0.001 s | 0.75 |
| CNT (Tolman) | 1.8 | 0.001 s | 0.80 |
| DFT-nucleation | 0.8 | 60 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (DFT): 100 × 0.90 = 90 PWM
Floor:           100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p332_hash>",
  "h_s": "sha256:<spec332_hash>",
  "h_b": "sha256:<bench332_hash>",
  "r": {"residual_norm": 0.8, "error_bound": 2.0, "ratio": 0.40},
  "c": {"fitted_rate": "exact", "theoretical_rate": "exact", "K": 3},
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
| L4 Solution | — | 75–90 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep cnt
pwm-node verify cnt/water_nucleation_s1_ideal.yaml
pwm-node mine cnt/water_nucleation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
