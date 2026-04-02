# Principle #296 — Post-Hartree-Fock (MP2, CCSD(T))

**Domain:** Computational Chemistry | **Carrier:** N/A (perturbative/CC) | **Difficulty:** Expert (δ=8)
**DAG:** E.hermitian → N.cluster → ∫.orbital |  **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→N.cluster→∫.orbital      post-hf     corr-energy       CCSD(T)
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  POST-HARTREE-FOCK (MP2,CCSD(T))  P = (E,G,W,C)   Principle #296│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ MP2: E⁽²⁾ = Σ |⟨ij||ab⟩|²/(ε_i+ε_j−ε_a−ε_b)        │
│        │ CCSD: Ψ = e^(T₁+T₂)|Φ₀⟩ ; project for amplitudes    │
│        │ (T): perturbative triples correction ΔE_T              │
│        │ Forward: given HF orbitals → correlated energy         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [N.cluster] ──→ [∫.orbital]          │
│        │ eigensolve  nonlinear  integrate                       │
│        │ V={E.hermitian, N.cluster, ∫.orbital}  A={E.hermitian→N.cluster, N.cluster→∫.orbital}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (CC equations have solution for RHF ref)│
│        │ Uniqueness: YES near HF reference (connected cluster)  │
│        │ Stability: CCSD(T) = "gold standard" for single-ref   │
│        │ Mismatch: multi-reference systems, basis incompleteness│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_method − E_FCI| (sub-kcal/mol target)          │
│        │ q = 5.0 (MP2: N⁵), 7.0 (CCSD(T): N⁷)               │
│        │ T = {correlation_energy, T1_diagnostic, CBS_extrap}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | MP2/CC amplitude equations dimensionally consistent | PASS |
| S2 | Size-extensive (CC) and size-consistent (MP2, CC) | PASS |
| S3 | CCSD converges in <50 iterations for single-reference systems | PASS |
| S4 | CCSD(T)/CBS error < 1 kcal/mol for single-reference molecules | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# post_hf/correlation_s1_ideal.yaml
principle_ref: sha256:<p296_hash>
omega:
  basis: cc-pVTZ
  method: CCSD(T)
  frozen_core: true
E:
  forward: "CCSD amplitude equations + perturbative (T)"
  convergence: 1.0e-8  # Hartree
  max_iterations: 100
B:
  reference: RHF
  T1_diagnostic_max: 0.02
I:
  scenario: W4-11_atomisation
  molecules: 140
  reference: W4/FCI_CBS
O: [MAE_kcal, max_error, T1_diagnostic]
epsilon:
  MAE_max: 1.0  # kcal/mol
  max_error_max: 3.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | cc-pVTZ with frozen core; 140 molecules all single-reference | PASS |
| S2 | CCSD(T) size-extensive; CBS extrapolation well-defined | PASS |
| S3 | CCSD converges for all 140 molecules (T1 < 0.02) | PASS |
| S4 | MAE < 1 kcal/mol with CBS extrapolation | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# post_hf/benchmark_w4.yaml
spec_ref: sha256:<spec296_hash>
principle_ref: sha256:<p296_hash>
dataset:
  name: W4-11_atomisation
  reference: "Karton et al. (2011) W4-11 dataset"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MP2/cc-pVTZ
    params: {frozen_core: true}
    results: {MAE: 4.5, RMSE: 6.2}
  - solver: CCSD/cc-pVTZ
    params: {frozen_core: true}
    results: {MAE: 2.8, RMSE: 3.5}
  - solver: CCSD(T)/cc-pVTZ
    params: {frozen_core: true}
    results: {MAE: 1.2, RMSE: 1.8}
quality_scoring:
  - {min_MAE: 0.3, Q: 1.00}
  - {min_MAE: 1.0, Q: 0.90}
  - {min_MAE: 3.0, Q: 0.80}
  - {min_MAE: 5.0, Q: 0.75}
```

**Baseline solver:** CCSD(T)/cc-pVTZ — MAE 1.2 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (kcal/mol) | RMSE | Runtime | Q |
|--------|----------------|------|---------|---|
| MP2/cc-pVTZ | 4.5 | 6.2 | 5 s | 0.80 |
| CCSD/cc-pVTZ | 2.8 | 3.5 | 300 s | 0.80 |
| CCSD(T)/cc-pVTZ | 1.2 | 1.8 | 600 s | 0.90 |
| CCSD(T)/CBS(TQ) | 0.25 | 0.35 | 7200 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (CBS): 800 × 1.00 = 800 PWM
Floor:           800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p296_hash>",
  "h_s": "sha256:<spec296_hash>",
  "h_b": "sha256:<bench296_hash>",
  "r": {"residual_norm": 0.25, "error_bound": 1.0, "ratio": 0.25},
  "c": {"fitted_rate": 6.85, "theoretical_rate": 7.0, "K": 4},
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
pwm-node benchmarks | grep post_hf
pwm-node verify post_hf/correlation_s1_ideal.yaml
pwm-node mine post_hf/correlation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
