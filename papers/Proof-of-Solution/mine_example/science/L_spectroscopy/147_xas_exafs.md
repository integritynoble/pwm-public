# Principle #147 — X-ray Absorption Spectroscopy (XAS/EXAFS)

**Domain:** Spectroscopy | **Carrier:** X-ray Photon | **Difficulty:** Research (δ=5)
**DAG:** G.broadband --> K.scatter.inelastic --> S.spectral | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broadband-->K.scatter.inelastic-->S.spectral    XAS         XASRef-15          FEFF/Fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  X-RAY ABSORPTION SPECTROSCOPY (XAS/EXAFS)   P = (E,G,W,C) #147│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ χ(k) = Σ_j (N_j S₀² f_j(k))/(k R_j²) sin(2kR_j+δ_j)│
│        │        × exp(−2σ_j²k²) exp(−2R_j/λ)                  │
│        │ EXAFS oscillations encode coordination number N, R, σ² │
│        │ Inverse: fit N_j, R_j, σ²_j from χ(k) or FT[χ(R)]    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broadband] --> [K.scatter.inelastic] --> [S.spectral] │
│        │  SynchrotronX  PhotoAbsorb  EnergyDisperse            │
│        │ V={G.broadband, K.scatter.inelastic, S.spectral}  A={G.broadband-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (EXAFS oscillations above absorption K) │
│        │ Uniqueness: YES (shell-by-shell fitting with FEFF paths│
│        │ Stability: κ ≈ 10 (1st shell), κ ≈ 50 (higher shells) │
│        │ Mismatch: multi-electron effects, self-absorption      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = R-factor (primary), bond distance RMSE Å (sec.)    │
│        │ q = 2.0 (Levenberg-Marquardt least-squares)            │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy range covers ≥ 1000 eV above edge; k-range extends to ≥ 12 Å⁻¹ | PASS |
| S2 | FEFF path calculation yields scattering amplitudes; unique shell fitting | PASS |
| S3 | LM fitting converges within 50 iterations for ≤ 4 shells | PASS |
| S4 | R-factor ≤ 0.02 and bond distance accuracy ≤ 0.02 Å for 1st shell | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xas_exafs/xasref_s1.yaml
principle_ref: sha256:<p147_hash>
omega:
  edge: Fe_K
  energy_range_eV: [7000, 8200]
  k_range_inv_A: [2, 14]
  R_range_A: [1.0, 4.0]
  k_weight: 3
E:
  forward: "chi(k) = EXAFS equation (FEFF paths)"
  fitting: "Artemis_IFEFFIT"
I:
  dataset: XASRef_15
  spectra: 15
  noise: {type: gaussian, sigma_chi: 0.005}
  scenario: ideal
O: [R_factor, bond_distance_RMSE_A]
epsilon:
  R_factor_max: 0.025
  bond_distance_RMSE_max: 0.03
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Fe K-edge 7000–8200 eV covers k = 2–14 Å⁻¹ | PASS |
| S2 | κ ≈ 10 for 1st shell Fe-O with k³-weighted χ | PASS |
| S3 | IFEFFIT fitting converges within 30 iterations | PASS |
| S4 | R-factor ≤ 0.025 and RMSE ≤ 0.03 Å feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xas_exafs/benchmark_s1.yaml
spec_ref: sha256:<spec147_hash>
principle_ref: sha256:<p147_hash>
dataset:
  name: XASRef_15
  spectra: 15
  energy_points: 600
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Shell-by-Shell
    params: {shells: 1, paths: FEFF}
    results: {R_factor: 0.03, bond_distance_RMSE_A: 0.025}
  - solver: IFEFFIT-Multi
    params: {shells: 3, paths: FEFF}
    results: {R_factor: 0.015, bond_distance_RMSE_A: 0.015}
  - solver: EXAFS-Wavelet
    params: {morlet_sigma: 1.0}
    results: {R_factor: 0.012, bond_distance_RMSE_A: 0.010}
quality_scoring:
  - {max_R: 0.012, Q: 1.00}
  - {max_R: 0.02, Q: 0.90}
  - {max_R: 0.03, Q: 0.80}
  - {max_R: 0.05, Q: 0.75}
```

**Baseline solver:** IFEFFIT-Multi — R-factor 0.015
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | R-factor | Bond RMSE (Å) | Runtime | Q |
|--------|----------|----------------|---------|---|
| Shell-by-Shell | 0.03 | 0.025 | 10 s | 0.80 |
| IFEFFIT-Multi | 0.015 | 0.015 | 1 min | 0.90 |
| EXAFS-Wavelet | 0.012 | 0.010 | 2 min | 1.00 |
| DL-XAS (XASNet) | 0.014 | 0.012 | 2 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Wavelet):   500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p147_hash>",
  "h_s": "sha256:<spec147_hash>",
  "h_b": "sha256:<bench147_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.025, "ratio": 0.48},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep xas_exafs
pwm-node verify xas_exafs/xasref_s1.yaml
pwm-node mine xas_exafs/xasref_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
