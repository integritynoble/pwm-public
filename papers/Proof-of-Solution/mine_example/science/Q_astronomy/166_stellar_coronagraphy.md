# Principle #166 — Stellar Coronagraphy

**Domain:** Astronomy | **Carrier:** Photon | **Difficulty:** Advanced (δ=3)
**DAG:** L.diag --> K.psf --> S.angular | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag-->K.psf-->S.angular    Coronag     CoronSim-10       PSF-Sub+Detect
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STELLAR CORONAGRAPHY   P = (E, G, W, C)   Principle #166       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,θ) = α·PSF_star(r) + β·PSF_planet(r−r_p) +        │
│        │          speckle(r) + n(r)                              │
│        │ Coronagraph suppresses on-axis starlight by factor C    │
│        │ Inverse: subtract residual starlight → detect companion │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag] --> [K.psf] --> [S.angular]                     │
│        │  CoronaMask  DiffractionPSF  AngularDiff               │
│        │ V={L.diag, K.psf, S.angular}  A={L.diag-->K.psf, K.psf-->S.angular}   L_DAG=3.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coronagraph creates dark hole)         │
│        │ Uniqueness: YES for sufficient contrast and separation  │
│        │ Stability: κ ≈ 20 (ground AO), κ ≈ 8 (space)         │
│        │ Mismatch: wavefront errors, speckle chromaticity        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = contrast (Δmag), TPR at fixed FPR                  │
│        │ q = 1.5 (ADI/SDI speckle subtraction convergence)    │
│        │ T = {contrast_5sigma, TPR, separation_lambda_D, SNR}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coronagraph inner working angle < target separation; Strehl consistent | PASS |
| S2 | Dark-hole contrast ≥ 10⁻⁶ → bounded residual; κ ≈ 20 (ground) | PASS |
| S3 | ADI rotation diversity enables speckle subtraction convergence | PASS |
| S4 | 5σ contrast ≤ 10⁻⁵ at 5 λ/D achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# coronagraphy/coronsim_s1_ideal.yaml
principle_ref: sha256:<p166_hash>
omega:
  grid: [256, 256]
  pixel_mas: 12.25
  wavelength_nm: 1600
  telescope_m: 8.0
  coronagraph: vortex_charge4
  AO_strehl: 0.90
  field_rotation_deg: 60
E:
  forward: "y = α·PSF_star + β·PSF_planet + speckle + n"
  suppression: "vortex coronagraph, raw contrast ~10⁻⁴"
I:
  dataset: CoronSim_10
  targets: 10
  noise: {type: poisson, background: photon_noise}
  scenario: ideal
O: [contrast_5sigma, TPR, SNR_companion]
epsilon:
  contrast_5sigma_max: 1.0e-5
  TPR_min_at_1pct_FPR: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Vortex IWA ≈ 1.7 λ/D; 60° rotation for ADI | PASS |
| S2 | Raw 10⁻⁴ → post-processing 10⁻⁵ feasible; κ ≈ 20 | PASS |
| S3 | ADI with 60° parallactic rotation converges | PASS |
| S4 | 5σ contrast ≤ 10⁻⁵ at 5 λ/D feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# coronagraphy/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec166_hash>
dataset:
  name: CoronSim_10
  targets: 10
  frames: 200
baselines:
  - solver: cADI
    params: {method: median_subtract}
    results: {contrast_5sig: 5.0e-5, TPR: 0.75}
  - solver: PCA-ADI
    params: {n_components: 10}
    results: {contrast_5sig: 1.2e-5, TPR: 0.88}
  - solver: PACO
    params: {method: GLRT, annuli: 10}
    results: {contrast_5sig: 4.5e-6, TPR: 0.95}
quality_scoring:
  metric: contrast_5sigma
  thresholds:
    - {max: 5.0e-6, Q: 1.00}
    - {max: 1.0e-5, Q: 0.90}
    - {max: 3.0e-5, Q: 0.80}
    - {max: 1.0e-4, Q: 0.75}
```

**Baseline:** cADI — contrast 5×10⁻⁵ | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | Contrast (5σ) | TPR | Runtime | Q |
|--------|--------------|-----|---------|---|
| cADI | 5.0e-5 | 0.75 | 5 s | 0.75 |
| PCA-ADI | 1.2e-5 | 0.88 | 15 s | 0.90 |
| PACO | 4.5e-6 | 0.95 | 60 s | 1.00 |
| ANDROMEDA | 8.0e-6 | 0.91 | 30 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (PACO):  300 × 1.00 = 300 PWM
Floor:        300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p166_hash>",
  "h_s": "sha256:<spec166_hash>",
  "h_b": "sha256:<bench166_hash>",
  "r": {"residual_norm": 4.5e-6, "error_bound": 1.0e-5, "ratio": 0.45},
  "c": {"fitted_rate": 1.42, "theoretical_rate": 1.5, "K": 4},
  "Q": 0.95,
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
pwm-node benchmarks | grep coronagraphy
pwm-node verify coronagraphy/coronsim_s1_ideal.yaml
pwm-node mine coronagraphy/coronsim_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
