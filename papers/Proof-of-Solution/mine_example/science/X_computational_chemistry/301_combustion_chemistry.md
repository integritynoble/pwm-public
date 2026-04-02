# Principle #301 — Combustion Chemistry (Arrhenius)

**Domain:** Computational Chemistry | **Carrier:** N/A (reactive ODE) | **Difficulty:** Hard (δ=5)
**DAG:** N.reaction.arrhenius → ∂.time.implicit |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction.arrhenius→∂.time.implicit      combust     ignition-delay    Cantera
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COMBUSTION CHEMISTRY (ARRHENIUS) P = (E,G,W,C)   Principle #301│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ k(T) = A T^n exp(−E_a/RT)  (modified Arrhenius)       │
│        │ dY_i/dt = (W_i/ρ)Σ ν_ij r_j  (species mass fractions) │
│        │ ρc_p dT/dt = −Σ h_i ω̇_i  (energy equation)            │
│        │ Forward: given mechanism + IC → ignition delay, T(t)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction.arrhenius] ──→ [∂.time.implicit]           │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction.arrhenius, ∂.time.implicit}  A={N.reaction.arrhenius→∂.time.implicit}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE with positive species, bounded T)  │
│        │ Uniqueness: YES for given mechanism and IC              │
│        │ Stability: extremely stiff (τ_chem/τ_flow ~ 10⁻¹⁰)    │
│        │ Mismatch: mechanism incompleteness, pressure dependence│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |τ_ign,sim − τ_ign,exp| / τ_ign,exp (delay error) │
│        │ q = varies (BDF implicit, operator-split)             │
│        │ T = {ignition_delay, flame_speed, species_profiles}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass fractions sum to 1; enthalpy consistent with NASA polynomials | PASS |
| S2 | GRI-Mech 3.0 validated against experimental τ_ign and S_L | PASS |
| S3 | Cantera CVODE solver converges for 0D constant-volume reactor | PASS |
| S4 | Ignition delay error < 20% for CH4/air at 1200–2000 K | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# combust/ignition_s1_ideal.yaml
principle_ref: sha256:<p301_hash>
omega:
  species: 53
  reactions: 325
  time: [0, 0.01]  # seconds
  dt: adaptive
E:
  forward: "0D constant-volume reactor with GRI-Mech 3.0"
  mechanism: GRI-Mech_3.0
  thermodynamics: NASA_7poly
B:
  initial: {T: 1500, P: 1atm, phi: 1.0}
  fuel: CH4
  oxidiser: air
I:
  scenario: CH4_air_ignition_delay
  T_range: [1200, 2000]  # K
  P_range: [1, 40]  # atm
O: [ignition_delay, T_max, species_peak]
epsilon:
  tau_error_max: 0.20  # relative
  mass_balance_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 53 species, 325 reactions; thermodynamic consistency verified | PASS |
| S2 | GRI-Mech 3.0 validated for CH4/air at 1–40 atm | PASS |
| S3 | CVODE-BDF converges with adaptive dt for all T,P conditions | PASS |
| S4 | Ignition delay within 20% of shock tube experiments | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# combust/benchmark_ignition.yaml
spec_ref: sha256:<spec301_hash>
principle_ref: sha256:<p301_hash>
dataset:
  name: CH4_air_shock_tube
  reference: "Petersen & Hanson (1999) shock tube data"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Cantera-GRI30
    params: {mechanism: GRI30, reactor: IdealGasReactor}
    results: {tau_error: 0.15, T_peak_error: 0.02}
  - solver: Cantera-USC-II
    params: {mechanism: USC_Mech_II}
    results: {tau_error: 0.12, T_peak_error: 0.015}
  - solver: FlameMaster-detailed
    params: {mechanism: AramcoMech_3.0}
    results: {tau_error: 0.08, T_peak_error: 0.01}
quality_scoring:
  - {min_tau_err: 0.05, Q: 1.00}
  - {min_tau_err: 0.10, Q: 0.90}
  - {min_tau_err: 0.20, Q: 0.80}
  - {min_tau_err: 0.40, Q: 0.75}
```

**Baseline solver:** Cantera-GRI30 — τ_ign error 15%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | τ Error | T Peak Error | Runtime | Q |
|--------|---------|--------------|---------|---|
| Cantera-GRI30 | 0.15 | 0.02 | 0.5 s | 0.80 |
| Cantera-USC-II | 0.12 | 0.015 | 1 s | 0.90 |
| FlameMaster-Aramco | 0.08 | 0.01 | 3 s | 0.90 |
| Aramco+bayesian-opt | 0.04 | 0.005 | 60 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Aramco+opt): 500 × 1.00 = 500 PWM
Floor:                  500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p301_hash>",
  "h_s": "sha256:<spec301_hash>",
  "h_b": "sha256:<bench301_hash>",
  "r": {"residual_norm": 0.04, "error_bound": 0.20, "ratio": 0.20},
  "c": {"fitted_rate": 4.85, "theoretical_rate": 5.0, "K": 4},
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
pwm-node benchmarks | grep combust
pwm-node verify combust/ignition_s1_ideal.yaml
pwm-node mine combust/ignition_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
