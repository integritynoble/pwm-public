# Principle #399 — Cardiac Electrophysiology (Bidomain)

**Domain:** Computational Biology | **Carrier:** transmembrane potential | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → ∂.space.laplacian → N.ionic → L.coupled |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.ionic→L.coupled      bidomain     cardiac-tissue    FEM/split
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CARDIAC ELECTROPHYSIOLOGY (BIDOMAIN) P=(E,G,W,C) Princ. #399  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·(σ_i ∇V_m) + ∇·(σ_i ∇φ_e) = χ(C_m ∂V_m/∂t + I_ion)│
│        │ ∇·((σ_i + σ_e)∇φ_e) + ∇·(σ_i ∇V_m) = 0              │
│        │ V_m = transmembrane potential, φ_e = extracellular     │
│        │ I_ion = f(V_m, gates) from cell model (e.g., ten Tusscher)│
│        │ Forward: given stimulus → V_m(x,t), φ_e(x,t) over heart│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.ionic] ──→ [L.coupled] │
│        │ derivative  derivative  nonlinear  linear-op           │
│        │ V={∂.time, ∂.space.laplacian, N.ionic, L.coupled}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.ionic, N.ionic→L.coupled}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic-elliptic system, weak sols)  │
│        │ Uniqueness: YES for bounded ionic models               │
│        │ Stability: CFL-like constraint on dt; stiff ionic terms│
│        │ Mismatch: fiber orientation, conductivity tensor values │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = activation time error |t_act − t_ref| (ms)        │
│        │ q = 2.0 (linear FEM), 1.0 (operator splitting)       │
│        │ T = {activation_error, V_m_L2, conduction_velocity}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Conductivity tensors, membrane capacitance dimensionally consistent | PASS |
| S2 | Bidomain system well-posed for bounded ionic current models | PASS |
| S3 | Operator-splitting FEM converges with fine spatial/temporal mesh | PASS |
| S4 | Activation time error measurable against monodomain/experimental reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cardiac_bidomain/tissue_slab_s1_ideal.yaml
principle_ref: sha256:<p399_hash>
omega:
  grid: [200, 200]
  domain: tissue_slab_2D
  size: [20.0, 20.0]   # mm
  time: [0, 100.0]   # ms
  dt: 0.01   # ms
E:
  forward: "Bidomain equations + ten Tusscher ionic model"
  sigma_i: 0.174   # S/m (intracellular)
  sigma_e: 0.625   # S/m (extracellular)
  C_m: 1.0   # uF/cm²
B:
  boundary: {insulated: true}
  stimulus: {location: corner, amplitude: 50, duration: 2.0}
I:
  scenario: planar_wave_propagation
  cell_model: ten_Tusscher_2006
  mesh_sizes_h: [0.2, 0.1, 0.05]   # mm
O: [activation_time_error, conduction_velocity_error]
epsilon:
  activation_err_max: 0.5   # ms
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | h=0.1 mm resolves wavefront (~0.2 mm); dt=0.01 ms stable | PASS |
| S2 | Planar wave in isotropic slab — well-defined conduction velocity | PASS |
| S3 | Godunov splitting + CG-FEM converges | PASS |
| S4 | Activation error < 0.5 ms achievable at h=0.05 mm | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cardiac_bidomain/benchmark_tissue.yaml
spec_ref: sha256:<spec399_hash>
principle_ref: sha256:<p399_hash>
dataset:
  name: Niederer_benchmark
  reference: "Niederer et al. (2011) cardiac benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Monodomain-FEM
    params: {h: 0.1, dt: 0.01, splitting: Godunov}
    results: {act_err: 0.8, CV_err: 2.5e-2}
  - solver: Bidomain-FEM
    params: {h: 0.1, dt: 0.01, splitting: Strang}
    results: {act_err: 0.4, CV_err: 1.2e-2}
  - solver: Bidomain-FEM-fine
    params: {h: 0.05, dt: 0.005}
    results: {act_err: 0.1, CV_err: 3.0e-3}
quality_scoring:
  - {max_act_err: 0.2, Q: 1.00}
  - {max_act_err: 0.5, Q: 0.90}
  - {max_act_err: 1.0, Q: 0.80}
  - {max_act_err: 2.0, Q: 0.75}
```

**Baseline solver:** Bidomain-FEM — activation error 0.4 ms
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Act. Error (ms) | CV Error | Runtime | Q |
|--------|----------------|----------|---------|---|
| Monodomain-FEM | 0.8 | 2.5e-2 | 30 s | 0.80 |
| Bidomain-FEM | 0.4 | 1.2e-2 | 120 s | 0.90 |
| Bidomain-FEM-fine | 0.1 | 3.0e-3 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (fine): 500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p399_hash>",
  "h_s": "sha256:<spec399_hash>",
  "h_b": "sha256:<bench399_hash>",
  "r": {"act_err": 0.1, "CV_err": 3.0e-3, "ratio": 0.20},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep cardiac_bidomain
pwm-node verify AE_computational_biology/cardiac_bidomain_s1_ideal.yaml
pwm-node mine AE_computational_biology/cardiac_bidomain_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
