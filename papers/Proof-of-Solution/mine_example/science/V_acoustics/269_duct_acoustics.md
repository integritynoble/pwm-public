# Principle #269 — Duct Acoustics

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Textbook (δ=1)
**DAG:** E.hermitian → L.hamiltonian → ∫.modal |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→L.hamiltonian→∫.modal    duct_acou   circular_duct_modes  mode-match
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DUCT ACOUSTICS                      P = (E,G,W,C)   Principle #269 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ p(x,r,θ) = Σₘₙ Aₘₙ Jₘ(αₘₙr) eⁱᵐᶿ eⁱᵏˣx            │
│        │ Acoustic mode decomposition in cylindrical ducts       │
│        │ Forward: given duct geometry, freq → modal propagation │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [L.hamiltonian] ──→ [∫.modal]        │
│        │ eigensolve  linear-op  integrate                       │
│        │ V={E.hermitian, L.hamiltonian, ∫.modal}  A={E.hermitian→L.hamiltonian, L.hamiltonian→∫.modal}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Sturm-Liouville modes in cross-section)│
│        │ Uniqueness: YES (complete modal expansion)             │
│        │ Stability: evanescent modes decay below cutoff         │
│        │ Mismatch: mean flow effects, liner impedance errors    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖p−p_ref‖/‖p_ref‖ (primary)    │
│        │ q = spectral (modal), 2.0 (FEM cross-section)        │
│        │ T = {modal_amplitude_error, TL_error}                  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Duct geometry and impedance BC well-defined; cutoff frequencies known | PASS |
| S2 | Complete modal expansion in uniform duct cross-section | PASS |
| S3 | Mode-matching converges with number of modes included | PASS |
| S4 | Transmission loss error bounded by truncation analysis | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# duct_acou/circular_duct_modes.yaml
principle_ref: sha256:<p269_hash>
omega:
  duct: {type: circular, radius: 0.1, length: 2.0}
  frequency_range: [100, 5000]  # Hz
E:
  forward: "modal decomposition in hard-walled circular duct"
  wall: rigid
I:
  scenario: circular_duct_modes
  num_modes: [5, 10, 20]
O: [TL_error_dB, modal_amplitude_L2]
epsilon:
  TL_error_max: 0.5  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Duct radius 0.1 m; first cutoff at ~1 kHz for hard walls | PASS |
| S2 | Analytic Bessel-function modes for circular cross-section | PASS |
| S3 | 20 modes sufficient below 5 kHz | PASS |
| S4 | TL error < 0.5 dB with all propagating modes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# duct_acou/benchmark_circular_duct.yaml
spec_ref: sha256:<spec269_hash>
principle_ref: sha256:<p269_hash>
dataset:
  name: circular_duct_reference
  reference: "Analytic Bessel-function modal solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Mode-matching (5 modes)
    params: {N_modes: 5}
    results: {TL_error: 2.8, amplitude_L2: 5.2e-3}
  - solver: Mode-matching (10 modes)
    params: {N_modes: 10}
    results: {TL_error: 0.3, amplitude_L2: 8.5e-5}
  - solver: Mode-matching (20 modes)
    params: {N_modes: 20}
    results: {TL_error: 0.02, amplitude_L2: 3.1e-7}
quality_scoring:
  - {min_TL_err: 0.05, Q: 1.00}
  - {min_TL_err: 0.5, Q: 0.90}
  - {min_TL_err: 2.0, Q: 0.80}
  - {min_TL_err: 5.0, Q: 0.75}
```

**Baseline solver:** Mode-matching (10 modes) — TL error 0.3 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | TL Error (dB) | Amplitude L2 | Runtime | Q |
|--------|---------------|--------------|---------|---|
| Mode-matching (5) | 2.8 | 5.2e-3 | 0.1 s | 0.75 |
| Mode-matching (10) | 0.3 | 8.5e-5 | 0.2 s | 0.90 |
| Mode-matching (20) | 0.02 | 3.1e-7 | 0.5 s | 1.00 |
| FEM cross-section | 0.05 | 5.0e-6 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case: 100 × 1.00 = 100 PWM
Floor:     100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p269_hash>",
  "h_s": "sha256:<spec269_hash>",
  "h_b": "sha256:<bench269_hash>",
  "r": {"residual_norm": 0.02, "error_bound": 0.5, "ratio": 0.04},
  "c": {"fitted_rate": 2.98, "theoretical_rate": 3.0, "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep duct_acou
pwm-node verify duct_acou/circular_duct_modes.yaml
pwm-node mine duct_acou/circular_duct_modes.yaml
pwm-node inspect sha256:<cert_hash>
```
