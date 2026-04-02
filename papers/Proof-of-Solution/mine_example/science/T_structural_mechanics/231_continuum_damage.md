# Principle #231 — Continuum Damage Mechanics

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.damage] --> [L.stiffness] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.damage→L.stiffness→B.dirichlet   CDM         tensile-damage     FEM-NR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONTINUUM DAMAGE MECHANICS        P = (E,G,W,C)  Principle #231│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ̃ = σ/(1−D),  σ = (1−D) C:ε  (effective stress)      │
│        │ Ḋ = f(Y, ε̄, D)  (damage evolution law)                │
│        │ Y = −∂ψ/∂D = ½ ε:C:ε  (energy release rate)           │
│        │ Forward: given BC/loads → solve for (u, D)(x,t)        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.damage] --> [L.stiffness] --> [B.dirichlet]│
│        │ load-step  damage-evolution  degraded-stiffness  displacement-BC│
│        │ V={∂.time,N.damage,L.stiffness,B.dirichlet}  L_DAG=3.0          │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (damage bounded D ∈ [0,1])             │
│        │ Uniqueness: CONDITIONAL (softening → localisation)     │
│        │ Stability: regularisation needed (nonlocal or gradient)│
│        │ Mismatch: damage threshold, evolution law parameters   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = load-displacement curve error + damage field error │
│        │ q = 1.0 (localisation band width controls convergence)│
│        │ T = {peak_load_error, damage_band_width, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Damage variable D ∈ [0,1]; irreversibility Ḋ ≥ 0 enforced | PASS |
| S2 | Nonlocal regularisation ensures mesh-independent dissipation | PASS |
| S3 | Newton-Raphson with consistent tangent converges (arc-length for snap) | PASS |
| S4 | Peak load and dissipated energy converge with mesh refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# continuum_damage/tensile_bar_s1_ideal.yaml
principle_ref: sha256:<p231_hash>
omega:
  grid: [128, 16]
  domain: notched_bar
  length: 0.1
  width: 0.02
  notch_width: 0.002
E:
  forward: "sigma = (1-D)*C*eps, damage evolution D(Y)"
  E_modulus: 30.0e9   # concrete
  poisson: 0.2
  damage:
    threshold: 1.0e-4   # strain threshold
    evolution: exponential
    kappa: 0.01   # nonlocal length
B:
  left: {u_x: 0}
  right: {u_x: controlled}   # displacement-controlled
I:
  scenario: notched_bar_tension
  mesh_sizes: [32x4, 64x8, 128x16]
O: [peak_load_error, dissipated_energy_error, damage_band_width]
epsilon:
  peak_load_error: 5.0e-2
  energy_error_max: 1.0e-1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Nonlocal length scale resolved by ≥ 3 elements; mesh ok | PASS |
| S2 | Nonlocal damage model gives mesh-independent results | PASS |
| S3 | Arc-length method handles snap-back in softening regime | PASS |
| S4 | Peak load error < 5% at 128×16 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# continuum_damage/benchmark_tensile.yaml
spec_ref: sha256:<spec231_hash>
principle_ref: sha256:<p231_hash>
dataset:
  name: notched_bar_damage
  reference: "Peerlings et al. (1996) — nonlocal damage benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-local (64×8)
    params: {nonlocal: false}
    results: {peak_error: 1.5e-1, note: "mesh-dependent"}
  - solver: FEM-nonlocal (64×8)
    params: {nonlocal: true, l_c: 0.01}
    results: {peak_error: 4.5e-2, energy_error: 8.0e-2}
  - solver: FEM-nonlocal (128×16)
    params: {nonlocal: true, l_c: 0.01}
    results: {peak_error: 2.0e-2, energy_error: 4.0e-2}
quality_scoring:
  - {min_err: 1.0e-2, Q: 1.00}
  - {min_err: 3.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** FEM-nonlocal (64×8) — peak error 4.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Peak Err | Energy Err | Runtime | Q |
|--------|----------|------------|---------|---|
| FEM-local (64×8) | 1.5e-1 | mesh-dep | 10 s | — |
| FEM-nonlocal (64×8) | 4.5e-2 | 8.0e-2 | 30 s | 0.80 |
| FEM-nonlocal (128×16) | 2.0e-2 | 4.0e-2 | 120 s | 0.90 |
| FEM-gradient (128×16) | 8.0e-3 | 2.0e-2 | 150 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (gradient): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p231_hash>",
  "h_s": "sha256:<spec231_hash>",
  "h_b": "sha256:<bench231_hash>",
  "r": {"residual_norm": 8.0e-3, "error_bound": 5.0e-2, "ratio": 0.16},
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
pwm-node benchmarks | grep continuum_damage
pwm-node verify continuum_damage/tensile_bar_s1_ideal.yaml
pwm-node mine continuum_damage/tensile_bar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
