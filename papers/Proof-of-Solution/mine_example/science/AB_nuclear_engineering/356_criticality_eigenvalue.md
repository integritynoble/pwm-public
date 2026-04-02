# Principle #356 — Criticality Eigenvalue (k-effective)

**Domain:** Nuclear Engineering | **Carrier:** neutron | **Difficulty:** Advanced (δ=5)
**DAG:** E.generalized → N.reaction.fission |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.generalized→N.reaction.fission   keff-eigen   GODIVA/JEZEBEL    power-iter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CRITICALITY EIGENVALUE (k-eff)  P = (E,G,W,C)  Principle #356 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·(D∇φ) − Σ_a φ + (1/k_eff) χ ∑_g νΣ_f,g φ_g = 0   │
│        │ k_eff = eigenvalue measuring neutron multiplication     │
│        │ φ_g = group flux, χ = fission spectrum                  │
│        │ Forward: given geometry/materials → find k_eff, φ(r)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.generalized] ──→ [N.reaction.fission]               │
│        │ eigensolve  nonlinear                                  │
│        │ V={E.generalized, N.reaction.fission}  A={E.generalized→N.reaction.fission}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Krein-Rutman for positive operators)   │
│        │ Uniqueness: YES (dominant eigenvalue is simple)        │
│        │ Stability: YES (power iteration converges for DR < 1)  │
│        │ Mismatch: cross-section uncertainty, geometry tolerance │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |k_eff − k_ref| in pcm (parts per 100,000)       │
│        │ q = convergence of power iteration                    │
│        │ T = {k_eff_error_pcm, flux_L2_error, dominance_ratio} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Group fluxes and cross-sections dimensionally consistent | PASS |
| S2 | Krein-Rutman guarantees dominant eigenvalue for positive fission operator | PASS |
| S3 | Power iteration with Wielandt shift converges | PASS |
| S4 | k_eff error measurable in pcm against MCNP reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# criticality/godiva_s1_ideal.yaml
principle_ref: sha256:<p356_hash>
omega:
  grid: [100, 100, 100]
  domain: sphere_bare_HEU
  energy_groups: 2
E:
  forward: "∇·(D∇φ_g) − Σ_a,g φ_g + (1/k) χ_g Σ νΣ_f,g' φ_g' = 0"
  materials: HEU-GODIVA
B:
  outer: {vacuum: true}
I:
  scenario: bare_sphere_criticality
  reference_keff: 1.00000
  mesh_sizes: [25, 50, 100]
O: [keff_pcm_error, flux_L2_error]
epsilon:
  keff_error_pcm: 50
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2-group adequate for fast spectrum; mesh resolves sphere | PASS |
| S2 | Bare sphere has well-defined fundamental mode | PASS |
| S3 | Power iteration converges with dominance ratio < 0.95 | PASS |
| S4 | k_eff error < 50 pcm achievable with fine mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# criticality/benchmark_godiva.yaml
spec_ref: sha256:<spec356_hash>
principle_ref: sha256:<p356_hash>
dataset:
  name: GODIVA_HEU_sphere
  reference: "ICSBEP HEU-MET-FAST-001, k_eff = 1.00000 ± 0.0010"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Diffusion-FDM
    params: {groups: 2, N: 50}
    results: {keff_pcm: 120, flux_L2: 2.1e-2}
  - solver: S_N-diamond
    params: {groups: 16, S_N: 8}
    results: {keff_pcm: 35, flux_L2: 5.0e-3}
  - solver: Monte-Carlo-analog
    params: {histories: 1e7}
    results: {keff_pcm: 8, flux_L2: 1.2e-2}
quality_scoring:
  - {max_pcm: 10, Q: 1.00}
  - {max_pcm: 50, Q: 0.90}
  - {max_pcm: 150, Q: 0.80}
  - {max_pcm: 300, Q: 0.75}
```

**Baseline solver:** S_N-diamond — k_eff error 35 pcm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | k_eff Error (pcm) | Flux L2 | Runtime | Q |
|--------|-------------------|---------|---------|---|
| Diffusion-FDM | 120 | 2.1e-2 | 2 s | 0.80 |
| S_N-diamond | 35 | 5.0e-3 | 45 s | 0.90 |
| Monte-Carlo | 8 | 1.2e-2 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (MC):  500 × 1.00 = 500 PWM
Floor:           500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p356_hash>",
  "h_s": "sha256:<spec356_hash>",
  "h_b": "sha256:<bench356_hash>",
  "r": {"keff_pcm": 8, "error_bound": 50, "ratio": 0.16},
  "c": {"dominance_ratio": 0.92, "converged_iterations": 85, "K": 3},
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
pwm-node benchmarks | grep criticality
pwm-node verify AB_nuclear_engineering/criticality_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/criticality_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
