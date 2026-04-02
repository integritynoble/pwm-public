# Principle #466 — GNSS Positioning

**Domain:** Geodesy | **Carrier:** N/A (estimation-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∫.temporal] --> [L.sparse] --> [O.l2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∫.temp-->L.sparse-->O.l2  GNSS-pos  IGS-stations  LSQ/Kalman
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GNSS POSITIONING              P = (E,G,W,C)   Principle #466   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρ_i = |r_user − r_sat_i| + c·δt_user − c·δt_sat_i    │
│        │       + I_i + T_i + ε_i   (pseudorange observation)    │
│        │ φ_i = |r_user − r_sat_i| + c·δt_user − c·δt_sat_i    │
│        │       − I_i + T_i + λ N_i + ε_φ  (carrier phase)      │
│        │ Forward: given observations → estimate (x,y,z,δt)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∫.temp] ──→ [L.sparse] ──→ [O.l2]                     │
│        │  time-integ  sparse-obs  least-squares                 │
│        │ V={∫.temp,L.sparse,O.l2}  A={∫.temp→L.sparse,L.sparse→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (≥4 satellites → solvable)              │
│        │ Uniqueness: YES with GDOP < threshold                  │
│        │ Stability: GDOP determines position dilution           │
│        │ Mismatch: multipath, ionospheric scintillation         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖r_est − r_true‖₂  (3D position error, meters)   │
│        │ q = N/A (statistical estimation)                      │
│        │ T = {position_RMS, clock_bias, GDOP}                   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pseudorange/phase equations dimensionally consistent (meters) | PASS |
| S2 | ≥ 4 satellites ensures solvability; GDOP finite | PASS |
| S3 | Iterative LSQ and extended Kalman filter converge | PASS |
| S4 | Position RMS bounded by GDOP × σ_range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gnss_pos/igs_static_s1.yaml
principle_ref: sha256:<p466_hash>
omega:
  stations: 10
  domain: IGS_network
  time: [0, 86400.0]    # 24 hours
  interval: 30.0         # seconds
E:
  forward: "pseudorange + carrier phase → position + clock"
  systems: [GPS, Galileo]
  corrections: [iono_dual_freq, tropo_Saastamoinen, solid_earth_tide]
B:
  orbits: IGS_precise_ephemeris
  clocks: IGS_precise_clocks
I:
  scenario: static_PPP
  processing: [SPP, PPP_float, PPP_fixed]
O: [position_RMS_3D, horizontal_RMS, vertical_RMS]
epsilon:
  position_RMS_max: 0.05   # meters (PPP)
  convergence_time_max: 1800   # seconds
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 IGS stations with known truth coordinates; 30 s data | PASS |
| S2 | Dual-freq removes first-order iono; PPP well-posed | PASS |
| S3 | PPP converges to cm-level within 30 minutes | PASS |
| S4 | 3D RMS < 5 cm achievable with precise products | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gnss_pos/benchmark_igs.yaml
spec_ref: sha256:<spec466_hash>
principle_ref: sha256:<p466_hash>
dataset:
  name: IGS_MGEX_daily_solutions
  reference: "IGS Analysis Centers combined solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SPP (code only)
    params: {obs: pseudorange, iono: broadcast}
    results: {RMS_3D: 2.5, horizontal: 1.8, vertical: 3.2}
  - solver: PPP-float
    params: {obs: code+phase, products: IGS_final}
    results: {RMS_3D: 0.035, horizontal: 0.015, vertical: 0.030}
  - solver: PPP-AR (ambiguity resolved)
    params: {obs: code+phase, products: IGS_final, AR: true}
    results: {RMS_3D: 0.012, horizontal: 0.006, vertical: 0.010}
quality_scoring:
  - {min_RMS: 0.01, Q: 1.00}
  - {min_RMS: 0.03, Q: 0.90}
  - {min_RMS: 0.05, Q: 0.80}
  - {min_RMS: 3.0, Q: 0.75}
```

**Baseline solver:** PPP-float — 3D RMS 3.5 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | 3D RMS (m) | Horiz RMS | Vert RMS | Q |
|--------|-----------|-----------|----------|---|
| SPP | 2.5 | 1.8 | 3.2 | 0.75 |
| PPP-float | 0.035 | 0.015 | 0.030 | 0.80 |
| PPP-float (24h) | 0.015 | 0.008 | 0.012 | 0.90 |
| PPP-AR | 0.012 | 0.006 | 0.010 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (PPP-AR): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p466_hash>",
  "h_s": "sha256:<spec466_hash>",
  "h_b": "sha256:<bench466_hash>",
  "r": {"RMS_3D": 0.012, "error_bound": 0.05, "ratio": 0.240},
  "c": {"convergence_time": 600, "stations": 10, "K": 3},
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
pwm-node benchmarks | grep gnss_pos
pwm-node verify gnss_pos/igs_static_s1.yaml
pwm-node mine gnss_pos/igs_static_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
