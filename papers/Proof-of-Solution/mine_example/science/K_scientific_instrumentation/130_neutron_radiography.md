# Principle #130 — Neutron Radiography / Tomography

**Domain:** Scientific Instrumentation | **Carrier:** Neutron | **Difficulty:** Research (δ=5)
**DAG:** Pi.radon --> S.angular | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.radon-->S.angular    NeutRad     NeutPhantom-15     FBP/Iter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NEUTRON RADIOGRAPHY / TOMOGRAPHY   P = (E, G, W, C)   #130    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(x,y) = I₀ exp(−∫ Σ_t(x,y,z) dz)                    │
│        │ Σ_t = macroscopic total cross-section (H-sensitive)    │
│        │ Tomography: Radon transform over angular projections   │
│        │ Inverse: reconstruct Σ_t(x,y,z) from sinogram         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon] --> [S.angular]                               │
│        │  NeutronProj  AngularSample                            │
│        │ V={Pi.radon, S.angular}  A={Pi.radon-->S.angular}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Beer-Lambert law, well-defined Σ_t)   │
│        │ Uniqueness: YES (sufficient angular coverage ≥ 180°)   │
│        │ Stability: κ ≈ 10 (thermal), κ ≈ 50 (epithermal/fast) │
│        │ Mismatch: beam hardening, scattering halo, activation  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), CNR (secondary)                    │
│        │ q = 2.0 (FBP exact; iterative O(1/k) convergence)    │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Neutron flux, exposure time, and pixel pitch yield adequate counting statistics | PASS |
| S2 | ≥ 180 projections over 180° provide Nyquist angular sampling for FBP | PASS |
| S3 | FBP converges exactly; SIRT converges monotonically for Poisson model | PASS |
| S4 | PSNR ≥ 28 dB achievable for 10⁴ counts/pixel thermal neutron images | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# neutron_radiography/neutphantom_s1.yaml
principle_ref: sha256:<p130_hash>
omega:
  grid: [512, 512]
  pixel_um: 50
  neutron_energy: thermal
  wavelength_A: 1.8
  n_projections: 360
E:
  forward: "I = I0 * exp(-Radon{Sigma_t})"
  transform: "Radon"
I:
  dataset: NeutPhantom_15
  projections: 360
  noise: {type: poisson, mean_counts: 8000}
  scenario: ideal
O: [PSNR, CNR]
epsilon:
  PSNR_min: 28.0
  CNR_min: 4.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 µm pixel at 1.8 Å wavelength with 360 projections covers full sinogram | PASS |
| S2 | κ ≈ 10 at 8000 mean counts for thermal neutrons | PASS |
| S3 | FBP/SIRT converges within 50 iterations for Poisson model | PASS |
| S4 | PSNR ≥ 28 dB feasible at 8000 counts/pixel | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# neutron_radiography/benchmark_s1.yaml
spec_ref: sha256:<spec130_hash>
principle_ref: sha256:<p130_hash>
dataset:
  name: NeutPhantom_15
  volumes: 15
  projections: 360
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FBP-RamLak
    params: {filter: ram_lak}
    results: {PSNR: 27.5, CNR: 4.2}
  - solver: SIRT
    params: {n_iter: 50}
    results: {PSNR: 29.8, CNR: 5.0}
  - solver: CGLS-TV
    params: {n_iter: 30, lambda: 0.01}
    results: {PSNR: 32.0, CNR: 6.5}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline solver:** SIRT — PSNR 29.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | CNR | Runtime | Q |
|--------|-----------|-----|---------|---|
| FBP-RamLak | 27.5 | 4.2 | 2 s | 0.78 |
| SIRT | 29.8 | 5.0 | 30 s | 0.88 |
| CGLS-TV | 32.0 | 6.5 | 2 min | 1.00 |
| DL-NeutCT (ResUNet) | 33.2 | 7.1 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DL-NeutCT):  500 × 1.00 = 500 PWM
Floor:                  500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p130_hash>",
  "h_s": "sha256:<spec130_hash>",
  "h_b": "sha256:<bench130_hash>",
  "r": {"residual_norm": 0.007, "error_bound": 0.02, "ratio": 0.35},
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
pwm-node benchmarks | grep neutron_radiography
pwm-node verify neutron_radiography/neutphantom_s1.yaml
pwm-node mine neutron_radiography/neutphantom_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
