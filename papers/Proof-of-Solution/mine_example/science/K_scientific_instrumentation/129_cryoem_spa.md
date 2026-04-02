# Principle #129 — Cryo-EM Single Particle Analysis

**Domain:** Scientific Instrumentation | **Carrier:** Electron | **Difficulty:** Research (δ=5)
**DAG:** Pi.area --> K.psf.ctf --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.area-->K.psf.ctf-->N.pointwise.abs2    CryoEM-SPA  EMPIAR-20          Refine3D
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CRYO-EM SINGLE PARTICLE ANALYSIS  P = (E, G, W, C)  #129      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_k(x,y) = CTF_k ⊛ ∫ V(R_k r) dz + n_k              │
│        │ CTF = contrast transfer function (defocus, Cs, λ)     │
│        │ R_k = unknown 3D rotation for particle k              │
│        │ Inverse: recover V(x,y,z) from 2D noisy projections   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.area] --> [K.psf.ctf] --> [N.pointwise.abs2]         │
│        │  AreaProject  CTF  ModSq                               │
│        │ V={Pi.area, K.psf.ctf, N.pointwise.abs2}  A={Pi.area-->K.psf.ctf, K.psf.ctf-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (projections always formed)             │
│        │ Uniqueness: YES with sufficient orientational coverage │
│        │ Stability: κ ≈ 10 (large complex), κ ≈ 100 (< 50kDa)│
│        │ Mismatch: preferred orientation, beam-induced motion   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = resolution Å at FSC=0.143 (primary), map-model CC │
│        │ q = 2.0 (iterative projection matching convergence)   │
│        │ T = {resolution_A, FSC_0.143, B_factor, map_model_CC} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Particle box size > 1.5× diameter; pixel size satisfies Nyquist for target res | PASS |
| S2 | CTF estimation converges; defocus range avoids zero-crossings at target freq | PASS |
| S3 | Orientation refinement converges (angular assignment improves FSC per iter) | PASS |
| S4 | Resolution ≤ 3.5 Å achievable for ≥ 100 kDa complex with ≥ 50k particles | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cryoem_spa/empiar_s1.yaml
principle_ref: sha256:<p129_hash>
omega:
  voltage_kV: 300
  Cs_mm: 2.7
  pixel_A: 1.0
  box_px: 256
  defocus_range_um: [1.0, 3.0]
E:
  forward: "I_k = CTF_k * Proj(V, R_k) + n_k"
  CTF: "phase_contrast, Cs=2.7mm, 300kV"
I:
  dataset: EMPIAR_20
  complexes: 20
  particles_per: [50000, 500000]
  noise: {type: gaussian, SNR: 0.05}
O: [resolution_A, map_model_CC]
epsilon:
  resolution_max: 3.5
  CC_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1.0 Å/px with 256 px box covers ≤ 25.6 nm particles; Nyquist OK for 2 Å | PASS |
| S2 | CTF estimation stable for 1.0–3.0 μm defocus at SNR=0.05 | PASS |
| S3 | RELION/cryoSPARC refinement converges for ≥ 50k particles | PASS |
| S4 | Resolution ≤ 3.5 Å feasible for ≥ 100 kDa complexes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cryoem_spa/benchmark_s1.yaml
spec_ref: sha256:<spec129_hash>
principle_ref: sha256:<p129_hash>
dataset:
  name: EMPIAR_20
  complexes: 20
  total_particles: 2e6
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RELION-3.1
    params: {K: 1, tau: 4}
    results: {resolution: 3.2, CC: 0.83}
  - solver: cryoSPARC-3
    params: {ab_initio: true}
    results: {resolution: 2.8, CC: 0.87}
  - solver: cisTEM
    params: {auto: true}
    results: {resolution: 3.0, CC: 0.85}
quality_scoring:
  - {max_resolution: 2.5, Q: 1.00}
  - {max_resolution: 3.0, Q: 0.90}
  - {max_resolution: 3.5, Q: 0.80}
  - {max_resolution: 4.0, Q: 0.75}
```

**Baseline solver:** RELION-3.1 — 3.2 Å
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Resolution (Å) | Map-Model CC | Runtime | Q |
|--------|-----------------|--------------|---------|---|
| RELION-3.1 | 3.2 | 0.83 | 24 hr | 0.85 |
| cryoSPARC-3 | 2.8 | 0.87 | 6 hr | 0.95 |
| cisTEM | 3.0 | 0.85 | 12 hr | 0.90 |
| DL-CryoEM (DRGNai) | 2.5 | 0.90 | 4 hr | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DRGNai):  500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p129_hash>",
  "h_s": "sha256:<spec129_hash>",
  "h_b": "sha256:<bench129_hash>",
  "r": {"residual_norm": 2.5, "error_bound": 3.5, "ratio": 0.71},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep cryoem_spa
pwm-node verify cryoem_spa/empiar_s1.yaml
pwm-node mine cryoem_spa/empiar_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
