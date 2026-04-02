# Principle #425 — Groundwater Contaminant Transport

**Domain:** Environmental Science | **Carrier:** solute concentration | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → ∂.space.laplacian → N.reaction → B.dirichlet |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.reaction→B.dirichlet      GW-transport  aquifer-plume     FEM/FDM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GROUNDWATER CONTAMINANT TRANSPORT P=(E,G,W,C)  Principle #425 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ θ ∂C/∂t = ∇·(D·∇C) − ∇·(qC) − λθC + q_s C_s        │
│        │ q = −K∇h   (Darcy velocity from flow equation)        │
│        │ ∇·q = Q_w  (groundwater flow, steady or transient)    │
│        │ C = solute concentration, θ = porosity, K = conductivity│
│        │ Forward: given K-field, sources → C(x,t) plume        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.reaction] ──→ [B.dirichlet] │
│        │ derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space.laplacian, N.reaction, B.dirichlet}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.reaction, N.reaction→B.dirichlet}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear parabolic PDE for given q)      │
│        │ Uniqueness: YES (unique for given IC/BC and q-field)   │
│        │ Stability: grid Peclet number Pe_h = |q|h/(2D) < 1    │
│        │ Mismatch: hydraulic conductivity heterogeneity, dispersivity│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖C−C_ref‖/‖C_ref‖              │
│        │ q = 1.0 (upwind FDM), 2.0 (MMOC), 2.0 (FEM)        │
│        │ T = {C_error, mass_balance, plume_extent_error}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Concentration, Darcy velocity, dispersivity dimensionally consistent | PASS |
| S2 | Linear parabolic PDE — well-posed for smooth K-field | PASS |
| S3 | FEM/MMOC converges; upwind FDM stable but diffusive | PASS |
| S4 | C error computable against Ogata-Banks analytic or MT3DMS reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gw_transport/aquifer_plume_s1_ideal.yaml
principle_ref: sha256:<p425_hash>
omega:
  grid: [200, 100]
  domain: confined_aquifer_2D
  size: [1000, 500]   # m
  time: [0, 365]   # days
  dt: 1.0   # day
E:
  forward: "θ ∂C/∂t = ∇·(D∇C) − ∇·(qC) − λθC"
  porosity: 0.3
  alpha_L: 10.0   # m (longitudinal dispersivity)
  alpha_T: 1.0   # m (transverse dispersivity)
  lambda: 0.0   # no decay
B:
  upstream: {C: 0.0}
  source: {well: {x: 200, y: 250, C_inj: 100}}
  downstream: {gradient: natural}
I:
  scenario: continuous_injection_plume
  K_values: [1e-4, 1e-3]   # m/s
  mesh_sizes: [50x25, 100x50, 200x100]
O: [C_L2_error, plume_length_error, mass_balance]
epsilon:
  C_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200x100 grid over 1km x 0.5km; dt=1 day stable | PASS |
| S2 | Continuous injection in uniform flow — well-characterized plume | PASS |
| S3 | MMOC handles advection-dominated transport (Pe >> 1) | PASS |
| S4 | C error < 0.5% achievable at 200x100 resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gw_transport/benchmark_aquifer.yaml
spec_ref: sha256:<spec425_hash>
principle_ref: sha256:<p425_hash>
dataset:
  name: MT3DMS_verification
  reference: "Zheng & Wang (1999) MT3DMS verification problems"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-upwind
    params: {N: [100, 50], dt: 1.0}
    results: {C_error: 1.5e-2, mass_err: 1.0e-6}
  - solver: MMOC
    params: {N: [100, 50], dt: 1.0}
    results: {C_error: 3.0e-3, mass_err: 5.0e-4}
  - solver: FEM-SUPG
    params: {N: [100, 50], dt: 1.0}
    results: {C_error: 2.0e-3, mass_err: 1.0e-8}
quality_scoring:
  - {min_C_err: 1.0e-3, Q: 1.00}
  - {min_C_err: 5.0e-3, Q: 0.90}
  - {min_C_err: 1.0e-2, Q: 0.80}
  - {min_C_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-SUPG — C error 2.0×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | C L2 Error | Mass Error | Runtime | Q |
|--------|-----------|-----------|---------|---|
| FDM-upwind | 1.5e-2 | 1.0e-6 | 2 s | 0.80 |
| MMOC | 3.0e-3 | 5.0e-4 | 5 s | 0.90 |
| FEM-SUPG | 2.0e-3 | 1.0e-8 | 8 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 0.90 = 270 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p425_hash>",
  "h_s": "sha256:<spec425_hash>",
  "h_b": "sha256:<bench425_hash>",
  "r": {"C_error": 2.0e-3, "mass_err": 1.0e-8, "ratio": 0.40},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep gw_transport
pwm-node verify AF_environmental_science/gw_transport_s1_ideal.yaml
pwm-node mine AF_environmental_science/gw_transport_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
