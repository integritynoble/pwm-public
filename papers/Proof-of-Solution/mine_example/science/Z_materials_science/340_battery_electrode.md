# Principle #340 — Battery Electrode Modeling (Newman)

**Domain:** Materials Science | **Carrier:** electrochemical state | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → ∂.space → N.exponential → B.electrode |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          φ→i→c→η     Newman-P2D  LiCoO2-discharge   FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BATTERY ELECTRODE (NEWMAN)     P = (E,G,W,C)   Principle #340 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂c_s/∂t = (D_s/r²)∂/∂r(r²∂c_s/∂r)  (solid diffusion)│
│        │ ∂(εc_e)/∂t = ∇·(D_eff∇c_e) + a_s j_n (electrolyte)  │
│        │ ∇·(σ_eff∇φ_s) = a_s F j_n  (solid-phase potential)   │
│        │ j_n = i₀[exp(αFη/RT) − exp(−αFη/RT)] (BV kinetics)  │
│        │ Forward: given C-rate → compute V(t), SOC(t)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space] ──→ [N.exponential] ──→ [B.electrode] │
│        │ derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space, N.exponential, B.electrode}  A={∂.time→∂.space, ∂.space→N.exponential, N.exponential→B.electrode}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled parabolic + elliptic system)   │
│        │ Uniqueness: YES (for given C-rate and parameters)      │
│        │ Stability: voltage monotonically decreasing in discharge│
│        │ Mismatch: effective properties, particle size dist.    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖V_sim(t) − V_expt(t)‖₂ / ‖V_expt‖₂ (primary)  │
│        │ q = 2.0 (FEM), 1.0 (FVM)                            │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Solid/electrolyte transport and kinetics coupled consistently | PASS |
| S2 | P2D model well-posed for porous electrode geometry | PASS |
| S3 | FEM/FVM converge for coupled PDE system | PASS |
| S4 | Discharge voltage curve measurable against experiment | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# newman/licoo2_discharge_s1_ideal.yaml
principle_ref: sha256:<p340_hash>
omega:
  grid_macro: [50]  # electrode thickness
  grid_micro: [20]  # particle radius
  time: [0, 3600]  # 1C discharge
  dt: 1.0
E:
  forward: "P2D Newman model: solid diffusion + electrolyte transport + BV"
  model: pseudo_2D
B:
  cathode: {material: LiCoO2, thickness: 80e-6, particle_radius: 5e-6}
  anode: {material: graphite, thickness: 60e-6}
  separator: {thickness: 25e-6}
I:
  scenario: 1C_discharge
  C_rate: 1.0
  T: 298  # K
O: [voltage_curve, capacity, concentration_profiles]
epsilon:
  voltage_rms_max: 0.02  # V
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 macro + 20 micro nodes resolve gradients at 1C | PASS |
| S2 | LiCoO2/graphite parameters well-established | PASS |
| S3 | Implicit time-stepping stable for stiff BV kinetics | PASS |
| S4 | Voltage RMS < 20 mV achievable with calibrated params | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# newman/benchmark_licoo2.yaml
spec_ref: sha256:<spec340_hash>
principle_ref: sha256:<p340_hash>
dataset:
  name: licoo2_discharge_experimental
  reference: "Doyle et al. (1993) P2D model validation"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: PyBaMM (P2D)
    params: {grid: [50, 20], dt: 1.0}
    results: {voltage_rms: 0.015}
  - solver: COMSOL (P2D)
    params: {mesh: fine}
    results: {voltage_rms: 0.012}
  - solver: SPM (single particle)
    params: {}
    results: {voltage_rms: 0.08}
quality_scoring:
  - {min_voltage_rms: 0.005, Q: 1.00}
  - {min_voltage_rms: 0.02, Q: 0.90}
  - {min_voltage_rms: 0.05, Q: 0.80}
  - {min_voltage_rms: 0.10, Q: 0.75}
```

**Baseline solver:** PyBaMM (P2D) — voltage RMS 15 mV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Voltage RMS (V) | Runtime | Q |
|--------|----------------|---------|---|
| SPM | 0.08 | 1 s | 0.80 |
| PyBaMM (P2D) | 0.015 | 30 s | 0.90 |
| COMSOL (P2D) | 0.012 | 60 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 0.90 = 270 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p340_hash>",
  "h_s": "sha256:<spec340_hash>",
  "h_b": "sha256:<bench340_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.02, "ratio": 0.60},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep newman
pwm-node verify newman/licoo2_discharge_s1_ideal.yaml
pwm-node mine newman/licoo2_discharge_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
