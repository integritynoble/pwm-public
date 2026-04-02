# Principle #326 — k.p Perturbation Theory

**Domain:** Quantum Mechanics | **Carrier:** effective-mass state | **Difficulty:** Textbook (δ=1)
**DAG:** E.hermitian → ∂.space → ∫.brillouin |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→∂.space→∫.brillouin kp-model    GaAs-8band        diag
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  k·p PERTURBATION THEORY        P = (E,G,W,C)   Principle #326 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H_kp = H₀ + (ℏk·p)/m + ℏ²k²/(2m)                    │
│        │ ⟨n|p|m⟩ = momentum matrix elements (Kane parameters)  │
│        │ ε_n(k) = E_n + ℏ²k²/(2m*_n) + higher-order terms     │
│        │ Forward: given band-edge params, k → compute ε_n(k)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [H₀] ──→ [P] ──→ [H_kp] ──→ [ε] ──→ [H₀]            │
│        │ band-edge  momentum  build-kp  diag  repeat            │
│        │ V={H₀,P,H_kp,ε}  A={H₀→P,P→H_kp,H_kp→ε,ε→H₀}       │
│        │ L_DAG=2.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (finite perturbation matrix)            │
│        │ Uniqueness: YES (eigenvalues of Hermitian k.p matrix)  │
│        │ Stability: valid near band extrema; breaks at large k  │
│        │ Mismatch: remote-band truncation, SO coupling accuracy │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ε_kp − ε_DFT|/bandwidth (primary)                │
│        │ q = exact (small matrix diag); model error ~O(k⁴)    │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | k.p Hamiltonian Hermitian; Kane parameters well-defined | PASS |
| S2 | Small-matrix eigenvalue problem always solvable | PASS |
| S3 | Diagonalization exact for given model; convergence with band count | PASS |
| S4 | Band energy error bounded by k.p model order | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# kp/gaas_8band_s1_ideal.yaml
principle_ref: sha256:<p326_hash>
omega:
  k_range: [-0.1, 0.1]  # 1/Angstrom around Gamma
  k_points: 200
  n_bands: 8
E:
  forward: "8×8 Kane Hamiltonian diag at each k"
  model: 8-band_Kane
B:
  symmetry: zinc_blende
I:
  scenario: GaAs_band_structure
  E_g: 1.519  # eV
  E_P: 25.7   # eV (Kane energy)
  Delta_SO: 0.341  # eV
  gamma_1: 6.98
O: [band_energies, effective_masses, Luttinger_parameters]
epsilon:
  mass_error_max: 0.05  # relative
  band_rms_max: 0.01  # eV near Gamma
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 k-points in [-0.1, 0.1] resolve curvature; 8 bands adequate | PASS |
| S2 | GaAs k.p parameters well-established experimentally | PASS |
| S3 | 8×8 diagonalization exact for given model | PASS |
| S4 | Effective mass error < 5% near Gamma | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# kp/benchmark_gaas.yaml
spec_ref: sha256:<spec326_hash>
principle_ref: sha256:<p326_hash>
dataset:
  name: GaAs_band_edge_experimental
  reference: "Vurgaftman et al. (2001) band parameters review"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: 2-band (parabolic)
    params: {n_bands: 2}
    results: {mass_error: 0.15, band_rms: 0.05}
  - solver: 4-band (Luttinger-Kohn)
    params: {n_bands: 4}
    results: {mass_error: 0.08, band_rms: 0.02}
  - solver: 8-band (Kane)
    params: {n_bands: 8}
    results: {mass_error: 0.02, band_rms: 0.005}
quality_scoring:
  - {min_mass_error: 0.01, Q: 1.00}
  - {min_mass_error: 0.05, Q: 0.90}
  - {min_mass_error: 0.10, Q: 0.80}
  - {min_mass_error: 0.20, Q: 0.75}
```

**Baseline solver:** 8-band Kane — mass error 2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Mass Error | Band RMS (eV) | Runtime | Q |
|--------|-----------|---------------|---------|---|
| 2-band (parabolic) | 0.15 | 0.05 | 0.001 s | 0.80 |
| 4-band (Luttinger) | 0.08 | 0.02 | 0.005 s | 0.80 |
| 8-band (Kane) | 0.02 | 0.005 | 0.01 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (8-band): 100 × 0.90 = 90 PWM
Floor:              100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p326_hash>",
  "h_s": "sha256:<spec326_hash>",
  "h_b": "sha256:<bench326_hash>",
  "r": {"residual_norm": 0.02, "error_bound": 0.05, "ratio": 0.40},
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
| L4 Solution | — | 75–90 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep kp
pwm-node verify kp/gaas_8band_s1_ideal.yaml
pwm-node mine kp/gaas_8band_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
