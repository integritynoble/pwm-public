# Principle #416 — Atmospheric Radiative Transfer

**Domain:** Environmental Science | **Carrier:** radiance/irradiance | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.angular → K.scatter → ∫.angular |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.angular→K.scatter→∫.angular   rad-transfer  clear-sky-flux    DISORT/2s
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ATMOSPHERIC RADIATIVE TRANSFER P = (E,G,W,C)   Principle #416 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ μ dI/dτ = I − (1−ω₀)B(T) − (ω₀/2) ∫ P(μ,μ')I dμ'  │
│        │ I(τ,μ,λ) = spectral radiance                          │
│        │ τ = optical depth, ω₀ = single-scatter albedo          │
│        │ P = phase function, B(T) = Planck function             │
│        │ Forward: given atmosphere profile → fluxes F↑, F↓     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.angular] ──→ [K.scatter] ──→ [∫.angular]            │
│        │ derivative  kernel  integrate                          │
│        │ V={∂.angular, K.scatter, ∫.angular}  A={∂.angular→K.scatter, K.scatter→∫.angular}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear integro-differential equation)  │
│        │ Uniqueness: YES (for given atmospheric state)          │
│        │ Stability: bounded radiance for bounded optical depth  │
│        │ Mismatch: gas absorption line-by-line vs band models   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |F − F_ref| / F_ref (flux error)                  │
│        │ q = depends on angular quadrature (2-stream vs N-stream)│
│        │ T = {flux_error, heating_rate_error, K_layers}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Radiance, optical depth, albedo dimensions consistent | PASS |
| S2 | Linear RTE well-posed for non-negative extinction | PASS |
| S3 | DISORT (discrete ordinates) converges; 2-stream for speed | PASS |
| S4 | Flux error computable against line-by-line reference (LBLRTM) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# radiative_transfer/clear_sky_s1_ideal.yaml
principle_ref: sha256:<p416_hash>
omega:
  layers: 50
  domain: atmosphere_0_to_TOA
  spectral_range: [200, 50000]   # nm
  spectral_resolution: correlated_k
E:
  forward: "μ dI/dτ = I − (1−ω₀)B − (ω₀/2)∫P·I dμ'"
  gas_absorption: HITRAN
  aerosol: none
B:
  TOA: {solar_flux: TOA_spectrum}
  surface: {albedo: 0.2, T_surface: 288.0}
I:
  scenario: clear_sky_midlatitude_summer
  solar_zenith: 30
  stream_counts: [2, 4, 8, 16]
O: [SW_flux_error, LW_flux_error, heating_rate_error]
epsilon:
  flux_error_max: 1.0   # W/m²
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 layers cover 0-80 km; correlated-k captures major bands | PASS |
| S2 | Clear-sky with HITRAN absorption — well-characterized regime | PASS |
| S3 | DISORT-16 converges to < 0.1 W/m² vs line-by-line | PASS |
| S4 | Flux error < 1 W/m² achievable with correlated-k + 16 streams | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# radiative_transfer/benchmark_clear_sky.yaml
spec_ref: sha256:<spec416_hash>
principle_ref: sha256:<p416_hash>
dataset:
  name: ICRCCM_clear_sky
  reference: "ICRCCM radiative transfer intercomparison"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: 2-stream
    params: {layers: 50}
    results: {SW_err: 5.0, LW_err: 3.0}
  - solver: DISORT-4stream
    params: {layers: 50}
    results: {SW_err: 1.5, LW_err: 1.0}
  - solver: DISORT-16stream
    params: {layers: 50}
    results: {SW_err: 0.3, LW_err: 0.2}
quality_scoring:
  - {max_flux_err: 0.5, Q: 1.00}
  - {max_flux_err: 2.0, Q: 0.90}
  - {max_flux_err: 5.0, Q: 0.80}
  - {max_flux_err: 10.0, Q: 0.75}
```

**Baseline solver:** DISORT-4stream — SW flux error 1.5 W/m²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | SW Flux Error (W/m²) | LW Flux Error (W/m²) | Runtime | Q |
|--------|---------------------|---------------------|---------|---|
| 2-stream | 5.0 | 3.0 | 0.01 s | 0.80 |
| DISORT-4 | 1.5 | 1.0 | 0.5 s | 0.90 |
| DISORT-16 | 0.3 | 0.2 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DISORT-16): 500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p416_hash>",
  "h_s": "sha256:<spec416_hash>",
  "h_b": "sha256:<bench416_hash>",
  "r": {"SW_err": 0.3, "LW_err": 0.2, "ratio": 0.06},
  "c": {"streams": 16, "layers": 50, "K": 3},
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
pwm-node benchmarks | grep radiative_transfer
pwm-node verify AF_environmental_science/radiative_transfer_s1_ideal.yaml
pwm-node mine AF_environmental_science/radiative_transfer_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
