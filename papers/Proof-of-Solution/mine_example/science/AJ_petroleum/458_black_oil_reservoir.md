# Principle #458 — Black Oil Reservoir Simulation

**Domain:** Petroleum Engineering | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.darcy] --> [∂.space] --> [B.well] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.darcy-->∂.x-->B.well  BlackOil  SPE1-benchmark  IMPES/FIM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BLACK OIL RESERVOIR SIMULATION   P = (E,G,W,C)   Principle #458│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂(φ S_α ρ_α)/∂t + ∇·(ρ_α u_α) = q_α                 │
│        │ u_α = −(k k_{rα}/μ_α)(∇p_α − ρ_α g∇D)  (Darcy)      │
│        │ α ∈ {oil, water, gas}; S_o+S_w+S_g = 1                │
│        │ PVT via B_o(p), R_s(p); capillary p_c(S)              │
│        │ Forward: given IC/BC/PVT/rel-perm → (p,S) over Ω×[0,T]│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.darcy] ──→ [∂.x] ──→ [B.well]             │
│        │  time-step  Darcy-flux  spatial-disc  well-BC          │
│        │ V={∂.t,N.darcy,∂.x,B.well}  A={∂.t→N.darcy,N.darcy→∂.x,∂.x→B.well}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (weak solutions for two-phase/three-phase)│
│        │ Uniqueness: YES under monotone flux / Corey rel-perm   │
│        │ Stability: CFL-limited for IMPES; unconditional for FIM│
│        │ Mismatch: rel-perm uncertainty, PVT data errors        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖p−p_ref‖/‖p_ref‖ (primary)    │
│        │ q = 2.0 (TPFA), 1.0 (upwind mobility)                │
│        │ T = {residual_norm, material_balance_error, K_meshes}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pressure/saturation dimensions consistent; saturation sum = 1 enforced | PASS |
| S2 | Monotone flux guarantees BV solutions; TPFA on K-orthogonal grids stable | PASS |
| S3 | IMPES / fully-implicit converge for SPE1-class problems | PASS |
| S4 | Material balance error < 10⁻⁸ achievable; pressure L2 bounded | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# black_oil/spe1_s1_ideal.yaml
principle_ref: sha256:<p458_hash>
omega:
  grid: [10, 10, 3]
  domain: SPE1_reservoir
  time: [0, 3650.0]   # 10 years
  dt: 30.0             # days
E:
  forward: "∂(φSρ)/∂t + ∇·(ρu) = q;  u = −(kk_r/μ)(∇p − ρg∇D)"
  phases: [oil, water, gas]
  PVT: SPE1_BO_table
B:
  wells:
    producer: {type: BHP, value: 4000 psi}
    injector: {type: rate, value: 5000 STB/d, fluid: water}
  boundaries: no_flow
I:
  scenario: SPE1_comparative
  grid_sizes: [10x10x3, 20x20x6, 40x40x12]
O: [pressure_L2, saturation_L1, material_balance_error]
epsilon:
  pressure_L2_max: 5.0e-3
  material_balance_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 10×10×3 matches SPE1 standard; dt=30 d stable for FIM | PASS |
| S2 | Well-posed with no-flow BC and well constraints | PASS |
| S3 | IMPES and FIM converge for SPE1 within 10⁴ Newton iterations | PASS |
| S4 | Pressure error < 5×10⁻³ achievable on fine grid | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# black_oil/benchmark_spe1.yaml
spec_ref: sha256:<spec458_hash>
principle_ref: sha256:<p458_hash>
dataset:
  name: SPE1_comparative_solution
  reference: "Odeh (1981) SPE1 Comparative Solution Project"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: IMPES
    params: {grid: 10x10x3, dt: 30d}
    results: {pressure_L2: 8.2e-3, material_balance: 1.1e-9}
  - solver: Fully-Implicit (Newton)
    params: {grid: 10x10x3, dt: 30d, max_newton: 10}
    results: {pressure_L2: 5.1e-3, material_balance: 3.2e-10}
  - solver: Fully-Implicit (fine)
    params: {grid: 20x20x6, dt: 15d}
    results: {pressure_L2: 1.3e-3, material_balance: 8.7e-11}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Fully-Implicit (Newton) — pressure L2 error 5.1×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pressure L2 | Mat-Bal Error | Runtime | Q |
|--------|-------------|---------------|---------|---|
| IMPES | 8.2e-3 | 1.1e-9 | 8 s | 0.75 |
| Fully-Implicit (10×10×3) | 5.1e-3 | 3.2e-10 | 25 s | 0.80 |
| Fully-Implicit (20×20×6) | 1.3e-3 | 8.7e-11 | 180 s | 0.90 |
| Fully-Implicit (40×40×12) | 3.8e-4 | 2.1e-11 | 1200 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (fine FIM): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p458_hash>",
  "h_s": "sha256:<spec458_hash>",
  "h_b": "sha256:<bench458_hash>",
  "r": {"residual_norm": 3.8e-4, "error_bound": 5.0e-3, "ratio": 0.076},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep black_oil
pwm-node verify black_oil/spe1_s1_ideal.yaml
pwm-node mine black_oil/spe1_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
