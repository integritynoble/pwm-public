# Principle #106 — Very Long Baseline Interferometry (VLBI)

**Domain:** Remote Sensing | **Carrier:** Radio wave | **Difficulty:** Expert (δ=8)
**DAG:** S.sparse --> F.dft --> integral.baseline | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        S.sparse-->F.dft-->integral.baseline    VLBI-img   VLBI-Quasar         Imaging
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VLBI   P = (E, G, W, C)   Principle #106                      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V(u,v) = ∫∫ I(l,m)·e^{-j2π(ul+vm)} dl dm + n        │
│        │ Sparse visibility sampling in (u,v) Fourier plane      │
│        │ Earth-rotation synthesis fills (u,v) tracks             │
│        │ Inverse: image I(l,m) from sparse visibilities V(u,v) │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.sparse] --> [F.dft] --> [integral.baseline]           │
│        │ SparseArray  Correlate  UVSynth                          │
│        │ V={S.sparse, F.dft, integral.baseline}  A={S.sparse-->F.dft, F.dft-->integral.baseline}   L_DAG=5.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Fourier samples → image via CLEAN)    │
│        │ Uniqueness: NO — massively under-sampled (u,v) plane   │
│        │ Stability: κ ≈ 30 (dense tracks), κ ≈ 300 (sparse)    │
│        │ Mismatch: atmospheric phase, clock errors, bandpass     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = dynamic range (primary), fidelity (secondary)      │
│        │ q = 1.0 (CLEAN convergence)                           │
│        │ T = {dynamic_range, residual_rms, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Baseline lengths consistent with angular resolution target | PASS |
| S2 | Sparse (u,v) regularizable with CLEAN / MEM priors | PASS |
| S3 | CLEAN / RML algorithms converge for stated (u,v) coverage | PASS |
| S4 | Dynamic range > 100:1 achievable with calibrated data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# vlbi/quasar_s1_ideal.yaml
principle_ref: sha256:<p106_hash>
omega:
  image_grid: [512, 512]
  pixel_uas: 10
  frequency_GHz: 86
  baselines: 10
  stations: 8
E:
  forward: "V(u,v) = FT{I(l,m)} sampled at sparse (u,v)"
I:
  dataset: VLBI_Quasar
  sources: 15
  noise: {type: gaussian, thermal_SNR: 100}
  scenario: ideal
O: [dynamic_range, fidelity_pct]
epsilon:
  dynamic_range_min: 100
  fidelity_min_pct: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 stations → 28 baselines; 10 μas pixel at 86 GHz | PASS |
| S2 | Earth-rotation synthesis + regularization; κ ≈ 30 | PASS |
| S3 | CLEAN converges for 28-baseline tracks | PASS |
| S4 | DR > 100 and fidelity > 90% feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# vlbi/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec106_hash>
principle_ref: sha256:<p106_hash>
dataset:
  name: VLBI_Quasar
  sources: 15
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CLEAN
    results: {dynamic_range: 120, fidelity_pct: 91.5}
  - solver: MEM
    results: {dynamic_range: 250, fidelity_pct: 94.2}
  - solver: RML-ehtim
    results: {dynamic_range: 800, fidelity_pct: 97.5}
quality_scoring:
  - {min_DR: 1000, Q: 1.00}
  - {min_DR: 500, Q: 0.90}
  - {min_DR: 200, Q: 0.80}
  - {min_DR: 80, Q: 0.75}
```

**Baseline:** CLEAN — DR 120 | **Layer 3 reward:** 60 PWM + upstream

---

## Layer 4 — Benchmark → Solution

| Solver | Dyn Range | Fidelity | Q |
|--------|-----------|----------|---|
| CLEAN | 120 | 91.5% | 0.78 |
| MEM | 250 | 94.2% | 0.82 |
| RML-ehtim | 800 | 97.5% | 0.95 |
| VLBI-DL | 1200 | 98.8% | 1.00 |

### Reward: `R = 100 × 8 × q` → Best: 800 PWM | Floor: 600 PWM

```json
{
  "h_p": "sha256:<p106_hash>", "Q": 0.95,
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
| L4 Solution | — | 600–800 PWM per solve |

## Quick-Start

```bash
pwm-node benchmarks | grep vlbi
pwm-node mine vlbi/quasar_s1_ideal.yaml
```
