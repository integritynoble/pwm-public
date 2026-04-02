# Principle #182 — Boussinesq Equations (Buoyancy-Driven Flow)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian→B.wall      Boussinesq  RB-convection     FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BOUSSINESQ EQUATIONS   P = (E,G,W,C)   Principle #182          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂u/∂t + (u·∇)u = −∇p/ρ₀ + ν∇²u − βg(T−T₀)ê_z       │
│        │ ∇·u = 0                                                │
│        │ ∂T/∂t + u·∇T = α∇²T                                   │
│        │ Density variation only in buoyancy term                │
│        │ Forward: IC/BC/Ra/Pr → solve (u,p,T) on Ω×[0,T]      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [∂.space.laplacian] --> [B.wall]│
│        │ time  advect+buoyancy  thermal-diffusion  wall-BC                       │
│        │ V={∂.time,N.bilinear.advection,∂.space.laplacian,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (weak solutions for all Ra)             │
│        │ Uniqueness: YES for Ra < Ra_c; statistical above       │
│        │ Stability: depends on Ra and Pr                        │
│        │ Mismatch: β error, thermal BC uncertainty              │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Nusselt number error, velocity profile L2 error    │
│        │ q = 2.0 (FEM-P2), spectral for benchmark cases       │
│        │ T = {Nu_error, T_profile_error, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled velocity-temperature system consistent; Boussinesq approx valid | PASS |
| S2 | Well-posed for bounded Ra; critical Ra computable from linear stability | PASS |
| S3 | FEM/FVM + projection method converges; spectral for low Ra | PASS |
| S4 | Nu error < 1% vs benchmark for Ra ≤ 10⁸ | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# boussinesq/rayleigh_benard_s1.yaml
principle_ref: sha256:<p182_hash>
omega:
  grid: [128, 128]
  domain: [4, 1]   # aspect ratio 4:1
  time: [0, 200]    # diffusion times
E:
  forward: "Boussinesq NS + energy equation"
  Pr: 0.71
  Ra: 1.0e6
B:
  bottom: {T: 1.0, u: [0,0]}
  top: {T: 0.0, u: [0,0]}
  sides: periodic
I:
  scenario: rayleigh_benard_2D
  Ra_values: [1e4, 1e5, 1e6]
O: [Nu_error, mean_T_profile_error, velocity_L2]
epsilon:
  Nu_error_max: 2.0e-2
  T_profile_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid adequate for thermal BL at Ra=10⁶; Pr=0.71 (air) | PASS |
| S2 | Steady convection rolls at Ra=10⁶; Nu well-defined | PASS |
| S3 | Projection + QUICK converges; Nu converges with grid | PASS |
| S4 | Nu error < 2% vs de Vahl Davis benchmark | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# boussinesq/benchmark_rb.yaml
spec_ref: sha256:<spec182_hash>
principle_ref: sha256:<p182_hash>
dataset:
  name: deVahlDavis_RB
  reference: "de Vahl Davis (1983) benchmark natural convection"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-QUICK
    params: {grid: 128x128, dt: 0.01}
    results: {Nu_error: 1.2%, T_profile_err: 3.1e-3}
  - solver: FEM-P2P1
    params: {grid: 64x64}
    results: {Nu_error: 0.8%, T_profile_err: 2.2e-3}
  - solver: Spectral (Chebyshev)
    params: {N: 48}
    results: {Nu_error: 0.1%, T_profile_err: 2.5e-4}
quality_scoring:
  - {min_Nu_err: 0.1%, Q: 1.00}
  - {min_Nu_err: 1.0%, Q: 0.90}
  - {min_Nu_err: 2.0%, Q: 0.80}
  - {min_Nu_err: 4.0%, Q: 0.75}
```

**Baseline solver:** FEM-P2P1 — Nu error 0.8%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Nu Error | T Profile Err | Runtime | Q |
|--------|----------|---------------|---------|---|
| FVM-QUICK | 1.2% | 3.1e-3 | 30 s | 0.90 |
| FEM-P2P1 | 0.8% | 2.2e-3 | 45 s | 0.90 |
| Spectral | 0.1% | 2.5e-4 | 10 s | 1.00 |
| LBM-thermal | 1.5% | 4.0e-3 | 20 s | 0.80 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p182_hash>",
  "h_s": "sha256:<spec182_hash>",
  "h_b": "sha256:<bench182_hash>",
  "r": {"residual_norm": 1.0e-3, "error_bound": 2.0e-2, "ratio": 0.05},
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
pwm-node benchmarks | grep boussinesq
pwm-node verify boussinesq/rayleigh_benard_s1.yaml
pwm-node mine boussinesq/rayleigh_benard_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
