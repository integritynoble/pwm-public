# Principle #319 — GW Approximation (Quasiparticle)

**Domain:** Quantum Mechanics | **Carrier:** quasiparticle | **Difficulty:** Frontier (δ=5)
**DAG:** E.hermitian → K.green → ∫.brillouin |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→K.green→∫.brillouin    GW-qp       Si/GaAs-gap       G₀W₀/scGW
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GW APPROXIMATION               P = (E,G,W,C)   Principle #319 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Σ(r,r';ω) = iG(r,r';ω)W(r,r';ω)                     │
│        │ W = ε⁻¹v  (screened Coulomb interaction)              │
│        │ ε = 1 − vP  (dielectric function, P = −iGG)          │
│        │ Forward: given DFT G₀ → compute Σ → quasiparticle E  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [K.green] ──→ [∫.brillouin]          │
│        │ eigensolve  kernel  integrate                          │
│        │ V={E.hermitian, K.green, ∫.brillouin}  A={E.hermitian→K.green, K.green→∫.brillouin}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (perturbative; well-defined for G₀W₀)  │
│        │ Uniqueness: G₀W₀ unique; scGW may have multiple fixpts│
│        │ Stability: κ depends on screening strength             │
│        │ Mismatch: starting DFT functional, basis-set truncation│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_gap^GW − E_gap^expt|  (primary, eV)           │
│        │ q = N/A (many-body; convergence w.r.t. basis & k-pts)│
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Self-energy Σ=iGW dimensionally consistent; Dyson equation well-formed | PASS |
| S2 | G₀W₀ well-defined perturbation of DFT; convergence with basis | PASS |
| S3 | Plane-wave + PAW implementations converge with cutoff and k-mesh | PASS |
| S4 | Band-gap error measurable against photoemission experiments | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gw/si_gap_s1_ideal.yaml
principle_ref: sha256:<p319_hash>
omega:
  k_grid: [6, 6, 6]
  E_cut: 30  # Ry
  n_bands: 200
E:
  forward: "Σ = iG₀W₀ → QP correction to DFT eigenvalues"
  starting_point: DFT-LDA
B:
  periodic: true
  pseudopotential: PAW
I:
  scenario: silicon_band_gap
  lattice_constant: 5.43
  expt_gap: 1.17  # eV (indirect Γ→X)
O: [qp_gap, qp_band_energies, spectral_function]
epsilon:
  gap_error_max: 0.10  # eV vs experiment
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6×6×6 k-grid and 200 bands adequate for Si convergence | PASS |
| S2 | Si G₀W₀ gap well-benchmarked in literature (1.1-1.2 eV) | PASS |
| S3 | G₀W₀ converges with E_cut and number of empty bands | PASS |
| S4 | Gap error < 0.1 eV achievable with standard G₀W₀ | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gw/benchmark_si_gap.yaml
spec_ref: sha256:<spec319_hash>
principle_ref: sha256:<p319_hash>
dataset:
  name: silicon_qp_gap_experimental
  reference: "ARPES/optical: indirect gap 1.17 eV, direct 3.4 eV"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: G₀W₀@LDA
    params: {k: [6,6,6], E_cut: 25, n_bands: 150}
    results: {gap_error: 0.08, direct_gap_error: 0.12}
  - solver: G₀W₀@PBE
    params: {k: [6,6,6], E_cut: 30, n_bands: 200}
    results: {gap_error: 0.05, direct_gap_error: 0.08}
  - solver: scGW
    params: {k: [4,4,4], E_cut: 20, n_iter: 5}
    results: {gap_error: 0.15, direct_gap_error: 0.20}
quality_scoring:
  - {min_gap_error: 0.02, Q: 1.00}
  - {min_gap_error: 0.05, Q: 0.90}
  - {min_gap_error: 0.10, Q: 0.80}
  - {min_gap_error: 0.20, Q: 0.75}
```

**Baseline solver:** G₀W₀@PBE — gap error 0.05 eV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Gap Error (eV) | Direct Gap Error (eV) | Runtime | Q |
|--------|---------------|----------------------|---------|---|
| scGW | 0.15 | 0.20 | 48 h | 0.80 |
| G₀W₀@LDA | 0.08 | 0.12 | 8 h | 0.80 |
| G₀W₀@PBE | 0.05 | 0.08 | 10 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (G₀W₀@PBE): 500 × 0.90 = 450 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p319_hash>",
  "h_s": "sha256:<spec319_hash>",
  "h_b": "sha256:<bench319_hash>",
  "r": {"residual_norm": 0.05, "error_bound": 0.10, "ratio": 0.50},
  "c": {"fitted_rate": 1.5, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep gw
pwm-node verify gw/si_gap_s1_ideal.yaml
pwm-node mine gw/si_gap_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
