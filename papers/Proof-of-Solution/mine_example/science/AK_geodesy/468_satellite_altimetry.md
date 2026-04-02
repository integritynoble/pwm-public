# Principle #468 — Satellite Altimetry

**Domain:** Geodesy | **Carrier:** N/A (measurement-based) | **Difficulty:** Standard (δ=3)
**DAG:** [K.green] --> [O.l2] --> [∫.temporal] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green-->O.l2-->∫.temp  SatAlt  Jason/Sentinel  retracking
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SATELLITE ALTIMETRY           P = (E,G,W,C)   Principle #468   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ SSH = h_sat − R − ΔR_corrections                       │
│        │ R = c·Δt/2  (two-way range from radar pulse)           │
│        │ ΔR = ΔR_iono + ΔR_tropo + ΔR_SSB + ΔR_tide + …       │
│        │ Waveform: P(t) = ∫ σ⁰(x)·PFS(t,x) dx  (Brown model) │
│        │ Forward: given waveform → estimate (R, SWH, σ⁰)       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [O.l2] ──→ [∫.temp]                      │
│        │  ocean-kernel  altim-fit  time-avg                     │
│        │ V={K.green,O.l2,∫.temp}  A={K.green→O.l2,O.l2→∫.temp}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Brown model well-defined over ocean)   │
│        │ Uniqueness: YES for ocean; ambiguous over ice/coast    │
│        │ Stability: noise-limited by pulse-limited footprint    │
│        │ Mismatch: non-Brown waveforms (sea-ice, coastal)       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMS(SSH − SSH_ref)  (sea surface height error, cm) │
│        │ q = N/A (statistical fitting)                         │
│        │ T = {SSH_RMS, SWH_bias, range_precision}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Range equation dimensionally consistent; corrections in meters | PASS |
| S2 | Brown model well-posed for open ocean waveforms | PASS |
| S3 | MLE3/MLE4 retracker converges for > 95% of ocean waveforms | PASS |
| S4 | SSH RMS < 4 cm achievable (crossover analysis) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sat_alt/ocean_ssh_s1.yaml
principle_ref: sha256:<p468_hash>
omega:
  tracks: 1000
  domain: global_ocean
  time: [0, 864000.0]   # 10-day cycle
E:
  forward: "Brown waveform model → MLE retracking → SSH"
  radar: Ku_band_13.6GHz
  corrections: [iono_dual_freq, wet_tropo_radiometer, dry_tropo, SSB, tides]
B:
  orbit: precise_POD
  geoid: EGM2008
I:
  scenario: open_ocean_SSH
  retrackers: [MLE3, MLE4, ALES]
O: [SSH_RMS, range_precision, SWH_RMSE]
epsilon:
  SSH_RMS_max: 4.0     # cm
  range_precision_max: 2.0   # cm
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1000 tracks over 10-day cycle; dual-freq iono correction | PASS |
| S2 | Open ocean waveforms follow Brown model | PASS |
| S3 | MLE4 converges for > 98% of waveforms | PASS |
| S4 | SSH RMS < 4 cm at crossovers | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sat_alt/benchmark_ssh.yaml
spec_ref: sha256:<spec468_hash>
principle_ref: sha256:<p468_hash>
dataset:
  name: Jason3_GDR_crossovers
  reference: "CNES/NASA Jason-3 GDR-F products"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MLE3
    params: {waveform: Brown, params: 3}
    results: {SSH_RMS: 3.8, range_precision: 1.8}
  - solver: MLE4
    params: {waveform: Brown, params: 4}
    results: {SSH_RMS: 3.5, range_precision: 1.6}
  - solver: ALES (adaptive)
    params: {waveform: sub_waveform, coastal: true}
    results: {SSH_RMS: 3.2, range_precision: 1.5}
quality_scoring:
  - {min_RMS: 2.5, Q: 1.00}
  - {min_RMS: 3.5, Q: 0.90}
  - {min_RMS: 4.0, Q: 0.80}
  - {min_RMS: 5.0, Q: 0.75}
```

**Baseline solver:** MLE4 — SSH RMS 3.5 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | SSH RMS (cm) | Range Prec (cm) | Runtime | Q |
|--------|-------------|-----------------|---------|---|
| MLE3 | 3.8 | 1.8 | 5 s | 0.80 |
| MLE4 | 3.5 | 1.6 | 8 s | 0.90 |
| ALES | 3.2 | 1.5 | 12 s | 0.90 |
| SAR-mode (Sentinel-6) | 2.3 | 1.1 | 20 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SAR): 300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p468_hash>",
  "h_s": "sha256:<spec468_hash>",
  "h_b": "sha256:<bench468_hash>",
  "r": {"SSH_RMS_cm": 2.3, "error_bound": 4.0, "ratio": 0.575},
  "c": {"crossovers": 5000, "cycles": 10, "K": 3},
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
pwm-node benchmarks | grep sat_alt
pwm-node verify sat_alt/ocean_ssh_s1.yaml
pwm-node mine sat_alt/ocean_ssh_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
