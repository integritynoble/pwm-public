# Principle #263 — Underwater Acoustics (Normal Modes)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian → L.hamiltonian → ∫.modal |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→L.hamiltonian→∫.modal    uw_modes     pekeris_waveguide   KRAKEN
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  UNDERWATER ACOUSTICS (NORMAL MODES) P = (E,G,W,C)   Principle #263 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ p(r,z) = Σₙ φₙ(z_s)φₙ(z) H₀⁽¹⁾(kₙr)/√(kₙr)        │
│        │ Depth eigenmodes of the ocean waveguide                │
│        │ Forward: given c(z), boundaries → compute modal field  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [L.hamiltonian] ──→ [∫.modal]        │
│        │ eigensolve  linear-op  integrate                       │
│        │ V={E.hermitian, L.hamiltonian, ∫.modal}  A={E.hermitian→L.hamiltonian, L.hamiltonian→∫.modal}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Sturm-Liouville eigenvalue problem)    │
│        │ Uniqueness: YES (complete orthogonal mode set)         │
│        │ Stability: mode stripping at long range; leaky modes   │
│        │ Mismatch: range dependence neglected in basic form     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖p−p_ref‖/‖p_ref‖ (primary)    │
│        │ q = spectral convergence with number of modes         │
│        │ T = {TL_rms_error, mode_eigenvalue_error}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sound speed profile and boundary conditions well-defined | PASS |
| S2 | Sturm-Liouville theory guarantees complete discrete mode set | PASS |
| S3 | KRAKEN normal-mode solver converges with depth discretization | PASS |
| S4 | TL error bounded by number of modes included | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# uw_modes/pekeris_waveguide.yaml
principle_ref: sha256:<p263_hash>
omega:
  depth: 100  # meters (shallow water)
  range: 10000  # meters
  source_depth: 50
  receiver_depth: 50
E:
  forward: "normal-mode expansion in range-independent waveguide"
  c_water: 1500  # m/s
  c_bottom: 1800  # m/s
  rho_bottom: 1.8  # g/cm³
I:
  scenario: pekeris_waveguide
  num_modes: [5, 10, 20, 50]
O: [TL_rms_error_dB, mode_eigenvalue_error]
epsilon:
  TL_rms_max: 1.0  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Pekeris waveguide well-defined; isovelocity water column | PASS |
| S2 | Analytic mode functions available for isovelocity Pekeris | PASS |
| S3 | 20 modes sufficient for convergence at 100 Hz in 100 m | PASS |
| S4 | TL rms < 1 dB achievable with all propagating modes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# uw_modes/benchmark_pekeris.yaml
spec_ref: sha256:<spec263_hash>
principle_ref: sha256:<p263_hash>
dataset:
  name: pekeris_waveguide_reference
  reference: "Analytic Pekeris waveguide solution (exact eigenvalues)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: KRAKEN (5 modes)
    params: {num_modes: 5}
    results: {TL_rms: 3.8, eigenvalue_error: 1.2e-4}
  - solver: KRAKEN (20 modes)
    params: {num_modes: 20}
    results: {TL_rms: 0.5, eigenvalue_error: 2.1e-6}
  - solver: KRAKEN (50 modes)
    params: {num_modes: 50}
    results: {TL_rms: 0.08, eigenvalue_error: 8.5e-8}
quality_scoring:
  - {min_TL_rms: 0.1, Q: 1.00}
  - {min_TL_rms: 1.0, Q: 0.90}
  - {min_TL_rms: 3.0, Q: 0.80}
  - {min_TL_rms: 5.0, Q: 0.75}
```

**Baseline solver:** KRAKEN (20 modes) — TL rms 0.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | TL rms (dB) | Eigenvalue Error | Runtime | Q |
|--------|-------------|------------------|---------|---|
| KRAKEN (5 modes) | 3.8 | 1.2e-4 | 1 s | 0.75 |
| KRAKEN (20 modes) | 0.5 | 2.1e-6 | 3 s | 0.90 |
| KRAKEN (50 modes) | 0.08 | 8.5e-8 | 8 s | 1.00 |
| Spectral-element modes | 0.03 | 1.2e-9 | 12 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p263_hash>",
  "h_s": "sha256:<spec263_hash>",
  "h_b": "sha256:<bench263_hash>",
  "r": {"residual_norm": 0.03, "error_bound": 1.0, "ratio": 0.03},
  "c": {"fitted_rate": 2.98, "theoretical_rate": 3.0, "K": 4},
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
pwm-node benchmarks | grep uw_modes
pwm-node verify uw_modes/pekeris_waveguide.yaml
pwm-node mine uw_modes/pekeris_waveguide.yaml
pwm-node inspect sha256:<cert_hash>
```
