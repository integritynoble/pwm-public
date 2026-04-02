# Principle #498 — Topology Optimization (SIMP)

**Domain:** Optimization | **Carrier:** N/A (PDE-constrained) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [O.adjoint] --> [N.simp] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiff-->O.adj-->N.simp  TopOpt-SIMP MBB-beam  FEM+OC/MMA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TOPOLOGY OPTIMIZATION (SIMP)  P = (E,G,W,C)  Principle #498   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min_ρ c(ρ) = Fᵀu   s.t. K(ρ)u = F                   │
│        │ K(ρ) = Σ_e E_e(ρ_e) k_e,  E_e = ρ_e^p E₀  (SIMP)   │
│        │ V(ρ) = Σ_e ρ_e v_e ≤ V*  (volume constraint)         │
│        │ 0 < ρ_min ≤ ρ_e ≤ 1  (density bounds)                │
│        │ Forward: given (loads, V*) → optimal material layout   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiff] ──→ [O.adj] ──→ [N.simp]                     │
│        │  FEM-matrix  sensitivity  density-update               │
│        │ V={L.stiff,O.adj,N.simp}  A={L.stiff→O.adj,O.adj→N.simp}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (with filtering/penalization)           │
│        │ Uniqueness: NO (multiple local minima; convexified)    │
│        │ Stability: density filter prevents checkerboard        │
│        │ Mismatch: penalization p, mesh dependency w/o filter   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |c − c_ref|/c_ref  (compliance error)             │
│        │ q = N/A (iterative optimization)                      │
│        │ T = {compliance, volume_fraction, gray_elements}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Compliance c > 0; volume constraint feasible; ρ bounded | PASS |
| S2 | Density filter ensures mesh-independent solutions | PASS |
| S3 | OC/MMA converge within 200 iterations for standard problems | PASS |
| S4 | Compliance within 1% of reference for MBB beam | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# topopt_simp/mbb_beam_s1.yaml
principle_ref: sha256:<p498_hash>
omega:
  grid: [300, 100]
  domain: MBB_beam_half_symmetry
  penalization: 3.0
E:
  forward: "SIMP + density filter + OC update"
  E0: 1.0           # normalized
  nu: 0.3
  filter_radius: 3.0   # elements
B:
  load: {point: top_left, F: -1.0}
  supports: {left: symmetry, right_bottom: roller}
  volume_fraction: 0.5
I:
  scenario: MBB_beam_compliance_minimization
  meshes: [60x20, 150x50, 300x100]
O: [compliance, volume_achieved, gray_fraction, topology]
epsilon:
  compliance_tol: 0.01
  gray_fraction_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 300×100 mesh; filter radius 3 elements; p=3 standard | PASS |
| S2 | MBB with symmetry well-posed; V* = 0.5 feasible | PASS |
| S3 | OC converges within 100 iterations | PASS |
| S4 | Compliance within 1% of finest-mesh reference | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# topopt_simp/benchmark_mbb.yaml
spec_ref: sha256:<spec498_hash>
principle_ref: sha256:<p498_hash>
dataset:
  name: MBB_beam_topology_optimization
  reference: "Sigmund (2001) 99-line topology optimization"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OC (no filter)
    params: {mesh: 60x20, filter: none}
    results: {compliance: 198.5, gray_fraction: 0.15}
  - solver: OC + density filter
    params: {mesh: 150x50, filter: 3.0}
    results: {compliance: 196.2, gray_fraction: 0.03}
  - solver: MMA + Heaviside projection
    params: {mesh: 300x100, filter: 3.0, beta: 16}
    results: {compliance: 195.8, gray_fraction: 0.008}
quality_scoring:
  - {min_c: 195.0, Q: 1.00}
  - {min_c: 196.0, Q: 0.90}
  - {min_c: 198.0, Q: 0.80}
  - {min_c: 200.0, Q: 0.75}
```

**Baseline solver:** OC + filter (150×50) — compliance 196.2
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Compliance | Gray Frac | Iterations | Q |
|--------|-----------|----------|-----------|---|
| OC (no filter) | 198.5 | 0.15 | 80 | 0.75 |
| OC + filter | 196.2 | 0.03 | 90 | 0.90 |
| MMA + Heaviside | 195.8 | 0.008 | 120 | 0.90 |
| MMA + robust | 195.2 | 0.003 | 150 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (MMA robust): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p498_hash>",
  "h_s": "sha256:<spec498_hash>",
  "h_b": "sha256:<bench498_hash>",
  "r": {"compliance": 195.2, "error_bound": 198.0, "ratio": 0.986},
  "c": {"gray_fraction": 0.003, "iterations": 150, "K": 3},
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
pwm-node benchmarks | grep topopt_simp
pwm-node verify topopt_simp/mbb_beam_s1.yaml
pwm-node mine topopt_simp/mbb_beam_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
