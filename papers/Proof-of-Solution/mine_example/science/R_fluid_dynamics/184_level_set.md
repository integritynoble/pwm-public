# Principle #184 — Level Set Method

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.reinit] --> [B.periodic] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→N.pointwise.reinit→B.periodic   LevelSet    Zalesak-disk      FDM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LEVEL SET METHOD   P = (E,G,W,C)   Principle #184              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂φ/∂t + u·∇φ = 0   (level set advection)             │
│        │ Interface: Γ = {x : φ(x,t) = 0}                       │
│        │ n̂ = ∇φ/|∇φ|,  κ = ∇·n̂  (curvature from φ)           │
│        │ Reinitialization: ∂φ/∂τ = sign(φ₀)(1−|∇φ|)           │
│        │ Forward: given velocity u → track interface via φ=0   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.reinit] --> [B.periodic]│
│        │ time  LS-advect  NS-solve  reinit  BC                                                        │
│        │ V={∂.time,N.bilinear.advection,L.poisson,N.pointwise.reinit,B.periodic}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Hamilton-Jacobi theory)                │
│        │ Uniqueness: YES (viscosity solution)                   │
│        │ Stability: CFL on advection; reinit stabilizes |∇φ|=1│
│        │ Mismatch: mass loss without correction, reinit freq.  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = interface position error, area/mass conservation   │
│        │ q = 2.0 (ENO-2), 5.0 (WENO-5)                       │
│        │ T = {interface_err, area_loss, curvature_error}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Level set advection + reinit consistent; signed distance maintained | PASS |
| S2 | Viscosity solution unique; curvature computable from smooth φ | PASS |
| S3 | WENO + TVD-RK converges; reinit restores |∇φ|=1 | PASS |
| S4 | Interface error bounded by mesh size; area loss quantifiable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# level_set/zalesak_disk_s1.yaml
principle_ref: sha256:<p184_hash>
omega:
  grid: [128, 128]
  domain: [0, 1]²
  time: [0, 2π]   # one full rotation
E:
  forward: "∂φ/∂t + u·∇φ = 0 with periodic reinitialization"
  velocity: "rigid body rotation u = (0.5−y, x−0.5)"
B:
  all: periodic
I:
  scenario: zalesak_disk_rotation
  disk: {center: [0.5, 0.75], radius: 0.15, slot_width: 0.05}
  mesh_sizes: [64, 128, 256]
O: [interface_L1_error, area_conservation, shape_fidelity]
epsilon:
  L1_error_max: 5.0e-3
  area_loss_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves slot width (0.05); rotation returns to IC at t=2π | PASS |
| S2 | Advection is purely transport; exact return expected | PASS |
| S3 | WENO-5 + RK3 converges; reinit every 5 steps | PASS |
| S4 | L1 interface error < 5×10⁻³ at 128² | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# level_set/benchmark_zalesak.yaml
spec_ref: sha256:<spec184_hash>
principle_ref: sha256:<p184_hash>
dataset:
  name: Zalesak_disk_exact
  reference: "Zalesak (1979) — exact return to initial shape"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Level-set (ENO-2)
    params: {grid: 128, reinit_freq: 5}
    results: {L1_error: 8.5e-3, area_loss: 3.2%}
  - solver: Level-set (WENO-5)
    params: {grid: 128, reinit_freq: 5}
    results: {L1_error: 3.1e-3, area_loss: 1.5%}
  - solver: CLSVOF (coupled)
    params: {grid: 128}
    results: {L1_error: 1.8e-3, area_loss: 0.1%}
quality_scoring:
  - {min_L1: 1.0e-3, Q: 1.00}
  - {min_L1: 3.0e-3, Q: 0.90}
  - {min_L1: 6.0e-3, Q: 0.80}
  - {min_L1: 1.0e-2, Q: 0.75}
```

**Baseline solver:** WENO-5 level set — L1 error 3.1×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L1 Error | Area Loss | Runtime | Q |
|--------|----------|-----------|---------|---|
| ENO-2 | 8.5e-3 | 3.2% | 2 s | 0.75 |
| WENO-5 | 3.1e-3 | 1.5% | 5 s | 0.90 |
| CLSVOF | 1.8e-3 | 0.1% | 8 s | 0.90 |
| Particle LS | 8.2e-4 | 0.02% | 12 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (Particle LS): 300 × 1.00 = 300 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p184_hash>",
  "h_s": "sha256:<spec184_hash>",
  "h_b": "sha256:<bench184_hash>",
  "r": {"residual_norm": 8.2e-4, "error_bound": 5.0e-3, "ratio": 0.164},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep level_set
pwm-node verify level_set/zalesak_disk_s1.yaml
pwm-node mine level_set/zalesak_disk_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
