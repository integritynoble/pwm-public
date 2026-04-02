# Principle #74 — Talbot-Lau X-ray Grating Interferometry

**Domain:** Coherent Imaging | **Carrier:** X-ray Photon | **Difficulty:** Research (δ=5)
**DAG:** G.structured.stripe --> K.green --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.structured.stripe-->K.green-->N.pointwise.abs2    TLGI        GratPhantom-12     PhaseStep
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TALBOT-LAU X-RAY GRATING INTERFEROMETRY   P = (E,G,W,C)  #74  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(x,x_g) = a₀ + a₁ cos(2πx/p₂ + φ(x))               │
│        │ Three contrasts: absorption a₀, differential phase φ,  │
│        │   dark-field visibility V = a₁/a₀                      │
│        │ Inverse: extract φ, a₀, V from phase-stepping series   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.structured.stripe] --> [K.green] --> [N.pointwise.abs2]│
│        │  Grating  Propagate  ModSq                             │
│        │ V={G.structured.stripe, K.green, N.pointwise.abs2}  A={G.structured.stripe-->K.green, K.green-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Talbot self-imaging at fractional dist)│
│        │ Uniqueness: YES (≥ 3 phase steps resolve a₀, a₁, φ)   │
│        │ Stability: κ ≈ 8 (≥ 8 steps), κ ≈ 40 (3 steps)       │
│        │ Mismatch: grating defects, beam hardening, vibration   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = phase sensitivity σ_φ (primary), CNR (secondary)   │
│        │ q = 2.0 (linear Fourier extraction, exact)             │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Grating periods, Talbot distance, and detector pixel pitch are self-consistent | PASS |
| S2 | ≥ 5 phase steps yield over-determined Fourier extraction; bounded κ | PASS |
| S3 | Fourier analysis of phase-stepping curve converges in one pass | PASS |
| S4 | Phase sensitivity σ_φ ≤ 50 µrad achievable for clinical-dose X-rays | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# talbot_lau/gratphantom_s1.yaml
principle_ref: sha256:<p074_hash>
omega:
  grid: [512, 512]
  pixel_um: 50
  energy_keV: 28
  p0_um: 24
  p1_um: 4.37
  p2_um: 2.4
  talbot_order: 1
  phase_steps: 8
E:
  forward: "I(x,x_g) = a0 + a1*cos(2*pi*x/p2 + phi(x))"
  extraction: "Fourier_phase_stepping"
I:
  dataset: GratPhantom_12
  projections: 12
  noise: {type: poisson, mean_counts: 5000}
  scenario: ideal
O: [phase_sensitivity_urad, CNR]
epsilon:
  phase_sensitivity_max: 60
  CNR_min: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | p0/p1/p2 and Talbot order 1 at 28 keV satisfy design equations | PASS |
| S2 | 8 phase steps give 4× over-determination for 3-parameter fit | PASS |
| S3 | Fourier extraction converges exactly for sinusoidal stepping curve | PASS |
| S4 | σ_φ ≤ 60 µrad at 5000 mean counts per pixel | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# talbot_lau/benchmark_s1.yaml
spec_ref: sha256:<spec074_hash>
principle_ref: sha256:<p074_hash>
dataset:
  name: GratPhantom_12
  projections: 12
  phase_steps: 8
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Fourier-1st
    params: {harmonics: 1}
    results: {phase_sensitivity_urad: 55, CNR: 5.5}
  - solver: LSQ-Fit
    params: {model: sinusoidal}
    results: {phase_sensitivity_urad: 48, CNR: 6.2}
  - solver: PCA-Extraction
    params: {components: 3}
    results: {phase_sensitivity_urad: 42, CNR: 7.0}
quality_scoring:
  - {max_sens: 40, Q: 1.00}
  - {max_sens: 48, Q: 0.90}
  - {max_sens: 60, Q: 0.80}
  - {max_sens: 80, Q: 0.75}
```

**Baseline solver:** LSQ-Fit — σ_φ 48 µrad
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | σ_φ (µrad) | CNR | Runtime | Q |
|--------|------------|-----|---------|---|
| Fourier-1st | 55 | 5.5 | 0.1 s | 0.80 |
| LSQ-Fit | 48 | 6.2 | 0.5 s | 0.90 |
| PCA-Extraction | 42 | 7.0 | 0.3 s | 0.98 |
| DL-Grating (CNN) | 38 | 7.8 | 0.05 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DL-Grating):  500 × 1.00 = 500 PWM
Floor:                   500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p074_hash>",
  "h_s": "sha256:<spec074_hash>",
  "h_b": "sha256:<bench074_hash>",
  "r": {"residual_norm": 0.005, "error_bound": 0.01, "ratio": 0.50},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep talbot_lau
pwm-node verify talbot_lau/gratphantom_s1.yaml
pwm-node mine talbot_lau/gratphantom_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
