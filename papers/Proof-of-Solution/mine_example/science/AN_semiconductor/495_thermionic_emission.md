# Principle #495 — Thermionic Emission (Richardson-Dushman)

**Domain:** Semiconductor Physics | **Carrier:** N/A (analytical) | **Difficulty:** Basic (δ=2)
**DAG:** [N.exponential] --> [∫.energy] --> [B.contact] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.exp-->∫.energy-->B.cont  ThermEmit  Schottky-bench  analytical
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THERMIONIC EMISSION (RICHARDSON-DUSHMAN) P=(E,G,W,C) Pr. #495 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ J = A* T² exp(−qφ_B/k_BT) [exp(qV/k_BT) − 1]        │
│        │ A* = 4πqm*k_B²/h³  (Richardson constant)              │
│        │ Δφ = √(qE/(4πε_s))  (Schottky barrier lowering)       │
│        │ φ_eff = φ_B − Δφ  (image-force corrected)             │
│        │ Forward: given (φ_B, T, V, A*) → J(V,T)              │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.exp] ──→ [∫.energy] ──→ [B.cont]                    │
│        │  Richardson  energy-integ  electrode-BC                │
│        │ V={N.exp,∫.energy,B.cont}  A={N.exp→∫.energy,∫.energy→B.cont}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytical, always evaluable)          │
│        │ Uniqueness: YES for given φ_B, T, A*                  │
│        │ Stability: exponential sensitivity to φ_B and T        │
│        │ Mismatch: tunneling at thin barriers, interface states │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |J_model − J_meas|/J_meas  (current error)        │
│        │ q = N/A (analytical)                                  │
│        │ T = {J_error, phi_B_extracted, ideality_factor}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | J > 0 for forward bias; A* has correct units (A/cm²K²) | PASS |
| S2 | Richardson-Dushman exact for thermionic regime (kT >> tunneling) | PASS |
| S3 | Analytical evaluation always converges | PASS |
| S4 | Barrier height extraction within 0.02 eV of C-V measurement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# therm_emit/schottky_s1.yaml
principle_ref: sha256:<p495_hash>
omega:
  temperature_range: [200, 400]   # K
  domain: Au_nSi_Schottky_diode
E:
  forward: "Richardson-Dushman + image-force lowering"
  phi_B: 0.80          # eV
  A_star: 112.0        # A/cm²K²
  epsilon_s: 11.7      # Si
B:
  voltage: [-2, 0.5]   # V
  doping: 1e16         # cm⁻³
I:
  scenario: Schottky_barrier_IV_T
  temperatures: [200, 250, 300, 350, 400]
O: [IV_curves, barrier_height, ideality_factor, Richardson_plot]
epsilon:
  phi_B_error_max: 0.02    # eV
  J_error_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 5 temperatures span 200-400 K; V range covers forward/reverse | PASS |
| S2 | Au/n-Si well-characterized; φ_B ≈ 0.8 eV standard | PASS |
| S3 | Analytical model evaluates at all T and V | PASS |
| S4 | φ_B from Richardson plot within 0.02 eV | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# therm_emit/benchmark_schottky.yaml
spec_ref: sha256:<spec495_hash>
principle_ref: sha256:<p495_hash>
dataset:
  name: Au_nSi_Schottky_IV
  reference: "Sze & Ng (2007) Semiconductor Devices textbook"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Pure thermionic (no image force)
    params: {image_force: false}
    results: {phi_B_error: 0.05, J_error: 0.25}
  - solver: Thermionic + image force
    params: {image_force: true}
    results: {phi_B_error: 0.015, J_error: 0.08}
  - solver: Thermionic-field emission (TFE)
    params: {tunneling: WKB}
    results: {phi_B_error: 0.008, J_error: 0.04}
quality_scoring:
  - {min_err: 0.005, Q: 1.00}
  - {min_err: 0.01, Q: 0.90}
  - {min_err: 0.02, Q: 0.80}
  - {min_err: 0.05, Q: 0.75}
```

**Baseline solver:** Thermionic + image force — φ_B error 0.015 eV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | φ_B Error (eV) | J Error | Runtime | Q |
|--------|---------------|---------|---------|---|
| Pure thermionic | 0.05 | 0.25 | 0.001 s | 0.75 |
| + Image force | 0.015 | 0.08 | 0.002 s | 0.80 |
| TFE (WKB) | 0.008 | 0.04 | 0.01 s | 0.90 |
| Full TCAD (DD) | 0.005 | 0.02 | 5.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (TCAD): 200 × 1.00 = 200 PWM
Floor:            200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p495_hash>",
  "h_s": "sha256:<spec495_hash>",
  "h_b": "sha256:<bench495_hash>",
  "r": {"phi_B_error": 0.005, "error_bound": 0.02, "ratio": 0.250},
  "c": {"J_error": 0.02, "temperatures": 5, "K": 5},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep therm_emit
pwm-node verify therm_emit/schottky_s1.yaml
pwm-node mine therm_emit/schottky_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
