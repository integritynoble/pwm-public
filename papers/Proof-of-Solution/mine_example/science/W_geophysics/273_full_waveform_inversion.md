# Principle #273 — Full Waveform Inversion (FWI)

**Domain:** Geophysics | **Carrier:** N/A (PDE-constrained inverse) | **Difficulty:** Hard (δ=5)
**DAG:** G.point → ∂.time → ∂.space.laplacian → B.absorbing |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→∂.time→∂.space.laplacian→B.absorbing      fwi-2d      Marmousi          adjoint-state
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FULL WAVEFORM INVERSION (FWI)    P = (E,G,W,C)   Principle #273│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂²u/∂t² = v(x)²∇²u + s(t)δ(x−x_s)  (acoustic wave)  │
│        │ d_obs = S u(x_r, t)  (observed data at receivers)      │
│        │ min_v J(v) = ½‖d_syn(v) − d_obs‖²                     │
│        │ Forward: wave equation; Inverse: recover v(x)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [∂.time] ──→ [∂.space.laplacian] ──→ [B.absorbing] │
│        │ source  derivative  derivative  boundary               │
│        │ V={G.point, ∂.time, ∂.space.laplacian, B.absorbing}  A={G.point→∂.time, ∂.time→∂.space.laplacian, ∂.space.laplacian→B.absorbing}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (least-squares minimiser exists)        │
│        │ Uniqueness: NO in general; cycle-skipping ambiguity    │
│        │ Stability: ill-posed; multi-scale + reg needed         │
│        │ Mismatch: source wavelet error, cycle-skipping         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖v_rec − v_true‖₂ / ‖v_true‖₂ (relative L2)      │
│        │ q = 1.0 (gradient descent), 2.0 (L-BFGS)             │
│        │ T = {data_misfit, model_update_norm, freq_bands}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wave equation PDE well-formed; velocity/data dimensions consistent | PASS |
| S2 | Adjoint-state gradient correct; multi-scale mitigates cycle-skipping | PASS |
| S3 | L-BFGS converges for Marmousi at low-to-high frequency sweep | PASS |
| S4 | Relative L2 velocity error bounded by frequency content and aperture | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fwi/marmousi_s1_ideal.yaml
principle_ref: sha256:<p273_hash>
omega:
  grid: [461, 151]
  domain: marmousi_2D
  time: [0, 3.0]
  dt: 0.001
E:
  forward: "∂²u/∂t² = v²∇²u + s(t)δ(x−x_s)"
  freq_bands: [3, 5, 8, 12]
  source_wavelet: ricker
B:
  top: free_surface
  sides: absorbing_PML
  bottom: absorbing_PML
I:
  scenario: Marmousi
  shots: 46
  receivers_per_shot: 461
O: [L2_velocity_error, data_misfit, structural_similarity]
epsilon:
  L2_error_max: 5.0e-2
  misfit_reduction: 0.95
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid spacing < λ_min/10 at 12 Hz; PML absorbs >99% | PASS |
| S2 | Multi-scale 3→12 Hz avoids cycle-skipping for Marmousi | PASS |
| S3 | L-BFGS with 30 iterations per band converges | PASS |
| S4 | L2 velocity error < 5% achievable with 46-shot coverage | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fwi/benchmark_marmousi.yaml
spec_ref: sha256:<spec273_hash>
principle_ref: sha256:<p273_hash>
dataset:
  name: Marmousi_synthetic
  reference: "Marmousi model (Versteeg 1994)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gradient-Descent
    params: {iterations: 100, freq_bands: [3,5,8,12]}
    results: {L2_error: 8.2e-2, misfit_red: 0.88}
  - solver: L-BFGS
    params: {iterations: 30_per_band, freq_bands: [3,5,8,12]}
    results: {L2_error: 4.1e-2, misfit_red: 0.96}
  - solver: Gauss-Newton
    params: {iterations: 10_per_band, freq_bands: [3,5,8,12]}
    results: {L2_error: 3.2e-2, misfit_red: 0.97}
quality_scoring:
  - {min_L2: 2.0e-2, Q: 1.00}
  - {min_L2: 4.0e-2, Q: 0.90}
  - {min_L2: 6.0e-2, Q: 0.80}
  - {min_L2: 1.0e-1, Q: 0.75}
```

**Baseline solver:** L-BFGS — L2 error 4.1×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Misfit Red. | Runtime | Q |
|--------|----------|-------------|---------|---|
| Gradient-Descent | 8.2e-2 | 0.88 | 2 h | 0.80 |
| L-BFGS | 4.1e-2 | 0.96 | 4 h | 0.90 |
| Gauss-Newton | 3.2e-2 | 0.97 | 12 h | 0.90 |
| GN + TV-reg | 1.8e-2 | 0.98 | 15 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (GN+TV): 500 × 1.00 = 500 PWM
Floor:             500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p273_hash>",
  "h_s": "sha256:<spec273_hash>",
  "h_b": "sha256:<bench273_hash>",
  "r": {"residual_norm": 1.8e-2, "error_bound": 5.0e-2, "ratio": 0.36},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 4},
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
pwm-node benchmarks | grep fwi
pwm-node verify fwi/marmousi_s1_ideal.yaml
pwm-node mine fwi/marmousi_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
