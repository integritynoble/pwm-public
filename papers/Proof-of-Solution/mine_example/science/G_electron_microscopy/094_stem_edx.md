# Principle #94 — STEM-EDX (Energy-Dispersive X-ray in STEM)

**Domain:** Electron Microscopy | **Carrier:** Electron → X-ray | **Difficulty:** Standard (δ=3)
**DAG:** G.beam --> K.scatter.electron --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.beam-->K.scatter.electron-->S.spectral    STEMEDX    EDX-Alloy          Unmixing
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STEM-EDX   P = (E, G, W, C)   Principle #94                   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,E) = Probe(r) · Σ_Z c_Z(r)·σ_Z(E)·ω_Z·ε(E) + n │
│        │ c_Z = concentration of element Z at position r         │
│        │ σ_Z = ionization cross-section; ω_Z = fluorescence yld │
│        │ Inverse: recover elemental maps c_Z(r) from SI data    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.electron] --> [S.spectral]       │
│        │  E-Beam  Excite  EnergyDisperse                         │
│        │ V={G.beam, K.scatter.electron, S.spectral}  A={G.beam-->K.scatter.electron, K.scatter.electron-->S.spectral}   L_DAG=3.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (element-specific X-ray lines)          │
│        │ Uniqueness: YES for non-overlapping lines               │
│        │ Stability: κ ≈ 12 (strong lines), κ ≈ 80 (trace elem) │
│        │ Mismatch: detector dead-time, absorption, peak overlap  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = element-map PSNR (primary), quantification err (s) │
│        │ q = 2.0 (least-squares fitting convergence)           │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy channels cover relevant X-ray lines; detector solid angle consistent | PASS |
| S2 | Characteristic lines element-specific → bounded inverse for unmixing | PASS |
| S3 | Least-squares spectral fitting converges for Gaussian peak model | PASS |
| S4 | Map PSNR ≥ 24 dB achievable at standard STEM-EDX dose | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# stem_edx/alloy_s1_ideal.yaml
principle_ref: sha256:<p094_hash>
omega:
  scan_grid: [256, 256]
  energy_channels: 2048
  energy_range_keV: [0, 20]
  dispersion_eV_per_ch: 10
E:
  forward: "y(r,E) = Probe · Σ_Z c_Z·σ_Z·ω_Z·ε + n"
  detector: "SDD, 0.8 sr solid angle"
I:
  dataset: EDX_Alloy
  spectrum_images: 30
  noise: {type: poisson, total_counts: 1e6}
  scenario: ideal
O: [PSNR_map, quantification_error_pct]
epsilon:
  PSNR_min: 24.0
  quant_error_max_pct: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2048 channels at 10 eV/ch covers 0–20 keV range | PASS |
| S2 | Major alloy peaks non-overlapping; κ ≈ 12 | PASS |
| S3 | LS fitting converges for Gaussian peak + Bremsstrahlung BG | PASS |
| S4 | PSNR ≥ 24 dB and < 5% quant error at 10⁶ total counts | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# stem_edx/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec094_hash>
principle_ref: sha256:<p094_hash>
dataset:
  name: EDX_Alloy
  spectrum_images: 30
  size: [256, 256, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Window-Integration
    params: {bg_model: linear}
    results: {PSNR: 24.8, quant_err_pct: 4.2}
  - solver: NMF-EDX
    params: {n_components: 6, n_iter: 300}
    results: {PSNR: 27.1, quant_err_pct: 2.8}
  - solver: EDXNet
    params: {pretrained: alloy}
    results: {PSNR: 30.5, quant_err_pct: 1.5}
quality_scoring:
  - {min: 31.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 23.0, Q: 0.75}
```

**Baseline solver:** Window-Integration — PSNR 24.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | Quant Err (%) | Runtime | Q |
|--------|-----------|---------------|---------|---|
| Window-Integration | 24.8 | 4.2 | 1 s | 0.80 |
| NMF-EDX | 27.1 | 2.8 | 20 s | 0.88 |
| EDXNet | 30.5 | 1.5 | 3 s | 0.96 |
| SpectralFormer | 31.8 | 1.0 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SpectralFormer): 300 × 1.00 = 300 PWM
Floor:                      300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p094_hash>",
  "h_s": "sha256:<spec094_hash>",
  "h_b": "sha256:<bench094_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep stem_edx
pwm-node verify stem_edx/alloy_s1_ideal.yaml
pwm-node mine stem_edx/alloy_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
