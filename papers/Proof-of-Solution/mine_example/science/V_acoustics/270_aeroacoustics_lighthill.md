# Principle #270 — Aeroacoustics (Lighthill Analogy)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Frontier (δ=5)
**DAG:** N.lighthill → K.green.acoustic → ∫.volume |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.lighthill→K.green.acoustic→∫.volume    aeroacoust   jet_noise_predict   LES+FW-H
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  AEROACOUSTICS (LIGHTHILL ANALOGY)   P = (E,G,W,C)   Principle #270 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂²ρ'/∂t² − c₀²∇²ρ' = ∂²Tᵢⱼ/∂xᵢ∂xⱼ                 │
│        │ Lighthill stress tensor Tᵢⱼ from CFD turbulent field  │
│        │ Forward: given CFD field → compute far-field noise     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.lighthill] ──→ [K.green.acoustic] ──→ [∫.volume]    │
│        │ nonlinear  kernel  integrate                           │
│        │ V={N.lighthill, K.green.acoustic, ∫.volume}  A={N.lighthill→K.green.acoustic, K.green.acoustic→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (wave equation with known source)       │
│        │ Uniqueness: YES (given Tᵢⱼ and radiation BC)          │
│        │ Stability: source accuracy depends on CFD resolution   │
│        │ Mismatch: turbulence model errors, compactness assumed │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = SPL error |SPL−SPL_ref| in dB (primary)           │
│        │ q = depends on CFD fidelity (RANS < LES < DNS)       │
│        │ T = {OASPL_error, spectral_shape_match, directivity}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | CFD domain and acoustic observer positions well-defined | PASS |
| S2 | Lighthill analogy exact reformulation of NS equations | PASS |
| S3 | LES+FW-H validated for subsonic jet noise problems | PASS |
| S4 | SPL error bounded by comparison with experimental data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# aeroacoust/jet_noise_prediction.yaml
principle_ref: sha256:<p270_hash>
omega:
  jet: {Mach: 0.9, diameter: 0.05, Re: 1e6}
  observers: {arc_radius: 50, angles: [30, 60, 90, 120, 150]}
E:
  forward: "LES → Lighthill/FW-H acoustic analogy"
  turbulence: LES_with_Smagorinsky
I:
  scenario: jet_noise_prediction
  grid_resolutions: [coarse, medium, fine]
O: [OASPL_error_dB, spectral_shape_error]
epsilon:
  OASPL_error_max: 3.0  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | M=0.9 subsonic jet; FW-H surface encloses sources | PASS |
| S2 | Extensive experimental databases exist for round jets | PASS |
| S3 | Fine LES grid resolves Strouhal-peak frequency | PASS |
| S4 | OASPL error < 3 dB achievable with fine LES | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# aeroacoust/benchmark_jet_noise.yaml
spec_ref: sha256:<spec270_hash>
principle_ref: sha256:<p270_hash>
dataset:
  name: subsonic_jet_noise_reference
  reference: "Tanna (1977) jet noise measurements, M=0.9"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RANS+Lighthill (Tam & Auriault)
    params: {model: k-epsilon}
    results: {OASPL_error: 5.2, spectral_error: 0.15}
  - solver: LES+FW-H (coarse)
    params: {grid: 2M_cells}
    results: {OASPL_error: 3.1, spectral_error: 0.08}
  - solver: LES+FW-H (fine)
    params: {grid: 20M_cells}
    results: {OASPL_error: 1.2, spectral_error: 0.03}
quality_scoring:
  - {min_OASPL_err: 1.0, Q: 1.00}
  - {min_OASPL_err: 3.0, Q: 0.90}
  - {min_OASPL_err: 5.0, Q: 0.80}
  - {min_OASPL_err: 8.0, Q: 0.75}
```

**Baseline solver:** LES+FW-H (coarse) — OASPL error 3.1 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | OASPL Error (dB) | Spectral Error | Runtime | Q |
|--------|-------------------|----------------|---------|---|
| RANS+Lighthill | 5.2 | 0.15 | 1 hr | 0.75 |
| LES+FW-H (coarse) | 3.1 | 0.08 | 12 hr | 0.90 |
| LES+FW-H (medium) | 1.8 | 0.05 | 48 hr | 0.95 |
| LES+FW-H (fine) | 1.2 | 0.03 | 200 hr | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 1.00 = 500 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p270_hash>",
  "h_s": "sha256:<spec270_hash>",
  "h_b": "sha256:<bench270_hash>",
  "r": {"residual_norm": 1.2, "error_bound": 3.0, "ratio": 0.40},
  "c": {"fitted_rate": 1.1, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep aeroacoust
pwm-node verify aeroacoust/jet_noise_prediction.yaml
pwm-node mine aeroacoust/jet_noise_prediction.yaml
pwm-node inspect sha256:<cert_hash>
```
