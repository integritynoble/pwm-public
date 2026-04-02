# Principle #474 — Dissipative Particle Dynamics (DPD)

**Domain:** Polymer Physics | **Carrier:** N/A (particle-based) | **Difficulty:** Standard (δ=3)
**DAG:** [S.random] --> [N.pointwise] --> [∂.time] --> [∫.ensemble] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.rand-->N.pw-->∂.t-->∫.ens  DPD-sim  polymer-melt  DPD-integrator
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DISSIPATIVE PARTICLE DYNAMICS (DPD) P=(E,G,W,C) Princ. #474   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ m dv_i/dt = Σ_j (F^C_ij + F^D_ij + F^R_ij)           │
│        │ F^C_ij = a_ij(1−r/r_c) r̂   (conservative, soft)      │
│        │ F^D_ij = −γ w^D(r)(r̂·v_ij) r̂  (dissipative)         │
│        │ F^R_ij = σ w^R(r) ξ_ij r̂ / √Δt  (random)            │
│        │ FDT: σ² = 2γk_BT,  w^D = (w^R)²                      │
│        │ Forward: given (a_ij,γ,T) → trajectories, ⟨observables⟩│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.rand] ──→ [N.pw] ──→ [∂.t] ──→ [∫.ens]              │
│        │  particles  pair-force  integration  average           │
│        │ V={S.rand,N.pw,∂.t,∫.ens}  A={S.rand→N.pw,N.pw→∂.t,∂.t→∫.ens}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Langevin-type SDE, well-posed)         │
│        │ Uniqueness: YES in distribution (ergodic thermostat)   │
│        │ Stability: FDT ensures canonical ensemble              │
│        │ Mismatch: coarse-graining level, a_ij parameterization │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |⟨O⟩ − O_ref|/O_ref  (observable error)           │
│        │ q = 1.0 (velocity-Verlet, weak order 1)              │
│        │ T = {temperature_drift, RDF_error, diffusion_coeff}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Forces pairwise, FDT satisfied σ²=2γk_BT; momentum conserved | PASS |
| S2 | Canonical ensemble maintained; ergodicity for soft potentials | PASS |
| S3 | Modified velocity-Verlet (DPD-VV) converges stably | PASS |
| S4 | RDF and diffusion coefficient match reference within 2% | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dpd_sim/polymer_melt_s1.yaml
principle_ref: sha256:<p474_hash>
omega:
  beads: 24000
  domain: cubic_box_L10
  time: [0, 100000.0]    # DPD units
  dt: 0.04
E:
  forward: "DPD forces + modified velocity-Verlet"
  a_ij: 25.0     # same-type repulsion
  gamma: 4.5
  kBT: 1.0
  chain_length: 10
B:
  periodic: [x, y, z]
  density: 3.0    # beads per r_c³
I:
  scenario: DPD_polymer_melt
  chain_lengths: [5, 10, 20, 50]
O: [temperature_stability, RDF, end_to_end_distance, diffusion]
epsilon:
  temperature_drift_max: 0.01
  RDF_error_max: 0.02
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 24000 beads at ρ=3; dt=0.04 within stability limit | PASS |
| S2 | FDT parameters consistent; periodic BC well-posed | PASS |
| S3 | DPD-VV integrator stable for 10⁵ steps | PASS |
| S4 | Temperature stable to <1%; RDF error <2% | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dpd_sim/benchmark_polymer.yaml
spec_ref: sha256:<spec474_hash>
principle_ref: sha256:<p474_hash>
dataset:
  name: DPD_polymer_melt_reference
  reference: "Groot & Warren (1997) DPD validation"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DPD-VV (standard)
    params: {dt: 0.04, gamma: 4.5}
    results: {T_drift: 0.008, RDF_error: 0.015, D_error: 0.03}
  - solver: DPD-VV (small dt)
    params: {dt: 0.02, gamma: 4.5}
    results: {T_drift: 0.003, RDF_error: 0.008, D_error: 0.015}
  - solver: DPD-S1 (Shardlow splitting)
    params: {dt: 0.04, gamma: 4.5}
    results: {T_drift: 0.002, RDF_error: 0.005, D_error: 0.010}
quality_scoring:
  - {min_err: 0.005, Q: 1.00}
  - {min_err: 0.01, Q: 0.90}
  - {min_err: 0.02, Q: 0.80}
  - {min_err: 0.05, Q: 0.75}
```

**Baseline solver:** DPD-VV (standard) — RDF error 1.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Drift | RDF Error | D Error | Q |
|--------|---------|-----------|---------|---|
| DPD-VV (dt=0.04) | 0.008 | 0.015 | 0.03 | 0.80 |
| DPD-VV (dt=0.02) | 0.003 | 0.008 | 0.015 | 0.90 |
| DPD-S1 (dt=0.04) | 0.002 | 0.005 | 0.010 | 1.00 |
| DPD-S1 (dt=0.02) | 0.001 | 0.003 | 0.005 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DPD-S1): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p474_hash>",
  "h_s": "sha256:<spec474_hash>",
  "h_b": "sha256:<bench474_hash>",
  "r": {"RDF_error": 0.005, "error_bound": 0.02, "ratio": 0.250},
  "c": {"T_drift": 0.002, "beads": 24000, "K": 4},
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
pwm-node benchmarks | grep dpd_sim
pwm-node verify dpd_sim/polymer_melt_s1.yaml
pwm-node mine dpd_sim/polymer_melt_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
