# Principle #413 — Sequence Alignment (HMM Forward Algorithm)

**Domain:** Computational Biology | **Carrier:** sequence probability | **Difficulty:** Standard (δ=3)
**DAG:** L.state → ∫.dp → N.pointwise |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∫.dp→N.pointwise   HMM-forward   profile-align    DP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HMM FORWARD ALGORITHM          P = (E,G,W,C)   Principle #413 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ f_k(i) = e_k(x_i) Σ_l f_l(i−1) a_{lk}               │
│        │ P(x|θ) = Σ_k f_k(L)     (total sequence probability) │
│        │ f_k(i) = forward variable for state k at position i   │
│        │ a_{lk} = transition probability, e_k = emission prob.  │
│        │ Forward: given HMM θ, sequence x → P(x|θ)            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∫.dp] ──→ [N.pointwise]                 │
│        │ linear-op  integrate  nonlinear                        │
│        │ V={L.state, ∫.dp, N.pointwise}  A={L.state→∫.dp, ∫.dp→N.pointwise}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (finite sum of products of probabilities)│
│        │ Uniqueness: YES (DP computes exact P(x|θ))            │
│        │ Stability: log-space scaling prevents underflow        │
│        │ Mismatch: model topology, emission distribution choice │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |log P − log P_ref| (log-probability difference)  │
│        │ q = N/A (exact DP computation)                       │
│        │ T = {logP_error, alignment_accuracy, runtime}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Transition/emission probabilities sum to 1; states well-defined | PASS |
| S2 | Forward algorithm computes exact P(x\|θ) in O(LK²) time | PASS |
| S3 | Log-space implementation numerically stable | PASS |
| S4 | log P error computable against brute-force enumeration (small cases) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hmm_alignment/profile_align_s1_ideal.yaml
principle_ref: sha256:<p413_hash>
omega:
  sequence_length: 500
  hmm_states: 300   # profile HMM (match/insert/delete)
  alphabet: 20   # amino acids
E:
  forward: "f_k(i) = e_k(x_i) Σ_l f_l(i-1) a_lk (log-space)"
  model: profile_HMM
B:
  parameters: {trained_on: Pfam_seed_alignment}
I:
  scenario: protein_domain_detection
  sequences: 1000
  log_space: true
O: [logP_error, alignment_accuracy, sensitivity]
epsilon:
  logP_error_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 300-state profile HMM standard for protein families; L=500 typical | PASS |
| S2 | Forward DP exact; O(L·K²) = O(500·300²) ≈ 45M operations | PASS |
| S3 | Log-space computation prevents underflow for L=500 | PASS |
| S4 | logP error < 10⁻¹⁰ (limited by floating-point precision) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hmm_alignment/benchmark_profile.yaml
spec_ref: sha256:<spec413_hash>
principle_ref: sha256:<p413_hash>
dataset:
  name: Pfam_benchmark_families
  reference: "Pfam 35.0 curated alignments"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: HMMER3-forward
    params: {algorithm: forward, log_space: true}
    results: {logP_err: 0.0, align_acc: 0.92}
  - solver: Naive-DP
    params: {log_space: false}
    results: {logP_err: NaN, align_acc: 0.92}  # underflow
  - solver: Naive-DP-logspace
    params: {log_space: true}
    results: {logP_err: 1e-12, align_acc: 0.92}
quality_scoring:
  - {max_logP_err: 1e-12, Q: 1.00}
  - {max_logP_err: 1e-8, Q: 0.90}
  - {max_logP_err: 1e-4, Q: 0.80}
  - {max_logP_err: 1e-2, Q: 0.75}
```

**Baseline solver:** HMMER3 — logP error 0 (exact)
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | logP Error | Align Accuracy | Runtime | Q |
|--------|-----------|---------------|---------|---|
| Naive-DP (no log) | NaN (underflow) | N/A | 0.5 s | 0.00 |
| Naive-DP-logspace | 1e-12 | 0.92 | 0.5 s | 1.00 |
| HMMER3-forward | 0.0 | 0.92 | 0.1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (HMMER3): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p413_hash>",
  "h_s": "sha256:<spec413_hash>",
  "h_b": "sha256:<bench413_hash>",
  "r": {"logP_err": 0.0, "align_acc": 0.92, "ratio": 0.0},
  "c": {"sequences_tested": 1000, "K": 3},
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
pwm-node benchmarks | grep hmm_alignment
pwm-node verify AE_computational_biology/hmm_alignment_s1_ideal.yaml
pwm-node mine AE_computational_biology/hmm_alignment_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
