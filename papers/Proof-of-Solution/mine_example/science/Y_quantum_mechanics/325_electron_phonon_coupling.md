# Principle #325 — Electron-Phonon Coupling

**Domain:** Quantum Mechanics | **Carrier:** coupling matrix element | **Difficulty:** Frontier (δ=5)
**DAG:** E.hermitian → K.green → ∫.brillouin |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ψ→g→Σ→λ     e-ph        Al-Eliashberg      DFPT/Wannier
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ELECTRON-PHONON COUPLING       P = (E,G,W,C)   Principle #325 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ g_{mn,ν}(k,q) = ⟨ψ_{mk+q}|∂V/∂u_{qν}|ψ_{nk}⟩       │
│        │ λ = 2∫ α²F(ω)/ω dω  (mass enhancement parameter)     │
│        │ α²F(ω) = Eliashberg spectral function                 │
│        │ Forward: given bands, phonons → compute g, λ, T_c     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [ψ] ──→ [g] ──→ [Σ_ep] ──→ [λ] ──→ [ψ]              │
│        │ Bloch-states  coupling  self-energy  integrate  repeat │
│        │ V={ψ,g,Σ_ep,λ}  A={ψ→g,g→Σ_ep,Σ_ep→λ,λ→ψ}           │
│        │ L_DAG=5.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (g well-defined for periodic systems)   │
│        │ Uniqueness: YES (for given electronic/phononic states) │
│        │ Stability: κ ~ Fermi-surface sampling density         │
│        │ Mismatch: q-mesh density, band window, Wannier spread │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |λ_num − λ_ref|/|λ_ref| (primary)                │
│        │ q = convergence with k,q mesh density                │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupling matrix elements dimensionally consistent; Bloch gauge fixed | PASS |
| S2 | DFPT provides exact linear-response coupling for given XC | PASS |
| S3 | Wannier interpolation enables dense k,q sampling | PASS |
| S4 | λ error bounded by mesh convergence and Wannier spread | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# elph/al_lambda_s1_ideal.yaml
principle_ref: sha256:<p325_hash>
omega:
  k_grid: [12, 12, 12]
  q_grid: [6, 6, 6]
  fine_grid: [60, 60, 60]  # Wannier interpolation
E:
  forward: "g = ⟨ψ|∂V/∂u|ψ⟩ via DFPT, λ from Eliashberg function"
  method: DFPT + Wannier
B:
  pseudopotential: PAW
  XC: PBE
I:
  scenario: aluminum_lambda
  lattice_constant: 4.05  # Angstrom
  expt_lambda: 0.44
  expt_Tc: 1.18  # K
O: [lambda, alpha2F, Tc_McMillan]
epsilon:
  lambda_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 12³ k-grid and 6³ q-grid capture Fermi surface topology | PASS |
| S2 | Al e-ph coupling well-benchmarked in literature (λ≈0.44) | PASS |
| S3 | Wannier interpolation to 60³ fine grid converges λ | PASS |
| S4 | λ error < 0.05 achievable with given mesh densities | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# elph/benchmark_aluminum.yaml
spec_ref: sha256:<spec325_hash>
principle_ref: sha256:<p325_hash>
dataset:
  name: aluminum_eliashberg
  reference: "Tunneling spectroscopy: λ=0.44, α²F from McMillan & Rowell"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DFPT (coarse)
    params: {k: [8,8,8], Q: [4,4,4]}
    results: {lambda_error: 0.08, Tc_error: 0.3}
  - solver: DFPT + Wannier
    params: {k: [12,12,12], Q: [6,6,6], fine: [60,60,60]}
    results: {lambda_error: 0.03, Tc_error: 0.1}
  - solver: Frozen-phonon finite-diff
    params: {supercell: [4,4,4]}
    results: {lambda_error: 0.12, Tc_error: 0.5}
quality_scoring:
  - {min_lambda_error: 0.01, Q: 1.00}
  - {min_lambda_error: 0.05, Q: 0.90}
  - {min_lambda_error: 0.10, Q: 0.80}
  - {min_lambda_error: 0.20, Q: 0.75}
```

**Baseline solver:** DFPT + Wannier — λ error 0.03
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | λ Error | Tc Error (K) | Runtime | Q |
|--------|---------|-------------|---------|---|
| Frozen-phonon | 0.12 | 0.5 | 8 h | 0.80 |
| DFPT (coarse) | 0.08 | 0.3 | 4 h | 0.80 |
| DFPT + Wannier | 0.03 | 0.1 | 6 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DFPT+Wannier): 500 × 0.90 = 450 PWM
Floor:                    500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p325_hash>",
  "h_s": "sha256:<spec325_hash>",
  "h_b": "sha256:<bench325_hash>",
  "r": {"residual_norm": 0.03, "error_bound": 0.05, "ratio": 0.60},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep elph
pwm-node verify elph/al_lambda_s1_ideal.yaml
pwm-node mine elph/al_lambda_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
