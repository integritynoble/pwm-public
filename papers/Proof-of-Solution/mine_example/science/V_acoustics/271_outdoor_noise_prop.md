# Principle #271 — Outdoor Noise Propagation

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** G.point → K.psf.gaussian → ∫.path |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.psf.gaussian→∫.path    outdoor_nse  point_over_ground   ISO9613/PE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OUTDOOR NOISE PROPAGATION           P = (E,G,W,C)   Principle #271 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ TL(r) = 20log₁₀(r) + α_atm·r + ΔL_ground + ΔL_barrier│
│        │ Atmospheric absorption, ground reflection, diffraction │
│        │ Forward: given source, terrain, atmo → compute SPL     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.psf.gaussian] ──→ [∫.path]            │
│        │ source  kernel  integrate                              │
│        │ V={G.point, K.psf.gaussian, ∫.path}  A={G.point→K.psf.gaussian, K.psf.gaussian→∫.path}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (well-posed propagation models)         │
│        │ Uniqueness: YES (deterministic atmosphere/terrain)     │
│        │ Stability: sensitive to wind/temperature gradients     │
│        │ Mismatch: atmospheric variability, ground impedance    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = SPL error |SPL−SPL_ref| in dB (primary)           │
│        │ q = depends on model (engineering vs PE)              │
│        │ T = {excess_attenuation_error, frequency_spectrum}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Source power, terrain profile, and atmosphere well-defined | PASS |
| S2 | Outdoor PE models validated against field measurements | PASS |
| S3 | PE marching solution converges with grid refinement | PASS |
| S4 | SPL error bounded by comparison with reference PE solutions | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# outdoor_nse/point_over_ground.yaml
principle_ref: sha256:<p271_hash>
omega:
  source_height: 2.0  # meters
  receiver_height: 1.5
  range: 1000  # meters
  frequency: [63, 125, 250, 500, 1000, 2000, 4000]
E:
  forward: "outdoor sound propagation over flat impedance ground"
  atmosphere: {temperature: 20, humidity: 60, wind: 0}
  ground: {sigma: 200}  # kPa·s/m² (grass)
I:
  scenario: point_source_over_ground
O: [excess_attenuation_error_dB, A_weighted_error]
epsilon:
  EA_error_max: 2.0  # dB per octave band
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Flat terrain; Delany-Bazley ground impedance model | PASS |
| S2 | Analytic ground-reflection solution exists for flat ground | PASS |
| S3 | PE outdoor propagation converges for 1 km range | PASS |
| S4 | EA error < 2 dB per band achievable with PE | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# outdoor_nse/benchmark_point_over_ground.yaml
spec_ref: sha256:<spec271_hash>
principle_ref: sha256:<p271_hash>
dataset:
  name: outdoor_propagation_reference
  reference: "Analytic Weyl-van der Pol ground reflection solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ISO 9613-2
    params: {standard: true}
    results: {EA_error: 4.5, A_weighted_error: 3.2}
  - solver: NORD2000
    params: {terrain: flat}
    results: {EA_error: 1.5, A_weighted_error: 1.0}
  - solver: PE outdoor (Δr=1m)
    params: {dr: 1.0, dz: 0.1}
    results: {EA_error: 0.3, A_weighted_error: 0.2}
quality_scoring:
  - {min_EA_err: 0.5, Q: 1.00}
  - {min_EA_err: 2.0, Q: 0.90}
  - {min_EA_err: 4.0, Q: 0.80}
  - {min_EA_err: 6.0, Q: 0.75}
```

**Baseline solver:** NORD2000 — EA error 1.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | EA Error (dB) | A-weighted Error (dB) | Runtime | Q |
|--------|---------------|----------------------|---------|---|
| ISO 9613-2 | 4.5 | 3.2 | 0.1 s | 0.75 |
| NORD2000 | 1.5 | 1.0 | 2 s | 0.90 |
| PE outdoor (coarse) | 0.8 | 0.5 | 15 s | 0.95 |
| PE outdoor (fine) | 0.3 | 0.2 | 60 s | 1.00 |

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
  "h_p": "sha256:<p271_hash>",
  "h_s": "sha256:<spec271_hash>",
  "h_b": "sha256:<bench271_hash>",
  "r": {"residual_norm": 0.3, "error_bound": 2.0, "ratio": 0.15},
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
pwm-node benchmarks | grep outdoor_nse
pwm-node verify outdoor_nse/point_over_ground.yaml
pwm-node mine outdoor_nse/point_over_ground.yaml
pwm-node inspect sha256:<cert_hash>
```
