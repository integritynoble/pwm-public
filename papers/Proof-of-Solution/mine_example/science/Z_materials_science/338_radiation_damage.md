# Principle #338 — Radiation Damage (Displacement Cascades)

**Domain:** Materials Science | **Carrier:** defect population | **Difficulty:** Frontier (δ=5)
**DAG:** S.random → N.bilinear.pair → ∂.time |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random→N.bilinear.pair→∂.time   rad-damage  Fe-cascade-MD      MD/BCA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RADIATION DAMAGE (CASCADES)    P = (E,G,W,C)   Principle #338 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ NRT: N_d = 0.8 E_dam / (2E_d)  (Norgett-Robinson-Torrens)│
│        │ MD: m_i d²r_i/dt² = −∇_i V(r₁...r_N)                 │
│        │ PKA → ballistic cascade → thermal spike → defect count│
│        │ Forward: given PKA energy, T → compute N_FP, cluster dist│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random] ──→ [N.bilinear.pair] ──→ [∂.time]          │
│        │ sample  nonlinear  derivative                          │
│        │ V={S.random, N.bilinear.pair, ∂.time}  A={S.random→N.bilinear.pair, N.bilinear.pair→∂.time}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (MD well-posed for short-range V)       │
│        │ Uniqueness: statistical (ensemble of PKA directions)   │
│        │ Stability: results converge with system size and runs  │
│        │ Mismatch: interatomic potential, electronic stopping   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |N_FP^sim − N_FP^expt| / N_FP^expt (primary)     │
│        │ q = O(1/√N_runs) statistical convergence             │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PKA energy and displacement threshold well-defined | PASS |
| S2 | MD equations well-posed; NRT gives analytic estimate | PASS |
| S3 | MD converges with system size and ensemble averaging | PASS |
| S4 | Surviving defect count measurable; NRT as upper bound | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# rad_damage/fe_cascade_s1_ideal.yaml
principle_ref: sha256:<p338_hash>
omega:
  atoms: 250000
  box: [50, 50, 50]  # lattice units
  time: [0, 20e-12]  # 20 ps
  dt: 0.1e-15  # adaptive
E:
  forward: "MD: F = -dV/dr, V = EAM potential for Fe"
  potential: Ackland_Fe_EAM
B:
  thermostat: {boundary_region: Berendsen, T: 300}
I:
  scenario: displacement_cascade
  PKA_energy: 10.0  # keV
  E_d: 40  # eV (displacement threshold)
  n_runs: 50
O: [surviving_FP, cluster_distribution, cascade_volume]
epsilon:
  N_FP_rel_error: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 250k atoms contain 10 keV cascade; boundary thermostat prevents artifacts | PASS |
| S2 | Fe EAM potential validated for displacement cascades | PASS |
| S3 | MD ensemble converges with 50 PKA directions | PASS |
| S4 | Surviving FP count compared to NRT and experimental DPA | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# rad_damage/benchmark_fe_cascade.yaml
spec_ref: sha256:<spec338_hash>
principle_ref: sha256:<p338_hash>
dataset:
  name: fe_cascade_md_reference
  reference: "Stoller (2012): surviving defect fractions in Fe"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: NRT (analytic)
    params: {E_d: 40}
    results: {N_FP: 100, survival_ratio: 1.0}
  - solver: MD (EAM, 100k atoms)
    params: {n_runs: 20}
    results: {N_FP: 35, survival_ratio: 0.35}
  - solver: MD (EAM, 250k atoms)
    params: {n_runs: 50}
    results: {N_FP: 32, survival_ratio: 0.32}
quality_scoring:
  - {min_FP_error: 0.05, Q: 1.00}
  - {min_FP_error: 0.10, Q: 0.90}
  - {min_FP_error: 0.20, Q: 0.80}
  - {min_FP_error: 0.30, Q: 0.75}
```

**Baseline solver:** MD (250k, 50 runs) — N_FP=32, survival ratio 0.32
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | N_FP | Survival Ratio | Runtime | Q |
|--------|------|---------------|---------|---|
| NRT (analytic) | 100 | 1.0 | 0.001 s | 0.75 |
| MD (100k, 20 runs) | 35 | 0.35 | 10 h | 0.80 |
| MD (250k, 50 runs) | 32 | 0.32 | 50 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (MD 250k): 500 × 0.90 = 450 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p338_hash>",
  "h_s": "sha256:<spec338_hash>",
  "h_b": "sha256:<bench338_hash>",
  "r": {"residual_norm": 0.08, "error_bound": 0.10, "ratio": 0.80},
  "c": {"fitted_rate": 0.5, "theoretical_rate": 0.5, "K": 3},
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
pwm-node benchmarks | grep rad_damage
pwm-node verify rad_damage/fe_cascade_s1_ideal.yaml
pwm-node mine rad_damage/fe_cascade_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
