# Principle #361 — Gamma-Ray Transport / Shielding

**Domain:** Nuclear Engineering | **Carrier:** photon | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.path → N.reaction |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.path→N.reaction   gamma-shield concrete-slab     buildup/MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GAMMA-RAY TRANSPORT / SHIELDING P = (E,G,W,C)  Principle #361 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Ω·∇ψ(r,Ω,E) + μ_t(E) ψ = ∫ μ_s(E'→E,Ω'→Ω) ψ dΩ'dE'│
│        │   + S(r,E)                                              │
│        │ ψ = photon angular flux, μ_t = total attenuation        │
│        │ Buildup: Φ(x) = B(E,x) · S₀/(4πr²) · e^{−μx}         │
│        │ Forward: given source/geometry → dose rate D(r)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.path] ──→ [N.reaction]                │
│        │ kernel  integrate  nonlinear                           │
│        │ V={K.green, ∫.path, N.reaction}  A={K.green→∫.path, ∫.path→N.reaction}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear transport, bounded cross-sections)│
│        │ Uniqueness: YES (subcritical photon transport)          │
│        │ Stability: YES (exponential attenuation dominates)      │
│        │ Mismatch: buildup factor accuracy, energy group collapse│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative dose error |D−D_ref|/D_ref                │
│        │ q = 0.5 (MC), 2.0 (multigroup S_N)                   │
│        │ T = {dose_error, attenuation_ratio, K_resolutions}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Photon flux and attenuation coefficients dimensionally consistent | PASS |
| S2 | Linear photon transport uniquely solvable for given source | PASS |
| S3 | MC and multigroup S_N converge; buildup factors tabulated | PASS |
| S4 | Dose rate error computable against experimental/MC reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gamma_shielding/concrete_slab_s1_ideal.yaml
principle_ref: sha256:<p361_hash>
omega:
  grid: [200]
  domain: slab_1D
  shield_material: concrete
  thickness: 100   # cm
E:
  forward: "1D gamma transport with buildup"
  source_energy: 1.0   # MeV (Co-60 average)
  source_type: point_isotropic
B:
  left: {source: isotropic}
  right: {vacuum: true}
I:
  scenario: concrete_slab_shielding
  thicknesses_mfp: [1, 5, 10, 20]
  mesh_sizes: [50, 100, 200]
O: [dose_transmission_error, buildup_factor_error]
epsilon:
  dose_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 cells over 100 cm adequate for attenuation profile | PASS |
| S2 | 1 MeV photons in concrete — well-characterized regime | PASS |
| S3 | Multigroup S_N and buildup factor methods converge | PASS |
| S4 | Dose error < 5% achievable against MCNP reference | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gamma_shielding/benchmark_concrete.yaml
spec_ref: sha256:<spec361_hash>
principle_ref: sha256:<p361_hash>
dataset:
  name: ANS_6_4_1_buildup
  reference: "ANS-6.4.1 gamma-ray buildup factors"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Buildup-GP
    params: {GP_fit: ANS_standard}
    results: {dose_err: 0.08, buildup_err: 0.05}
  - solver: S_N-multigroup
    params: {groups: 25, S_N: 16, N: 100}
    results: {dose_err: 0.03, buildup_err: 0.02}
  - solver: MCNP6-photon
    params: {N: 1e8}
    results: {dose_err: 0.01, buildup_err: 0.01}
quality_scoring:
  - {max_dose_err: 0.01, Q: 1.00}
  - {max_dose_err: 0.05, Q: 0.90}
  - {max_dose_err: 0.10, Q: 0.80}
  - {max_dose_err: 0.15, Q: 0.75}
```

**Baseline solver:** S_N-multigroup — dose error 3%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Dose Error | Buildup Error | Runtime | Q |
|--------|-----------|---------------|---------|---|
| Buildup-GP | 0.08 | 0.05 | 0.01 s | 0.80 |
| S_N-multigroup | 0.03 | 0.02 | 5 s | 0.90 |
| MCNP6-photon | 0.01 | 0.01 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (MCNP): 300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p361_hash>",
  "h_s": "sha256:<spec361_hash>",
  "h_b": "sha256:<bench361_hash>",
  "r": {"dose_err": 0.01, "buildup_err": 0.01, "ratio": 0.20},
  "c": {"fitted_rate": 0.51, "theoretical_rate": 0.5, "K": 3},
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
pwm-node benchmarks | grep gamma_shielding
pwm-node verify AB_nuclear_engineering/gamma_shielding_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/gamma_shielding_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
