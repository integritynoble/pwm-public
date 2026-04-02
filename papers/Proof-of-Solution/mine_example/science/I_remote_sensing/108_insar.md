# Principle #108 — Interferometric SAR (InSAR)

**Domain:** Remote Sensing | **Carrier:** Microwave | **Difficulty:** Hard (δ=5)
**DAG:** G.pulse --> K.green --> F.dft --> N.phase | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse-->K.green-->F.dft-->N.phase    InSAR      Sentinel1-DEM       PhaseUnwrap
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  InSAR   P = (E, G, W, C)   Principle #108                     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Δφ(r) = (4π/λ)·B_⊥·h(r)/(R·sinθ) + φ_atm + n        │
│        │ Interferometric phase encodes topographic height h     │
│        │ Phase wrapping: Δφ observed modulo 2π                  │
│        │ Inverse: unwrap phase → recover DEM h(r)              │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [K.green] --> [F.dft] --> [N.phase]        │
│        │ Chirp  Propagate  RangeCompress  InSARPhase             │
│        │ V={G.pulse, K.green, F.dft, N.phase}  A={G.pulse-->K.green, K.green-->F.dft, F.dft-->N.phase}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (phase-to-height is bijective locally)  │
│        │ Uniqueness: CONDITIONAL (requires successful unwrap)   │
│        │ Stability: κ ≈ 10 (high coherence), κ ≈ 100 (low)     │
│        │ Mismatch: atmospheric delay, orbit error, decorrelation│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = height RMSE (primary), unwrap error rate (second.) │
│        │ q = 2.0 (least-squares unwrapping convergence)        │
│        │ T = {height_RMSE_m, unwrap_error_pct, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Baseline length consistent with height ambiguity | PASS |
| S2 | Phase-to-height invertible for coherence > 0.3 | PASS |
| S3 | SNAPHU / MCF unwrapping converges for stated coherence | PASS |
| S4 | Height RMSE < 5 m achievable for coherence > 0.5 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# insar/sentinel1_s1_ideal.yaml
principle_ref: sha256:<p108_hash>
omega:
  grid: [2048, 2048]
  pixel_m: 15
  wavelength_cm: 5.55
  baseline_m: 150
E:
  forward: "Δφ = (4π/λ)·B_⊥·h/(R·sinθ) + φ_atm + n"
I:
  dataset: Sentinel1_DEM
  pairs: 30
  noise: {type: circular_gaussian, coherence: 0.7}
  scenario: ideal
O: [height_RMSE_m, unwrap_error_pct]
epsilon:
  height_RMSE_max_m: 5.0
  unwrap_error_max_pct: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 150 m baseline at C-band → ~15 m ambiguity height | PASS |
| S2 | Coherence 0.7 → κ ≈ 12; well-posed | PASS |
| S3 | SNAPHU converges for coherence 0.7 | PASS |
| S4 | RMSE < 5 m feasible at stated coherence | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# insar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec108_hash>
principle_ref: sha256:<p108_hash>
dataset:
  name: Sentinel1_DEM
  pairs: 30
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SNAPHU
    results: {height_RMSE_m: 3.8, unwrap_err_pct: 1.5}
  - solver: MCF
    results: {height_RMSE_m: 4.2, unwrap_err_pct: 1.8}
  - solver: DeepInSAR
    results: {height_RMSE_m: 2.1, unwrap_err_pct: 0.5}
quality_scoring:
  - {max_RMSE: 2.0, Q: 1.00}
  - {max_RMSE: 3.5, Q: 0.90}
  - {max_RMSE: 5.0, Q: 0.80}
  - {max_RMSE: 8.0, Q: 0.75}
```

**Baseline:** SNAPHU — RMSE 3.8 m | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (m) | Unwrap Err (%) | Q |
|--------|----------|----------------|---|
| SNAPHU | 3.8 | 1.5 | 0.85 |
| MCF | 4.2 | 1.8 | 0.80 |
| DeepInSAR | 2.1 | 0.5 | 0.97 |
| InSAR-Former | 1.8 | 0.3 | 1.00 |

### Reward: `R = 100 × 5 × q` → Best: 500 PWM | Floor: 375 PWM

```json
{
  "h_p": "sha256:<p108_hash>", "Q": 0.97,
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

## Quick-Start

```bash
pwm-node benchmarks | grep insar
pwm-node mine insar/sentinel1_s1_ideal.yaml
```
