# Principle #152 — XFEL Serial Femtosecond Crystallography (SFX)

**Domain:** Ultrafast Imaging | **Carrier:** X-ray (XFEL) | **Difficulty:** Frontier (δ=8)
**DAG:** G.pulse.laser --> K.scatter.bragg --> N.pointwise.abs2 | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.bragg-->N.pointwise.abs2    SFX         SFXSim-10          CrystFEL
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  XFEL SERIAL FEMTOSECOND CRYSTALLOGRAPHY   P = (E,G,W,C) #152  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(hkl) = |F(hkl)|² · P(ω) · L · A                    │
│        │ Single-crystal still shots; random orientations        │
│        │ "Diffract before destroy": fs pulse outruns damage     │
│        │ Inverse: merge partial intensities → full dataset → ρ  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.bragg] --> [N.pointwise.abs2]│
│        │  XFELPulse  BraggDiffract  ModSq                       │
│        │ V={G.pulse.laser, K.scatter.bragg, N.pointwise.abs2}  A={G.pulse.laser-->K.scatter.bragg, K.scatter.bragg-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bragg peaks from crystals > 200 nm)   │
│        │ Uniqueness: YES (random orientation sampling Ewald cap)│
│        │ Stability: κ ≈ 15 (10⁵ shots), κ ≈ 80 (10³ shots)     │
│        │ Mismatch: partiality, indexing ambiguity, jitter       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = R_split (primary), CC_1/2 (secondary)              │
│        │ q = 1.5 (Monte-Carlo integration √N convergence)      │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | XFEL photon energy, pulse duration, detector geometry, and crystal size consistent | PASS |
| S2 | ≥ 10⁴ indexed patterns yield sufficient redundancy for Monte-Carlo merging | PASS |
| S3 | MC integration converges as 1/√N; partiality correction bounded | PASS |
| S4 | R_split ≤ 15% and CC_1/2 ≥ 0.9 achievable at 3 Å resolution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xfel_sfx/sfxsim_s1.yaml
principle_ref: sha256:<p152_hash>
omega:
  photon_energy_keV: 9.5
  pulse_fs: 30
  resolution_A: 2.5
  crystal_size_um: 5
  n_patterns: 50000
  space_group: P2_1_2_1_2_1
E:
  forward: "I(hkl) = |F(hkl)|^2 * P(omega) * L * A (still-shot)"
  merging: "Monte_Carlo"
I:
  dataset: SFXSim_10
  proteins: 10
  patterns_per: 50000
  noise: {type: poisson, photons_per_pulse: 1e12}
  scenario: ideal
O: [R_split_pct, CC_half]
epsilon:
  R_split_max: 18.0
  CC_half_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 9.5 keV pulses at 30 fs for 5 µm crystals; geometry consistent | PASS |
| S2 | 50000 patterns with ~100× redundancy per reflection | PASS |
| S3 | MC merging converges as 1/√50000 for overall scale factors | PASS |
| S4 | R_split ≤ 18% and CC_1/2 ≥ 0.85 feasible at 2.5 Å | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xfel_sfx/benchmark_s1.yaml
spec_ref: sha256:<spec152_hash>
principle_ref: sha256:<p152_hash>
dataset:
  name: SFXSim_10
  proteins: 10
  patterns_per: 50000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CrystFEL-MC
    params: {iterations: 3}
    results: {R_split_pct: 16.0, CC_half: 0.88}
  - solver: CrystFEL-Partiality
    params: {model: ewald_offset}
    results: {R_split_pct: 12.0, CC_half: 0.93}
  - solver: cctbx-SFX
    params: {partiality: full, post_refine: true}
    results: {R_split_pct: 9.5, CC_half: 0.96}
quality_scoring:
  - {max_R: 10.0, Q: 1.00}
  - {max_R: 13.0, Q: 0.90}
  - {max_R: 18.0, Q: 0.80}
  - {max_R: 25.0, Q: 0.75}
```

**Baseline solver:** CrystFEL-Partiality — R_split 12.0%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | R_split (%) | CC_1/2 | Runtime | Q |
|--------|-------------|--------|---------|---|
| CrystFEL-MC | 16.0 | 0.88 | 10 min | 0.80 |
| CrystFEL-Partiality | 12.0 | 0.93 | 30 min | 0.90 |
| cctbx-SFX | 9.5 | 0.96 | 1 hr | 1.00 |
| DL-SFX (MergeNet) | 10.5 | 0.95 | 5 min | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (cctbx):     800 × 1.00 = 800 PWM
Floor:                 800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p152_hash>",
  "h_s": "sha256:<spec152_hash>",
  "h_b": "sha256:<bench152_hash>",
  "r": {"residual_norm": 0.095, "error_bound": 0.18, "ratio": 0.53},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
| L4 Solution | — | 600–800 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep xfel_sfx
pwm-node verify xfel_sfx/sfxsim_s1.yaml
pwm-node mine xfel_sfx/sfxsim_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
