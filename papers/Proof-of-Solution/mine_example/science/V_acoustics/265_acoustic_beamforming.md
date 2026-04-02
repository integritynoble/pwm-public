# Principle #265 — Acoustic Source Localization (Beamforming)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** S.array → ∫.temporal → F.dft |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.array→∫.temporal→F.dft    beamform     source_localize     DAS/MVDR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ACOUSTIC SOURCE LOCALIZATION        P = (E,G,W,C)   Principle #265 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ B(θ) = |Σₙ wₙ xₙ exp(ikdₙ sin θ)|²                   │
│        │ Delay-and-sum or adaptive beamforming on array data    │
│        │ Forward: given array data, geometry → source DOA/map   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.array] ──→ [∫.temporal] ──→ [F.dft]                 │
│        │ sample  integrate  transform                           │
│        │ V={S.array, ∫.temporal, F.dft}  A={S.array→∫.temporal, ∫.temporal→F.dft}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (well-posed estimation problem)         │
│        │ Uniqueness: depends on array aperture and SNR          │
│        │ Stability: Rayleigh resolution limit λ/(2D)            │
│        │ Mismatch: Green's function model errors, noise corr.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = DOA estimation error |θ̂−θ_true| (primary)         │
│        │ q = depends on algorithm (DAS, MVDR, MUSIC)           │
│        │ T = {DOA_error, sidelobe_level, resolution}            │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Array geometry and signal model well-defined | PASS |
| S2 | Cramér-Rao bound establishes achievable DOA accuracy | PASS |
| S3 | DAS/MVDR/MUSIC converge with sufficient snapshots | PASS |
| S4 | DOA error bounded by CRB for given SNR and aperture | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# beamform/source_localization.yaml
principle_ref: sha256:<p265_hash>
omega:
  array: {type: ULA, N_elements: 16, spacing: 0.1}  # meters
  frequency: 1000  # Hz
  source_DOA: 30  # degrees
  SNR: 10  # dB
E:
  forward: "delay-and-sum / MVDR / MUSIC beamforming"
I:
  scenario: point_source_localization
  snapshots: [10, 100, 1000]
O: [DOA_error_deg, sidelobe_dB, resolution_deg]
epsilon:
  DOA_error_max: 1.0  # degrees
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | ULA with λ/2 spacing at 1 kHz; no spatial aliasing | PASS |
| S2 | Single source at 30° well within visible region | PASS |
| S3 | 1000 snapshots provide sufficient averaging for MVDR | PASS |
| S4 | DOA error < 1° achievable at SNR=10 dB with MUSIC | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# beamform/benchmark_source_localization.yaml
spec_ref: sha256:<spec265_hash>
principle_ref: sha256:<p265_hash>
dataset:
  name: ULA_source_localization_reference
  reference: "Monte Carlo CRB-achieving estimator"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DAS beamformer
    params: {snapshots: 1000}
    results: {DOA_error: 2.5, sidelobe: -13}
  - solver: MVDR (Capon)
    params: {snapshots: 1000}
    results: {DOA_error: 0.8, sidelobe: -25}
  - solver: MUSIC
    params: {snapshots: 1000}
    results: {DOA_error: 0.15, sidelobe: -40}
quality_scoring:
  - {min_DOA_error: 0.1, Q: 1.00}
  - {min_DOA_error: 1.0, Q: 0.90}
  - {min_DOA_error: 3.0, Q: 0.80}
  - {min_DOA_error: 5.0, Q: 0.75}
```

**Baseline solver:** MVDR — DOA error 0.8°
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | DOA Error (°) | Sidelobe (dB) | Runtime | Q |
|--------|---------------|---------------|---------|---|
| DAS | 2.5 | -13 | 0.1 s | 0.80 |
| MVDR | 0.8 | -25 | 0.5 s | 0.90 |
| MUSIC | 0.15 | -40 | 1 s | 1.00 |
| ESPRIT | 0.12 | N/A | 0.8 s | 1.00 |

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
  "h_p": "sha256:<p265_hash>",
  "h_s": "sha256:<spec265_hash>",
  "h_b": "sha256:<bench265_hash>",
  "r": {"residual_norm": 0.12, "error_bound": 1.0, "ratio": 0.12},
  "c": {"fitted_rate": 0.98, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep beamform
pwm-node verify beamform/source_localization.yaml
pwm-node mine beamform/source_localization.yaml
pwm-node inspect sha256:<cert_hash>
```
