# Principle #492 — MOSFET Compact Models (BSIM)

**Domain:** Semiconductor Physics | **Carrier:** N/A (analytical/empirical) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [L.dense] --> [B.contact] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->L.dense-->B.cont  BSIM-MOS  SPICE-bench  param-extract
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MOSFET COMPACT MODELS (BSIM)  P = (E,G,W,C)  Principle #492   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_ds = μ_eff C_ox (W/L) ∫_{ψ_s}^{ψ_d} Q_i dψ_s     │
│        │ Q_i = −C_ox(V_gs − V_fb − ψ_s − γ√ψ_s) (charge)     │
│        │ μ_eff = μ₀/(1 + θ₁(V_gs−V_th) + θ₂(V_gs−V_th)²)    │
│        │ Short-channel: DIBL, velocity saturation, CLM          │
│        │ Forward: given (V_gs,V_ds,params) → I_ds, g_m, C_gg   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [L.dense] ──→ [B.cont]                      │
│        │  mobility-model  compact-eq  terminal-BC               │
│        │ V={N.pw,L.dense,B.cont}  A={N.pw→L.dense,L.dense→B.cont}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytical model, always evaluable)    │
│        │ Uniqueness: YES for given parameter set                │
│        │ Stability: smooth transitions sub/super-threshold      │
│        │ Mismatch: parameter extraction quality, process var    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMS(I_model − I_meas)/I_max  (relative IV error)  │
│        │ q = N/A (analytical model)                            │
│        │ T = {IV_error, gm_error, Cgg_error, Gummel_symmetry}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Ids continuous across all regions; gm = dIds/dVgs smooth | PASS |
| S2 | Surface-potential based: physically founded, unique ψ_s | PASS |
| S3 | Parameter extraction converges for standard MOSFET data | PASS |
| S4 | IV error < 3% RMS across full bias range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# bsim_mos/nmos_65nm_s1.yaml
principle_ref: sha256:<p492_hash>
omega:
  device: NMOS_65nm
  bias_grid: {Vgs: [-0.5, 1.2, 50pts], Vds: [0, 1.2, 25pts]}
E:
  forward: "BSIM4 surface-potential model"
  params: 120   # total BSIM4 parameters
  key_params: [VTH0, K1, K2, U0, UA, VSAT, RDSW]
B:
  measurements: DC_IV + CV + noise
  temperature: [−40, 27, 125]   # °C
I:
  scenario: 65nm_NMOS_compact_model
  models: [BSIM4, PSP, EKV3]
O: [IV_RMS_error, gm_error, Cgg_error, scalability]
epsilon:
  IV_error_max: 0.03
  gm_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50×25 bias grid covers full operating range; 3 temperatures | PASS |
| S2 | BSIM4 surface-potential formulation well-posed | PASS |
| S3 | Parameter extraction + optimization converges | PASS |
| S4 | IV RMS < 3% achievable with proper extraction | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# bsim_mos/benchmark_65nm.yaml
spec_ref: sha256:<spec492_hash>
principle_ref: sha256:<p492_hash>
dataset:
  name: NMOS_65nm_measured_IV_CV
  reference: "BSIM Group, UC Berkeley (BSIM4 documentation)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BSIM4 (default extraction)
    params: {method: standard_sequence}
    results: {IV_error: 0.028, gm_error: 0.045}
  - solver: PSP (surface-potential)
    params: {method: PSP_extraction}
    results: {IV_error: 0.022, gm_error: 0.038}
  - solver: BSIM4 (optimized)
    params: {method: global_optimization}
    results: {IV_error: 0.015, gm_error: 0.025}
quality_scoring:
  - {min_err: 0.01, Q: 1.00}
  - {min_err: 0.02, Q: 0.90}
  - {min_err: 0.03, Q: 0.80}
  - {min_err: 0.05, Q: 0.75}
```

**Baseline solver:** BSIM4 (default) — IV error 2.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | IV Error | gm Error | Runtime | Q |
|--------|---------|---------|---------|---|
| BSIM4 default | 0.028 | 0.045 | 1 s | 0.80 |
| PSP | 0.022 | 0.038 | 1 s | 0.90 |
| BSIM4 optimized | 0.015 | 0.025 | 60 s | 0.90 |
| BSIM-CMG (FinFET) | 0.010 | 0.018 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (BSIM-CMG): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p492_hash>",
  "h_s": "sha256:<spec492_hash>",
  "h_b": "sha256:<bench492_hash>",
  "r": {"IV_error": 0.010, "error_bound": 0.03, "ratio": 0.333},
  "c": {"gm_error": 0.018, "bias_points": 1250, "K": 3},
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
pwm-node benchmarks | grep bsim_mos
pwm-node verify bsim_mos/nmos_65nm_s1.yaml
pwm-node mine bsim_mos/nmos_65nm_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
