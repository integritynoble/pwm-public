# Principle #284 — Induced Polarization (IP)

**Domain:** Geophysics | **Carrier:** N/A (complex resistivity inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → L.sparse → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→L.sparse→O.tikhonov      ip-inv      chargeability-2D  GN-smooth
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INDUCED POLARIZATION (IP)        P = (E,G,W,C)   Principle #284│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ*(ω) = σ₀[1 − m(1 − 1/(1+(iωτ)^c))]  (Cole-Cole)   │
│        │ m = chargeability; τ = time constant; c = exponent     │
│        │ Forward: given σ*(x,ω) → solve complex DC → V(t)      │
│        │ Inverse: given V(t) decay → recover m(x,z), τ(x,z)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [L.sparse] ──→ [O.tikhonov]              │
│        │ kernel  linear-op  optimize                            │
│        │ V={K.green, L.sparse, O.tikhonov}  A={K.green→L.sparse, L.sparse→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (complex-valued extension of ERT)       │
│        │ Uniqueness: trade-off between m and σ₀                 │
│        │ Stability: EM coupling noise at long offsets            │
│        │ Mismatch: electrode polarization, EM coupling          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖m_rec − m_true‖₂ / ‖m_true‖₂ (relative L2)      │
│        │ q = 1.0 (linearised), 2.0 (spectral IP)              │
│        │ T = {chargeability_misfit, phase_error, spectral_fit}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Cole-Cole model dimensionally consistent; complex conductivity valid | PASS |
| S2 | Sequential ERT → IP inversion ensures stable chargeability recovery | PASS |
| S3 | GN converges for chargeability after resistivity model is fixed | PASS |
| S4 | Chargeability error bounded by signal-to-noise of secondary voltage | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ip_inv/chargeability_2d_s1_ideal.yaml
principle_ref: sha256:<p284_hash>
omega:
  grid: [96, 24]
  domain: surface_2D
  electrodes: 48
  spacing: 2.0  # metres
E:
  forward: "complex DC FE solver with Cole-Cole model"
  array: dipole_dipole
  time_windows: 10  # decay curve samples
  noise_std: 3%  # of apparent chargeability
B:
  background_m: 0.01
  background_resistivity: 100
I:
  scenario: disseminated_sulphide
  target_chargeability: 0.15
  target_resistivity: 50
  depth: [5, 15]
O: [L2_chargeability_error, RMS_IP_misfit, depth_recovery]
epsilon:
  L2_error_max: 1.0e-1
  RMS_max: 1.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1128 IP measurements; 10 time windows per datum | PASS |
| S2 | Sequential ERT→IP inversion well-posed after resistivity fix | PASS |
| S3 | GN converges in <7 iterations for chargeability | PASS |
| S4 | L2 error < 10% for m=0.15 target at 5–15 m | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ip_inv/benchmark_sulphide.yaml
spec_ref: sha256:<spec284_hash>
principle_ref: sha256:<p284_hash>
dataset:
  name: synthetic_disseminated_sulphide
  reference: "48-electrode DD survey with IP decay"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: L2-smooth-GN
    params: {iterations: 7, lambda: 5}
    results: {L2_error: 9.5e-2, RMS: 1.03}
  - solver: Spectral-IP-GN
    params: {Cole_Cole_params: 4, iterations: 10}
    results: {L2_error: 7.2e-2, RMS: 1.01}
  - solver: Joint-ERT-IP
    params: {coupled: true, iterations: 12}
    results: {L2_error: 5.5e-2, RMS: 1.00}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 6.0e-2, Q: 0.90}
  - {min_L2: 1.0e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** L2-smooth-GN — L2 error 9.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | RMS | Runtime | Q |
|--------|----------|-----|---------|---|
| L2-smooth-GN | 9.5e-2 | 1.03 | 8 s | 0.80 |
| Spectral-IP-GN | 7.2e-2 | 1.01 | 20 s | 0.90 |
| Joint-ERT-IP | 5.5e-2 | 1.00 | 30 s | 0.90 |
| 3D-spectral-IP | 2.2e-2 | 1.00 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (3D-SIP): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p284_hash>",
  "h_s": "sha256:<spec284_hash>",
  "h_b": "sha256:<bench284_hash>",
  "r": {"residual_norm": 2.2e-2, "error_bound": 1.0e-1, "ratio": 0.22},
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
pwm-node benchmarks | grep ip_inv
pwm-node verify ip_inv/chargeability_2d_s1_ideal.yaml
pwm-node mine ip_inv/chargeability_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
