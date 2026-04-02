# Principle #43 — Functional MRI (BOLD fMRI)

**Domain:** Medical Imaging | **Carrier:** Spin | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix.coil] --> [F.dft] --> [S.kspace] --> [∫.temporal]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix.coil --> F.dft --> S.kspace --> ∫.temporal    fMRI-act     fMRI_Task-30      GLM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FUNCTIONAL MRI (BOLD)   P = (E, G, W, C)   Principle #43       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(t) = X·β + ε; X = stim(t) ⊛ HRF(t)                 │
│        │ S(t) = S₀·exp(−TE·R₂*(t)); ΔR₂* ∝ ΔHBO               │
│        │ Inverse: estimate activation map β from BOLD time      │
│        │ series via general linear model                         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix.coil] ──→ [F.dft] ──→ [S.kspace] ──→ [∫.temporal]│
│        │  Excite  Encode  Sample  Accumulate Detect             │
│        │ V={L.mix.coil,F.dft,S.kspace,∫.temporal}  A={L.mix.coil→F.dft, F.dft→S.kspace, S.kspace→∫.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (BOLD signal measurable with GRE-EPI)  │
│        │ Uniqueness: YES (GLM with known design matrix)         │
│        │ Stability: κ ≈ 15 (block design), κ ≈ 50 (event-rel.) │
│        │ Mismatch: Δ_motion, Δ_HRF, Δ_drift (physiological)   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = t-stat AUC (primary), activation overlap (second.)│
│        │ q = 1.0 (GLM least-squares convergence)              │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TR, TE, voxel size consistent with BOLD contrast and brain coverage | PASS |
| S2 | Design matrix full-rank → invertible GLM | PASS |
| S3 | OLS/GLS converges; Bayesian methods converge | PASS |
| S4 | AUC ≥ 0.85 achievable for block-design at 3T with SNR > 100 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fmri/task_s1_ideal.yaml
principle_ref: sha256:<p043_hash>
omega:
  grid: [64, 64, 36]
  TR_ms: 2000
  TE_ms: 30
  voxel_mm: [3, 3, 3]
  field_T: 3.0
E:
  forward: "y(t) = X·β + ε; X = stim ⊛ HRF"
  HRF: "canonical double-gamma, SPM default"
I:
  dataset: fMRI_Task_30
  subjects: 30
  noise: {type: gaussian, tSNR: 80}
  scenario: ideal
O: [t_stat_AUC, activation_Dice]
epsilon:
  AUC_min: 0.85
  Dice_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 64×64×36 at 3 mm, TR=2 s covers whole brain with BOLD sensitivity | PASS |
| S2 | κ ≈ 15 within well-posed regime for block design | PASS |
| S3 | GLM least-squares converges for Gaussian noise model | PASS |
| S4 | AUC ≥ 0.85 feasible for tSNR=80 block-design | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fmri/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec043_hash>
principle_ref: sha256:<p043_hash>
dataset:
  name: fMRI_Task_30
  subjects: 30
  size: [64, 64, 36]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: GLM_OLS
    params: {hrf: canonical}
    results: {AUC: 0.87, Dice: 0.72}
  - solver: GLM_AR1
    params: {hrf: canonical, prewhiten: true}
    results: {AUC: 0.90, Dice: 0.76}
  - solver: BrainNet_DL
    params: {pretrained: true}
    results: {AUC: 0.94, Dice: 0.84}
quality_scoring:
  - {min_AUC: 0.95, Q: 1.00}
  - {min_AUC: 0.92, Q: 0.90}
  - {min_AUC: 0.88, Q: 0.80}
  - {min_AUC: 0.85, Q: 0.75}
```

**Baseline solver:** GLM-OLS — AUC 0.87
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | AUC | Dice | Runtime | Q |
|--------|-----|------|---------|---|
| GLM-OLS | 0.87 | 0.72 | 5 s | 0.78 |
| GLM-AR1 | 0.90 | 0.76 | 10 s | 0.84 |
| BrainNet (DL) | 0.94 | 0.84 | 3 s | 0.96 |
| Bayesian-GLM | 0.96 | 0.88 | 60 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian-GLM):  300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p043_hash>",
  "h_s": "sha256:<spec043_hash>",
  "h_b": "sha256:<bench043_hash>",
  "r": {"residual_norm": 0.035, "error_bound": 0.07, "ratio": 0.50},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.96,
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
pwm-node benchmarks | grep fmri
pwm-node verify fmri/task_s1_ideal.yaml
pwm-node mine fmri/task_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
