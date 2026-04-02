# Principle #268 — Vibroacoustics (Structure-Borne Sound)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** L.sparse → K.green.acoustic → L.dense |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.sparse→K.green.acoustic→L.dense    vibroacoust  plate_radiation     FEM-BEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VIBROACOUSTICS (STRUCTURE-BORNE)    P = (E,G,W,C)   Principle #268 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [K_s − ω²M_s + C_fs] u = f;  p = C_sf u              │
│        │ Coupled FEM-structural + BEM-acoustic system           │
│        │ Forward: given structure vibration → radiated sound    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.sparse] ──→ [K.green.acoustic] ──→ [L.dense]        │
│        │ linear-op  kernel  linear-op                           │
│        │ V={L.sparse, K.green.acoustic, L.dense}  A={L.sparse→K.green.acoustic, K.green.acoustic→L.dense}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled linear system at each ω)      │
│        │ Uniqueness: YES (at non-resonant frequencies)          │
│        │ Stability: fluid-structure coupling shifts frequencies │
│        │ Mismatch: damping model, boundary impedance, mesh      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖p−p_ref‖/‖p_ref‖ (primary)    │
│        │ q = 2.0 (linear FEM-BEM), 4.0 (quadratic)            │
│        │ T = {radiated_power_error, directivity_match}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Structural and acoustic meshes compatible; coupling well-defined | PASS |
| S2 | Linear coupled system has unique solution at non-resonant ω | PASS |
| S3 | FEM-BEM coupling converges with mesh refinement | PASS |
| S4 | Radiated power error bounded by mesh-dependent estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# vibroacoust/plate_radiation.yaml
principle_ref: sha256:<p268_hash>
omega:
  plate: {Lx: 0.5, Ly: 0.3, thickness: 0.002}
  baffle: infinite_rigid
  frequency_range: [100, 2000]  # Hz
E:
  forward: "FEM structural + BEM acoustic radiation"
  material: {E: 70e9, rho: 2700, nu: 0.33}  # aluminum
I:
  scenario: plate_radiation_baffled
  mesh_sizes: [10, 20, 40]  # elements per side
O: [radiated_power_error_dB, directivity_L2]
epsilon:
  power_error_max: 1.0  # dB
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Plate mesh resolves bending wavelength at 2 kHz | PASS |
| S2 | Baffled plate has analytic radiation impedance reference | PASS |
| S3 | FEM-BEM converges with 40 elements per side | PASS |
| S4 | Radiated power error < 1 dB achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# vibroacoust/benchmark_plate_radiation.yaml
spec_ref: sha256:<spec268_hash>
principle_ref: sha256:<p268_hash>
dataset:
  name: baffled_plate_radiation_reference
  reference: "Rayleigh integral analytic solution for baffled piston modes"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-BEM (linear, 10×10)
    params: {mesh: 10, element: linear}
    results: {power_error: 3.5, directivity_L2: 0.08}
  - solver: FEM-BEM (linear, 20×20)
    params: {mesh: 20, element: linear}
    results: {power_error: 0.9, directivity_L2: 0.02}
  - solver: FEM-BEM (quadratic, 20×20)
    params: {mesh: 20, element: quadratic}
    results: {power_error: 0.2, directivity_L2: 0.004}
quality_scoring:
  - {min_power_err: 0.2, Q: 1.00}
  - {min_power_err: 1.0, Q: 0.90}
  - {min_power_err: 3.0, Q: 0.80}
  - {min_power_err: 5.0, Q: 0.75}
```

**Baseline solver:** FEM-BEM (linear, 20×20) — power error 0.9 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Power Error (dB) | Directivity L2 | Runtime | Q |
|--------|-----------------|-----------------|---------|---|
| FEM-BEM (10×10) | 3.5 | 0.08 | 5 s | 0.75 |
| FEM-BEM (20×20) | 0.9 | 0.02 | 25 s | 0.90 |
| FEM-BEM quad (20×20) | 0.2 | 0.004 | 60 s | 1.00 |
| Rayleigh integral (40×40) | 0.15 | 0.003 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p268_hash>",
  "h_s": "sha256:<spec268_hash>",
  "h_b": "sha256:<bench268_hash>",
  "r": {"residual_norm": 0.15, "error_bound": 1.0, "ratio": 0.15},
  "c": {"fitted_rate": 2.05, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep vibroacoust
pwm-node verify vibroacoust/plate_radiation.yaml
pwm-node mine vibroacoust/plate_radiation.yaml
pwm-node inspect sha256:<cert_hash>
```
