# Principle #491 — Quantum Transport (NEGF)

**Domain:** Semiconductor Physics | **Carrier:** N/A (Green's function) | **Difficulty:** Expert (δ=5)
**DAG:** [L.sparse] --> [E.hermitian] --> [∫.energy] | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.sparse-->E.herm-->∫.energy  NEGF  RTD/nanowire  RGF-solver
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM TRANSPORT (NEGF)      P = (E,G,W,C)  Principle #491   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ G^R(E) = [(E+iη)I − H − Σ^R_L − Σ^R_R]⁻¹            │
│        │ G^<(E) = G^R Σ^<_contacts G^A  (lesser Green's fn)    │
│        │ n(r) = −i ∫ diag[G^<(E)] dE / (2π)  (electron density)│
│        │ I = (e/h) ∫ T(E)[f_L(E)−f_R(E)] dE  (Landauer)       │
│        │ Forward: given H, contacts → T(E), I-V, n(r)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.sparse] ──→ [E.herm] ──→ [∫.energy]                 │
│        │  tight-bind  diagonalize  band-integ                   │
│        │ V={L.sparse,E.herm,∫.energy}  A={L.sparse→E.herm,E.herm→∫.energy}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (NEGF well-defined for finite systems)  │
│        │ Uniqueness: YES for given self-energies                │
│        │ Stability: self-consistent Poisson-NEGF may oscillate  │
│        │ Mismatch: self-energy approximation, phonon scattering │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |I_sim − I_ref|/I_ref  (current error)            │
│        │ q = N/A (matrix inversion / RGF)                     │
│        │ T = {current_error, transmission, charge_convergence}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hamiltonian Hermitian; self-energies satisfy causality | PASS |
| S2 | Open-system BC via contact self-energies well-defined | PASS |
| S3 | RGF algorithm scales as O(N) for 1D; NEGF-Poisson converges | PASS |
| S4 | Transmission matches analytical for rectangular barriers | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# negf/rtd_s1.yaml
principle_ref: sha256:<p491_hash>
omega:
  sites: 200
  domain: 1D_GaAs_AlGaAs_RTD
  energy_grid: 500
E:
  forward: "NEGF (ballistic) + self-consistent Poisson"
  material: GaAs/Al0.3Ga0.7As
  barrier_width: 3e-9     # m
  well_width: 5e-9        # m
  effective_mass: 0.067   # m₀
B:
  contacts: semi_infinite_leads
  voltage: [0, 0.1, 0.2, ..., 0.5]   # V
I:
  scenario: resonant_tunneling_diode_IV
  methods: [ballistic_NEGF, scattering_NEGF_Buttiker, WKB_reference]
O: [IV_curve, transmission, NDR_peak_valley_ratio]
epsilon:
  current_error_max: 0.05
  transmission_error_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 sites resolve double barrier; 500 energy points for T(E) | PASS |
| S2 | Semi-infinite leads provide open BC; well-posed scattering | PASS |
| S3 | RGF + Poisson converges within 20 self-consistent iterations | PASS |
| S4 | NDR captured; transmission peak matches analytical | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# negf/benchmark_rtd.yaml
spec_ref: sha256:<spec491_hash>
principle_ref: sha256:<p491_hash>
dataset:
  name: GaAs_RTD_benchmark
  reference: "Klimeck et al. (1995) NEMO RTD validation"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: WKB (transfer matrix)
    params: {method: TMM}
    results: {current_error: 0.20, PVR_error: 0.30}
  - solver: Ballistic NEGF (RGF)
    params: {sites: 200, E_pts: 500}
    results: {current_error: 0.05, PVR_error: 0.08}
  - solver: Scattering NEGF (Buttiker probes)
    params: {sites: 200, E_pts: 500, probes: every_5_sites}
    results: {current_error: 0.08, PVR_error: 0.12}
quality_scoring:
  - {min_err: 0.03, Q: 1.00}
  - {min_err: 0.05, Q: 0.90}
  - {min_err: 0.10, Q: 0.80}
  - {min_err: 0.25, Q: 0.75}
```

**Baseline solver:** Ballistic NEGF — current error 5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Current Error | PVR Error | Runtime | Q |
|--------|-------------|----------|---------|---|
| WKB/TMM | 0.20 | 0.30 | 0.1 s | 0.75 |
| Ballistic NEGF | 0.05 | 0.08 | 30 s | 0.90 |
| Scattering NEGF | 0.08 | 0.12 | 120 s | 0.80 |
| Full NEGF (phonon SE) | 0.03 | 0.05 | 1800 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (full NEGF): 500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p491_hash>",
  "h_s": "sha256:<spec491_hash>",
  "h_b": "sha256:<bench491_hash>",
  "r": {"current_error": 0.03, "error_bound": 0.05, "ratio": 0.600},
  "c": {"PVR_error": 0.05, "sites": 200, "K": 3},
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
pwm-node benchmarks | grep negf
pwm-node verify negf/rtd_s1.yaml
pwm-node mine negf/rtd_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
