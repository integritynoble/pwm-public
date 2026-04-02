# Principle #132 — Muon Tomography

**Domain:** Scientific Instrumentation | **Carrier:** Cosmic-ray Muon | **Difficulty:** Frontier (δ=8)
**DAG:** K.scatter.nuclear --> S.angular | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.nuclear-->S.angular    MuonTomo    MuonSim-10         POCA/MLP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MUON TOMOGRAPHY   P = (E, G, W, C)   Principle #132           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ θ_rms = (13.6 MeV/pβc)√(L/X₀)[1+0.038 ln(L/X₀)]    │
│        │ Δp/p from energy loss; scattering ∝ Z/A of material   │
│        │ Multiple Coulomb scattering encodes material Z/density │
│        │ Inverse: reconstruct Z/ρ distribution from muon tracks │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.nuclear] --> [S.angular]                      │
│        │  MuonScatter  AngularMeas                              │
│        │ V={K.scatter.nuclear, S.angular}  A={K.scatter.nuclear-->S.angular}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (cosmic muon flux ~1/cm²/min at sea lvl)│
│        │ Uniqueness: YES with sufficient track statistics       │
│        │ Stability: κ ≈ 20 (high-Z), κ ≈ 100 (low-Z contrast)  │
│        │ Mismatch: momentum spectrum spread, tracker resolution │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Z discrimination accuracy (primary), spatial (sec.)│
│        │ q = 1.0 (POCA discrete; MLEM O(1/√k))                │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Tracker spatial resolution ≤ 200 µm; angular resolution ≤ 0.3 mrad consistent | PASS |
| S2 | 10⁶ muon tracks discriminate U (Z=92) from Pb (Z=82) at 5σ | PASS |
| S3 | POCA converges for point scatter; MLEM converges monotonically | PASS |
| S4 | Z discrimination ≥ 95% for high-Z objects with 10 min exposure | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# muon_tomography/muonsim_s1.yaml
principle_ref: sha256:<p132_hash>
omega:
  grid: [64, 64, 64]
  voxel_cm: 2.0
  muon_flux: 1.0  # per cm^2 per min
  exposure_min: 10
  tracker_res_um: 200
E:
  forward: "theta_rms = Highland(p, L/X0); track entry/exit"
  scattering_model: "multiple_coulomb"
I:
  dataset: MuonSim_10
  scenarios: 10
  tracks_per: 500000
  noise: {type: gaussian, sigma_angle_mrad: 0.3}
O: [Z_discrimination_pct, spatial_res_cm]
epsilon:
  Z_discrimination_min: 90.0
  spatial_res_max: 3.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2 cm voxels with 200 µm tracker resolution at 10 min exposure | PASS |
| S2 | 5×10⁵ tracks yield κ ≈ 20 for high-Z discrimination | PASS |
| S3 | MLEM converges within 30 iterations for voxelised scattering model | PASS |
| S4 | Z discrimination ≥ 90% feasible with 5×10⁵ tracks | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# muon_tomography/benchmark_s1.yaml
spec_ref: sha256:<spec132_hash>
principle_ref: sha256:<p132_hash>
dataset:
  name: MuonSim_10
  scenarios: 10
  tracks_per: 500000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: POCA
    params: {voxel_cm: 2.0}
    results: {Z_discrimination_pct: 85, spatial_res_cm: 4.0}
  - solver: MLEM
    params: {n_iter: 30}
    results: {Z_discrimination_pct: 92, spatial_res_cm: 2.5}
  - solver: MLP-MLEM
    params: {n_iter: 20, path: MLP}
    results: {Z_discrimination_pct: 96, spatial_res_cm: 2.0}
quality_scoring:
  - {min_disc: 95, Q: 1.00}
  - {min_disc: 92, Q: 0.90}
  - {min_disc: 88, Q: 0.80}
  - {min_disc: 82, Q: 0.75}
```

**Baseline solver:** MLEM — Z discrimination 92%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Z discrim. (%) | Spatial res (cm) | Runtime | Q |
|--------|----------------|-------------------|---------|---|
| POCA | 85 | 4.0 | 2 s | 0.78 |
| MLEM | 92 | 2.5 | 5 min | 0.90 |
| MLP-MLEM | 96 | 2.0 | 10 min | 1.00 |
| DL-Muon (3D-CNN) | 97 | 1.8 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (MLP-MLEM/DL):  800 × 1.00 = 800 PWM
Floor:                    800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p132_hash>",
  "h_s": "sha256:<spec132_hash>",
  "h_b": "sha256:<bench132_hash>",
  "r": {"residual_norm": 0.04, "error_bound": 0.10, "ratio": 0.40},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 600–800 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep muon_tomography
pwm-node verify muon_tomography/muonsim_s1.yaml
pwm-node mine muon_tomography/muonsim_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
