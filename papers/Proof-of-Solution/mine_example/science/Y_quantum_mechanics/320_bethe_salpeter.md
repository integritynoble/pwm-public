# Principle #320 — Bethe-Salpeter Equation (Excitons)

**Domain:** Quantum Mechanics | **Carrier:** exciton | **Difficulty:** Frontier (δ=5)
**DAG:** E.hermitian → K.green → L.dense |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→K.green→L.dense      BSE-exciton Si/LiF-optical     Haydock/diag
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BETHE-SALPETER EQUATION        P = (E,G,W,C)   Principle #320  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ (ε_ck − ε_vk)A^S_cvk + Σ K_cvk,c'v'k' A^S_c'v'k' = Ω_S A^S│
│        │ K = K_x(exchange) + K_d(direct/screened)              │
│        │ ε₂(ω) = (8π²/Ω) Σ_S |⟨0|v|S⟩|² δ(ω−Ω_S)            │
│        │ Forward: given GW bands, W → solve BSE → ε₂(ω)       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [K.green] ──→ [L.dense]              │
│        │ eigensolve  kernel  linear-op                          │
│        │ V={E.hermitian, K.green, L.dense}  A={E.hermitian→K.green, K.green→L.dense}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (finite-dim BSE Hamiltonian)            │
│        │ Uniqueness: YES (eigenvalues of Hermitian BSE kernel)  │
│        │ Stability: κ ~ exciton binding energy⁻¹               │
│        │ Mismatch: k-mesh, screening approximation, band count │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ε₂_peak^BSE − ε₂_peak^expt| (primary, eV)       │
│        │ q = N/A (many-body; convergence w.r.t. k, bands)     │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | BSE kernel K constructed consistently from GW quantities | PASS |
| S2 | Hermitian BSE matrix guarantees real exciton energies | PASS |
| S3 | Haydock recursion and direct diag converge with k-mesh | PASS |
| S4 | Optical spectrum peaks measurable against experiment | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# bse/lif_exciton_s1_ideal.yaml
principle_ref: sha256:<p320_hash>
omega:
  k_grid: [8, 8, 8]
  n_val: 4
  n_cond: 4
E:
  forward: "BSE: (ε_c-ε_v)A + KA = ΩA"
  starting_point: G₀W₀@LDA
B:
  periodic: true
  pseudopotential: PAW
I:
  scenario: LiF_optical_absorption
  expt_exciton_peak: 12.6  # eV
  expt_binding_energy: 1.6  # eV
O: [optical_spectrum, exciton_energies, binding_energy]
epsilon:
  peak_error_max: 0.2  # eV
  binding_error_max: 0.3  # eV
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8×8×8 k-grid with 4+4 bands resolves LiF exciton | PASS |
| S2 | LiF strongly bound exciton well-characterized (1.6 eV binding) | PASS |
| S3 | BSE converges with k-mesh and band count | PASS |
| S4 | Peak position error < 0.2 eV achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# bse/benchmark_lif.yaml
spec_ref: sha256:<spec320_hash>
principle_ref: sha256:<p320_hash>
dataset:
  name: LiF_optical_experiment
  reference: "Roessler & Walker (1967) reflectance spectroscopy"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BSE (direct diag)
    params: {k: [8,8,8], n_bands: 8}
    results: {peak_error: 0.15, binding_error: 0.20}
  - solver: BSE (Haydock)
    params: {k: [8,8,8], n_iter: 200}
    results: {peak_error: 0.18, binding_error: 0.25}
  - solver: TD-DFT (ALDA)
    params: {k: [8,8,8]}
    results: {peak_error: 1.50, binding_error: 1.60}
quality_scoring:
  - {min_peak_error: 0.05, Q: 1.00}
  - {min_peak_error: 0.15, Q: 0.90}
  - {min_peak_error: 0.30, Q: 0.80}
  - {min_peak_error: 0.50, Q: 0.75}
```

**Baseline solver:** BSE direct diag — peak error 0.15 eV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Peak Error (eV) | Binding Error (eV) | Runtime | Q |
|--------|----------------|--------------------|---------|----|
| TD-DFT (ALDA) | 1.50 | 1.60 | 1 h | 0.75 |
| BSE (Haydock) | 0.18 | 0.25 | 6 h | 0.90 |
| BSE (direct diag) | 0.15 | 0.20 | 12 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (BSE diag): 500 × 0.90 = 450 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p320_hash>",
  "h_s": "sha256:<spec320_hash>",
  "h_b": "sha256:<bench320_hash>",
  "r": {"residual_norm": 0.15, "error_bound": 0.30, "ratio": 0.50},
  "c": {"fitted_rate": 1.0, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep bse
pwm-node verify bse/lif_exciton_s1_ideal.yaml
pwm-node mine bse/lif_exciton_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
