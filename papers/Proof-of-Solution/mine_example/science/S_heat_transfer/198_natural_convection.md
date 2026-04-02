# Principle #198 — Natural Convection

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian→B.wall      NatConv     diff-heated-cav   FVM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NATURAL CONVECTION   P = (E,G,W,C)   Principle #198            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂u/∂t + (u·∇)u = −∇p/ρ₀ + ν∇²u + gβ(T−T₀)ê_y       │
│        │ ∇·u = 0;   ∂T/∂t + u·∇T = α∇²T                      │
│        │ Boussinesq approximation; Ra = gβΔTL³/(να)            │
│        │ Forward: IC/BC/Ra/Pr → solve (u,T) → compute Nu      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.wall]│
│        │ time  buoyant-advection  thermal-diffusion  wall-BC                     │
│        │ V={∂.time,N.bilinear.advection,∂.space.laplacian,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Boussinesq well-posed for all Ra)      │
│        │ Uniqueness: YES (steady for Ra < ~10⁸)                │
│        │ Stability: Ra-dependent; turbulent transition ~10⁹    │
│        │ Mismatch: β uncertainty, cavity aspect ratio          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Nu error, velocity/temperature profile errors      │
│        │ q = 2.0 (FVM 2nd-order)                               │
│        │ T = {Nu_error, max_velocity_error, T_profile_error}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Boussinesq coupling consistent; Ra well-defined | PASS |
| S2 | de Vahl Davis benchmark exists for cavity Ra ≤ 10⁶ | PASS |
| S3 | FVM/FEM converge; Nu converges with grid refinement | PASS |
| S4 | Nu error < 1% vs benchmark for Ra ≤ 10⁶ | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nat_conv/diff_heated_cavity_s1.yaml
principle_ref: sha256:<p198_hash>
omega:
  grid: [128, 128]
  domain: unit_square
  time: steady_state
E:
  forward: "Boussinesq NS + energy"
  Pr: 0.71
  Ra: 1.0e6
B:
  left: {T: 1.0}   # hot wall
  right: {T: 0.0}   # cold wall
  top_bottom: {flux: 0, u: [0,0]}
I:
  scenario: differentially_heated_cavity
  Ra_values: [1e3, 1e4, 1e5, 1e6]
  mesh_sizes: [32, 64, 128]
O: [Nu_error, u_max_error, T_midplane_error]
epsilon:
  Nu_error_max: 1.0e-2
  T_profile_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves thermal BL at Ra=10⁶ (~h ≤ 1/100) | PASS |
| S2 | Steady solution exists; de Vahl Davis reference available | PASS |
| S3 | SIMPLE/projection converges; under-relaxation for high Ra | PASS |
| S4 | Nu < 1% error at 128² for Ra=10⁶ | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# nat_conv/benchmark_cavity.yaml
spec_ref: sha256:<spec198_hash>
principle_ref: sha256:<p198_hash>
dataset:
  name: deVahlDavis_cavity
  reference: "de Vahl Davis (1983) benchmark solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-QUICK (OpenFOAM)
    params: {grid: 128x128}
    results: {Nu_error: 0.5%, u_max_err: 0.3%}
  - solver: FEM-P2P1
    params: {grid: 64x64}
    results: {Nu_error: 0.3%, u_max_err: 0.2%}
  - solver: Spectral
    params: {N: 48}
    results: {Nu_error: 0.01%, u_max_err: 0.01%}
quality_scoring:
  - {min_Nu_err: 0.05%, Q: 1.00}
  - {min_Nu_err: 0.5%, Q: 0.90}
  - {min_Nu_err: 1.0%, Q: 0.80}
  - {min_Nu_err: 2.0%, Q: 0.75}
```

**Baseline solver:** FVM-QUICK — Nu error 0.5%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Nu Error | u_max Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FVM-upwind | 1.5% | 1.2% | 15 s | 0.80 |
| FVM-QUICK | 0.5% | 0.3% | 30 s | 0.90 |
| FEM-P2P1 | 0.3% | 0.2% | 45 s | 0.90 |
| Spectral | 0.01% | 0.01% | 10 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p198_hash>",
  "h_s": "sha256:<spec198_hash>",
  "h_b": "sha256:<bench198_hash>",
  "r": {"residual_norm": 1.0e-4, "error_bound": 1.0e-2, "ratio": 0.01},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep nat_conv
pwm-node verify nat_conv/diff_heated_cavity_s1.yaml
pwm-node mine nat_conv/diff_heated_cavity_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
