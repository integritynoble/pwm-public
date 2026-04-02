# Principle #278 — Earthquake Source Inversion (CMT)

**Domain:** Geophysics | **Carrier:** N/A (moment tensor inverse) | **Difficulty:** Standard (δ=3)
**DAG:** G.point → K.green → O.l2 |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.green→O.l2      cmt-inv     global-Mw5+       lin-inversion
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EARTHQUAKE SOURCE INVERSION (CMT) P = (E,G,W,C)  Principle #278│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u(x,t) = M_ij * G_ij(x,ξ,t)  (representation theorem)│
│        │ M = moment tensor (6 independent components)           │
│        │ Forward: given M, location → synthetic seismograms     │
│        │ Inverse: given waveforms → recover M, centroid, t₀     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.green] ──→ [O.l2]                     │
│        │ source  kernel  optimize                               │
│        │ V={G.point, K.green, O.l2}  A={G.point→K.green, K.green→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (overdetermined linear system)          │
│        │ Uniqueness: YES for >6 well-distributed stations       │
│        │ Stability: κ(G) moderate; sensitive to earth model     │
│        │ Mismatch: 3-D structure, source finiteness              │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖M_rec − M_true‖_F / ‖M_true‖_F  (Frobenius)     │
│        │ q = 2.0 (linear waveform inversion)                   │
│        │ T = {variance_reduction, DC%, location_error}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Moment tensor 6 components; Green's functions dimensionally correct | PASS |
| S2 | Linear system for M given Green's functions; well-posed with >6 stations | PASS |
| S3 | Least-squares inversion converges; variance reduction >80% typical | PASS |
| S4 | Frobenius error bounded by station coverage and earth model accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cmt_inv/global_s1_ideal.yaml
principle_ref: sha256:<p278_hash>
omega:
  stations: 40
  components: 3  # Z, R, T
  period_band: [40, 150]  # seconds
  time_window: 200  # seconds
E:
  forward: "normal-mode summation for Green's functions"
  earth_model: PREM
  source_depth: 15.0  # km
B:
  moment_constraint: deviatoric  # trace(M)=0
I:
  scenario: shallow_thrust_Mw6
  true_M: [[1.2e18, 0.3e18, -0.5e18],
            [0.3e18, -0.8e18, 0.2e18],
            [-0.5e18, 0.2e18, -0.4e18]]
O: [M_error_Frobenius, variance_reduction, DC_percentage]
epsilon:
  M_error_max: 5.0e-2
  VR_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 40 stations × 3 components = 120 data; 6 unknowns well-overdetermined | PASS |
| S2 | PREM Green's functions accurate at 40–150 s periods | PASS |
| S3 | Linear least-squares converges in single step | PASS |
| S4 | M error < 5% with 40 globally distributed stations | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cmt_inv/benchmark_global.yaml
spec_ref: sha256:<spec278_hash>
principle_ref: sha256:<p278_hash>
dataset:
  name: synthetic_shallow_thrust_Mw6
  reference: "40-station global CMT scenario"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linear-LS
    params: {components: ZRT, periods: [40,150]}
    results: {M_error: 3.5e-2, VR: 0.93}
  - solver: Time-domain-CMT
    params: {grid_search: true, dt: 1.0}
    results: {M_error: 2.8e-2, VR: 0.95}
  - solver: W-phase
    params: {periods: [100,500]}
    results: {M_error: 4.2e-2, VR: 0.89}
quality_scoring:
  - {min_VR: 0.98, Q: 1.00}
  - {min_VR: 0.95, Q: 0.90}
  - {min_VR: 0.90, Q: 0.80}
  - {min_VR: 0.85, Q: 0.75}
```

**Baseline solver:** Linear-LS — M error 3.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | M Error | VR | Runtime | Q |
|--------|---------|-----|---------|---|
| W-phase | 4.2e-2 | 0.89 | 2 s | 0.80 |
| Linear-LS | 3.5e-2 | 0.93 | 5 s | 0.90 |
| TD-CMT | 2.8e-2 | 0.95 | 30 s | 0.90 |
| 3D-GF + bootstrap | 1.2e-2 | 0.98 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (3D-GF): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p278_hash>",
  "h_s": "sha256:<spec278_hash>",
  "h_b": "sha256:<bench278_hash>",
  "r": {"residual_norm": 1.2e-2, "error_bound": 5.0e-2, "ratio": 0.24},
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
pwm-node benchmarks | grep cmt_inv
pwm-node verify cmt_inv/global_s1_ideal.yaml
pwm-node mine cmt_inv/global_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
