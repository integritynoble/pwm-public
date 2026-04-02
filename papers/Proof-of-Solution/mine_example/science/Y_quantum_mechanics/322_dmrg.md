# Principle #322 — Density Matrix Renormalization Group (DMRG)

**Domain:** Quantum Mechanics | **Carrier:** matrix product state | **Difficulty:** Frontier (δ=7)
**DAG:** L.mps → E.lanczos → L.truncate |  **Reward:** 7× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mps→E.lanczos→L.truncate   DMRG-1D     Heisenberg-chain   DMRG/tDMRG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DMRG (MATRIX PRODUCT STATE)    P = (E,G,W,C)   Principle #322 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ |ψ⟩ = Σ A^{s₁}A^{s₂}...A^{sₙ}|s₁s₂...sₙ⟩ (MPS)     │
│        │ min_MPS ⟨ψ|H|ψ⟩/⟨ψ|ψ⟩  (variational)               │
│        │ Sweep left-right optimizing one site at a time        │
│        │ Forward: given H, χ_max → compute E₀, |ψ₀⟩ as MPS    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mps] ──→ [E.lanczos] ──→ [L.truncate]               │
│        │ linear-op  eigensolve  linear-op                       │
│        │ V={L.mps, E.lanczos, L.truncate}  A={L.mps→E.lanczos, E.lanczos→L.truncate}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (variational over MPS manifold)         │
│        │ Uniqueness: YES (for gapped 1D systems with area law)  │
│        │ Stability: truncation error ε_trunc ~ exp(−αχ) in 1D  │
│        │ Mismatch: bond dimension χ, sweep convergence          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_DMRG − E_exact|/|E_exact| (primary)            │
│        │ q = exponential in χ for gapped 1D systems            │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | MPO representation of H consistent; MPS dimensions valid | PASS |
| S2 | Variational principle ensures E_DMRG ≥ E_exact | PASS |
| S3 | DMRG sweeps converge; truncation error controllable via χ | PASS |
| S4 | Energy error bounded by truncation error and sweep count | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dmrg/heisenberg_chain_s1_ideal.yaml
principle_ref: sha256:<p322_hash>
omega:
  L: 100  # chain length
  chi_max: 256  # bond dimension
  sweeps: 10
E:
  forward: "H = J Σ S_i·S_{i+1}, variational MPS optimization"
  model: antiferromagnetic_Heisenberg
B:
  boundary: open
  S: 0.5
I:
  scenario: AFM_Heisenberg_S1/2
  J: 1.0
  reference: Bethe_ansatz
O: [ground_state_energy, correlation_length, entanglement_entropy]
epsilon:
  energy_density_error_max: 1.0e-8
  truncation_error_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | L=100 with χ=256 well within DMRG capability | PASS |
| S2 | Bethe ansatz gives exact E/N = 1/4 − ln2 = −0.443147... | PASS |
| S3 | DMRG converges exponentially in χ for gapped/critical 1D | PASS |
| S4 | Energy density error < 10⁻⁸ achievable at χ=256 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dmrg/benchmark_heisenberg.yaml
spec_ref: sha256:<spec322_hash>
principle_ref: sha256:<p322_hash>
dataset:
  name: heisenberg_chain_bethe_ansatz
  reference: "Bethe (1931): E/N → 1/4 − ln2"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DMRG (χ=64)
    params: {L: 100, chi: 64, sweeps: 10}
    results: {energy_density_error: 2.1e-5, trunc_error: 1.5e-6}
  - solver: DMRG (χ=256)
    params: {L: 100, chi: 256, sweeps: 10}
    results: {energy_density_error: 3.8e-9, trunc_error: 1.2e-10}
  - solver: Exact diag (L=20)
    params: {L: 20}
    results: {energy_density_error: 0.0, trunc_error: 0.0}
quality_scoring:
  - {min_energy_error: 1.0e-8, Q: 1.00}
  - {min_energy_error: 1.0e-6, Q: 0.90}
  - {min_energy_error: 1.0e-4, Q: 0.80}
  - {min_energy_error: 1.0e-2, Q: 0.75}
```

**Baseline solver:** DMRG (χ=256) — energy density error 3.8×10⁻⁹
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | E/N Error | Trunc. Error | Runtime | Q |
|--------|----------|--------------|---------|---|
| DMRG (χ=64) | 2.1e-5 | 1.5e-6 | 30 s | 0.80 |
| DMRG (χ=256) | 3.8e-9 | 1.2e-10 | 10 min | 1.00 |
| Exact diag (L=20) | 0.0 | 0.0 | 2 min | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 7 × 1.0 × Q
Best case (DMRG χ=256): 700 × 1.00 = 700 PWM
Floor:                  700 × 0.75 = 525 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p322_hash>",
  "h_s": "sha256:<spec322_hash>",
  "h_b": "sha256:<bench322_hash>",
  "r": {"residual_norm": 3.8e-9, "error_bound": 1.0e-6, "ratio": 0.0038},
  "c": {"fitted_rate": 3.5, "theoretical_rate": "exp", "K": 4},
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
| L4 Solution | — | 525–700 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep dmrg
pwm-node verify dmrg/heisenberg_chain_s1_ideal.yaml
pwm-node mine dmrg/heisenberg_chain_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
