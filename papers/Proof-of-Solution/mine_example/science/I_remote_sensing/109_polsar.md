# Principle #109 — Polarimetric SAR (PolSAR)

**Domain:** Remote Sensing | **Carrier:** Microwave | **Difficulty:** Hard (δ=5)
**DAG:** G.pulse --> K.green --> F.dft --> L.mix | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse-->K.green-->F.dft-->L.mix    PolSAR     ALOS2-PolSAR        Decompose
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PolSAR   P = (E, G, W, C)   Principle #109                    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [S] = [[S_HH, S_HV],[S_VH, S_VV]]                    │
│        │ Scattering matrix encodes target polarimetric response │
│        │ Coherency matrix T = <k·k†>; k = Pauli target vector  │
│        │ Inverse: decompose T into scattering mechanisms        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [K.green] --> [F.dft] --> [L.mix]          │
│        │ Chirp  Propagate  RangeCompress  PolCoherence           │
│        │ V={G.pulse, K.green, F.dft, L.mix}  A={G.pulse-->K.green, K.green-->F.dft, F.dft-->L.mix}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coherency matrix decomposable)         │
│        │ Uniqueness: YES for 3-component model-based decomp.    │
│        │ Stability: κ ≈ 8 (full-pol), κ ≈ 30 (dual-pol)        │
│        │ Mismatch: cross-pol calibration error, Faraday rotation│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = classification OA (primary), decomp RMSE (second.) │
│        │ q = 2.0 (eigenvalue decomposition convergence)        │
│        │ T = {OA_pct, decomp_RMSE, K_resolutions}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Full polarimetric (HH,HV,VH,VV) channels available | PASS |
| S2 | Coherency matrix positive semi-definite; decomp well-posed | PASS |
| S3 | Freeman-Durden / Yamaguchi decomposition converges | PASS |
| S4 | Classification OA > 85% achievable for land-cover mapping | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# polsar/alos2_s1_ideal.yaml
principle_ref: sha256:<p109_hash>
omega:
  grid: [1024, 1024]
  pixel_m: 6
  frequency_GHz: 1.27
  polarizations: [HH, HV, VH, VV]
E:
  forward: "T = <k·k†> from scattering matrix S"
  decomposition: Freeman-Durden
I:
  dataset: ALOS2_PolSAR
  scenes: 25
  looks: 16
  scenario: ideal
O: [classification_OA_pct, decomp_error]
epsilon:
  OA_min_pct: 85.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Full-pol L-band; 16-look averaging | PASS |
| S2 | κ ≈ 8 with 16 looks; well-posed | PASS |
| S3 | Freeman-Durden decomposition converges | PASS |
| S4 | OA > 85% feasible for L-band land-cover | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# polsar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec109_hash>
principle_ref: sha256:<p109_hash>
dataset:
  name: ALOS2_PolSAR
  scenes: 25
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Freeman-Durden
    results: {OA_pct: 86.5}
  - solver: Yamaguchi-4comp
    results: {OA_pct: 89.2}
  - solver: PolSAR-CNN
    results: {OA_pct: 94.8}
quality_scoring:
  - {min_OA: 95.0, Q: 1.00}
  - {min_OA: 90.0, Q: 0.90}
  - {min_OA: 86.0, Q: 0.80}
  - {min_OA: 82.0, Q: 0.75}
```

**Baseline:** Freeman-Durden — OA 86.5% | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | OA (%) | Q |
|--------|--------|---|
| Freeman-Durden | 86.5 | 0.80 |
| Yamaguchi-4comp | 89.2 | 0.88 |
| PolSAR-CNN | 94.8 | 0.98 |
| PolFormer | 95.5 | 1.00 |

### Reward: `R = 100 × 5 × q` → Best: 500 PWM | Floor: 375 PWM

```json
{
  "h_p": "sha256:<p109_hash>", "Q": 0.98,
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
| L4 Solution | — | 375–500 PWM per solve |

## Quick-Start

```bash
pwm-node benchmarks | grep polsar
pwm-node mine polsar/alos2_s1_ideal.yaml
```
