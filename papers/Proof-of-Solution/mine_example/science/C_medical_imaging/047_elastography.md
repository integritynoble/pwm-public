# Principle #47 — Shear-Wave Elastography

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Standard (delta=3)
**DAG:** [G.pulse.acoustic] --> [K.elastic] --> [∫.temporal]
**Modality:** Shear-wave elastography (SWE)

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 shear wave eqn +       specific SWE         displacement data +   estimate stiffness
 inversion model        recon tasks          baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
rho * d^2u/dt^2 = mu * nabla^2 u     (shear wave equation)
v_s = sqrt(mu/rho),  E = 3*mu = 3*rho*v_s^2   (Young's modulus)
y(x,z,t) = u(x,z,t) + n             (tracked displacement)

  G.pulse.acoustic --> K.elastic --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.pulse.acoustic | Generate | Acoustic pulse excitation |
| K.elastic | Kernel | Elastic wave propagation kernel |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- shear wave speed measurable for given push
- Uniqueness: YES -- local v_s determines local stiffness uniquely
- Stability: kappa ~ 12 (homogeneous), kappa ~ 40 (heterogeneous with reflections)
- Mismatch: guided wave effects (d_guide), reflection artifacts (d_refl), viscosity (d_visc)

### Error Method

- Primary: stiffness RMSE (kPa), bias (%)
- Secondary: spatial resolution (mm), CNR between regions
- Convergence rate: q = 2.0 (time-of-flight), q = 1.0 (inversion-based)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Tracking frame rate sufficient for shear wave speed | PASS |
| S2 | Push amplitude generates measurable displacement | PASS |
| S3 | Time-of-flight estimator converges; inversion converges | PASS |
| S4 | Stiffness RMSE <= 15% achievable for CIRS phantom | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p47_hash>

omega:
  grid: [128, 64]
  tracking_fps: 10000
  push_duration_us: 200
  stiffness_range_kPa: [3, 80]

E:
  forward: "rho*d^2u/dt^2 = mu*nabla^2(u)"
  task: "shear modulus estimation from tracked displacements"

I:
  dataset: SWE_CIRS_Sim
  phantoms: 15
  noise: {type: gaussian, displacement_SNR: 20}
  scenario: ideal
  mismatch: null

O: [stiffness_RMSE_kPa, stiffness_bias_pct, CNR]

epsilon:
  stiffness_RMSE_max_pct: 15.0
  CNR_min: 2.0
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Homogeneous background | None | RMSE <= 15% |
| S2 Mismatch | Nominal density | d_refl, d_visc present | RMSE <= 25% |
| S3 Oracle | True density + viscosity | Known | RMSE <= 18% |
| S4 Blind Cal | Estimate from reference region | Calibration | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec47_hash>
principle_ref: sha256:<p47_hash>

dataset:
  name: SWE_CIRS_Sim
  phantoms: 15
  grid: [128, 64]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Time_of_Flight
    results: {mean_RMSE_pct: 12.5, mean_CNR: 2.3}
  - solver: Phase_Velocity
    results: {mean_RMSE_pct: 9.8, mean_CNR: 2.8}
  - solver: DL_Elastography
    results: {mean_RMSE_pct: 6.2, mean_CNR: 3.5}

quality_scoring:
  metric: mean_RMSE_pct
  thresholds:
    - {max: 4.0, Q: 1.00}
    - {max: 7.0, Q: 0.90}
    - {max: 12.0, Q: 0.80}
    - {max: 18.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | RMSE (%) | CNR | GPU Time | Q | Reward |
|--------|----------|-----|----------|---|--------|
| Time-of-Flight | 12.5 | 2.3 | <1 s | 0.80 | 240 PWM |
| Phase Velocity | 9.8 | 2.8 | ~5 s | 0.85 | 255 PWM |
| DL-Elastography | 6.2 | 3.5 | ~1 s | 0.92 | 276 PWM |
| Physics-NN SWE | 3.5 | 4.2 | ~2 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p47_hash>",
  "spec": "sha256:<spec47_hash>",
  "benchmark": "sha256:<bench47_hash>",
  "r": {"residual_norm": 0.035, "error_bound": 0.065, "ratio": 0.54},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.92,
  "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"}
}
```

---

## Reward Summary

```
Layer    One-time Seed          Ongoing Upstream
L1       200 x phi PWM          15% L2 + 10% L3 + 5% L4 mint
L2       105 PWM (x4 specs)     15% L3 + 10% L4 mint
L3        60 PWM (x4 benches)   15% L4 mint
L4       300 x q PWM per solve  Miner keeps 100%
```

---

## Quick-Start Commands

```bash
pwm-node benchmarks | grep elastography
pwm-node verify elastography/cirs_s1_ideal.yaml
pwm-node mine elastography/cirs_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
