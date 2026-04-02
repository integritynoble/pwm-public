# Principle #493 — Solar Cell Device Physics

**Domain:** Semiconductor Physics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [G.broadband] --> [N.pointwise.exp] --> [∂.space] --> [B.contact] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broad-->N.pw.exp-->∂.x-->B.cont  SolarCell  Si-cell-bench  DD+optical
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SOLAR CELL DEVICE PHYSICS     P = (E,G,W,C)  Principle #493   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ DD equations + optical generation:                     │
│        │ G(x) = ∫ α(λ) Φ(λ) exp(−α(λ)x) dλ  (Beer-Lambert)   │
│        │ J_sc = q ∫ G(x) · collection_efficiency dx             │
│        │ J(V) = J_sc − J₀[exp(qV/nk_BT) − 1]  (diode)        │
│        │ η = P_max / P_in = (J_mp V_mp) / (E_sun A)            │
│        │ Forward: given cell structure → J-V, η, EQE           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broad] ──→ [N.pw.exp] ──→ [∂.x] ──→ [B.cont]        │
│        │  spectrum  absorption  transport  contact-BC           │
│        │ V={G.broad,N.pw.exp,∂.x,B.cont}  A={G.broad→N.pw.exp,N.pw.exp→∂.x,∂.x→B.cont}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (DD + generation well-posed)            │
│        │ Uniqueness: YES for given illumination and structure   │
│        │ Stability: Newton convergence for V near V_oc          │
│        │ Mismatch: surface recombination, AR coating details    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |η_sim − η_expt|/η_expt  (efficiency error)      │
│        │ q = 2.0 (SG discretization)                          │
│        │ T = {efficiency_error, Jsc_error, Voc_error, FF_error} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Current density J continuous; generation G ≥ 0; η ∈ [0,1] | PASS |
| S2 | DD + Beer-Lambert well-posed for standard Si cell | PASS |
| S3 | SG + Newton converges across full J-V curve | PASS |
| S4 | Efficiency within 2% absolute of measured value | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# solar_cell/si_cell_s1.yaml
principle_ref: sha256:<p493_hash>
omega:
  mesh: 500
  domain: 1D_Si_pn_solar_cell
  thickness: 200e-6   # m
E:
  forward: "optical generation (Beer-Lambert) + drift-diffusion"
  material: Si
  spectrum: AM1.5G
  SRH_lifetime: {tau_n: 1e-5, tau_p: 1e-5}   # s
B:
  front_surface: {S: 100}     # cm/s
  back_surface: {S: 1000}
  ARC: SiN_80nm
I:
  scenario: standard_Si_solar_cell
  thicknesses: [50, 100, 200, 300]   # μm
O: [efficiency, Jsc, Voc, FF, EQE]
epsilon:
  efficiency_error_max: 0.02    # absolute %
  Jsc_error_max: 0.5            # mA/cm²
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 mesh for 200 μm; AM1.5G spectrum standard | PASS |
| S2 | SRH lifetimes, surface velocities physical | PASS |
| S3 | DD solver converges for illuminated J-V | PASS |
| S4 | η within 2% absolute of PC1Dmod reference | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# solar_cell/benchmark_si.yaml
spec_ref: sha256:<spec493_hash>
principle_ref: sha256:<p493_hash>
dataset:
  name: PC1D_Si_solar_cell
  reference: "Basore & Clugston (1997) PC1D reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Analytical (single diode)
    params: {model: Shockley}
    results: {efficiency_error: 0.03, Jsc_error: 1.5}
  - solver: PC1Dmod (numerical)
    params: {mesh: 500}
    results: {efficiency_error: 0.008, Jsc_error: 0.3}
  - solver: Sentaurus (2D)
    params: {mesh: 50000, 2D: true}
    results: {efficiency_error: 0.005, Jsc_error: 0.15}
quality_scoring:
  - {min_err: 0.003, Q: 1.00}
  - {min_err: 0.01, Q: 0.90}
  - {min_err: 0.02, Q: 0.80}
  - {min_err: 0.05, Q: 0.75}
```

**Baseline solver:** PC1Dmod — efficiency error 0.8% absolute
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | η Error (abs) | Jsc Error | Runtime | Q |
|--------|-------------|----------|---------|---|
| Analytical | 0.03 | 1.5 | 0.01 s | 0.75 |
| PC1Dmod | 0.008 | 0.3 | 0.5 s | 0.90 |
| Sentaurus 2D | 0.005 | 0.15 | 60 s | 0.90 |
| Full 3D (Silvaco) | 0.002 | 0.08 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (3D): 300 × 1.00 = 300 PWM
Floor:          300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p493_hash>",
  "h_s": "sha256:<spec493_hash>",
  "h_b": "sha256:<bench493_hash>",
  "r": {"efficiency_error": 0.002, "error_bound": 0.02, "ratio": 0.100},
  "c": {"Jsc_error": 0.08, "thicknesses": 4, "K": 3},
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
pwm-node benchmarks | grep solar_cell
pwm-node verify solar_cell/si_cell_s1.yaml
pwm-node mine solar_cell/si_cell_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
