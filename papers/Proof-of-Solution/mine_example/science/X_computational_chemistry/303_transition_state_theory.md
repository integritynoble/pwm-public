# Principle #303 — Transition State Theory

**Domain:** Computational Chemistry | **Carrier:** N/A (statistical mechanics) | **Difficulty:** Hard (δ=5)
**DAG:** N.reaction.arrhenius → ∫.path → O.l2 |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction.arrhenius→∫.path→O.l2      tst-rate    barrier-heights   Eyring
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSITION STATE THEORY          P = (E,G,W,C)   Principle #303│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ k(T) = (k_B T/h) (Q‡/Q_R) exp(−ΔE‡/k_BT)  (Eyring) │
│        │ Q = partition function; ΔE‡ = barrier height           │
│        │ Forward: given PES → locate TS → compute k(T)         │
│        │ κ(T) = tunnelling correction (Wigner/Eckart)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction.arrhenius] ──→ [∫.path] ──→ [O.l2]         │
│        │ nonlinear  integrate  optimize                         │
│        │ V={N.reaction.arrhenius, ∫.path, O.l2}  A={N.reaction.arrhenius→∫.path, ∫.path→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (saddle point on PES)                   │
│        │ Uniqueness: conditional; multiple TS possible           │
│        │ Stability: sensitive to barrier height accuracy         │
│        │ Mismatch: recrossing, tunnelling, variational effects  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |log k_TST − log k_exp| (log rate constant error) │
│        │ q = depends on electronic structure method used        │
│        │ T = {barrier_height, rate_constant, Arrhenius_params}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Eyring equation dimensionally correct; partition functions consistent | PASS |
| S2 | Saddle point has exactly one imaginary frequency (verified) | PASS |
| S3 | TST with CCSD(T) barriers reproduces k within factor of 3 | PASS |
| S4 | Log rate constant error < 0.5 for benchmark H-transfer reactions | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tst_rate/barrier_s1_ideal.yaml
principle_ref: sha256:<p303_hash>
omega:
  method: CCSD(T)/cc-pVTZ
  temperature_range: [200, 2000]  # K
  reactions: 38
E:
  forward: "Eyring TST with Wigner tunnelling correction"
  barrier_method: CCSD(T)/CBS
  partition_fn: RRHO
B:
  reference_state: 1_mol/L
  pressure: 1_atm
I:
  scenario: HTBH38_barrier_heights
  reference: W3.2 composite method
O: [barrier_MAE, log_k_error, tunnelling_factor]
epsilon:
  barrier_MAE_max: 1.0  # kcal/mol
  log_k_error_max: 0.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 38 reactions with well-defined TS; RRHO valid for non-fluxional TS | PASS |
| S2 | CCSD(T)/CBS barriers within 1 kcal/mol of W3.2 reference | PASS |
| S3 | TS geometry optimisation converges with QST2/Berny algorithm | PASS |
| S4 | Barrier MAE < 1 kcal/mol yields log k error < 0.5 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tst_rate/benchmark_htbh38.yaml
spec_ref: sha256:<spec303_hash>
principle_ref: sha256:<p303_hash>
dataset:
  name: HTBH38_barrier_heights
  reference: "Zheng et al. (2009) HTBH38/08"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: B3LYP/cc-pVTZ
    params: {method: DFT}
    results: {barrier_MAE: 4.2, log_k_MAE: 1.5}
  - solver: M06-2X/cc-pVTZ
    params: {method: DFT}
    results: {barrier_MAE: 1.3, log_k_MAE: 0.6}
  - solver: CCSD(T)/cc-pVTZ
    params: {method: coupled_cluster}
    results: {barrier_MAE: 0.8, log_k_MAE: 0.35}
quality_scoring:
  - {min_barrier_MAE: 0.3, Q: 1.00}
  - {min_barrier_MAE: 0.8, Q: 0.90}
  - {min_barrier_MAE: 1.5, Q: 0.80}
  - {min_barrier_MAE: 4.0, Q: 0.75}
```

**Baseline solver:** CCSD(T)/cc-pVTZ — barrier MAE 0.8 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Barrier MAE | log k MAE | Runtime | Q |
|--------|-------------|-----------|---------|---|
| B3LYP | 4.2 | 1.5 | 5 s | 0.75 |
| M06-2X | 1.3 | 0.6 | 8 s | 0.80 |
| CCSD(T)/cc-pVTZ | 0.8 | 0.35 | 600 s | 0.90 |
| CCSD(T)/CBS + VTST | 0.25 | 0.12 | 7200 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (CBS+VTST): 500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p303_hash>",
  "h_s": "sha256:<spec303_hash>",
  "h_b": "sha256:<bench303_hash>",
  "r": {"residual_norm": 0.25, "error_bound": 1.0, "ratio": 0.25},
  "c": {"fitted_rate": 6.90, "theoretical_rate": 7.0, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep tst_rate
pwm-node verify tst_rate/barrier_s1_ideal.yaml
pwm-node mine tst_rate/barrier_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
