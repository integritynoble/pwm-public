# Principle #45 — Diffusion MRI (DTI/DWI)

**Domain:** Medical Imaging | **Carrier:** Spin | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix.coil] --> [F.dft] --> [S.kspace]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix.coil --> F.dft --> S.kspace      dMRI-fit     HCP_dMRI-20       WLS-DTI
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DIFFUSION MRI (DTI/DWI)   P = (E, G, W, C)   Principle #45    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ S(g,b) = S₀·exp(−b·gᵀDg) + n        (DTI model)      │
│        │ S(g,b) = S₀·∫ F(θ,φ)K(g,b,θ,φ) dΩ + n   (CSD/HARDI) │
│        │ Inverse: estimate diffusion tensor D or fiber ODF F    │
│        │ from diffusion-weighted signals along multiple g dirs  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix.coil] ──→ [F.dft] ──→ [S.kspace]               │
│        │  Excite  DiffEncode Sample  Detect                     │
│        │ V={L.mix.coil,F.dft,S.kspace}  A={L.mix.coil→F.dft, F.dft→S.kspace}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (diffusion attenuation measurable)      │
│        │ Uniqueness: YES (DTI: 6 unknowns, ≥6 dirs); COND (CSD)│
│        │ Stability: κ ≈ 10 (DTI high SNR), κ ≈ 40 (CSD sparse) │
│        │ Mismatch: Δ_eddy, Δ_susceptibility, Δ_gradient        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = FA error % (primary), angular error deg (second.)  │
│        │ q = 2.0 (WLS-DTI convergence), q = 1.0 (CSD iter.)  │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gradient directions and b-values consistent with tensor/CSD model | PASS |
| S2 | Sufficient directions for rank-6 tensor → bounded LS inversion | PASS |
| S3 | WLS-DTI converges; CSD with regularization converges | PASS |
| S4 | FA error ≤ 5% achievable for SNR ≥ 20 single-shell | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# diffusion_mri/hcp_s1_ideal.yaml
principle_ref: sha256:<p045_hash>
omega:
  grid: [96, 96, 60]
  b_values: [0, 1000, 2000]
  n_directions: [1, 30, 60]
  voxel_mm: [2, 2, 2]
E:
  forward: "S(g,b) = S₀·exp(−b·gᵀDg) + n"
  model: "diffusion tensor (6 DoF)"
I:
  dataset: HCP_dMRI_20
  subjects: 20
  noise: {type: rician, SNR: 25}
  scenario: ideal
O: [FA_error_pct, angular_error_deg]
epsilon:
  FA_error_max_pct: 5.0
  angular_error_max_deg: 10.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 91 total directions across 2 shells satisfies DTI and CSD needs | PASS |
| S2 | κ ≈ 10 within well-posed regime for DTI at SNR=25 | PASS |
| S3 | WLS-DTI converges for Rician noise model | PASS |
| S4 | FA error ≤ 5% feasible for SNR=25 multi-shell | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# diffusion_mri/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec045_hash>
principle_ref: sha256:<p045_hash>
dataset:
  name: HCP_dMRI_20
  subjects: 20
  size: [96, 96, 60]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: WLS_DTI
    params: {method: weighted_least_squares}
    results: {FA_error_pct: 4.5, angular_error_deg: 8.2}
  - solver: CSD_MRtrix
    params: {lmax: 8}
    results: {FA_error_pct: 3.8, angular_error_deg: 6.5}
  - solver: DeepDTI
    params: {pretrained: true}
    results: {FA_error_pct: 2.5, angular_error_deg: 4.2}
quality_scoring:
  - {max_ang_err: 3.0, Q: 1.00}
  - {max_ang_err: 5.0, Q: 0.90}
  - {max_ang_err: 8.0, Q: 0.80}
  - {max_ang_err: 12.0, Q: 0.75}
```

**Baseline solver:** WLS-DTI — angular error 8.2°
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | FA Error (%) | Ang. Error (°) | Runtime | Q |
|--------|-------------|-----------------|---------|---|
| WLS-DTI | 4.5 | 8.2 | 5 s | 0.80 |
| CSD-MRtrix | 3.8 | 6.5 | 30 s | 0.85 |
| DeepDTI | 2.5 | 4.2 | 3 s | 0.92 |
| FOD-Net | 1.5 | 2.5 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FOD-Net):  300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p045_hash>",
  "h_s": "sha256:<spec045_hash>",
  "h_b": "sha256:<bench045_hash>",
  "r": {"residual_norm": 0.030, "error_bound": 0.06, "ratio": 0.50},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.92,
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
pwm-node benchmarks | grep diffusion_mri
pwm-node verify diffusion_mri/hcp_s1_ideal.yaml
pwm-node mine diffusion_mri/hcp_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
