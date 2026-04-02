# Principle #223 — Phase-Field Fracture

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Frontier (δ=5)
**DAG:** [∂.time] --> [N.damage] --> [∂.space.laplacian] --> [L.stiffness] |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.damage→∂.space.laplacian→L.stiffness   PF-frac     branching-crack    FEM-stag
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE-FIELD FRACTURE              P = (E,G,W,C)  Principle #223│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E[u,d] = ∫ [(1−d)² ψ⁺(ε) + ψ⁻(ε)] dΩ                │
│        │        + G_c ∫ [d²/(2l) + l/2 |∇d|²] dΩ              │
│        │ d ∈ [0,1] = phase-field damage; l = regularisation len │
│        │ Forward: given BC/G_c/l → solve for (u, d) over Ω     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.damage] --> [∂.space.laplacian] --> [L.stiffness]│
│        │ load-step  damage-update  crack-diffusion  degraded-stiffness    │
│        │ V={∂.time,N.damage,∂.space.laplacian,L.stiffness}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Γ-convergence to Griffith as l→0)     │
│        │ Uniqueness: NO (non-convex coupling; staggered scheme  │
│        │   gives local minimiser)                                │
│        │ Stability: l/h ratio must be ≥ 2; irreversibility ḋ≥0 │
│        │ Mismatch: l calibration, G_c error, tension-compression│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = crack path error + G_c dissipation error (primary) │
│        │ q = 1.0 (damage localisation limits convergence)      │
│        │ T = {dissipated_energy, crack_path, K_resolutions}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Variational energy functional well-defined; tension-compression split | PASS |
| S2 | Γ-convergence proven (Bourdin et al.); staggered scheme converges | PASS |
| S3 | Staggered alternate minimisation converges to local minimum | PASS |
| S4 | Dissipated energy converges to G_c × crack area as l/h → 0 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# phase_field_fracture/branching_crack_s1_ideal.yaml
principle_ref: sha256:<p223_hash>
omega:
  grid: [256, 256]
  domain: rectangular_plate
  size: [1.0, 0.5]
E:
  forward: "Variational phase-field fracture (AT2 model)"
  G_c: 2700.0    # J/m²
  l: 0.01        # regularisation length
  E_modulus: 210.0e9
  poisson: 0.3
B:
  top: {u_y: controlled}   # displacement-controlled
  bottom: {u: [0, 0]}
  initial_notch: {y: 0.25, length: 0.25}
I:
  scenario: notched_plate_tension
  l_over_h: [2, 4, 8]
  mesh_sizes: [128², 256², 512²]
O: [crack_path, dissipated_energy_error, peak_load_error]
epsilon:
  dissipation_error_max: 5.0e-2
  peak_load_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | l/h ≥ 2 at all mesh levels; irreversibility enforced | PASS |
| S2 | Γ-convergence ensures mesh-independent crack path as l→0 | PASS |
| S3 | Staggered scheme converges in < 50 iterations per load step | PASS |
| S4 | Dissipation error < 5% at 256² with l/h=4 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# phase_field_fracture/benchmark_notched_plate.yaml
spec_ref: sha256:<spec223_hash>
principle_ref: sha256:<p223_hash>
dataset:
  name: PF_fracture_notched_plate
  reference: "Miehe et al. (2010) — phase-field fracture benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-staggered (128²)
    params: {l_over_h: 4, AT2: true}
    results: {dissipation_error: 8.5e-2, peak_load_error: 6.0e-2}
  - solver: FEM-staggered (256²)
    params: {l_over_h: 4, AT2: true}
    results: {dissipation_error: 3.5e-2, peak_load_error: 2.8e-2}
  - solver: FEM-monolithic (256²)
    params: {l_over_h: 4, AT2: true}
    results: {dissipation_error: 2.0e-2, peak_load_error: 1.5e-2}
quality_scoring:
  - {min_err: 1.0e-2, Q: 1.00}
  - {min_err: 3.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** FEM-staggered (256²) — dissipation error 3.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Dissip. Err | Peak Ld Err | Runtime | Q |
|--------|-------------|-------------|---------|---|
| FEM-staggered (128²) | 8.5e-2 | 6.0e-2 | 120 s | 0.75 |
| FEM-staggered (256²) | 3.5e-2 | 2.8e-2 | 600 s | 0.90 |
| FEM-monolithic (256²) | 2.0e-2 | 1.5e-2 | 900 s | 0.90 |
| AMR-staggered (eff. 512²) | 8.0e-3 | 5.0e-3 | 800 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (AMR):  500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p223_hash>",
  "h_s": "sha256:<spec223_hash>",
  "h_b": "sha256:<bench223_hash>",
  "r": {"residual_norm": 8.0e-3, "error_bound": 5.0e-2, "ratio": 0.16},
  "c": {"fitted_rate": 1.02, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep phase_field_fracture
pwm-node verify phase_field_fracture/branching_crack_s1_ideal.yaml
pwm-node mine phase_field_fracture/branching_crack_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
