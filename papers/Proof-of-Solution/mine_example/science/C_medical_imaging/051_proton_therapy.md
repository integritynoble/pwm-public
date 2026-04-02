# Principle #51 — Proton Therapy Imaging

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Hard (δ=4)
**DAG:** [Π.radon.parallel] --> [S.angular.full]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.radon.parallel --> S.angular.full      pCT-recon    ProtonPhantom-10  IterRecon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PROTON THERAPY IMAGING   P = (E, G, W, C)   Principle #51     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ WEPL = ∫ ρ_s(l) dl  (water-equivalent path length)    │
│        │ y_i = WEPL_i + n_i;  ρ_s = relative stopping power    │
│        │ Inverse: reconstruct 3D stopping-power map from       │
│        │ measured WEPL along multiple proton trajectories       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.radon.parallel] ──→ [S.angular.full]              │
│        │  Propagate Project Transform Detect                    │
│        │ V={Π.radon.parallel,S.angular.full}  A={Π.radon.parallel→S.angular.full}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (WEPL measurable via residual range)    │
│        │ Uniqueness: YES (sufficient angular coverage)          │
│        │ Stability: κ ≈ 20 (curved paths), κ ≈ 60 (scattering) │
│        │ Mismatch: Δ_MCS (multiple Coulomb scattering), Δ_nucl │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RSP RMSE % (primary), spatial resolution mm (sec.) │
│        │ q = 1.0 (iterative ART convergence with curved paths) │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Proton energy and detector geometry support full angular coverage | PASS |
| S2 | Sufficient proton statistics → bounded ART/SART inversion | PASS |
| S3 | Iterative reconstruction with MLP tracking converges | PASS |
| S4 | RSP RMSE ≤ 1% achievable for head phantom with 10⁸ protons | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# proton_ct/head_s1_ideal.yaml
principle_ref: sha256:<p051_hash>
omega:
  grid: [256, 256, 128]
  voxel_mm: [1, 1, 2]
  proton_energy_MeV: 200
  n_projections: 360
E:
  forward: "WEPL = ∫ ρ_s dl along curved proton path"
  model: "most-likely-path + energy-loss straggling"
I:
  dataset: ProtonPhantom_10
  phantoms: 10
  noise: {type: gaussian, straggling_pct: 3}
  scenario: ideal
O: [RSP_RMSE_pct, spatial_res_mm]
epsilon:
  RSP_RMSE_max_pct: 1.0
  spatial_res_max_mm: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 360 projections at 200 MeV covers full rotation for 256³ grid | PASS |
| S2 | κ ≈ 20 within well-posed regime for MLP-tracked paths | PASS |
| S3 | ART/DROP with MLP converges for straggling noise model | PASS |
| S4 | RSP RMSE ≤ 1% feasible for 10⁸ proton histories | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# proton_ct/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec051_hash>
principle_ref: sha256:<p051_hash>
dataset:
  name: ProtonPhantom_10
  phantoms: 10
  size: [256, 256, 128]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FBP_StraightLine
    params: {filter: ram-lak}
    results: {RSP_RMSE_pct: 2.5, spatial_res_mm: 3.0}
  - solver: ART_MLP
    params: {n_iter: 20}
    results: {RSP_RMSE_pct: 0.8, spatial_res_mm: 1.5}
  - solver: DeepProtonCT
    params: {pretrained: true}
    results: {RSP_RMSE_pct: 0.5, spatial_res_mm: 1.2}
quality_scoring:
  - {max_RMSE: 0.4, Q: 1.00}
  - {max_RMSE: 0.7, Q: 0.90}
  - {max_RMSE: 1.0, Q: 0.80}
  - {max_RMSE: 1.5, Q: 0.75}
```

**Baseline solver:** FBP straight-line — RSP RMSE 2.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RSP RMSE (%) | Res. (mm) | Runtime | Q |
|--------|-------------|-----------|---------|---|
| FBP Straight-Line | 2.5 | 3.0 | 5 s | 0.75 |
| ART-MLP | 0.8 | 1.5 | 120 s | 0.88 |
| DeepProtonCT (learned) | 0.5 | 1.2 | 10 s | 0.95 |
| Hybrid-MLP-DL | 0.35 | 1.0 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (Hybrid-MLP-DL):  400 × 1.00 = 400 PWM
Floor:                      400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p051_hash>",
  "h_s": "sha256:<spec051_hash>",
  "h_b": "sha256:<bench051_hash>",
  "r": {"residual_norm": 0.035, "error_bound": 0.07, "ratio": 0.50},
  "c": {"fitted_rate": 0.92, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep proton_ct
pwm-node verify proton_ct/head_s1_ideal.yaml
pwm-node mine proton_ct/head_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
