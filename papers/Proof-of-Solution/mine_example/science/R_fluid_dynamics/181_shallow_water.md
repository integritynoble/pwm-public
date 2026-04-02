# Principle #181 — Shallow Water Equations

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.flux] --> [∂.space.gradient] --> [B.coast] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux→∂.space.gradient→B.coast        SWE         dam-break-1D      FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SHALLOW WATER EQUATIONS   P = (E,G,W,C)   Principle #181       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂h/∂t + ∇·(hu) = 0                                    │
│        │ ∂(hu)/∂t + ∇·(hu⊗u + ½gh²I) = −ghS₀ − ghSf          │
│        │ h = water depth, u = depth-averaged velocity           │
│        │ S₀ = bed slope, Sf = friction slope (Manning)          │
│        │ Hyperbolic system; admits bores and dry fronts         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.flux] --> [∂.space.gradient] --> [B.coast]│
│        │ time  Riemann-flux  bathymetry-gradient  coast-BC         │
│        │ V={∂.time,N.flux,∂.space.gradient,B.coast}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (entropy weak solutions, Ritter for dam)│
│        │ Uniqueness: YES with entropy condition                  │
│        │ Stability: CFL on √(gh); well-balanced schemes needed │
│        │ Mismatch: bathymetry error, Manning n error            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L1 error in h and hu                      │
│        │ q = 1.0 (1st order FVM), 2.0 (MUSCL)                 │
│        │ T = {wave_front_error, mass_conservation, K_mesh}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hyperbolic conservation law; eigenvalues u±√(gh) real | PASS |
| S2 | Exact Riemann solution exists (Stoker, Ritter) | PASS |
| S3 | Well-balanced FVM (HLL/HLLC) preserves lake-at-rest; converges | PASS |
| S4 | L1 error bounded; mass conservation to machine precision | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# swe/dam_break_1d_s1.yaml
principle_ref: sha256:<p181_hash>
omega:
  grid: [1000]
  domain: [0, 50]
  time: [0, 5.0]
E:
  forward: "∂h/∂t + ∂(hu)/∂x = 0; ∂(hu)/∂t + ∂(hu²+½gh²)/∂x = 0"
  g: 9.81
B:
  left: {h: 10.0, u: 0.0}
  right: {h: 1.0, u: 0.0}
  walls: reflective
I:
  scenario: dam_break_wet_bed
  mesh_sizes: [100, 500, 1000]
O: [L1_depth_error, wave_speed_error, mass_conservation]
epsilon:
  L1_error_max: 5.0e-3
  mass_error_max: 1.0e-12
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D grid; dam-break IC well-formed; wet bed on both sides | PASS |
| S2 | Exact Riemann solution exists (Stoker 1957) | PASS |
| S3 | HLLC/Roe FVM converges at O(h) near bores | PASS |
| S4 | L1 error < 5×10⁻³ at N=1000 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# swe/benchmark_dam_break.yaml
spec_ref: sha256:<spec181_hash>
principle_ref: sha256:<p181_hash>
dataset:
  name: Stoker_dam_break_exact
  reference: "Stoker (1957) exact Riemann solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-HLL (1st order)
    params: {N: 500}
    results: {L1_error: 1.2e-2, mass_err: 1e-14}
  - solver: FVM-MUSCL-HLLC
    params: {N: 500, limiter: minmod}
    results: {L1_error: 3.8e-3, mass_err: 1e-14}
  - solver: DG-P1 (well-balanced)
    params: {N_elem: 250}
    results: {L1_error: 2.1e-3, mass_err: 1e-14}
quality_scoring:
  - {min_L1: 1.0e-3, Q: 1.00}
  - {min_L1: 4.0e-3, Q: 0.90}
  - {min_L1: 8.0e-3, Q: 0.80}
  - {min_L1: 1.5e-2, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL-HLLC — L1 error 3.8×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L1 Error | Mass Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FVM-HLL (1st) | 1.2e-2 | 1e-14 | 0.3 s | 0.80 |
| FVM-MUSCL-HLLC | 3.8e-3 | 1e-14 | 0.8 s | 0.90 |
| DG-P1 | 2.1e-3 | 1e-14 | 1.5 s | 0.90 |
| WENO-5 + HLLC | 7.5e-4 | 1e-14 | 2.0 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (WENO-5): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p181_hash>",
  "h_s": "sha256:<spec181_hash>",
  "h_b": "sha256:<bench181_hash>",
  "r": {"residual_norm": 7.5e-4, "error_bound": 5.0e-3, "ratio": 0.15},
  "c": {"fitted_rate": 0.97, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep swe
pwm-node verify swe/dam_break_1d_s1.yaml
pwm-node mine swe/dam_break_1d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
