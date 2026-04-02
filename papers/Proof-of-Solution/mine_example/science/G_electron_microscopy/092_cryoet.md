# Principle #92 — Cryo-Electron Tomography (Cryo-ET)

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Expert (δ=8)
**DAG:** Pi.radon --> K.psf.ctf --> N.pointwise.abs2 --> S.tilt | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        Pi.radon-->K.psf.ctf-->N.pointwise.abs2-->S.tilt    CryoET     EMPIAR-CryoET      SubtomoAvg
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CRYO-ET   P = (E, G, W, C)   Principle #92                    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_θ(r) = CTF_θ · ∫ V(r,z) dz|_{rot_θ} + n(r)        │
│        │ Tilt series of vitrified biological specimen            │
│        │ Missing wedge + CTF + extreme low dose (2-5 e⁻/Å²)    │
│        │ Inverse: 3D volume from low-SNR tilt series            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon] --> [K.psf.ctf] --> [N.pointwise.abs2] --> [S.tilt]│
│        │  RadonProj  CTF  ModSq  TiltSeries                      │
│        │ V={Pi.radon, K.psf.ctf, N.pointwise.abs2, S.tilt}  A={Pi.radon-->K.psf.ctf, K.psf.ctf-->N.pointwise.abs2, N.pointwise.abs2-->S.tilt}   L_DAG=5.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Radon invertible with regularization)  │
│        │ Uniqueness: NO — missing wedge; sub-tomo avg helps      │
│        │ Stability: κ ≈ 100 (single tomo), κ ≈ 30 (avg'd)      │
│        │ Mismatch: tilt-axis, CTF defocus, beam-induced motion   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = FSC resolution (primary), SNR (secondary)          │
│        │ q = 1.0 (SIRT convergence for missing-wedge data)     │
│        │ T = {FSC_resolution, gold_standard_FSC}                │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Tilt geometry consistent; CTF parameters match voltage/defocus | PASS |
| S2 | Sub-tomogram averaging fills missing wedge; regularizable | PASS |
| S3 | WBP/SIRT + sub-tomo alignment converge for low-SNR data | PASS |
| S4 | Sub-nm resolution achievable with >1000 sub-tomograms | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cryoet/empiar_s1_ideal.yaml
principle_ref: sha256:<p092_hash>
omega:
  grid: [4096, 4096]
  tilt_range_deg: [-60, 60]
  tilt_step_deg: 3
  pixel_A: 1.35
E:
  forward: "y_θ = CTF · Proj_θ(V) + n"
  voltage_kV: 300
  defocus_um: [-2, -5]
I:
  dataset: EMPIAR_CryoET
  tomograms: 15
  dose_e_per_A2: 3
  scenario: ideal
O: [FSC_resolution_A, subtomo_SNR]
epsilon:
  FSC_resolution_max_A: 10.0
  subtomo_count_min: 500
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4096² at 1.35 Å pixel; 41 tilts over ±60° at 3° steps | PASS |
| S2 | κ ≈ 100 single; sub-tomo averaging reduces to κ ≈ 30 | PASS |
| S3 | WBP + RELION sub-tomo pipeline converges | PASS |
| S4 | FSC < 10 Å feasible with 500+ sub-tomograms at 3 e⁻/Å² | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cryoet/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec092_hash>
principle_ref: sha256:<p092_hash>
dataset:
  name: EMPIAR_CryoET
  tomograms: 15
  size: [4096, 4096, 41]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: WBP
    params: {filter: hamming}
    results: {FSC_res_A: 25.0}
  - solver: SIRT
    params: {n_iter: 30}
    results: {FSC_res_A: 18.0}
  - solver: IsoNet-CryoET
    params: {pretrained: true}
    results: {FSC_res_A: 8.5}
quality_scoring:
  - {max_res_A: 6.0, Q: 1.00}
  - {max_res_A: 10.0, Q: 0.90}
  - {max_res_A: 15.0, Q: 0.80}
  - {max_res_A: 25.0, Q: 0.75}
```

**Baseline solver:** WBP — FSC 25 Å
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | FSC (Å) | Runtime | Q |
|--------|---------|---------|---|
| WBP | 25.0 | 5 min | 0.75 |
| SIRT | 18.0 | 30 min | 0.80 |
| IsoNet-CryoET | 8.5 | 2 hr | 0.92 |
| CryoET-DeepTomo | 5.5 | 4 hr | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (DeepTomo):  800 × 1.00 = 800 PWM
Floor:                 800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p092_hash>",
  "h_s": "sha256:<spec092_hash>",
  "h_b": "sha256:<bench092_hash>",
  "r": {"FSC_resolution_A": 8.5, "gold_standard": true},
  "c": {"fitted_rate": 0.98, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 600–800 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep cryoet
pwm-node verify cryoet/empiar_s1_ideal.yaml
pwm-node mine cryoet/empiar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
