# Principle #298 — Ab Initio Molecular Dynamics (AIMD)

**Domain:** Computational Chemistry | **Carrier:** N/A (DFT+dynamics) | **Difficulty:** Hard (δ=5)
**DAG:** E.hermitian → N.xc → ∂.time.symplectic |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→N.xc→∂.time.symplectic      aimd        water-dynamics     CPMD/BOMD
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  AB INITIO MOLECULAR DYNAMICS     P = (E,G,W,C)   Principle #298│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ M_I R̈_I = −∂E_DFT[{R}]/∂R_I  (Born-Oppenheimer MD)   │
│        │ Or: Car-Parrinello: μφ̈ = −Hφ + Λφ (fictitious e⁻ mass)│
│        │ E_DFT computed on-the-fly at each time step            │
│        │ Forward: given initial {R,V} → trajectory {R(t),V(t)}  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [N.xc] ──→ [∂.time.symplectic]       │
│        │ eigensolve  nonlinear  derivative                      │
│        │ V={E.hermitian, N.xc, ∂.time.symplectic}  A={E.hermitian→N.xc, N.xc→∂.time.symplectic}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (BO surface well-defined for gapped sys)│
│        │ Uniqueness: deterministic given IC; ergodic in NVT      │
│        │ Stability: dt ≤ 0.5 fs for H; energy drift < 1 μHa/ps │
│        │ Mismatch: DFT functional error, finite-size effects    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |⟨O⟩_AIMD − ⟨O⟩_exp| (structural/dynamical obs.) │
│        │ q = 3.0 (DFT cost per step, N³)                      │
│        │ T = {RDF, diffusion_coeff, vibrational_spectrum}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Forces = −∇E_DFT consistent; Verlet symplectic integrator | PASS |
| S2 | BO approximation valid for gapped systems (water, organics) | PASS |
| S3 | BOMD with PBE converges to correct liquid water RDF | PASS |
| S4 | RDF peak position error < 0.05 A with revPBE-D3 at 64 H2O | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# aimd/water_s1_ideal.yaml
principle_ref: sha256:<p298_hash>
omega:
  atoms: 192  # 64 H2O
  box: [12.42, 12.42, 12.42]  # Angstrom, cubic
  time: 20.0  # ps
  dt: 0.5  # fs
E:
  forward: "BOMD with PBE+D3 / plane-wave basis"
  cutoff: 400  # eV
  SCF_convergence: 1.0e-6
B:
  ensemble: NVT
  thermostat: Nose-Hoover_330K
  PBC: true
I:
  scenario: liquid_water_300K
  density: 0.997  # g/cm³
  equilibration: 5  # ps
O: [RDF_OO, diffusion_coeff, vibrational_DOS]
epsilon:
  RDF_peak_error: 0.05  # Angstrom
  D_error_max: 0.5e-5  # cm²/s
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 64 H2O in 12.42 A box gives correct density; dt=0.5 fs adequate | PASS |
| S2 | PBE+D3 yields structured liquid water at 330 K (empirical T) | PASS |
| S3 | 20 ps trajectory provides converged RDF statistics | PASS |
| S4 | RDF O-O peak within 0.05 A of experiment (2.8 A) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# aimd/benchmark_water.yaml
spec_ref: sha256:<spec298_hash>
principle_ref: sha256:<p298_hash>
dataset:
  name: liquid_water_exp_RDF
  reference: "Skinner et al. (2013) X-ray RDF at 300 K"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BOMD-PBE
    params: {cutoff: 400eV, T: 330K}
    results: {RDF_peak_err: 0.08, D: 1.8e-5}
  - solver: BOMD-revPBE-D3
    params: {cutoff: 400eV, T: 300K}
    results: {RDF_peak_err: 0.04, D: 2.1e-5}
  - solver: BOMD-SCAN
    params: {cutoff: 600eV, T: 330K}
    results: {RDF_peak_err: 0.03, D: 2.3e-5}
quality_scoring:
  - {min_RDF_err: 0.02, Q: 1.00}
  - {min_RDF_err: 0.04, Q: 0.90}
  - {min_RDF_err: 0.08, Q: 0.80}
  - {min_RDF_err: 0.15, Q: 0.75}
```

**Baseline solver:** BOMD-revPBE-D3 — RDF peak error 0.04 A
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RDF Error (A) | D (cm²/s) | Runtime | Q |
|--------|---------------|-----------|---------|---|
| BOMD-PBE | 0.08 | 1.8e-5 | 48 h | 0.80 |
| BOMD-revPBE-D3 | 0.04 | 2.1e-5 | 48 h | 0.90 |
| BOMD-SCAN | 0.03 | 2.3e-5 | 72 h | 0.90 |
| BOMD-r²SCAN+D4 | 0.015 | 2.3e-5 | 72 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (r²SCAN): 500 × 1.00 = 500 PWM
Floor:              500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p298_hash>",
  "h_s": "sha256:<spec298_hash>",
  "h_b": "sha256:<bench298_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.05, "ratio": 0.30},
  "c": {"fitted_rate": 3.05, "theoretical_rate": 3.0, "K": 4},
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
pwm-node benchmarks | grep aimd
pwm-node verify aimd/water_s1_ideal.yaml
pwm-node mine aimd/water_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
