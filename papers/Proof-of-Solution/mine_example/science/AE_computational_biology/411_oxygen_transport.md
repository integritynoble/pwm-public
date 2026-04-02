# Principle #411 — Oxygen Transport in Tissue (Krogh Cylinder)

**Domain:** Computational Biology | **Carrier:** oxygen partial pressure | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → ∂.space.laplacian → N.reaction |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.reaction        Krogh-cyl    tissue-pO2        FDM/analyt
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OXYGEN TRANSPORT (KROGH CYL.)  P = (E,G,W,C)   Principle #411 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ D_O2 (1/r) d/dr(r dP/dr) = M₀            (steady)    │
│        │ P(r_c) = P_cap  (capillary wall BC)                    │
│        │ dP/dr|_{r=R} = 0  (tissue cylinder outer BC)          │
│        │ P = pO₂, D_O2 = O₂ diffusivity, M₀ = consumption rate│
│        │ Forward: given P_cap, M₀, geometry → P(r) profile     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.reaction]      │
│        │ derivative  derivative  nonlinear                      │
│        │ V={∂.time, ∂.space.laplacian, N.reaction}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.reaction}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear elliptic BVP in radial coords)  │
│        │ Uniqueness: YES (unique for given BC and M₀)           │
│        │ Stability: YES (smooth radial solution)                │
│        │ Mismatch: M₀ heterogeneity, capillary tortuosity       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖P−P_ref‖/‖P_ref‖                  │
│        │ q = 2.0 (FDM central), exact (analytic solution)     │
│        │ T = {pO2_error, lethal_corner_pO2, K_mesh_sizes}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | pO₂, diffusivity, consumption rate dimensionally consistent | PASS |
| S2 | Linear radial BVP — analytic solution exists (Krogh 1919) | PASS |
| S3 | FDM in radial coords converges at O(h²) | PASS |
| S4 | pO₂ error computable against Krogh analytic formula | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# krogh_cylinder/tissue_pO2_s1_ideal.yaml
principle_ref: sha256:<p411_hash>
omega:
  grid: [100]   # radial nodes
  domain: radial_r_c_to_R
  r_capillary: 5.0   # um
  R_tissue: 25.0   # um
E:
  forward: "D(1/r)d/dr(r dP/dr) = M0 (Krogh cylinder)"
  D_O2: 2.0e-5   # cm²/s
  M0: 5.0e-4     # mL O₂/(mL·s)
B:
  inner: {P_cap: 95.0}   # mmHg
  outer: {dPdr: 0.0}     # no-flux
I:
  scenario: steady_state_tissue_oxygenation
  mesh_sizes: [25, 50, 100]
O: [pO2_L2_error, lethal_corner_error]
epsilon:
  pO2_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 radial nodes over 20 um tissue — well-resolved | PASS |
| S2 | Constant M₀ — analytic Krogh solution applies | PASS |
| S3 | Radial FDM converges at O(h²) | PASS |
| S4 | pO₂ error < 10⁻⁴ achievable at 100 nodes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# krogh_cylinder/benchmark_tissue.yaml
spec_ref: sha256:<spec411_hash>
principle_ref: sha256:<p411_hash>
dataset:
  name: Krogh_analytic_1919
  reference: "Krogh (1919) analytic cylinder solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FDM-central
    params: {N: 50}
    results: {pO2_err: 2.5e-4, corner_err: 0.3}
  - solver: FDM-fine
    params: {N: 200}
    results: {pO2_err: 1.5e-5, corner_err: 0.02}
  - solver: Analytic
    params: {}
    results: {pO2_err: 0.0, corner_err: 0.0}
quality_scoring:
  - {min_pO2_err: 1.0e-5, Q: 1.00}
  - {min_pO2_err: 1.0e-4, Q: 0.90}
  - {min_pO2_err: 1.0e-3, Q: 0.80}
  - {min_pO2_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FDM-central — pO₂ error 2.5×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | pO₂ L2 Error | Corner Error | Runtime | Q |
|--------|-------------|-------------|---------|---|
| FDM-central (50) | 2.5e-4 | 0.3 mmHg | 0.001 s | 0.90 |
| FDM-fine (200) | 1.5e-5 | 0.02 mmHg | 0.002 s | 1.00 |
| Analytic | 0.0 | 0.0 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (analytic): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p411_hash>",
  "h_s": "sha256:<spec411_hash>",
  "h_b": "sha256:<bench411_hash>",
  "r": {"pO2_err": 0.0, "corner_err": 0.0, "ratio": 0.0},
  "c": {"method": "analytic", "K": 3},
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
pwm-node benchmarks | grep krogh_cylinder
pwm-node verify AE_computational_biology/krogh_cylinder_s1_ideal.yaml
pwm-node mine AE_computational_biology/krogh_cylinder_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
