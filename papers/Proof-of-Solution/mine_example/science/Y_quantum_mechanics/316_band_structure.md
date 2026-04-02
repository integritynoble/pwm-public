# Principle #316 — Band Structure Calculation

**Domain:** Quantum Mechanics | **Carrier:** Bloch state | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian.bloch → ∫.brillouin |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian.bloch→∫.brillouin band-struct  Si-diamond        plane-wave
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BAND STRUCTURE CALCULATION     P = (E,G,W,C)   Principle #316  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H(k)ψₙₖ = εₙ(k)ψₙₖ                                   │
│        │ H(k) = (−iℏ∇+ℏk)²/2m + V_periodic(r)                 │
│        │ Bloch theorem: ψₙₖ(r) = eⁱᵏ·ʳuₙₖ(r)                  │
│        │ Forward: given V_per, k-path → compute εₙ(k) bands    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [V] ──→ [H_k] ──→ [ε] ──→ [ψ_k] ──→ [V]             │
│        │ potential  build-H(k)  diag  extract-Bloch  repeat     │
│        │ V={V,H_k,ε,ψ_k}  A={V→H_k,H_k→ε,ε→ψ_k,ψ_k→V}      │
│        │ L_DAG=3.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bloch theory for periodic potentials)  │
│        │ Uniqueness: YES (eigenvalues at each k unique)         │
│        │ Stability: κ ~ band-gap⁻¹ near crossings              │
│        │ Mismatch: pseudopotential error, basis truncation      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ε_num − ε_ref|/|ε_ref| (primary)                 │
│        │ q = spectral (plane-wave), 2.0 (FEM)                  │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | k-vector sampling and plane-wave cutoff consistent | PASS |
| S2 | Bloch theorem guarantees discrete bands at each k | PASS |
| S3 | Plane-wave expansion converges with cutoff energy | PASS |
| S4 | Band energy error bounded by basis-set completeness | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# band_structure/si_diamond_s1_ideal.yaml
principle_ref: sha256:<p316_hash>
omega:
  k_path: [Gamma, X, W, L, Gamma, K]
  k_points: 200
  E_cut: 15.0  # Ry
E:
  forward: "H(k)u_nk = ε_n(k) u_nk, plane-wave basis"
  potential: empirical_pseudopotential
B:
  periodic: true
I:
  scenario: silicon_diamond
  lattice_constant: 5.43  # Angstrom
  pseudopotential_form_factors: {V3S: -0.21, V8S: 0.04, V11S: 0.08}
O: [band_energies, band_gap, effective_masses]
epsilon:
  band_gap_error_max: 0.05  # eV
  band_energy_rms_max: 0.02  # eV
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 k-points along high-symmetry path; E_cut = 15 Ry adequate | PASS |
| S2 | Si band structure well-established experimentally | PASS |
| S3 | Plane-wave EPM converges systematically with E_cut | PASS |
| S4 | Band gap error < 0.05 eV achievable with given form factors | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# band_structure/benchmark_silicon.yaml
spec_ref: sha256:<spec316_hash>
principle_ref: sha256:<p316_hash>
dataset:
  name: silicon_band_structure_EPM
  reference: "Cohen & Bergstresser (1966) empirical pseudopotential"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Plane-wave EPM
    params: {E_cut: 10, k_pts: 100}
    results: {gap_error: 0.08, band_rms: 0.05}
  - solver: Plane-wave EPM
    params: {E_cut: 15, k_pts: 200}
    results: {gap_error: 0.02, band_rms: 0.01}
  - solver: LCAO (sp3s*)
    params: {orbitals: 10}
    results: {gap_error: 0.15, band_rms: 0.08}
quality_scoring:
  - {min_gap_error: 0.01, Q: 1.00}
  - {min_gap_error: 0.05, Q: 0.90}
  - {min_gap_error: 0.10, Q: 0.80}
  - {min_gap_error: 0.20, Q: 0.75}
```

**Baseline solver:** Plane-wave EPM (E_cut=15) — gap error 0.02 eV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Gap Error (eV) | Band RMS (eV) | Runtime | Q |
|--------|---------------|----------------|---------|---|
| LCAO (sp3s*) | 0.15 | 0.08 | 0.1 s | 0.80 |
| PW-EPM (E_cut=10) | 0.08 | 0.05 | 1 s | 0.80 |
| PW-EPM (E_cut=15) | 0.02 | 0.01 | 3 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (PW high-cut): 300 × 0.90 = 270 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p316_hash>",
  "h_s": "sha256:<spec316_hash>",
  "h_b": "sha256:<bench316_hash>",
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep band_structure
pwm-node verify band_structure/si_diamond_s1_ideal.yaml
pwm-node mine band_structure/si_diamond_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
