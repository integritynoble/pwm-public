# Principle #417 — General Circulation Model (GCM)

**Domain:** Environmental Science | **Carrier:** atmospheric state | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → N.bilinear.advection → ∂.space → B.periodic → N.param |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space→B.periodic→N.param   GCM          Held-Suarez       spectral/FV
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GENERAL CIRCULATION MODEL (GCM) P = (E,G,W,C)  Principle #417 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂u/∂t = −(u·∇)u − 2Ω×u − ∇Φ − (1/ρ)∇p + F          │
│        │ ∂T/∂t = −u·∇T + (RT/c_p p)ω + Q/c_p     (thermo)    │
│        │ ∂q/∂t = −u·∇q + E − P                    (moisture)  │
│        │ ∇·(ρu) = 0                                (continuity)│
│        │ Forward: given IC/forcing → u,T,p,q on sphere over time│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space] ──→ [B.periodic] ──→ [N.param] │
│        │ derivative  nonlinear  derivative  boundary  nonlinear │
│        │ V={∂.time, N.bilinear.advection, ∂.space, B.periodic, N.param}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space, ∂.space→B.periodic, B.periodic→N.param}  L_DAG=4.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (primitive equations on sphere)         │
│        │ Uniqueness: conditional (sensitive to initial conditions)│
│        │ Stability: CFL constraint; climate statistics converge │
│        │ Mismatch: sub-grid parameterizations, resolution       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = zonal mean temperature/wind RMSE vs reanalysis     │
│        │ q = resolution-dependent (spectral truncation)        │
│        │ T = {T_RMSE, u_RMSE, precip_bias, K_resolutions}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Primitive equation variables on spherical grid consistent | PASS |
| S2 | Primitive equations well-posed for finite-time integration | PASS |
| S3 | Spectral transform or FV methods converge at given resolution | PASS |
| S4 | Climate statistics computable against ERA5 reanalysis | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gcm/held_suarez_s1_ideal.yaml
principle_ref: sha256:<p417_hash>
omega:
  grid: T42L20   # spectral T42, 20 vertical levels
  domain: global_sphere
  time: [0, 1200]   # days (spinup + statistics)
  dt: 1200   # s
E:
  forward: "Primitive equations with Held-Suarez forcing"
  forcing: Newtonian_relaxation
  friction: Rayleigh_damping
B:
  initial: {isothermal: 300}   # K
I:
  scenario: Held_Suarez_1994
  resolutions: [T21, T42, T85]
O: [zonal_T_RMSE, zonal_u_RMSE, eddy_KE]
epsilon:
  T_RMSE_max: 2.0   # K vs HS94 reference
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | T42 resolution (~2.8 deg) standard for HS94; 20 levels adequate | PASS |
| S2 | Held-Suarez forcing removes physics complexity — clean dynamics test | PASS |
| S3 | Spectral transform at T42 converges for large-scale dynamics | PASS |
| S4 | Zonal T RMSE < 2 K achievable after 1000-day spinup | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gcm/benchmark_held_suarez.yaml
spec_ref: sha256:<spec417_hash>
principle_ref: sha256:<p417_hash>
dataset:
  name: HS94_reference_climatology
  reference: "Held & Suarez (1994) J. Atmos. Sci."
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Spectral-T42
    params: {levels: 20, dt: 1200}
    results: {T_RMSE: 1.2, u_RMSE: 2.5}
  - solver: FV-cubed-sphere-C48
    params: {levels: 20, dt: 900}
    results: {T_RMSE: 1.5, u_RMSE: 3.0}
  - solver: SE-ne16
    params: {levels: 20, dt: 600}
    results: {T_RMSE: 1.3, u_RMSE: 2.8}
quality_scoring:
  - {max_T_RMSE: 1.0, Q: 1.00}
  - {max_T_RMSE: 2.0, Q: 0.90}
  - {max_T_RMSE: 3.0, Q: 0.80}
  - {max_T_RMSE: 5.0, Q: 0.75}
```

**Baseline solver:** Spectral-T42 — T RMSE 1.2 K
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T RMSE (K) | u RMSE (m/s) | Runtime | Q |
|--------|-----------|-------------|---------|---|
| FV-C48 | 1.5 | 3.0 | 2 hr | 0.90 |
| SE-ne16 | 1.3 | 2.8 | 3 hr | 0.90 |
| Spectral-T42 | 1.2 | 2.5 | 1.5 hr | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p417_hash>",
  "h_s": "sha256:<spec417_hash>",
  "h_b": "sha256:<bench417_hash>",
  "r": {"T_RMSE": 1.2, "u_RMSE": 2.5, "ratio": 0.60},
  "c": {"resolution": "T42", "spinup_days": 200, "K": 3},
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
pwm-node benchmarks | grep gcm
pwm-node verify AF_environmental_science/gcm_held_suarez_s1_ideal.yaml
pwm-node mine AF_environmental_science/gcm_held_suarez_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
