# Principle #229 — Piezoelectricity

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.coupled.electromech] --> [B.electrode] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.coupled.electromech→B.electrode   piezo       PZT-actuator       FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PIEZOELECTRICITY                  P = (E,G,W,C)  Principle #229│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ = Cε − eᵀE   (mechanical constitutive)              │
│        │ D = eε + κE     (electrical constitutive)              │
│        │ ∇·σ = f,  ∇·D = ρ_f  (balance laws)                   │
│        │ Forward: given BC/voltage → solve for (u, φ)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.coupled.electromech] --> [B.electrode]           │
│        │ coupled-piezo-solve  electrode-BC                      │
│        │ V={L.coupled.electromech,B.electrode}  L_DAG=1.0      │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (symmetric saddle-point; well-posed)    │
│        │ Uniqueness: YES (positive-definite mechanical + dielec)│
│        │ Stability: coupling coefficient e controls sensitivity │
│        │ Mismatch: piezoelectric coefficient error, electrode BC│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-Q2); coupled u-φ convergence            │
│        │ T = {displacement_error, voltage_error, K_resolutions} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled mechanical-electrical system consistent; tensor symmetries ok | PASS |
| S2 | Linear coupled system; unique solution for given electrode BCs | PASS |
| S3 | FEM with coupled u-φ DOFs converges for piezoelectric problems | PASS |
| S4 | L2 error bounded by mesh-dependent coupled estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# piezoelectricity/pzt_actuator_s1_ideal.yaml
principle_ref: sha256:<p229_hash>
omega:
  grid: [64, 16]
  domain: PZT_patch_on_beam
  patch_length: 0.02
  beam_length: 0.1
E:
  forward: "Coupled sigma=Ce-eE, D=ee+kappaE"
  PZT_material:
    C_11: 121e9
    e_31: -5.4
    kappa_33: 13.0e-9
  substrate: {E: 70e9, nu: 0.3}
B:
  electrodes: {top: 100, bottom: 0}   # V
  beam_left: {u: [0,0], phi: ground}
I:
  scenario: PZT_bending_actuator
  voltages: [50, 100, 200]
  mesh_sizes: [16x4, 32x8, 64x16]
O: [L2_displacement_error, tip_deflection_error, electric_field_error]
epsilon:
  L2_error_max: 1.0e-3
  tip_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Electrode BCs properly modelled; mesh captures PZT layer | PASS |
| S2 | Linear piezoelectric coupling; analytical beam solution available | PASS |
| S3 | Coupled FEM converges for piezoelectric actuator problems | PASS |
| S4 | L2 error < 10⁻³ at 64×16 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# piezoelectricity/benchmark_pzt.yaml
spec_ref: sha256:<spec229_hash>
principle_ref: sha256:<p229_hash>
dataset:
  name: PZT_bending_actuator
  reference: "Crawley & de Luis (1987) — piezoelectric actuator beam model"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4 coupled (32×8)
    params: {h: 1/32}
    results: {L2_error: 3.8e-3, tip_error: 6.5e-3}
  - solver: FEM-Q8 coupled (32×8)
    params: {h: 1/32}
    results: {L2_error: 5.5e-4, tip_error: 1.0e-3}
  - solver: FEM-Q8 coupled (64×16)
    params: {h: 1/64}
    results: {L2_error: 1.3e-4, tip_error: 2.5e-4}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 5.0e-4, Q: 0.90}
  - {min_L2: 2.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 coupled (32×8) — L2 error 5.5×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Tip Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q4 coupled (32×8) | 3.8e-3 | 6.5e-3 | 3 s | 0.80 |
| FEM-Q8 coupled (32×8) | 5.5e-4 | 1.0e-3 | 10 s | 0.90 |
| FEM-Q8 coupled (64×16) | 1.3e-4 | 2.5e-4 | 40 s | 1.00 |
| Analytical beam model | 0.0 | 0.0 | 0.01 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (analytical): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p229_hash>",
  "h_s": "sha256:<spec229_hash>",
  "h_b": "sha256:<bench229_hash>",
  "r": {"residual_norm": 1.3e-4, "error_bound": 1.0e-3, "ratio": 0.13},
  "c": {"fitted_rate": 2.01, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep piezoelectricity
pwm-node verify piezoelectricity/pzt_actuator_s1_ideal.yaml
pwm-node mine piezoelectricity/pzt_actuator_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
