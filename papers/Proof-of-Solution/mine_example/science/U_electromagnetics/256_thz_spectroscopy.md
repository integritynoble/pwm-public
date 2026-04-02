# THz Spectroscopy — Four-Layer Walkthrough

**Principle #256 · Terahertz Time-Domain Spectroscopy**
Domain: Electromagnetics & Optics | Carrier: photon (THz) | Difficulty: standard (δ=3) | DAG: [G.pulse.thz] --> [F.dft] --> [N.pointwise.lorentz] --> [∫.spectral]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ THz pulse, FFT   │→│ Material sample  │→│ Known dielectric │→│ Deconvolution /  │
│ transfer function│ │ transmission,    │ │ functions, ref   │ │ iterative solver │
│ n(ω), α(ω)      │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

H(ω) = E_sam(ω)/E_ref(ω) = T₁₂·T₂₁·exp(−j(ñ−1)ωd/c) · FP(ω)
Complex refractive index: ñ(ω) = n(ω) + jκ(ω)
Absorption: α(ω) = 2ωκ(ω)/c

### DAG

```
[G.pulse.thz] --> [F.dft] --> [N.pointwise.lorentz] --> [∫.spectral]
THz-pulse-source  Fourier-transform  Lorentz-model  spectral-integral
```
V={G.pulse.thz,F.dft,N.pointwise.lorentz,∫.spectral}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Transfer function always computable |
| Uniqueness | CONDITIONAL | Phase unwrapping ambiguity for thick samples |
| Stability | CONDITIONAL | Low SNR at band edges; Fabry-Perot oscillations |

Mismatch: sample thickness, alignment, water vapor absorption

### Error Method

e = relative n(ω) error, α(ω) error (%); q = 2.0

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #256"
omega:
  sample: HDPE
  thickness_mm: 1.0
  freq_THz: [0.1, 3.0]
E:
  forward: "H(w) = T12*T21*exp(-j*(n_tilde-1)*w*d/c)*FP"
I:
  scenario: S1_ideal
  SNR_dB: 60
O: [n_error_pct, alpha_error_pct, thickness_error_um]
epsilon:
  n_error_max_pct: 0.5
  alpha_error_max_pct: 5.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known d, no etalon | None | n err ≤ 0.5% |
| S2 Mismatch | d ± 50 μm | Δd | n err ≤ 3% |
| S3 Oracle | True d given | Known Δd | n err ≤ 0.8% |
| S4 Blind Cal | Estimate d from FP oscillations | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: thz_spectroscopy
  cases: 8  # HDPE, quartz, lactose, water
  ref: published_dielectric_functions
baselines:
  - solver: standard_extraction
    n_err_pct: 0.3
  - solver: iterative_Fabry_Perot
    n_err_pct: 0.1
quality_scoring:
  metric: n_error_pct
  thresholds:
    - {max: 0.05, Q: 1.00}
    - {max: 0.2, Q: 0.90}
    - {max: 0.5, Q: 0.80}
    - {max: 2.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | n err | Time | Q | Reward |
|--------|-------|------|---|--------|
| standard_extraction | 0.3% | 0.1s | 0.80 | 240 PWM |
| iterative_FP | 0.1% | 1s | 0.90 | 270 PWM |
| Bayesian_extraction | 0.03% | 10s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 256,
  "r": {"residual_norm": 0.0003, "error_bound": 0.005, "ratio": 0.06},
  "c": {"resolutions": [256,512,1024], "fitted_rate": 2.0, "theoretical_rate": 2.0},
  "Q": 1.00,
  "gates": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | One-time | Ongoing |
|-------|----------|---------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec | 150 PWM × 4 | 10% of L4 mints |
| L3 Benchmark | 100 PWM × 4 | 15% of L4 mints |
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep thz
pwm-node mine thz/hdpe_s1_ideal.yaml
```
