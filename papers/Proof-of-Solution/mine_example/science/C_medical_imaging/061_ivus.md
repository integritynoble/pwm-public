# Principle #61 — Intravascular Ultrasound

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Standard (delta=3)
**DAG:** [G.pulse.acoustic] --> [K.green.acoustic] --> [∫.temporal]
**Modality:** Intravascular ultrasound (IVUS)

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 rotary transducer +    specific IVUS        pullback data +       segment lumen
 vessel wall model      tasks                baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y(r, theta) = sum_k sigma_k * h(r - r_k, theta) + n
r = radial depth, theta = rotary angle (360 deg coverage)

  G.pulse.acoustic --> K.green.acoustic --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.pulse.acoustic | Generate | Acoustic pulse excitation |
| K.green.acoustic | Kernel | Acoustic Green’s function propagation |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- vessel wall reflectivity generates echoes
- Uniqueness: YES -- radial + angular scanning covers cross-section
- Stability: kappa ~ 12 (blood-free), kappa ~ 30 (with blood speckle)
- Mismatch: catheter eccentricity (d_ecc), NURD (non-uniform rotational distortion) (d_nurd), ring-down artifact (d_ring)

### Error Method

- Primary: lumen area error (%), wall segmentation Dice
- Secondary: plaque burden accuracy (%), media-adventitia Dice
- Convergence rate: q = 2.0 (polar-to-Cartesian), q = 1.0 (iterative segmentation)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular lines and radial samples consistent with catheter geometry | PASS |
| S2 | Frequency and aperture sufficient for wall resolution | PASS |
| S3 | Active contour / CNN segmentation converges | PASS |
| S4 | Lumen area error <= 10% for coronary phantom | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p61_hash>

omega:
  radial_samples: 1024
  angular_lines: 256
  freq_MHz: 40
  catheter_od_mm: 1.0

E:
  forward: "y(r,theta) = sum sigma_k*h(r-r_k,theta) + n"
  task: "lumen and vessel wall segmentation"

I:
  dataset: IVUS_Coronary_Sim
  pullbacks: 20
  noise: {type: speckle, SNR_dB: 30}
  scenario: ideal
  mismatch: null

O: [lumen_area_error_pct, wall_Dice]

epsilon:
  lumen_error_max_pct: 10.0
  wall_Dice_min: 0.80
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Centered catheter | None | lumen error <= 10% |
| S2 Mismatch | Eccentric catheter | d_ecc=0.3mm, d_nurd=5% | lumen error <= 18% |
| S3 Oracle | True geometry | Known | lumen error <= 12% |
| S4 Blind Cal | Estimate center from data | Edge detection | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec61_hash>
principle_ref: sha256:<p61_hash>

dataset:
  name: IVUS_Coronary_Sim
  pullbacks: 20
  frames: 200
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Active_Contour
    results: {mean_lumen_error_pct: 9.5, wall_Dice: 0.81}
  - solver: U-Net_IVUS
    results: {mean_lumen_error_pct: 5.8, wall_Dice: 0.88}
  - solver: TransIVUS
    results: {mean_lumen_error_pct: 3.2, wall_Dice: 0.93}

quality_scoring:
  metric: mean_lumen_error_pct
  thresholds:
    - {max: 2.0, Q: 1.00}
    - {max: 4.0, Q: 0.90}
    - {max: 8.0, Q: 0.80}
    - {max: 12.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | Lumen Error (%) | Wall Dice | GPU Time | Q | Reward |
|--------|-----------------|-----------|----------|---|--------|
| Active Contour | 9.5 | 0.81 | ~5 s | 0.78 | 234 PWM |
| U-Net IVUS | 5.8 | 0.88 | ~1 s | 0.88 | 264 PWM |
| TransIVUS | 3.2 | 0.93 | ~2 s | 0.93 | 279 PWM |
| IVUS-SegNet | 1.5 | 0.96 | ~3 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p61_hash>",
  "spec": "sha256:<spec61_hash>",
  "benchmark": "sha256:<bench61_hash>",
  "r": {"residual_norm": 0.025, "error_bound": 0.05, "ratio": 0.50},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.93,
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
pwm-node benchmarks | grep ivus
pwm-node verify ivus/coronary_s1_ideal.yaml
pwm-node mine ivus/coronary_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
