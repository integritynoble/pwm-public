# Principle #280 — Magnetic Field Inversion

**Domain:** Geophysics | **Carrier:** N/A (potential field inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.volume → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.volume→O.tikhonov      mag-inv     suscept-2D        Tikhonov
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MAGNETIC FIELD INVERSION         P = (E,G,W,C)   Principle #280│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔT(x) = −∇ · ∫ χ(x') H₀ G(x,x') dV'  (TMI anomaly) │
│        │ χ = magnetic susceptibility; H₀ = inducing field       │
│        │ Forward: given χ(x) → compute ΔT at surface            │
│        │ Inverse: given ΔT(x_obs) → recover χ(x) at depth      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.volume] ──→ [O.tikhonov]              │
│        │ kernel  integrate  optimize                            │
│        │ V={K.green, ∫.volume, O.tikhonov}  A={K.green→∫.volume, ∫.volume→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (magnetic potential well-defined)       │
│        │ Uniqueness: NO (annihilator exists; RTP helps)         │
│        │ Stability: ill-posed; depth weighting essential        │
│        │ Mismatch: remanent magnetisation, self-demagnetisation │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖χ_rec − χ_true‖₂ / ‖χ_true‖₂ (relative L2)      │
│        │ q = 1.0 (smooth), 2.0 (compact inversion)            │
│        │ T = {data_misfit, model_norm, RTP_quality}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TMI anomaly formulation consistent; kernel dimensions correct | PASS |
| S2 | Tikhonov + depth weighting mitigates non-uniqueness | PASS |
| S3 | CG-based inversion converges for well-sampled grids | PASS |
| S4 | Relative L2 error bounded by inclination, noise, regularisation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mag_inv/suscept_2d_s1_ideal.yaml
principle_ref: sha256:<p280_hash>
omega:
  grid: [50, 20]
  domain: cross_section_2D
  depth_range: [0, 1500]  # metres
E:
  forward: "ΔT from susceptibility via kernel integration"
  stations: 50
  noise_std: 2.0  # nT
  inclination: 60  # degrees
  declination: 0
B:
  depth_weighting: z^1.5
  RTP: applied
I:
  scenario: buried_intrusion
  true_susceptibility: 0.05  # SI
  depth: [100, 500]
O: [L2_suscept_error, data_misfit, depth_recovery]
epsilon:
  L2_error_max: 1.0e-1
  chi2_max: 1.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 stations adequate; RTP reduces dipolar asymmetry | PASS |
| S2 | Depth weighting constrains solution below surface | PASS |
| S3 | CG converges in <50 iterations for 50×20 cells | PASS |
| S4 | L2 error < 10% achievable for χ=0.05 SI contrast | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mag_inv/benchmark_suscept.yaml
spec_ref: sha256:<spec280_hash>
principle_ref: sha256:<p280_hash>
dataset:
  name: synthetic_buried_intrusion
  reference: "50-station 2-D magnetic profile"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Tikhonov-CG
    params: {lambda: 1e-2, depth_weight: z1.5}
    results: {L2_error: 9.2e-2, chi2: 1.06}
  - solver: Compact-L1
    params: {p_norm: 1, lambda: 1e-3}
    results: {L2_error: 6.8e-2, chi2: 1.04}
  - solver: MVI (magnetisation vector)
    params: {lambda: 1e-3, components: 3}
    results: {L2_error: 5.1e-2, chi2: 1.02}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 6.0e-2, Q: 0.90}
  - {min_L2: 1.0e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** Tikhonov-CG — L2 error 9.2×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | χ² | Runtime | Q |
|--------|----------|----|---------|---|
| Tikhonov-CG | 9.2e-2 | 1.06 | 2 s | 0.80 |
| Compact-L1 | 6.8e-2 | 1.04 | 5 s | 0.90 |
| MVI | 5.1e-2 | 1.02 | 10 s | 0.90 |
| Joint grav+mag | 2.5e-2 | 1.01 | 60 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (joint): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p280_hash>",
  "h_s": "sha256:<spec280_hash>",
  "h_b": "sha256:<bench280_hash>",
  "r": {"residual_norm": 2.5e-2, "error_bound": 1.0e-1, "ratio": 0.25},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep mag_inv
pwm-node verify mag_inv/suscept_2d_s1_ideal.yaml
pwm-node mine mag_inv/suscept_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
