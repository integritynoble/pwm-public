# Principle #15 — MINFLUX Nanoscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=10)
**DAG:** G.structured --> N.pointwise --> S.minimum | **Reward:** 10× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.structured-->N.pointwise-->S.minimum  MINFLUX  MINFLUX-Origami-6  MLE-Loc
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MINFLUX NANOSCOPY   P = (E, G, W, C)   Principle #15           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ n_i = N · p_i(r_mol) + b_i                             │
│        │ p_i = I_exc(r_i - r_mol) / Σ_j I_exc(r_j - r_mol)     │
│        │ I_exc = donut/zero-minimum pattern at position r_i      │
│        │ Inverse: MLE of r_mol from photon ratios {n_i}          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.structured]──→[N.pointwise]──→[S.minimum]           │
│        │  Source(donut/zero)  Nonlinear(ratio)  Sample(min-flux)  │
│        │ V={G,N,S}  A={G-->N, N-->S}   L_DAG=8.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (zero-intensity minimum → localizable)  │
│        │ Uniqueness: YES (≥3 beam positions in 2D)              │
│        │ Stability: κ ≈ 5 (near zero) but N ~ 50 photons       │
│        │ Mismatch: beam positioning error, background photons   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE_xy (nm), CRB efficiency                       │
│        │ q = 2.0 (MLE achieves CRB for sufficient N)          │
│        │ T = {RMSE_loc, CRB_ratio, N_photons}                   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Donut zero-minimum pattern consistent with beam steering positions | PASS |
| S2 | CRB ∝ L/√N at molecular position near zero → sub-nm precision | PASS |
| S3 | MLE converges for N ≥ 50 photons per iteration cycle | PASS |
| S4 | RMSE ≤ 2 nm achievable with iterative refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# minflux/origami_s1_ideal.yaml
principle_ref: sha256:<p015_hash>
omega:
  beam_positions: 4
  pattern: donut_2D
  L_initial_nm: 400
  L_final_nm: 20
  iterations: 4
  photons_per_cycle: 50
  wavelength_nm: 642
E:
  forward: "n_i = N · p_i(r_mol) + b"
I:
  dataset: MINFLUX_Origami_6
  traces: 6
  noise: {type: poisson, bg_per_beam: 0.5}
  scenario: ideal
O: [RMSE_xy_nm, CRB_efficiency]
epsilon:
  RMSE_max_nm: 2.0
  CRB_eff_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4 beam positions, 4 refinement iterations: consistent with protocol | PASS |
| S2 | L_final=20 nm, N=50: CRB ≈ 1.2 nm | PASS |
| S3 | MLE converges per cycle with 50 photons | PASS |
| S4 | RMSE ≤ 2 nm feasible with bg < 1 photon/beam | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# minflux/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec015_hash>
dataset:
  name: MINFLUX_Origami_6
  traces: 6
  photons_per_trace: 200
baselines:
  - solver: MLE-MINFLUX
    params: {method: iterative_MLE, cycles: 4}
    results: {RMSE_xy: 1.8, CRB_eff: 0.78}
  - solver: Bayesian-MINFLUX
    params: {prior: uniform, MCMC: true}
    results: {RMSE_xy: 1.5, CRB_eff: 0.84}
  - solver: DeepMINFLUX
    params: {arch: MLP, pretrained: true}
    results: {RMSE_xy: 1.1, CRB_eff: 0.92}
quality_scoring:
  metric: RMSE_xy_nm
  thresholds:
    - {max: 1.0, Q: 1.00}
    - {max: 1.5, Q: 0.90}
    - {max: 2.0, Q: 0.80}
    - {max: 3.0, Q: 0.75}
```

**Baseline:** MLE-MINFLUX — RMSE 1.8 nm | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (nm) | CRB Eff. | Runtime | Q |
|--------|-----------|----------|---------|---|
| MLE-MINFLUX | 1.8 | 0.78 | 0.5 s | 0.80 |
| Bayesian-MINFLUX | 1.5 | 0.84 | 5 s | 0.90 |
| DeepMINFLUX | 1.1 | 0.92 | 0.1 s | 0.98 |
| Weighted-Centroid | 2.0 | 0.72 | 0.01 s | 0.80 |

### Reward Calculation

```
R = 100 × 1.0 × 10 × 1.0 × Q = 1000 × Q
Best (DeepMINFLUX):  1000 × 0.98 = 980 PWM
Floor:               1000 × 0.75 = 750 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p015_hash>",
  "h_s": "sha256:<spec015_hash>",
  "h_b": "sha256:<bench015_hash>",
  "r": {"residual_norm": 1.1, "error_bound": 2.0, "ratio": 0.55},
  "c": {"fitted_rate": 1.88, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 750–980 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep minflux
pwm-node verify minflux/origami_s1_ideal.yaml
pwm-node mine minflux/origami_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
