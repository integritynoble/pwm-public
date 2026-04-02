# Principle #154 — Quantum Illumination

**Domain:** Quantum Imaging | **Carrier:** Photon (entangled pair) | **Difficulty:** Frontier (δ=5)
**DAG:** S.correlated --> N.pointwise --> integral.coincidence | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.correlated-->N.pointwise-->integral.coincidence    QI-Det      QI-Target-8       OPA-Recv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM ILLUMINATION   P = (E, G, W, C)   Principle #154       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρ_ret = η|T⟩⟨T| ⊗ ρ_idler + (1−η)ρ_thermal ⊗ ρ_idler │
│        │ Signal photon reflects off low-reflectivity target      │
│        │ in bright thermal background; idler retained locally    │
│        │ Inverse: detect target presence via joint measurement   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.correlated] --> [N.pointwise] --> [integral.coincidence]│
│        │  EntangledPairs  Interaction  CoincidenceCount         │
│        │ V={S.correlated, N.pointwise, integral.coincidence}  A={S.correlated-->N.pointwise, N.pointwise-->integral.coincidence}   L_DAG=4.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (6 dB advantage over classical in       │
│        │   error exponent even after entanglement is lost)       │
│        │ Uniqueness: YES for binary hypothesis testing           │
│        │ Stability: robust to high thermal background (N_B≫1)   │
│        │ Mismatch: imperfect OPA receiver, mode mismatch         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = P_err (error probability), ROC-AUC                 │
│        │ q = exponential decay in M (number of signal modes)   │
│        │ T = {P_err, AUC, SNR_gain_dB, M_modes}                │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mode count M, thermal noise N_B, reflectivity η self-consistent | PASS |
| S2 | Chernoff bound yields finite error exponent for η > 0 | PASS |
| S3 | P_err decreases exponentially with M signal modes | PASS |
| S4 | 6 dB gain over classical illumination achievable at N_B = 20 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# quantum_illumination/qi_target_s1_ideal.yaml
principle_ref: sha256:<p154_hash>
omega:
  M_modes: 100000
  N_S: 0.01
  N_B: 20
  eta: 0.01
  receiver: OPA
E:
  forward: "ρ_ret = η|T⟩⟨T|⊗ρ_idler + (1-η)ρ_th⊗ρ_idler"
  hypothesis: "H0: no target, H1: target present"
I:
  dataset: QI_Target_8
  scenarios: 8
  noise: {type: thermal, N_B: 20}
  scenario: ideal
O: [P_err, AUC, SNR_gain_dB]
epsilon:
  P_err_max: 0.01
  AUC_min: 0.99
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | M=100k modes, N_S=0.01, N_B=20: parameter regime valid | PASS |
| S2 | Error exponent ≈ η·N_S/N_B > 0 → well-posed detection | PASS |
| S3 | P_err ~ exp(−M·ξ_QI) converges exponentially | PASS |
| S4 | P_err ≤ 0.01 achievable with 100k modes | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# quantum_illumination/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec154_hash>
dataset:
  name: QI_Target_8
  scenarios: 8
  M_modes: 100000
baselines:
  - solver: Classical-Correlator
    params: {method: homodyne}
    results: {P_err: 0.08, AUC: 0.96}
  - solver: OPA-Receiver
    params: {gain: optimal}
    results: {P_err: 0.005, AUC: 0.998}
  - solver: FF-SFG-Receiver
    params: {method: sum_frequency}
    results: {P_err: 0.003, AUC: 0.999}
quality_scoring:
  metric: P_err
  thresholds:
    - {max: 0.003, Q: 1.00}
    - {max: 0.005, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

**Baseline:** Classical-Correlator — P_err 0.08 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | P_err | AUC | SNR gain (dB) | Q |
|--------|-------|-----|---------------|---|
| Classical-Correlator | 0.080 | 0.960 | 0.0 | 0.75 |
| OPA-Receiver | 0.005 | 0.998 | 5.8 | 0.90 |
| FF-SFG-Receiver | 0.003 | 0.999 | 6.0 | 1.00 |
| PC-Receiver | 0.004 | 0.998 | 5.9 | 0.95 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (FF-SFG):  500 × 1.00 = 500 PWM
Floor:          500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p154_hash>",
  "h_s": "sha256:<spec154_hash>",
  "h_b": "sha256:<bench154_hash>",
  "r": {"residual_norm": 0.003, "error_bound": 0.01, "ratio": 0.30},
  "c": {"fitted_rate": 5.85, "theoretical_rate": 6.0, "K": 4},
  "Q": 0.95,
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

---

## Quick-Start

```bash
pwm-node benchmarks | grep quantum_illumination
pwm-node verify quantum_illumination/qi_target_s1_ideal.yaml
pwm-node mine quantum_illumination/qi_target_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
