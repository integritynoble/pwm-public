# Principle #138 — Coherent Anti-Stokes Raman (CARS) Microscopy

**Domain:** Spectroscopy | **Carrier:** Photon (nonlinear) | **Difficulty:** Research (δ=5)
**DAG:** G.pulse.laser --> K.scatter.inelastic --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.inelastic-->N.pointwise.abs2    CARS        CARSTissue-12      MEM/KK
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COHERENT ANTI-STOKES RAMAN (CARS)   P = (E, G, W, C)   #138   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_CARS ∝ |χ⁽³⁾_R(Ω) + χ⁽³⁾_NR|² · I_p² · I_S        │
│        │ χ⁽³⁾_R = resonant susceptibility at Ω = ω_p - ω_S    │
│        │ Non-resonant background (NRB) distorts lineshape       │
│        │ Inverse: extract Im[χ⁽³⁾_R] (Raman-like) from CARS   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.inelastic] --> [N.pointwise.abs2]│
│        │  PumpStokes  CARSScatter  CoherentDetect              │
│        │ V={G.pulse.laser, K.scatter.inelastic, N.pointwise.abs2}  A={G.pulse.laser-->K.scatter.inelastic, K.scatter.inelastic-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (phase-matched CARS signal present)     │
│        │ Uniqueness: YES after NRB removal (KK / MEM)           │
│        │ Stability: κ ≈ 10 (strong resonance), κ ≈ 50 (weak)   │
│        │ Mismatch: NRB fluctuation, phase-matching deviation    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Raman retrieval RMSE (primary), SNR (secondary)    │
│        │ q = 2.0 (KK transform exact; MEM iterative O(1/k))   │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pump/Stokes wavelengths, bandwidth, and phase-matching geometry consistent | PASS |
| S2 | KK or MEM retrieval removes NRB; Im[χ⁽³⁾] uniquely recovered | PASS |
| S3 | MEM converges within 50 iterations for typical NRB/resonance ratio | PASS |
| S4 | Raman retrieval RMSE ≤ 8% achievable for lipid-rich tissue | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cars/carstissue_s1.yaml
principle_ref: sha256:<p138_hash>
omega:
  grid: [256, 256]
  pixel_um: 0.3
  pump_nm: 816
  stokes_nm: 1064
  spectral_range_cm: [2700, 3100]
  spectral_points: 64
E:
  forward: "I_CARS = |chi3_R + chi3_NR|^2 * Ip^2 * Is"
  retrieval: "maximum_entropy_method"
I:
  dataset: CARSTissue_12
  images: 12
  noise: {type: shot, peak: 5000}
  scenario: ideal
O: [raman_retrieval_RMSE_pct, SNR]
epsilon:
  raman_RMSE_max: 10.0
  SNR_min: 15.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 816/1064 nm pump/Stokes target CH-stretch 2700–3100 cm⁻¹ | PASS |
| S2 | κ ≈ 10 with MEM for NRB/resonance ratio < 5 | PASS |
| S3 | MEM converges within 30 iterations at 5000 peak counts | PASS |
| S4 | Raman RMSE ≤ 10% and SNR ≥ 15 feasible for lipid imaging | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cars/benchmark_s1.yaml
spec_ref: sha256:<spec138_hash>
principle_ref: sha256:<p138_hash>
dataset:
  name: CARSTissue_12
  images: 12
  size: [256, 256]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Raw-CARS
    params: {normalization: none}
    results: {raman_RMSE_pct: 35.0, SNR: 20}
  - solver: KK-Retrieval
    params: {phase_correction: true}
    results: {raman_RMSE_pct: 8.5, SNR: 18}
  - solver: MEM-CARS
    params: {n_iter: 50}
    results: {raman_RMSE_pct: 5.2, SNR: 22}
quality_scoring:
  - {max_RMSE: 5.0, Q: 1.00}
  - {max_RMSE: 8.0, Q: 0.90}
  - {max_RMSE: 10.0, Q: 0.80}
  - {max_RMSE: 15.0, Q: 0.75}
```

**Baseline solver:** KK-Retrieval — Raman RMSE 8.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Raman RMSE (%) | SNR | Runtime | Q |
|--------|----------------|-----|---------|---|
| Raw-CARS | 35.0 | 20 | 0 s | 0.75 |
| KK-Retrieval | 8.5 | 18 | 0.5 s | 0.88 |
| MEM-CARS | 5.2 | 22 | 5 s | 0.95 |
| DL-CARS (NRBNet) | 4.5 | 25 | 0.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DL-CARS):   500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p138_hash>",
  "h_s": "sha256:<spec138_hash>",
  "h_b": "sha256:<bench138_hash>",
  "r": {"residual_norm": 0.045, "error_bound": 0.10, "ratio": 0.45},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep cars
pwm-node verify cars/carstissue_s1.yaml
pwm-node mine cars/carstissue_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
