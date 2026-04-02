# Principle #128 — Atom Probe Tomography (APT)

**Domain:** Scientific Instrumentation | **Carrier:** Field-evaporated Ion | **Difficulty:** Research (δ=5)
**DAG:** G.pulse --> N.exponential --> S.spectral | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse-->N.exponential-->S.spectral    APT         AlloyNeedle-15     Recon3D
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ATOM PROBE TOMOGRAPHY (APT)   P = (E, G, W, C)   #128         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ (x,y) = L/k_f × (X,Y)_det / (R + d)                  │
│        │ m/z = 2eV t²/d²; field evaporation F = V/(k_f R)      │
│        │ Point-projection model; z from evaporation sequence    │
│        │ Inverse: reconstruct 3D atomic positions + chemistry   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [N.exponential] --> [S.spectral]           │
│        │  FieldPulse  FieldEvap  ToFMass                        │
│        │ V={G.pulse, N.exponential, S.spectral}  A={G.pulse-->N.exponential, N.exponential-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (field evaporation always produces ions)│
│        │ Uniqueness: LIMITED (trajectory aberrations, multi-hits)│
│        │ Stability: κ ≈ 20 (metallic), κ ≈ 100 (oxide/semi)  │
│        │ Mismatch: local magnification, preferential evaporation│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = spatial resolution nm (primary), composition acc.  │
│        │ q = 1.0 (point-projection reconstruction)             │
│        │ T = {spatial_resolution, composition_accuracy, yield}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Detector covers full projection cone; TOF resolution separates isotopes | PASS |
| S2 | Point-projection model valid for tip radius R < 100 nm | PASS |
| S3 | z-increment converges with voltage curve for known tip shape | PASS |
| S4 | Spatial resolution ≤ 0.3 nm lateral achievable for pure metals | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# apt/alloyneedle_s1.yaml
principle_ref: sha256:<p128_hash>
omega:
  tip_radius_nm: 50
  flight_path_mm: 100
  detector_efficiency: 0.60
  field_factor: 3.3
  temperature_K: 50
E:
  forward: "(x,y) = L * (X,Y)_det / (k_f * R + d)"
  mass: "m/z = 2eV * t^2 / d^2"
I:
  dataset: AlloyNeedle_15
  specimens: 15
  alloy_types: [NiCrAl_superalloy, FeCrNi_steel, AlCuMg]
  ions_per_specimen: 10e6
O: [spatial_resolution_nm, composition_accuracy_pct]
epsilon:
  resolution_max: 0.5
  composition_error_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 60% detector efficiency with 100 mm flight path resolves m/z | PASS |
| S2 | κ ≈ 20 for metallic alloy tips at 50 K | PASS |
| S3 | Voltage-curve-based z-spacing converges for 10M ions | PASS |
| S4 | Resolution ≤ 0.5 nm and composition error ≤ 2% feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# apt/benchmark_s1.yaml
spec_ref: sha256:<spec128_hash>
principle_ref: sha256:<p128_hash>
dataset:
  name: AlloyNeedle_15
  specimens: 15
  ions_total: 150e6
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Bas-Protocol
    params: {image_compression: 1.65}
    results: {resolution: 0.40, composition_error: 1.8}
  - solver: Geiser-Protocol
    params: {cone_angle: auto}
    results: {resolution: 0.35, composition_error: 1.5}
  - solver: ML-Trajectory-Correction
    params: {model: GNN}
    results: {resolution: 0.25, composition_error: 1.0}
quality_scoring:
  - {max_resolution: 0.25, Q: 1.00}
  - {max_resolution: 0.35, Q: 0.90}
  - {max_resolution: 0.50, Q: 0.80}
  - {max_resolution: 0.70, Q: 0.75}
```

**Baseline solver:** Bas-Protocol — resolution 0.40 nm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Resolution (nm) | Comp. Error (%) | Runtime | Q |
|--------|-----------------|-----------------|---------|---|
| Bas-Protocol | 0.40 | 1.8 | 30 s | 0.80 |
| Geiser-Protocol | 0.35 | 1.5 | 60 s | 0.90 |
| ML-Trajectory-Correction | 0.25 | 1.0 | 5 min | 1.00 |
| Field-Simulation-Corrected | 0.30 | 1.2 | 30 min | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (ML-Traj.):  500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p128_hash>",
  "h_s": "sha256:<spec128_hash>",
  "h_b": "sha256:<bench128_hash>",
  "r": {"residual_norm": 0.25, "error_bound": 0.50, "ratio": 0.50},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep apt
pwm-node verify apt/alloyneedle_s1.yaml
pwm-node mine apt/alloyneedle_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
