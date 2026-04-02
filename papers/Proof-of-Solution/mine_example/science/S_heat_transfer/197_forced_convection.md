# Principle #197 — Forced Convection Heat Transfer

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.robin] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian→B.robin      ForcedConv  pipe-Re2300       FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FORCED CONVECTION   P = (E,G,W,C)   Principle #197             │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂T/∂t + u·∇T = α∇²T   (energy equation)             │
│        │ Coupled with NS: ∂u/∂t + (u·∇)u = −∇p/ρ + ν∇²u      │
│        │ Nu = hL/k (Nusselt number, key output)                │
│        │ Forward: IC/BC/Re/Pr → solve (u,T) → compute Nu      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.robin]│
│        │ time  forced-convection  thermal-diffusion  convective-BC                │
│        │ V={∂.time,N.bilinear.advection,∂.space.laplacian,B.robin}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled parabolic system)              │
│        │ Uniqueness: YES for laminar; statistical for turbulent │
│        │ Stability: depends on Re and Pr                        │
│        │ Mismatch: wall roughness, inlet turbulence intensity  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Nu error vs correlation/DNS, T profile L2 error    │
│        │ q = 2.0 (FVM 2nd-order)                               │
│        │ T = {Nu_error, T_profile_error, friction_factor_error}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled NS + energy consistent; Nu definition well-formed | PASS |
| S2 | Graetz solution for developing flow; Shah-London correlations | PASS |
| S3 | FVM + SIMPLE converges; thermal BL resolved | PASS |
| S4 | Nu within 2% of Dittus-Boelter / Gnielinski correlation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# forced_conv/pipe_flow_s1.yaml
principle_ref: sha256:<p197_hash>
omega:
  grid: [200, 50]   # axial × radial
  domain: pipe_2D_axisymmetric
  L: 2.0
  R: 0.025
  time: steady_state
E:
  forward: "NS + energy, axisymmetric"
  Pr: 0.71
B:
  inlet: {u: parabolic, T: 300}
  wall: {T: 350}   # isothermal wall
  outlet: {zero_gradient: true}
I:
  scenario: pipe_forced_convection
  Re: 2300
  mesh_sizes: [100x25, 200x50]
O: [Nu_local_error, Nu_avg_error, T_profile_L2]
epsilon:
  Nu_error_max: 3.0e-2
  T_profile_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Axisymmetric mesh; thermal entry length L/D adequate | PASS |
| S2 | Graetz solution for developing thermal BL | PASS |
| S3 | SIMPLE converges for laminar Re=2300 | PASS |
| S4 | Nu error < 3% vs Shah-London | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# forced_conv/benchmark_pipe.yaml
spec_ref: sha256:<spec197_hash>
principle_ref: sha256:<p197_hash>
dataset:
  name: Shah_London_pipe
  reference: "Shah & London (1978) laminar duct flow"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-SIMPLE (OpenFOAM)
    params: {mesh: 200x50}
    results: {Nu_avg_error: 2.1%, T_profile_err: 5.8e-3}
  - solver: FEM-P2P1 (Fenics)
    params: {mesh: 100x25}
    results: {Nu_avg_error: 1.5%, T_profile_err: 3.2e-3}
  - solver: Spectral (Chebyshev-Fourier)
    params: {N: 48}
    results: {Nu_avg_error: 0.2%, T_profile_err: 1.5e-4}
quality_scoring:
  - {min_Nu_err: 0.5%, Q: 1.00}
  - {min_Nu_err: 2.0%, Q: 0.90}
  - {min_Nu_err: 4.0%, Q: 0.80}
  - {min_Nu_err: 8.0%, Q: 0.75}
```

**Baseline solver:** FEM-P2P1 — Nu error 1.5%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Nu Error | T Prof Err | Runtime | Q |
|--------|----------|-----------|---------|---|
| FVM-SIMPLE | 2.1% | 5.8e-3 | 20 s | 0.90 |
| FEM-P2P1 | 1.5% | 3.2e-3 | 30 s | 0.90 |
| Spectral | 0.2% | 1.5e-4 | 5 s | 1.00 |
| FVM (fine mesh) | 0.8% | 1.5e-3 | 60 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p197_hash>",
  "h_s": "sha256:<spec197_hash>",
  "h_b": "sha256:<bench197_hash>",
  "r": {"residual_norm": 2.0e-3, "error_bound": 3.0e-2, "ratio": 0.067},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 2},
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
pwm-node benchmarks | grep forced_conv
pwm-node verify forced_conv/pipe_flow_s1.yaml
pwm-node mine forced_conv/pipe_flow_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
