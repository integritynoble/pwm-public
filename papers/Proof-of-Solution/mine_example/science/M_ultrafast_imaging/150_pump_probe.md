# Principle #150 — Pump-Probe Microscopy

**Domain:** Ultrafast Imaging | **Carrier:** Photon (ultrafast) | **Difficulty:** Research (δ=5)
**DAG:** G.pulse.laser --> N.pointwise --> integral.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->N.pointwise-->integral.temporal    PumpProbe   PPSim-12           Fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PUMP-PROBE MICROSCOPY   P = (E, G, W, C)   Principle #150     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔI(r, τ) = Σ_k A_k(r) · exp(−τ/τ_k) + B(r)          │
│        │ Pump excites; probe measures transient absorption/refl.│
│        │ Multi-exponential decay reveals ultrafast dynamics      │
│        │ Inverse: extract A_k(r), τ_k from delay-scan images   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [N.pointwise] --> [integral.temporal]│
│        │  PumpProbe  TransientResp  DelayScan                   │
│        │ V={G.pulse.laser, N.pointwise, integral.temporal}  A={G.pulse.laser-->N.pointwise, N.pointwise-->integral.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (transient signal from excited states)  │
│        │ Uniqueness: YES (≥ 2N delay points for N lifetimes)    │
│        │ Stability: κ ≈ 10 (distinct τ_k), κ ≈ 60 (overlapping)│
│        │ Mismatch: coherent artifacts, thermal effects, jitter  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = lifetime RMSE (primary), amplitude RMSE (secondary)│
│        │ q = 2.0 (Levenberg-Marquardt for multi-exponential)    │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Delay range covers ≥ 5τ_max; step size ≤ τ_min/5 for adequate sampling | PASS |
| S2 | ≥ 3× more delay points than fitting parameters ensures over-determination | PASS |
| S3 | LM fitting converges within 50 iterations for ≤ 3 exponential components | PASS |
| S4 | Lifetime RMSE ≤ 10% achievable at ΔI/I SNR > 50 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pump_probe/ppsim_s1.yaml
principle_ref: sha256:<p150_hash>
omega:
  grid: [128, 128]
  pixel_um: 0.3
  pump_nm: 400
  probe_nm: 800
  delay_range_ps: [0, 500]
  delay_points: 64
  pulse_fs: 100
E:
  forward: "dI(r, tau) = sum_k A_k(r) * exp(-tau/tau_k) + B(r)"
  fitting: "Levenberg-Marquardt"
I:
  dataset: PPSim_12
  images: 12
  noise: {type: gaussian, sigma_rel: 0.01}
  scenario: ideal
O: [lifetime_RMSE_pct, amplitude_RMSE_pct]
epsilon:
  lifetime_RMSE_max: 12.0
  amplitude_RMSE_max: 10.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 0–500 ps with 64 delays and 100 fs pulse covers ps–ns dynamics | PASS |
| S2 | 64 delay points for ≤ 3 lifetimes gives 10× over-determination | PASS |
| S3 | LM converges within 30 iterations at σ_rel = 0.01 | PASS |
| S4 | Lifetime RMSE ≤ 12% feasible at 1% relative noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pump_probe/benchmark_s1.yaml
spec_ref: sha256:<spec150_hash>
principle_ref: sha256:<p150_hash>
dataset:
  name: PPSim_12
  maps: 12
  delay_points: 64
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Mono-Exp
    params: {components: 1}
    results: {lifetime_RMSE_pct: 25.0, amplitude_RMSE_pct: 20.0}
  - solver: LM-MultiExp
    params: {components: 3}
    results: {lifetime_RMSE_pct: 8.0, amplitude_RMSE_pct: 6.0}
  - solver: SVD-GlobalFit
    params: {components: 3, global: true}
    results: {lifetime_RMSE_pct: 5.0, amplitude_RMSE_pct: 4.0}
quality_scoring:
  - {max_RMSE: 5.0, Q: 1.00}
  - {max_RMSE: 8.0, Q: 0.90}
  - {max_RMSE: 12.0, Q: 0.80}
  - {max_RMSE: 20.0, Q: 0.75}
```

**Baseline solver:** LM-MultiExp — lifetime RMSE 8.0%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Lifetime RMSE (%) | Amp. RMSE (%) | Runtime | Q |
|--------|---------------------|---------------|---------|---|
| Mono-Exp | 25.0 | 20.0 | 1 s | 0.75 |
| LM-MultiExp | 8.0 | 6.0 | 30 s | 0.90 |
| SVD-GlobalFit | 5.0 | 4.0 | 2 min | 1.00 |
| DL-PumpProbe | 4.5 | 3.5 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (SVD/DL):    500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p150_hash>",
  "h_s": "sha256:<spec150_hash>",
  "h_b": "sha256:<bench150_hash>",
  "r": {"residual_norm": 0.045, "error_bound": 0.10, "ratio": 0.45},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep pump_probe
pwm-node verify pump_probe/ppsim_s1.yaml
pwm-node mine pump_probe/ppsim_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
