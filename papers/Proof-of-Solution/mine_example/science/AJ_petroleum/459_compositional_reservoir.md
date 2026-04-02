# Principle #459 — Compositional Reservoir Simulation

**Domain:** Petroleum Engineering | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [N.darcy] --> [∂.space] --> [N.pointwise] --> [B.well] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.darcy-->∂.x-->N.pw-->B.well  CompSim  SPE3-benchmark  FIM+flash
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COMPOSITIONAL RESERVOIR SIM   P = (E,G,W,C)   Principle #459   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂(φ Σ_α S_α ρ_α x_{iα})/∂t + ∇·Σ_α(ρ_α x_{iα} u_α)│
│        │   = q_i,   i = 1…N_c  (component conservation)        │
│        │ u_α = −(k k_{rα}/μ_α)(∇p_α − ρ_α g∇D)               │
│        │ Phase equilibrium: f_i^L(p,T,x) = f_i^V(p,T,y)  (EOS)│
│        │ Forward: given IC/BC/EOS → (p,S,x_i) over Ω×[0,T]    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.darcy] ──→ [∂.x] ──→ [N.pw] ──→ [B.well]  │
│        │  time-step  Darcy-flux  spatial  flash-calc  well-BC   │
│        │ V={∂.t,N.darcy,∂.x,N.pw,B.well}  A={∂.t→N.darcy,N.darcy→∂.x,∂.x→N.pw,N.pw→B.well}  L_DAG=4.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (weak solutions with Peng-Robinson EOS) │
│        │ Uniqueness: YES when flash converges to unique root    │
│        │ Stability: Newton convergence requires good initial    │
│        │ Mismatch: EOS parameter uncertainty, near-critical     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖z−z_ref‖/‖z_ref‖ (composition)│
│        │ q = 2.0 (TPFA), 1.0 (upstream mobility weighting)    │
│        │ T = {residual_norm, component_balance, K_meshes}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Component mole fractions sum to 1; fugacity equality well-defined | PASS |
| S2 | Peng-Robinson flash yields unique phase split away from critical | PASS |
| S3 | Fully-implicit + Successive Substitution / Newton flash converge | PASS |
| S4 | Component balance error < 10⁻⁸; composition L2 bounded | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# comp_sim/spe3_s1_ideal.yaml
principle_ref: sha256:<p459_hash>
omega:
  grid: [9, 9, 4]
  domain: SPE3_reservoir
  time: [0, 5475.0]   # 15 years
  dt: 30.0
E:
  forward: "component conservation + Darcy + Peng-Robinson EOS flash"
  components: [C1, C3, C6, C10, C15, CO2]
  EOS: Peng_Robinson
B:
  wells:
    producer: {type: BHP, value: 2000 psi}
    injector: {type: rate, fluid: CO2_enriched_gas}
  boundaries: no_flow
I:
  scenario: SPE3_gas_injection
  grid_sizes: [9x9x4, 18x18x8, 36x36x16]
O: [pressure_L2, composition_L2, recovery_factor]
epsilon:
  pressure_L2_max: 5.0e-3
  component_balance_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 9×9×4 matches SPE3; dt=30 d with adaptive sub-stepping | PASS |
| S2 | CO₂ injection well-posed; flash converges for PR EOS | PASS |
| S3 | FIM + Newton converges within 15 iterations per step | PASS |
| S4 | Pressure L2 < 5×10⁻³ on refined grid | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# comp_sim/benchmark_spe3.yaml
spec_ref: sha256:<spec459_hash>
principle_ref: sha256:<p459_hash>
dataset:
  name: SPE3_comparative_solution
  reference: "Kenyon & Behie (1987) SPE3 Comparative Solution Project"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FIM-SSI-flash
    params: {grid: 9x9x4, dt: 30d}
    results: {pressure_L2: 7.5e-3, recovery_factor_error: 2.1e-2}
  - solver: FIM-Newton-flash
    params: {grid: 9x9x4, dt: 30d}
    results: {pressure_L2: 5.8e-3, recovery_factor_error: 1.5e-2}
  - solver: FIM-Newton-flash (fine)
    params: {grid: 18x18x8, dt: 15d}
    results: {pressure_L2: 1.8e-3, recovery_factor_error: 4.2e-3}
quality_scoring:
  - {min_L2: 1.0e-3, Q: 1.00}
  - {min_L2: 3.0e-3, Q: 0.90}
  - {min_L2: 6.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FIM-Newton-flash — pressure L2 error 5.8×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pressure L2 | Recovery Error | Runtime | Q |
|--------|-------------|----------------|---------|---|
| FIM-SSI-flash | 7.5e-3 | 2.1e-2 | 45 s | 0.75 |
| FIM-Newton-flash | 5.8e-3 | 1.5e-2 | 65 s | 0.80 |
| FIM-Newton (fine) | 1.8e-3 | 4.2e-3 | 520 s | 0.90 |
| FIM-Newton (finest) | 6.1e-4 | 1.1e-3 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (finest): 400 × 1.00 = 400 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p459_hash>",
  "h_s": "sha256:<spec459_hash>",
  "h_b": "sha256:<bench459_hash>",
  "r": {"residual_norm": 6.1e-4, "error_bound": 5.0e-3, "ratio": 0.122},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep comp_sim
pwm-node verify comp_sim/spe3_s1_ideal.yaml
pwm-node mine comp_sim/spe3_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
