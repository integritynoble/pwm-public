# Principle #484 — Charged Particle Tracking in Detectors

**Domain:** Particle Physics | **Carrier:** N/A (algorithmic) | **Difficulty:** Standard (δ=3)
**DAG:** [S.sparse] --> [K.green] --> [O.l2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.sparse-->K.green-->O.l2  Tracking  TrackML-bench  Kalman/CKF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CHARGED PARTICLE TRACKING      P = (E,G,W,C)  Principle #484  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ x_{k+1} = F_k x_k + w_k   (state propagation in B)   │
│        │ m_k = H_k x_k + v_k       (measurement model)         │
│        │ x = (x,y,z,p_x,p_y,p_z)   (track state)              │
│        │ Helix in B: R = p_T/(qB),  sagitta → p_T resolution   │
│        │ Forward: given hits → reconstruct tracks (p, vertex)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.sparse] ──→ [K.green] ──→ [O.l2]                    │
│        │  hit-pattern  propagator  track-fit                    │
│        │ V={S.sparse,K.green,O.l2}  A={S.sparse→K.green,K.green→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Kalman filter well-defined)            │
│        │ Uniqueness: combinatorial ambiguity resolved by χ²     │
│        │ Stability: bounded by measurement noise and B-field    │
│        │ Mismatch: material interactions, misalignment          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = track efficiency / fake rate / p_T resolution      │
│        │ q = N/A (estimation)                                  │
│        │ T = {efficiency, fake_rate, pT_resolution, d0_resol}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | State vector 5/6-param; Jacobian from helix in B consistent | PASS |
| S2 | Kalman filter optimal for Gaussian noise; well-posed | PASS |
| S3 | CKF (combinatorial Kalman) converges for track densities < 100/event | PASS |
| S4 | Efficiency > 95%, fake rate < 5% for isolated tracks | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tracking/trackml_s1.yaml
principle_ref: sha256:<p484_hash>
omega:
  events: 1000
  domain: generic_LHC_detector
  pileup: 200
E:
  forward: "seeding + Kalman filter track following"
  B_field: 2.0      # Tesla
  layers: 10
  sigma_hit: 50e-6   # meters
B:
  geometry: cylindrical_silicon_tracker
  material: silicon_300um
I:
  scenario: TrackML_challenge
  pileup_levels: [1, 50, 200]
O: [efficiency, fake_rate, pT_resolution, score]
epsilon:
  efficiency_min: 0.90
  fake_rate_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 layers, σ=50 μm, B=2T; standard LHC-like geometry | PASS |
| S2 | Kalman filter well-posed for given geometry and noise | PASS |
| S3 | CKF + ambiguity resolver converges per event | PASS |
| S4 | Efficiency > 90% at pileup 200 achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tracking/benchmark_trackml.yaml
spec_ref: sha256:<spec484_hash>
principle_ref: sha256:<p484_hash>
dataset:
  name: TrackML_particle_tracking_challenge
  reference: "Amrouche et al. (2020) TrackML challenge"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Hough transform
    params: {bins: 1000}
    results: {efficiency: 0.82, fake_rate: 0.12, score: 0.75}
  - solver: CKF (ACTS)
    params: {seeding: default, chi2_cut: 15}
    results: {efficiency: 0.92, fake_rate: 0.04, score: 0.88}
  - solver: GNN tracking
    params: {model: interaction_network}
    results: {efficiency: 0.95, fake_rate: 0.03, score: 0.93}
quality_scoring:
  - {min_score: 0.95, Q: 1.00}
  - {min_score: 0.90, Q: 0.90}
  - {min_score: 0.85, Q: 0.80}
  - {min_score: 0.75, Q: 0.75}
```

**Baseline solver:** CKF (ACTS) — score 0.88
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Efficiency | Fake Rate | Score | Q |
|--------|-----------|-----------|-------|---|
| Hough transform | 0.82 | 0.12 | 0.75 | 0.75 |
| CKF (ACTS) | 0.92 | 0.04 | 0.88 | 0.80 |
| GNN tracking | 0.95 | 0.03 | 0.93 | 0.90 |
| GNN + CKF hybrid | 0.97 | 0.02 | 0.96 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (hybrid): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p484_hash>",
  "h_s": "sha256:<spec484_hash>",
  "h_b": "sha256:<bench484_hash>",
  "r": {"score": 0.96, "error_bound": 0.90, "ratio": 1.067},
  "c": {"efficiency": 0.97, "events": 1000, "K": 3},
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
pwm-node benchmarks | grep tracking
pwm-node verify tracking/trackml_s1.yaml
pwm-node mine tracking/trackml_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
