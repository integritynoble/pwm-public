# Principle #414 — Gaussian Plume Dispersion

**Domain:** Environmental Science | **Carrier:** pollutant concentration | **Difficulty:** Introductory (δ=2)
**DAG:** G.point → K.psf.gaussian → ∫.temporal |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.psf.gaussian→∫.temporal      gauss-plume  stack-emission    analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GAUSSIAN PLUME DISPERSION      P = (E,G,W,C)   Principle #414  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C(x,y,z) = Q/(2π u σ_y σ_z)                          │
│        │   × exp(−y²/(2σ_y²))                                   │
│        │   × [exp(−(z−H)²/(2σ_z²)) + exp(−(z+H)²/(2σ_z²))]   │
│        │ Q = emission rate, u = wind speed, H = effective height│
│        │ σ_y, σ_z = dispersion coefficients (Pasquill-Gifford)  │
│        │ Forward: given Q, u, H, stability → C(x,y,z)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.psf.gaussian] ──→ [∫.temporal]        │
│        │ source  kernel  integrate                              │
│        │ V={G.point, K.psf.gaussian, ∫.temporal}  A={G.point→K.psf.gaussian, K.psf.gaussian→∫.temporal}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (closed-form solution)                  │
│        │ Uniqueness: YES (analytic formula, deterministic)      │
│        │ Stability: YES (Gaussian tails decay rapidly)          │
│        │ Mismatch: stability class, terrain effects, wind shear │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |C_pred − C_obs| / C_obs (concentration error)    │
│        │ q = N/A (analytic; accuracy limited by σ_y, σ_z)     │
│        │ T = {conc_error, max_ground_error, plume_width_error}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Concentration, emission rate, wind speed dimensionally consistent | PASS |
| S2 | Analytic solution exists for steady-state uniform wind | PASS |
| S3 | Direct evaluation — no iteration needed | PASS |
| S4 | Concentration error computable against tracer experiments | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gaussian_plume/stack_emission_s1_ideal.yaml
principle_ref: sha256:<p414_hash>
omega:
  domain: [0, 10000, -2000, 2000, 0, 500]   # x,y,z in meters
  grid: [200, 80, 50]
E:
  forward: "C(x,y,z) = Gaussian plume formula (Pasquill-Gifford)"
  Q: 100.0   # g/s
  u: 5.0   # m/s
  H_eff: 100.0   # m (effective stack height)
B:
  stability_class: D   # neutral
  ground: {reflection: true}
I:
  scenario: flat_terrain_neutral
  stability_classes: [A, B, C, D, E, F]
O: [ground_level_max_error, centerline_error]
epsilon:
  conc_error_max: 0.10   # 10% against tracer data
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Domain extends 10 km downwind; grid resolves plume width | PASS |
| S2 | Neutral stability (D) — standard Gaussian plume applies | PASS |
| S3 | Analytic evaluation — no convergence issues | PASS |
| S4 | 10% error against tracer data achievable for class D | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gaussian_plume/benchmark_stack.yaml
spec_ref: sha256:<spec414_hash>
principle_ref: sha256:<p414_hash>
dataset:
  name: Prairie_Grass_tracer
  reference: "Barad (1958) Prairie Grass diffusion experiment"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gaussian-PG
    params: {sigma: Pasquill_Gifford}
    results: {conc_err: 0.25, max_ground_err: 0.30}
  - solver: Gaussian-Briggs
    params: {sigma: Briggs_urban}
    results: {conc_err: 0.18, max_ground_err: 0.22}
  - solver: AERMOD-simplified
    params: {terrain: flat}
    results: {conc_err: 0.12, max_ground_err: 0.15}
quality_scoring:
  - {max_conc_err: 0.10, Q: 1.00}
  - {max_conc_err: 0.20, Q: 0.90}
  - {max_conc_err: 0.30, Q: 0.80}
  - {max_conc_err: 0.50, Q: 0.75}
```

**Baseline solver:** Gaussian-Briggs — concentration error 18%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Conc Error | Max Ground Error | Runtime | Q |
|--------|-----------|-----------------|---------|---|
| Gaussian-PG | 0.25 | 0.30 | 0.01 s | 0.80 |
| Gaussian-Briggs | 0.18 | 0.22 | 0.01 s | 0.90 |
| AERMOD-simplified | 0.12 | 0.15 | 1 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case: 200 × 0.90 = 180 PWM
Floor:     200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p414_hash>",
  "h_s": "sha256:<spec414_hash>",
  "h_b": "sha256:<bench414_hash>",
  "r": {"conc_err": 0.12, "max_ground_err": 0.15, "ratio": 0.60},
  "c": {"stability_classes_tested": 6, "K": 3},
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
| L4 Solution | — | 150–180 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep gaussian_plume
pwm-node verify AF_environmental_science/gaussian_plume_s1_ideal.yaml
pwm-node mine AF_environmental_science/gaussian_plume_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
