# Principle #485 — Neutrino Oscillation

**Domain:** Particle Physics | **Carrier:** N/A (quantum mechanical) | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix] --> [∂.time] --> [N.pointwise.abs2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix-->∂.t-->N.pw.abs2  NuOscill  reactor/accel  PMNS-fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NEUTRINO OSCILLATION          P = (E,G,W,C)   Principle #485   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ P(ν_α→ν_β) = |Σ_i U*_αi U_βi exp(−im²_i L/2E)|²    │
│        │ U = PMNS matrix (θ₁₂, θ₂₃, θ₁₃, δ_CP)               │
│        │ 2-flavor: P = sin²(2θ) sin²(Δm²L/4E)                 │
│        │ Matter effect: V = √2 G_F n_e  (MSW potential)        │
│        │ Forward: given (θ_ij, Δm², L, E) → P(ν_α→ν_β)       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix] ──→ [∂.t] ──→ [N.pw.abs2]                      │
│        │  PMNS-mix  propagate  prob-|A|^2                       │
│        │ V={L.mix,∂.t,N.pw.abs2}  A={L.mix→∂.t,∂.t→N.pw.abs2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (unitary evolution, well-defined P)     │
│        │ Uniqueness: YES for given PMNS parameters              │
│        │ Stability: continuous in parameters; octant degeneracy │
│        │ Mismatch: sterile neutrinos, NSI, mass ordering        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Δ(sin²2θ)/sin²2θ  (parameter precision)           │
│        │ q = N/A (parameter estimation)                        │
│        │ T = {parameter_precision, chi2_fit, CP_sensitivity}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PMNS unitary; probability P ∈ [0,1]; Σ_β P = 1 | PASS |
| S2 | Oscillation formula exact in vacuum; MSW adds real potential | PASS |
| S3 | χ² fit to spectral data converges for 6 parameters | PASS |
| S4 | Parameter precision matches PDG global fit uncertainties | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nu_oscill/reactor_s1.yaml
principle_ref: sha256:<p485_hash>
omega:
  baseline: 52.5      # km (Daya Bay / JUNO)
  energy_range: [1.8, 8.0]   # MeV
  bins: 200
E:
  forward: "3-flavor oscillation + matter effect + reactor flux"
  parameters: [theta12, theta13, theta23, delta_cp, dm21_sq, dm31_sq]
  matter: constant_density_crust
B:
  flux: Huber_Mueller_reactor_spectrum
  detector: liquid_scintillator
  exposure: 6_GW_thermal_years
I:
  scenario: reactor_antineutrino_disappearance
  experiments: [Daya_Bay, JUNO, KamLAND]
O: [sin2_2theta13, dm2_ee, mass_ordering_sensitivity]
epsilon:
  theta13_precision: 0.005
  dm2_precision: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 energy bins; IBD threshold 1.8 MeV; baseline well-defined | PASS |
| S2 | Reactor disappearance well-understood; θ₁₃ measured | PASS |
| S3 | Spectral fit converges for all 6 oscillation parameters | PASS |
| S4 | θ₁₃ precision < 0.5% achievable with Daya Bay statistics | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# nu_oscill/benchmark_reactor.yaml
spec_ref: sha256:<spec485_hash>
principle_ref: sha256:<p485_hash>
dataset:
  name: Daya_Bay_final_oscillation
  reference: "Daya Bay Collaboration (2022) final θ₁₃ result"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: 2-flavor approximation
    params: {flavors: 2, matter: none}
    results: {theta13_error: 0.012, dm2_error: 0.03}
  - solver: 3-flavor vacuum
    params: {flavors: 3, matter: none}
    results: {theta13_error: 0.005, dm2_error: 0.015}
  - solver: 3-flavor + matter (full)
    params: {flavors: 3, matter: constant}
    results: {theta13_error: 0.004, dm2_error: 0.010}
quality_scoring:
  - {min_prec: 0.003, Q: 1.00}
  - {min_prec: 0.005, Q: 0.90}
  - {min_prec: 0.010, Q: 0.80}
  - {min_prec: 0.020, Q: 0.75}
```

**Baseline solver:** 3-flavor vacuum — θ₁₃ error 0.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | θ₁₃ Error | Δm² Error | Runtime | Q |
|--------|----------|----------|---------|---|
| 2-flavor approx | 0.012 | 0.03 | 0.1 s | 0.75 |
| 3-flavor vacuum | 0.005 | 0.015 | 1 s | 0.90 |
| 3-flavor + matter | 0.004 | 0.010 | 5 s | 0.90 |
| Full global fit | 0.003 | 0.005 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (global): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p485_hash>",
  "h_s": "sha256:<spec485_hash>",
  "h_b": "sha256:<bench485_hash>",
  "r": {"theta13_error": 0.003, "error_bound": 0.005, "ratio": 0.600},
  "c": {"chi2_dof": 1.02, "experiments": 3, "K": 3},
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
pwm-node benchmarks | grep nu_oscill
pwm-node verify nu_oscill/reactor_s1.yaml
pwm-node mine nu_oscill/reactor_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
