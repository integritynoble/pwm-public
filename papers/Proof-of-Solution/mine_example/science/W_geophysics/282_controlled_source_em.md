# Principle #282 — Controlled-Source EM (CSEM)

**Domain:** Geophysics | **Carrier:** N/A (EM inverse) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → L.impedance → S.surface |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.impedance→S.surface      csem-inv    marine-2D         GN/NLCG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONTROLLED-SOURCE EM (CSEM)      P = (E,G,W,C)   Principle #282│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇×H = σE + J_s ;  ∇×E = −iωμ₀H  (freq-domain Maxwell)│
│        │ J_s = controlled source (HED at seafloor)              │
│        │ Forward: given σ(x) → solve for E,H at receivers       │
│        │ Inverse: given E_x(offset,ω) → recover σ(x,z)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.impedance] ──→ [S.surface]             │
│        │ derivative  linear-op  sample                          │
│        │ V={∂.time, L.impedance, S.surface}  A={∂.time→L.impedance, L.impedance→S.surface}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Maxwell diffusion with source)         │
│        │ Uniqueness: improved over MT by active source control   │
│        │ Stability: sensitive to water depth & resistor thickness│
│        │ Mismatch: airwave contamination, anisotropy, bathymetry │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖log σ_rec − log σ_true‖₂ / ‖log σ_true‖₂        │
│        │ q = 1.0 (smooth), 2.0 (sharp-boundary)               │
│        │ T = {data_misfit, normalized_amplitude, phase_error}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Maxwell equations with source term dimensionally correct | PASS |
| S2 | FE forward solver stable for diffusive regime at 0.1–10 Hz | PASS |
| S3 | Gauss-Newton converges for marine CSEM with 20 receivers | PASS |
| S4 | Log-resistivity error bounded by offset range and noise floor | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# csem_inv/marine_2d_s1_ideal.yaml
principle_ref: sha256:<p282_hash>
omega:
  grid: [200, 80]
  domain: marine_2D
  frequencies: [0.25, 0.75, 1.25]  # Hz
E:
  forward: "2-D FE for freq-domain Maxwell (HED source)"
  receivers: 20
  offsets: [1000, 12000]  # metres
  noise_floor: 1.0e-15  # V/Am²
B:
  water_depth: 1000  # metres
  water_resistivity: 0.3  # Ohm·m
  seabed: 1.0  # Ohm·m
I:
  scenario: thin_resistive_layer
  target_resistivity: 100  # Ohm·m
  target_depth: 1500  # metres below seafloor
  target_thickness: 50  # metres
O: [log_resistivity_L2, amplitude_misfit, phase_misfit]
epsilon:
  L2_error_max: 1.0e-1
  misfit_max: 1.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3 frequencies × 20 receivers = 60 complex data; grid adequate | PASS |
| S2 | Thin resistive layer at 1.5 km detectable at 0.25 Hz | PASS |
| S3 | GN with regularisation converges in <30 iterations | PASS |
| S4 | Log-resistivity error < 10% for 100 Ω·m target | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# csem_inv/benchmark_marine.yaml
spec_ref: sha256:<spec282_hash>
principle_ref: sha256:<p282_hash>
dataset:
  name: synthetic_thin_resistor
  reference: "Marine CSEM, 20 receivers, 3 frequencies"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Occam-1D
    params: {per_receiver: true}
    results: {L2_error: 1.8e-1, misfit: 1.03}
  - solver: NLCG-2D
    params: {iterations: 80, tau: 5.0}
    results: {L2_error: 8.2e-2, misfit: 1.01}
  - solver: Gauss-Newton-2D
    params: {iterations: 20, lambda: 1e-2}
    results: {L2_error: 6.5e-2, misfit: 1.00}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 7.0e-2, Q: 0.90}
  - {min_L2: 1.2e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** NLCG-2D — L2 error 8.2×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Misfit | Runtime | Q |
|--------|----------|--------|---------|---|
| Occam-1D | 1.8e-1 | 1.03 | 5 s | 0.75 |
| NLCG-2D | 8.2e-2 | 1.01 | 180 s | 0.90 |
| GN-2D | 6.5e-2 | 1.00 | 300 s | 0.90 |
| Joint CSEM+MT | 2.5e-2 | 1.00 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (joint): 500 × 1.00 = 500 PWM
Floor:             500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p282_hash>",
  "h_s": "sha256:<spec282_hash>",
  "h_b": "sha256:<bench282_hash>",
  "r": {"residual_norm": 2.5e-2, "error_bound": 1.0e-1, "ratio": 0.25},
  "c": {"fitted_rate": 1.15, "theoretical_rate": 1.0, "K": 4},
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
pwm-node benchmarks | grep csem_inv
pwm-node verify csem_inv/marine_2d_s1_ideal.yaml
pwm-node mine csem_inv/marine_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
