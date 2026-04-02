# Principle #461 — Hydraulic Fracture Modeling

**Domain:** Petroleum Engineering | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [∂.space] --> [L.coupled] --> [B.crack] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->∂.x-->L.coupled-->B.crack  HydFrac  KGD/PKN-bench  FEM+lubrication
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HYDRAULIC FRACTURE MODELING   P = (E,G,W,C)   Principle #461   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂w/∂t + ∇·q = Q_inj δ(x₀)  (mass conservation)       │
│        │ q = −w³/(12μ) ∇p  (lubrication / Poiseuille)          │
│        │ p(x) − σ₀ = E'/(4π) ∫ ∂w/∂s · ds/(x−s)  (elasticity)│
│        │ K_I = K_Ic at tip  (propagation criterion)             │
│        │ Forward: given Q_inj,μ,E',K_Ic → w(x,t), L(t), p(t)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [∂.x] ──→ [L.coupled] ──→ [B.crack]          │
│        │  time-step  spatial  poroelastic  fracture-BC          │
│        │ V={∂.t,∂.x,L.coupled,B.crack}  A={∂.t→∂.x,∂.x→L.coupled,L.coupled→B.crack}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (KGD/PKN self-similar solutions exist)  │
│        │ Uniqueness: YES for given propagation regime            │
│        │ Stability: tip asymptotics determine regime (M,K,O)    │
│        │ Mismatch: leak-off uncertainty, layered stress contrast │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖w−w_exact‖/‖w_exact‖ (width)      │
│        │ q = 1.0 (tip singular), 2.0 (smooth body)            │
│        │ T = {width_error, length_error, pressure_error}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Width/pressure/length dimensions consistent; tip singularity handled | PASS |
| S2 | Self-similar solutions in viscosity/toughness regimes validated | PASS |
| S3 | Implicit tip-element algorithms converge for KGD and PKN | PASS |
| S4 | Width error bounded by mesh-dependent estimates near tip | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hyd_frac/kgd_s1_ideal.yaml
principle_ref: sha256:<p461_hash>
omega:
  elements: 100
  domain: plane_strain_KGD
  time: [0, 600.0]    # seconds
  dt: 1.0
E:
  forward: "lubrication + elasticity integral + propagation"
  E_prime: 25.0e9     # Pa
  K_Ic: 1.5e6         # Pa√m
  mu_fluid: 0.1       # Pa·s
B:
  injection: {rate: 0.001, location: center}   # m²/s
  tip: {criterion: LEFM, K_I_eq_K_Ic: true}
I:
  scenario: KGD_viscosity_dominated
  mesh_sizes: [50, 100, 200, 400]
O: [width_L2, length_error, pressure_inlet]
epsilon:
  width_L2_max: 1.0e-2
  length_error_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 elements adequate for viscosity regime; dt=1 s stable | PASS |
| S2 | Viscosity-dominated regime well-posed; self-similar solution exists | PASS |
| S3 | Implicit tip-element method converges within 5 Picard iterations | PASS |
| S4 | Width L2 < 1% achievable with 200+ elements | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hyd_frac/benchmark_kgd.yaml
spec_ref: sha256:<spec461_hash>
principle_ref: sha256:<p461_hash>
dataset:
  name: KGD_self_similar_viscosity
  reference: "Spence & Sharp (1985); Adachi & Detournay (2002)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Fixed-mesh FEM
    params: {elements: 100, tip: standard}
    results: {width_L2: 3.5e-2, length_error: 5.1e-2}
  - solver: Implicit tip-element
    params: {elements: 100, tip: asymptotic}
    results: {width_L2: 8.2e-3, length_error: 1.2e-2}
  - solver: Implicit tip-element (fine)
    params: {elements: 400, tip: asymptotic}
    results: {width_L2: 2.1e-3, length_error: 3.5e-3}
quality_scoring:
  - {min_L2: 1.0e-3, Q: 1.00}
  - {min_L2: 5.0e-3, Q: 0.90}
  - {min_L2: 1.0e-2, Q: 0.80}
  - {min_L2: 5.0e-2, Q: 0.75}
```

**Baseline solver:** Implicit tip-element (N=100) — width L2 error 8.2×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Width L2 | Length Error | Runtime | Q |
|--------|----------|-------------|---------|---|
| Fixed-mesh FEM | 3.5e-2 | 5.1e-2 | 5 s | 0.75 |
| Tip-element (N=100) | 8.2e-3 | 1.2e-2 | 12 s | 0.80 |
| Tip-element (N=200) | 3.8e-3 | 5.8e-3 | 45 s | 0.90 |
| Tip-element (N=400) | 2.1e-3 | 3.5e-3 | 180 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (fine tip): 400 × 1.00 = 400 PWM
Floor:                400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p461_hash>",
  "h_s": "sha256:<spec461_hash>",
  "h_b": "sha256:<bench461_hash>",
  "r": {"residual_norm": 2.1e-3, "error_bound": 1.0e-2, "ratio": 0.210},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 4},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep hyd_frac
pwm-node verify hyd_frac/kgd_s1_ideal.yaml
pwm-node mine hyd_frac/kgd_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
