# Principle #317 — Phonon Dispersion (Dynamical Matrix)

**Domain:** Quantum Mechanics | **Carrier:** phonon mode | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian → ∂.space.laplacian → ∫.brillouin |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→∂.space.laplacian→∫.brillouin     phonon-disp  Si/NaCl           DFPT/frozen
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHONON DISPERSION (DYN. MATRIX)  P = (E,G,W,C) Principle #317 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ D(q)εₛ(q) = ω²ₛ(q)εₛ(q)                              │
│        │ D_αβ(q) = (1/√MᵢMⱼ) Σ_R Φ_αβ(0,R) exp(iq·R)         │
│        │ Φ = force-constant matrix, ω = phonon frequency        │
│        │ Forward: given Φ, q-path → compute ωₛ(q) branches     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [∂.space.laplacian] ──→ [∫.brillouin] │
│        │ eigensolve  derivative  integrate                      │
│        │ V={E.hermitian, ∂.space.laplacian, ∫.brillouin}  A={E.hermitian→∂.space.laplacian, ∂.space.laplacian→∫.brillouin}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (D(q) Hermitian → real eigenvalues)     │
│        │ Uniqueness: YES (eigenvalues unique at each q)         │
│        │ Stability: κ ~ acoustic-branch slope near Γ point      │
│        │ Mismatch: force-constant range truncation, anharmonicity│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ω_num − ω_ref|/ω_max (primary)                   │
│        │ q = exact (direct diagonalization)                    │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dynamical matrix Hermitian; acoustic sum rule enforced | PASS |
| S2 | D(q) Hermitian guarantees real ω² at each q-point | PASS |
| S3 | Direct diagonalization exact; DFPT systematic with cutoff | PASS |
| S4 | Frequency error bounded by force-constant truncation range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# phonon/si_diamond_s1_ideal.yaml
principle_ref: sha256:<p317_hash>
omega:
  q_path: [Gamma, X, W, L, Gamma, K]
  q_points: 200
E:
  forward: "D(q)ε = ω²ε, dynamical matrix from force constants"
  force_constants: frozen_phonon
B:
  acoustic_sum_rule: enforced
I:
  scenario: silicon_diamond
  lattice_constant: 5.43
  supercell: [4, 4, 4]
  interaction_range: 4  # nearest-neighbor shells
O: [phonon_frequencies, DOS, group_velocities]
epsilon:
  freq_rms_max: 0.3  # THz
  acoustic_slope_error: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 q-points along high-symmetry path; 4×4×4 supercell adequate | PASS |
| S2 | Si phonon dispersion well-characterized experimentally | PASS |
| S3 | Frozen-phonon method converges with supercell size | PASS |
| S4 | Frequency RMS < 0.3 THz achievable with 4-shell interaction | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# phonon/benchmark_silicon.yaml
spec_ref: sha256:<spec317_hash>
principle_ref: sha256:<p317_hash>
dataset:
  name: silicon_phonon_neutron_scattering
  reference: "Nilsson & Nelin (1972) inelastic neutron scattering"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Frozen-phonon (4×4×4)
    params: {supercell: [4,4,4], DFT: LDA}
    results: {freq_rms: 0.35, max_error: 0.8}
  - solver: DFPT
    params: {q_grid: [8,8,8], XC: LDA}
    results: {freq_rms: 0.25, max_error: 0.6}
  - solver: Empirical (Tersoff)
    params: {cutoff: 3.0}
    results: {freq_rms: 0.80, max_error: 2.1}
quality_scoring:
  - {min_freq_rms: 0.10, Q: 1.00}
  - {min_freq_rms: 0.30, Q: 0.90}
  - {min_freq_rms: 0.50, Q: 0.80}
  - {min_freq_rms: 1.00, Q: 0.75}
```

**Baseline solver:** DFPT — frequency RMS 0.25 THz
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Freq RMS (THz) | Max Error (THz) | Runtime | Q |
|--------|----------------|-----------------|---------|---|
| Empirical (Tersoff) | 0.80 | 2.1 | 1 s | 0.75 |
| Frozen-phonon (4×4×4) | 0.35 | 0.8 | 30 min | 0.90 |
| DFPT | 0.25 | 0.6 | 15 min | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DFPT): 300 × 0.90 = 270 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p317_hash>",
  "h_s": "sha256:<spec317_hash>",
  "h_b": "sha256:<bench317_hash>",
  "r": {"residual_norm": 0.25, "error_bound": 0.50, "ratio": 0.50},
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep phonon
pwm-node verify phonon/si_diamond_s1_ideal.yaml
pwm-node mine phonon/si_diamond_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
