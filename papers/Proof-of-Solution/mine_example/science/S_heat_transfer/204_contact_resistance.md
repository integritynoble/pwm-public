# Principle #204 — Thermal Contact Resistance

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [∂.space.laplacian] --> [N.pointwise.contact] --> [B.interface] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.pointwise.contact→B.interface        TCR         bolted-joint      FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THERMAL CONTACT RESISTANCE   P = (E,G,W,C)   Principle #204    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇·(k∇T) = Q  in each body                            │
│        │ Interface: q = (T₁−T₂)/R_c  (contact conductance)     │
│        │ R_c = f(pressure, roughness, material, interstitial)  │
│        │ R_c may depend on T (nonlinear)                        │
│        │ Forward: BC/geometry/R_c → T(x) across joint          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space.laplacian] --> [N.pointwise.contact] --> [B.interface]│
│        │ time  thermal-diffusion  contact-resistance  interface-BC                   │
│        │ V={∂.time,∂.space.laplacian,N.pointwise.contact,B.interface}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (elliptic with Robin-type interface)    │
│        │ Uniqueness: YES for R_c > 0                            │
│        │ Stability: κ depends on R_c magnitude                  │
│        │ Mismatch: R_c model uncertainty (CMY, Mikic, etc.)    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = temperature jump error at interface, flux error     │
│        │ q = 2.0 (FEM with interface elements)                 │
│        │ T = {T_jump_error, flux_error, R_c_sensitivity}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Robin-type interface condition consistent; R_c > 0 | PASS |
| S2 | Well-posed elliptic with jump condition | PASS |
| S3 | FEM with interface elements converges | PASS |
| S4 | Temperature jump error bounded by mesh size at interface | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tcr/bolted_joint_s1.yaml
principle_ref: sha256:<p204_hash>
omega:
  grid: [100, 50]
  domain: two_blocks_1D
  time: steady_state
E:
  forward: "−k∇²T = 0 with contact resistance R_c at interface"
  k: {body1: 50, body2: 200}
  R_c: 5.0e-4   # m²·K/W
B:
  top: {T: 100}
  bottom: {T: 20}
I:
  scenario: bolted_joint_conduction
  R_c_values: [1e-4, 5e-4, 1e-3]
  mesh_sizes: [25, 50, 100]
O: [T_jump_error, heat_flux_error, effective_R_error]
epsilon:
  T_jump_error_max: 1.0e-2
  flux_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Two blocks; R_c interface well-defined | PASS |
| S2 | 1D exact solution exists for uniform R_c | PASS |
| S3 | FEM with interface elements converges | PASS |
| S4 | T jump error < 1% at N=100 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# tcr/benchmark_joint.yaml
spec_ref: sha256:<spec204_hash>
principle_ref: sha256:<p204_hash>
dataset:
  name: TCR_1D_exact
  reference: "Madhusudana (2014) thermal contact conductance"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1 (interface)
    params: {N: 50}
    results: {T_jump_err: 5.2e-3, flux_error: 3.8e-3}
  - solver: FEM-P2 (interface)
    params: {N: 50}
    results: {T_jump_err: 1.2e-4, flux_error: 8.5e-5}
  - solver: FDM (harmonic mean)
    params: {N: 100}
    results: {T_jump_err: 8.5e-3, flux_error: 6.2e-3}
quality_scoring:
  - {min_T_jump: 1.0e-4, Q: 1.00}
  - {min_T_jump: 1.0e-3, Q: 0.90}
  - {min_T_jump: 5.0e-3, Q: 0.80}
  - {min_T_jump: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-P2 — T jump error 1.2×10⁻⁴
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Jump Err | Flux Err | Runtime | Q |
|--------|-----------|---------|---------|---|
| FDM (harmonic) | 8.5e-3 | 6.2e-3 | 0.01 s | 0.80 |
| FEM-P1 | 5.2e-3 | 3.8e-3 | 0.05 s | 0.80 |
| FEM-P2 | 1.2e-4 | 8.5e-5 | 0.1 s | 0.90 |
| FEM-P2 (fine) | 8.1e-6 | 5.5e-6 | 0.5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p204_hash>",
  "h_s": "sha256:<spec204_hash>",
  "h_b": "sha256:<bench204_hash>",
  "r": {"residual_norm": 8.1e-6, "error_bound": 1.0e-2, "ratio": 8.1e-4},
  "c": {"fitted_rate": 3.0, "theoretical_rate": 3.0, "K": 3},
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
pwm-node benchmarks | grep tcr
pwm-node verify tcr/bolted_joint_s1.yaml
pwm-node mine tcr/bolted_joint_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
