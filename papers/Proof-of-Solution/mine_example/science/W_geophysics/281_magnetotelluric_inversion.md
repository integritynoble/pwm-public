# Principle #281 — Magnetotelluric (MT) Inversion

**Domain:** Geophysics | **Carrier:** N/A (EM inverse) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → L.impedance → S.surface |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.impedance→S.surface      mt-inv      resistivity-2D    NLCG/Occam
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MAGNETOTELLURIC (MT) INVERSION   P = (E,G,W,C)   Principle #281│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Z(ω) = E(ω) / H(ω)  (impedance tensor)               │
│        │ ρ_a(ω) = |Z|²/(ωμ₀)  (apparent resistivity)           │
│        │ Forward: given σ(x) → solve Maxwell's eqns → Z(ω)     │
│        │ Inverse: given Z(ω) at stations → recover σ(x,z)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.impedance] ──→ [S.surface]             │
│        │ derivative  linear-op  sample                          │
│        │ V={∂.time, L.impedance, S.surface}  A={∂.time→L.impedance, L.impedance→S.surface}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (diffusive EM has smooth solutions)     │
│        │ Uniqueness: NO in 1-D (Weidelt ambiguity); better in 2D│
│        │ Stability: κ depends on frequency range & station density│
│        │ Mismatch: static shift, galvanic distortion, 3-D effects│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖log σ_rec − log σ_true‖₂ / ‖log σ_true‖₂        │
│        │ q = 1.0 (Occam smooth), 2.0 (NLCG sharp)             │
│        │ T = {RMS_misfit, model_roughness, static_shift_est}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Impedance tensor well-defined; apparent resistivity dimensionally correct | PASS |
| S2 | 2-D FE forward solver stable for diffusive Maxwell equations | PASS |
| S3 | NLCG converges for 2-D models with 20 stations, 20 periods | PASS |
| S4 | Log-resistivity error bounded by frequency range and station spacing | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mt_inv/resistivity_2d_s1_ideal.yaml
principle_ref: sha256:<p281_hash>
omega:
  grid: [100, 50]
  domain: cross_section_2D
  periods: 20  # log-spaced 0.01–1000 s
E:
  forward: "2-D FE solution of Maxwell diffusion equation"
  stations: 20
  noise_floor: 5%  # of |Z|
B:
  boundaries: 1D_layered_extension
  mode: TE+TM
I:
  scenario: conductive_zone_at_depth
  resistivity_range: [1, 10000]  # Ohm·m
  target_depth: [5, 20]  # km
O: [log_resistivity_L2, RMS_misfit, depth_resolution]
epsilon:
  L2_error_max: 1.0e-1
  RMS_max: 1.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 stations × 20 periods × 2 modes = 800 data points adequate | PASS |
| S2 | Period range 0.01–1000 s spans skin depths 0.5–50 km | PASS |
| S3 | NLCG converges to RMS ≈ 1.0 in <100 iterations | PASS |
| S4 | Log-resistivity error < 10% for conductive target | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mt_inv/benchmark_resistivity.yaml
spec_ref: sha256:<spec281_hash>
principle_ref: sha256:<p281_hash>
dataset:
  name: synthetic_conductive_zone
  reference: "20-station 2-D MT profile, TE+TM"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Occam-1D
    params: {per_station: true, roughness_min: true}
    results: {L2_error: 1.5e-1, RMS: 1.02}
  - solver: NLCG-2D
    params: {iterations: 100, tau: 3.0}
    results: {L2_error: 7.5e-2, RMS: 1.01}
  - solver: Data-space-Occam
    params: {iterations: 50, target_RMS: 1.0}
    results: {L2_error: 6.8e-2, RMS: 1.00}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 7.0e-2, Q: 0.90}
  - {min_L2: 1.2e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** NLCG-2D — L2 error 7.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | RMS | Runtime | Q |
|--------|----------|-----|---------|---|
| Occam-1D | 1.5e-1 | 1.02 | 10 s | 0.80 |
| NLCG-2D | 7.5e-2 | 1.01 | 120 s | 0.90 |
| DS-Occam | 6.8e-2 | 1.00 | 90 s | 0.90 |
| 3D-ModEM | 2.8e-2 | 1.00 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (3D-ModEM): 500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p281_hash>",
  "h_s": "sha256:<spec281_hash>",
  "h_b": "sha256:<bench281_hash>",
  "r": {"residual_norm": 2.8e-2, "error_bound": 1.0e-1, "ratio": 0.28},
  "c": {"fitted_rate": 1.12, "theoretical_rate": 1.0, "K": 4},
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
pwm-node benchmarks | grep mt_inv
pwm-node verify mt_inv/resistivity_2d_s1_ideal.yaml
pwm-node mine mt_inv/resistivity_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
