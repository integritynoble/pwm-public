# Principle #483 — Calorimeter Response Simulation

**Domain:** Particle Physics | **Carrier:** N/A (Monte Carlo transport) | **Difficulty:** Standard (δ=3)
**DAG:** [S.random] --> [K.green] --> [∫.volume] --> [N.pointwise] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.rand-->K.green-->∫.vol-->N.pw  CaloSim  test-beam  Geant4/fast
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CALORIMETER RESPONSE SIMULATION P=(E,G,W,C) Principle #483     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E_vis = Σ_i f_s(E_i) · ΔE_i   (sampling calorimeter) │
│        │ EM shower: X_0, E_c → longitudinal/lateral profile     │
│        │ Had shower: λ_I, e/h ratio → compensation              │
│        │ σ_E/E = a/√E ⊕ b/E ⊕ c  (resolution)                │
│        │ Forward: given (particle, E, geometry) → E_vis, σ     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.rand] ──→ [K.green] ──→ [∫.vol] ──→ [N.pw]          │
│        │  particle-gen  shower-kernel  calo-integ  response     │
│        │ V={S.rand,K.green,∫.vol,N.pw}  A={S.rand→K.green,K.green→∫.vol,∫.vol→N.pw}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Geant4 physics lists well-validated)   │
│        │ Uniqueness: statistical (shower fluctuations)          │
│        │ Stability: cross-section tables ensure convergence     │
│        │ Mismatch: hadronic model uncertainties, dead material  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |σ/E_sim − σ/E_data| (resolution difference)      │
│        │ q = N/A (MC transport)                                │
│        │ T = {linearity, resolution, e_h_ratio}                 │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy conservation per shower; sampling fraction consistent | PASS |
| S2 | EM showers well-understood (QED); hadronic within 5% | PASS |
| S3 | Geant4 FTFP_BERT produces convergent distributions | PASS |
| S4 | Resolution matches test-beam data within 10% relative | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# calo_sim/ecal_testbeam_s1.yaml
principle_ref: sha256:<p483_hash>
omega:
  events_per_energy: 10000
  domain: PbWO4_electromagnetic_calorimeter
  energies: [1, 2, 5, 10, 20, 50, 100, 200]   # GeV
E:
  forward: "Geant4 EM shower + optical photon collection"
  material: PbWO4
  X0: 0.89   # cm
  geometry: 5x5_crystal_matrix
B:
  beam: electron
  incidence: normal
  calibration: MIP_intercalibration
I:
  scenario: ECAL_electron_response
  physics_lists: [FTFP_BERT, QGSP_BERT, emstandard_opt4]
O: [linearity, resolution_stochastic, resolution_constant]
epsilon:
  linearity_max: 0.005    # relative
  resolution_match_max: 0.10   # relative difference
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10⁴ events/energy across 8 points; 5×5 matrix standard | PASS |
| S2 | EM showers in PbWO4 well-characterized | PASS |
| S3 | Geant4 produces stable shower statistics | PASS |
| S4 | Linearity < 0.5%; resolution within 10% of data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# calo_sim/benchmark_ecal.yaml
spec_ref: sha256:<spec483_hash>
principle_ref: sha256:<p483_hash>
dataset:
  name: CMS_ECAL_test_beam_2006
  reference: "CMS ECAL test beam results (Adzic et al., 2007)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Geant4 (FTFP_BERT)
    params: {events: 10k/E, physics: FTFP_BERT}
    results: {linearity: 0.003, resolution_diff: 0.08}
  - solver: Geant4 (emstandard_opt4)
    params: {events: 10k/E, physics: emstandard_opt4}
    results: {linearity: 0.002, resolution_diff: 0.05}
  - solver: Fast simulation (parameterized)
    params: {events: 100k/E}
    results: {linearity: 0.008, resolution_diff: 0.12}
quality_scoring:
  - {min_diff: 0.03, Q: 1.00}
  - {min_diff: 0.06, Q: 0.90}
  - {min_diff: 0.10, Q: 0.80}
  - {min_diff: 0.15, Q: 0.75}
```

**Baseline solver:** Geant4 (emstandard_opt4) — resolution diff 5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Linearity | Resol Diff | Runtime/event | Q |
|--------|-----------|-----------|---------------|---|
| Fast sim | 0.008 | 0.12 | 0.01 s | 0.75 |
| Geant4 FTFP_BERT | 0.003 | 0.08 | 2.0 s | 0.80 |
| Geant4 emopt4 | 0.002 | 0.05 | 2.5 s | 0.90 |
| Geant4 tuned + optical | 0.001 | 0.03 | 5.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (tuned): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p483_hash>",
  "h_s": "sha256:<spec483_hash>",
  "h_b": "sha256:<bench483_hash>",
  "r": {"resolution_diff": 0.03, "error_bound": 0.10, "ratio": 0.300},
  "c": {"linearity": 0.001, "energies": 8, "K": 3},
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
pwm-node benchmarks | grep calo_sim
pwm-node verify calo_sim/ecal_testbeam_s1.yaml
pwm-node mine calo_sim/ecal_testbeam_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
