# Principle #275 — Receiver Function Analysis

**Domain:** Geophysics | **Carrier:** N/A (deconvolution-based) | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → L.impedance → ∫.temporal |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.impedance→∫.temporal      recv-fn     crustal-model     deconv+inv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RECEIVER FUNCTION ANALYSIS       P = (E,G,W,C)   Principle #275│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ RF(t) = Z⁻¹{V(ω)/H(ω)}  (spectral deconvolution)     │
│        │ V = vertical, H = radial component of teleseismic P    │
│        │ Forward: given Vs(z) → synthetic RF via propagator     │
│        │ Inverse: given RF(t) → recover crustal Vs(z) profile   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.impedance] ──→ [∫.temporal]            │
│        │ derivative  linear-op  integrate                       │
│        │ V={∂.time, L.impedance, ∫.temporal}  A={∂.time→L.impedance, L.impedance→∫.temporal}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (deconvolution well-defined with reg)   │
│        │ Uniqueness: non-unique; trade-off Vs/depth             │
│        │ Stability: water-level deconv stabilises spectrum      │
│        │ Mismatch: noise, lateral heterogeneity, multiples      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖RF_syn − RF_obs‖₂ / ‖RF_obs‖₂ (waveform misfit) │
│        │ q = 1.0 (linearised), 2.0 (NA/MCMC)                  │
│        │ T = {waveform_misfit, Moho_depth_error, Vp/Vs_ratio}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Deconvolution dimensions consistent; water-level regularised | PASS |
| S2 | Propagator matrix forward well-posed for layered media | PASS |
| S3 | Neighbourhood algorithm converges for 5-layer crustal models | PASS |
| S4 | Waveform misfit bounded by SNR and number of stacked events | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# recv_fn/crustal_s1_ideal.yaml
principle_ref: sha256:<p275_hash>
omega:
  layers: 5
  depth_max: 60.0  # km
  time_window: [0, 30.0]  # seconds
E:
  forward: "propagator matrix for P-to-S conversion"
  gauss_width: 2.5
  water_level: 0.01
B:
  half_space: {Vs: 4.5, Vp: 8.1, rho: 3300}
I:
  scenario: continental_crust
  Moho_depth: 35.0
  events: 50
O: [waveform_misfit, Moho_depth_error, Vp_Vs_ratio]
epsilon:
  waveform_misfit_max: 5.0e-2
  Moho_error_max: 2.0  # km
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 events provide adequate azimuthal coverage for stacking | PASS |
| S2 | 5-layer model with Moho at 35 km has unique Ps arrival | PASS |
| S3 | NA inversion converges for 5 parameters in <5000 samples | PASS |
| S4 | Waveform misfit < 5% with 50-event stack | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# recv_fn/benchmark_crustal.yaml
spec_ref: sha256:<spec275_hash>
principle_ref: sha256:<p275_hash>
dataset:
  name: synthetic_continental_crust
  reference: "5-layer crustal model, 50 stacked events"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: H-kappa-stacking
    params: {H_range: [25,50], kappa_range: [1.6,1.9]}
    results: {Moho_error: 1.5, Vp_Vs_error: 0.02}
  - solver: Neighbourhood-Algorithm
    params: {samples: 5000, layers: 5}
    results: {waveform_misfit: 3.8e-2, Moho_error: 1.2}
  - solver: MCMC-TransD
    params: {chains: 4, samples: 20000}
    results: {waveform_misfit: 2.9e-2, Moho_error: 0.8}
quality_scoring:
  - {min_misfit: 1.0e-2, Q: 1.00}
  - {min_misfit: 3.0e-2, Q: 0.90}
  - {min_misfit: 5.0e-2, Q: 0.80}
  - {min_misfit: 1.0e-1, Q: 0.75}
```

**Baseline solver:** NA — waveform misfit 3.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Waveform Misfit | Moho Error (km) | Runtime | Q |
|--------|-----------------|------------------|---------|---|
| H-κ stacking | — | 1.5 | 1 s | 0.80 |
| NA | 3.8e-2 | 1.2 | 20 s | 0.90 |
| MCMC-TransD | 2.9e-2 | 0.8 | 300 s | 0.90 |
| Joint RF+SWD | 8.5e-3 | 0.4 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Joint): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p275_hash>",
  "h_s": "sha256:<spec275_hash>",
  "h_b": "sha256:<bench275_hash>",
  "r": {"residual_norm": 8.5e-3, "error_bound": 5.0e-2, "ratio": 0.17},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep recv_fn
pwm-node verify recv_fn/crustal_s1_ideal.yaml
pwm-node mine recv_fn/crustal_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
