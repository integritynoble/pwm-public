# Principle #125 — X-ray Crystallography

**Domain:** Scientific Instrumentation | **Carrier:** X-ray Photon | **Difficulty:** Research (δ=5)
**DAG:** K.scatter.bragg --> S.reciprocal --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.bragg-->S.reciprocal-->N.pointwise.abs2    Xtal        ProteinXtal-20     Phase
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  X-RAY CRYSTALLOGRAPHY   P = (E, G, W, C)   Principle #125      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(hkl) = |F(hkl)|² = |Σ_j f_j exp(2πi(hx+ky+lz))|² │
│        │ Phase problem: measured I loses φ(hkl)                 │
│        │ Bragg's law: 2d sinθ = nλ; structure factor F(hkl)    │
│        │ Inverse: recover ρ(x,y,z) from |F(hkl)| via phasing  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.bragg] --> [S.reciprocal] --> [N.pointwise.abs2]│
│        │  BraggDiffract  Reciprocal  ModSq                      │
│        │ V={K.scatter.bragg, S.reciprocal, N.pointwise.abs2}  A={K.scatter.bragg-->S.reciprocal, S.reciprocal-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bragg peaks always present for crystal)│
│        │ Uniqueness: YES (with sufficient resolution & phasing) │
│        │ Stability: κ ≈ 5 (high-res), κ ≈ 50 (low-res/twinned)│
│        │ Mismatch: radiation damage, twinning, anisotropic B   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = R_work / R_free (primary), resolution Å (sec.)    │
│        │ q = 2.0 (least-squares refinement convergence)        │
│        │ T = {R_work, R_free, resolution, completeness}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wavelength, crystal-to-detector distance, and rotation range cover reciprocal space | PASS |
| S2 | Completeness ≥ 95%; redundancy ≥ 4; I/σ ≥ 2 at resolution limit | PASS |
| S3 | Molecular replacement or SAD/MAD phasing converges; density interpretable | PASS |
| S4 | R_free ≤ 0.25 achievable at resolution ≤ 2.5 Å | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xray_crystallography/proteinxtal_s1.yaml
principle_ref: sha256:<p125_hash>
omega:
  wavelength_A: 1.0
  detector: Pilatus_6M
  resolution_A: 2.0
  space_group: P2_1_2_1_2_1
  cell_A: [50, 60, 70]
E:
  forward: "I(hkl) = |F(hkl)|^2 = |sum_j f_j exp(2pi*i*h.r_j)|^2"
  phasing: "molecular_replacement"
I:
  dataset: ProteinXtal_20
  structures: 20
  completeness: 0.98
  redundancy: 6
  noise: {type: poisson, I_sigma_cutoff: 2.0}
O: [R_free, resolution_A]
epsilon:
  R_free_max: 0.25
  resolution_max: 2.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1.0 Å wavelength with Pilatus 6M covers 2.0 Å resolution sphere | PASS |
| S2 | κ ≈ 5 at 2.0 Å with 98% completeness | PASS |
| S3 | MR phasing converges for homologous model with ≥ 30% identity | PASS |
| S4 | R_free ≤ 0.25 feasible at 2.0 Å resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xray_crystallography/benchmark_s1.yaml
spec_ref: sha256:<spec125_hash>
principle_ref: sha256:<p125_hash>
dataset:
  name: ProteinXtal_20
  structures: 20
  reflections_per: 50000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MR-Refmac
    params: {cycles: 20}
    results: {R_free: 0.24, resolution: 2.0}
  - solver: AutoBuild-Phenix
    params: {build_cycles: 5}
    results: {R_free: 0.22, resolution: 2.0}
  - solver: ARP-wARP
    params: {auto: true}
    results: {R_free: 0.20, resolution: 2.0}
quality_scoring:
  - {max_Rfree: 0.20, Q: 1.00}
  - {max_Rfree: 0.22, Q: 0.90}
  - {max_Rfree: 0.25, Q: 0.80}
  - {max_Rfree: 0.28, Q: 0.75}
```

**Baseline solver:** MR-Refmac — R_free 0.24
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | R_free | R_work | Runtime | Q |
|--------|--------|--------|---------|---|
| MR-Refmac | 0.24 | 0.20 | 30 min | 0.80 |
| AutoBuild-Phenix | 0.22 | 0.18 | 2 hr | 0.90 |
| ARP-wARP | 0.20 | 0.16 | 3 hr | 1.00 |
| DL-Phase (AlphaFold-MR) | 0.21 | 0.17 | 15 min | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (ARP-wARP):  500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p125_hash>",
  "h_s": "sha256:<spec125_hash>",
  "h_b": "sha256:<bench125_hash>",
  "r": {"residual_norm": 0.20, "error_bound": 0.25, "ratio": 0.80},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep xray_crystallography
pwm-node verify xray_crystallography/proteinxtal_s1.yaml
pwm-node mine xray_crystallography/proteinxtal_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
