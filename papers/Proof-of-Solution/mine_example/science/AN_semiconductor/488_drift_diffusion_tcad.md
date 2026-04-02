# Principle #488 — Drift-Diffusion + Poisson (TCAD)

**Domain:** Semiconductor Physics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.space.gradient] --> [N.exponential] --> [L.poisson] --> [B.contact] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.x.grad-->N.exp-->L.poisson-->B.cont  DD-Poisson  pn-junction  Scharfetter-G
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DRIFT-DIFFUSION + POISSON (TCAD) P=(E,G,W,C) Principle #488   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·(ε∇ψ) = −q(p − n + N_D − N_A)  (Poisson)           │
│        │ ∂n/∂t = (1/q)∇·J_n − R,  J_n = qnμ_n E + qD_n∇n     │
│        │ ∂p/∂t = −(1/q)∇·J_p − R, J_p = qpμ_p E − qD_p∇p     │
│        │ R = SRH + Auger + radiative recombination              │
│        │ Forward: given doping/BC → (ψ,n,p,J) over device      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.x.grad] ──→ [N.exp] ──→ [L.poisson] ──→ [B.cont]    │
│        │  drift-field  Boltzmann  Poisson-eq  ohmic-BC          │
│        │ V={∂.x.grad,N.exp,L.poisson,B.cont}  A={∂.x.grad→N.exp,N.exp→L.poisson,L.poisson→B.cont}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Gummel/Newton converge for moderate V) │
│        │ Uniqueness: YES for thermal equilibrium; locally unique│
│        │ Stability: Scharfetter-Gummel discretization stable    │
│        │ Mismatch: mobility models, incomplete ionization       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |J_sim − J_expt|/J_expt  (current error)          │
│        │ q = 2.0 (SG discretization)                          │
│        │ T = {current_error, potential_L2, convergence_Newton}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Charge neutrality at contacts; current continuity ∇·J = qR | PASS |
| S2 | Scharfetter-Gummel ensures positivity of n,p | PASS |
| S3 | Gummel iteration / coupled Newton converges for V < 10V | PASS |
| S4 | IV curve matches experiment within 5% for standard diode | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dd_poisson/pn_diode_s1.yaml
principle_ref: sha256:<p488_hash>
omega:
  mesh: 500
  domain: 1D_silicon_pn_junction
  voltage_sweep: [-5, 1.0]
E:
  forward: "Poisson + electron/hole continuity (Scharfetter-Gummel)"
  material: Si
  N_D: 1.0e17   # cm⁻³
  N_A: 1.0e17
  recombination: [SRH, Auger]
B:
  anode: {type: ohmic}
  cathode: {type: ohmic}
I:
  scenario: silicon_pn_diode_IV
  mesh_sizes: [100, 500, 2000]
O: [IV_curve, depletion_width, breakdown_voltage]
epsilon:
  current_error_max: 0.05
  potential_L2_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 mesh points resolve depletion region; SG stable | PASS |
| S2 | Symmetric pn junction well-posed with ohmic contacts | PASS |
| S3 | Gummel + Newton converges for full voltage sweep | PASS |
| S4 | IV curve within 5% of analytical Shockley diode equation | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dd_poisson/benchmark_pn.yaml
spec_ref: sha256:<spec488_hash>
principle_ref: sha256:<p488_hash>
dataset:
  name: Silicon_pn_diode_reference
  reference: "Selberherr (1984) TCAD validation; Sze textbook"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gummel iteration
    params: {mesh: 500, tol: 1e-8}
    results: {current_error: 0.035, Newton_iters: 15}
  - solver: Coupled Newton
    params: {mesh: 500, tol: 1e-10}
    results: {current_error: 0.022, Newton_iters: 8}
  - solver: Coupled Newton (fine)
    params: {mesh: 2000, tol: 1e-12}
    results: {current_error: 0.008, Newton_iters: 8}
quality_scoring:
  - {min_err: 0.005, Q: 1.00}
  - {min_err: 0.02, Q: 0.90}
  - {min_err: 0.05, Q: 0.80}
  - {min_err: 0.10, Q: 0.75}
```

**Baseline solver:** Coupled Newton (500) — current error 2.2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Current Error | Newton Iters | Runtime | Q |
|--------|-------------|-------------|---------|---|
| Gummel (500) | 0.035 | 15 | 0.5 s | 0.80 |
| Newton (500) | 0.022 | 8 | 0.3 s | 0.90 |
| Newton (2000) | 0.008 | 8 | 1.2 s | 0.90 |
| Newton (adaptive) | 0.003 | 6 | 0.8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (adaptive): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p488_hash>",
  "h_s": "sha256:<spec488_hash>",
  "h_b": "sha256:<bench488_hash>",
  "r": {"current_error": 0.003, "error_bound": 0.05, "ratio": 0.060},
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
pwm-node benchmarks | grep dd_poisson
pwm-node verify dd_poisson/pn_diode_s1.yaml
pwm-node mine dd_poisson/pn_diode_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
