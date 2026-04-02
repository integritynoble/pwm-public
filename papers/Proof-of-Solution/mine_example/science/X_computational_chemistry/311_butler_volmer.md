# Principle #311 — Butler-Volmer Electrochemistry

**Domain:** Computational Chemistry | **Carrier:** N/A (electrode kinetics) | **Difficulty:** Standard (δ=3)
**DAG:** N.exponential → ∂.space → B.electrode |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          η→J→C→T      bv-echem    voltammetry        fit/sim
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BUTLER-VOLMER ELECTROCHEMISTRY   P = (E,G,W,C)   Principle #311│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ j = j₀[exp(αFη/RT) − exp(−(1−α)Fη/RT)]  (BV equation)│
│        │ η = E − E_eq (overpotential); j₀ = exchange current   │
│        │ α = transfer coefficient; F = Faraday constant         │
│        │ Forward: given j₀, α → predict j(η) polarisation curve│
│        │ Inverse: given j(η) data → fit j₀, α                  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.exponential] ──→ [∂.space] ──→ [B.electrode]        │
│        │ nonlinear  derivative  boundary                        │
│        │ V={N.exponential, ∂.space, B.electrode}  A={N.exponential→∂.space, ∂.space→B.electrode}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (BV well-defined for |η| < 1 V)        │
│        │ Uniqueness: YES for single-electron transfer step      │
│        │ Stability: Tafel regime at high |η|; linear at low |η| │
│        │ Mismatch: mass transport, double-layer, multi-step mech│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖j_fit − j_obs‖₂ / ‖j_obs‖₂ (current misfit)     │
│        │ q = 2.0 (NLLS fit converges quadratically)            │
│        │ T = {j0_error, alpha_error, Tafel_slope, iR_drop}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | BV equation dimensionally correct; α ∈ (0,1) physically valid | PASS |
| S2 | Single-step electron transfer uniquely parameterised by j₀ and α | PASS |
| S3 | NLLS fit converges from Tafel-slope initial guess | PASS |
| S4 | j₀ and α errors bounded by ohmic drop correction accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# bv_echem/voltammetry_s1_ideal.yaml
principle_ref: sha256:<p311_hash>
omega:
  potential_range: [-0.5, 0.5]  # V vs E_eq
  scan_rate: 0.050  # V/s
  electrode_area: 0.01  # cm²
E:
  forward: "Butler-Volmer + planar diffusion (Randles-Sevcik)"
  D: 1.0e-5  # cm²/s
  C_bulk: 1.0e-3  # mol/cm³
  n_electrons: 1
B:
  solution_resistance: 10  # Ohm
  iR_compensation: 85%
  temperature: 298  # K
I:
  scenario: quasi_reversible_CV
  true_j0: 1.0e-3  # A/cm²
  true_alpha: 0.50
  noise_std: 1%  # of peak current
O: [j0_error, alpha_error, current_misfit]
epsilon:
  j0_error_max: 1.0e-1  # relative
  alpha_error_max: 0.05  # absolute
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | η range ±0.5 V spans both Tafel and linear regimes | PASS |
| S2 | iR compensation corrects 85% of solution resistance | PASS |
| S3 | NLLS fit converges for quasi-reversible kinetics | PASS |
| S4 | j₀ error < 10%, α error < 0.05 with 1% noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# bv_echem/benchmark_cv.yaml
spec_ref: sha256:<spec311_hash>
principle_ref: sha256:<p311_hash>
dataset:
  name: synthetic_quasi_reversible_CV
  reference: "Simulated CV with known j₀=10⁻³ A/cm², α=0.5"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Tafel-extrapolation
    params: {region: |η|>120mV}
    results: {j0_error: 0.15, alpha_error: 0.08}
  - solver: NLLS-BV-fit
    params: {iR_corrected: true, iterations: 30}
    results: {j0_error: 0.06, alpha_error: 0.03}
  - solver: DigiSim-numerical
    params: {method: implicit_FDM, grid: 1000}
    results: {j0_error: 0.03, alpha_error: 0.015}
quality_scoring:
  - {min_j0_err: 0.01, Q: 1.00}
  - {min_j0_err: 0.05, Q: 0.90}
  - {min_j0_err: 0.10, Q: 0.80}
  - {min_j0_err: 0.20, Q: 0.75}
```

**Baseline solver:** NLLS-BV-fit — j₀ error 6%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | j₀ Error | α Error | Runtime | Q |
|--------|----------|---------|---------|---|
| Tafel-extrap | 0.15 | 0.08 | 0.01 s | 0.80 |
| NLLS-BV | 0.06 | 0.03 | 0.1 s | 0.90 |
| DigiSim-FDM | 0.03 | 0.015 | 1 s | 0.90 |
| Bayesian-CV-fit | 0.008 | 0.004 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p311_hash>",
  "h_s": "sha256:<spec311_hash>",
  "h_b": "sha256:<bench311_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.10, "ratio": 0.08},
  "c": {"fitted_rate": 2.02, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep bv_echem
pwm-node verify bv_echem/voltammetry_s1_ideal.yaml
pwm-node mine bv_echem/voltammetry_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
