# Principle #487 — Jet Reconstruction (Anti-kT)

**Domain:** Particle Physics | **Carrier:** N/A (algorithmic) | **Difficulty:** Standard (δ=3)
**DAG:** [S.sparse] --> [N.pointwise] --> [∫.ensemble] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.sparse-->N.pw-->∫.ens  JetReco  LHC-dijet  FastJet
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  JET RECONSTRUCTION (ANTI-KT)  P = (E,G,W,C)  Principle #487   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ d_ij = min(p²ᵖ_Ti, p²ᵖ_Tj) ΔR²_ij/R²                │
│        │ d_iB = p²ᵖ_Ti   (beam distance)                       │
│        │ p = −1: anti-k_T (hard seeds → circular jets)         │
│        │ ΔR²_ij = (y_i−y_j)² + (φ_i−φ_j)²                    │
│        │ Forward: given particles → jet 4-vectors               │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.sparse] ──→ [N.pw] ──→ [∫.ens]                      │
│        │  tower-hits  recombine  jet-avg                        │
│        │ V={S.sparse,N.pw,∫.ens}  A={S.sparse→N.pw,N.pw→∫.ens}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (algorithm terminates in finite steps)  │
│        │ Uniqueness: YES (deterministic clustering)             │
│        │ Stability: IRC safe (infrared and collinear)           │
│        │ Mismatch: pileup contamination, UE subtraction         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |p_T^reco − p_T^truth|/p_T^truth (JES residual)  │
│        │ q = N/A (algorithmic, exact)                          │
│        │ T = {JES_residual, JER, IRC_safety_check}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Distance metric Lorentz-invariant; 4-momentum conserved in merge | PASS |
| S2 | Anti-k_T IRC safe by construction (p = −1) | PASS |
| S3 | FastJet O(N ln N) algorithm terminates for N < 10⁶ | PASS |
| S4 | JES residual < 1% after calibration; JER bounded | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# jet_reco/dijet_s1.yaml
principle_ref: sha256:<p487_hash>
omega:
  events: 100000
  domain: pp_collisions_13TeV
  R_param: 0.4
E:
  forward: "anti-k_T clustering via FastJet"
  p_exponent: -1
  recombination: E_scheme
B:
  particles: truth_stable + detector_smearing
  pileup: {mu: 50, subtraction: area_based}
I:
  scenario: dijet_reconstruction
  R_values: [0.2, 0.4, 0.6, 1.0]
O: [JES_residual, JER, pileup_offset]
epsilon:
  JES_max: 0.01
  JER_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10⁵ events at 13 TeV; R=0.4 standard for ATLAS/CMS | PASS |
| S2 | Anti-k_T IRC safe; area subtraction removes pileup bias | PASS |
| S3 | FastJet clustering completes in < 0.1 s per event | PASS |
| S4 | JES < 1% after area-based pileup subtraction | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# jet_reco/benchmark_dijet.yaml
spec_ref: sha256:<spec487_hash>
principle_ref: sha256:<p487_hash>
dataset:
  name: LHC_dijet_MC_truth
  reference: "Cacciari, Salam & Soyez (2008) anti-k_T"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Anti-k_T (no pileup sub)
    params: {R: 0.4, pileup: none}
    results: {JES: 0.08, JER: 0.12}
  - solver: Anti-k_T + area subtraction
    params: {R: 0.4, pileup: area, rho_estimation: median}
    results: {JES: 0.008, JER: 0.10}
  - solver: Anti-k_T + PUPPI
    params: {R: 0.4, pileup: PUPPI}
    results: {JES: 0.005, JER: 0.08}
quality_scoring:
  - {min_JES: 0.003, Q: 1.00}
  - {min_JES: 0.008, Q: 0.90}
  - {min_JES: 0.015, Q: 0.80}
  - {min_JES: 0.050, Q: 0.75}
```

**Baseline solver:** Anti-k_T + area sub — JES 0.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | JES | JER | Runtime/event | Q |
|--------|-----|-----|---------------|---|
| No pileup sub | 0.08 | 0.12 | 0.01 s | 0.75 |
| Area subtraction | 0.008 | 0.10 | 0.02 s | 0.90 |
| PUPPI | 0.005 | 0.08 | 0.05 s | 0.90 |
| SoftKiller + trimming | 0.003 | 0.07 | 0.03 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SoftKiller): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p487_hash>",
  "h_s": "sha256:<spec487_hash>",
  "h_b": "sha256:<bench487_hash>",
  "r": {"JES": 0.003, "error_bound": 0.01, "ratio": 0.300},
  "c": {"JER": 0.07, "events": 100000, "K": 4},
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
pwm-node benchmarks | grep jet_reco
pwm-node verify jet_reco/dijet_s1.yaml
pwm-node mine jet_reco/dijet_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
