# CASSI quality log

Per `pwm-team/coordination/MAINNET_DEPLOY_PLAN.md` Stream 1, Director
logs CASSI reference-solver PSNR weekly (Friday).

**Done criterion (Stream 1):** average PSNR over KAIST-10 ≥ 24 dB.

## Schema

Each entry: date · solver tag · per-sample PSNR list · average · notes.

## Entries

| Date | Solver tag | sample_01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | avg | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-04-28 | baseline (stored solution.npz from `scripts/generate_demos.py`) — naive PSNR (no normalization) | 24.85 | 18.04 | 14.54 | 21.48 | 19.81 | 21.82 | 14.46 | 22.05 | 17.34 | 20.89 | **19.53** | First measured baseline. Reflects scale mismatch between gt range and solution range. |
| 2026-04-28 | baseline — normalized PSNR (each array divided by its own max — matches `generate_demos.py` convention and InverseNet [0,1] convention) | 19.86 | 17.25 | 12.34 | 14.60 | 15.47 | 18.75 | 13.46 | 18.46 | 11.66 | 14.68 | **15.65** | This is the metric the demo-generation log uses. 0/10 clear 24 dB. |

## InverseNet paper benchmarks (target reference)

Per `papers/inversenet/RECONSTRUCTION_ALGORITHM_GUIDE.md` and
`papers/inversenet/tables/cassi_results_table.csv`:

| Method | Scenario I (ideal) | Scenario II (mismatch) | Notes |
|---|---|---|---|
| **GAP-TV** (classical) | 24.34 ± 1.90 dB | 20.96 ± 1.62 dB | What our reference solver claims to be |
| **PnP-HSICNN** | 25.12 ± 1.88 dB | 20.40 ± 1.71 dB | |
| **HDNet** (deep) | **34.66 ± 2.62 dB** | 21.88 ± 1.72 dB | Best for ideal forward model |
| **MST-L** (deep) | **34.81 ± 2.11 dB** | 20.83 ± 2.01 dB | Best overall |

Our current 15.65 dB is materially below the GAP-TV Scenario I baseline (24.34 dB) and even below the GAP-TV Scenario II baseline (20.96 dB), suggesting the demo generation is operating with non-ideal-and-non-baseline parameters — investigate `scripts/generate_demos.py` solver hyperparameters and forward-model configuration. Achieving the 24 dB target via GAP-TV alone is realistic under Scenario I; alternatively, integrate HDNet or MST-L from `papers/inversenet/scripts/validate_cassi_inversenet_v2.py`.

## Single-sample proof (2026-04-28): public algorithm_base hits target

Ran `scripts/reproduce_inversenet_baseline.py` which uses the canonical
`pwm_core.recon.gap_tv.gap_tv_cassi` from
`public/algorithm_base/cassi/`:

```
CASSI sample_01:  26.49 dB  (29.8s; GAP-TV iter=100 lam=0.1 step=2; target >= 24, InverseNet claim 24.34 +/- 1.90)
CASSI PASS (target 24 dB)
```

Four deltas vs the existing demo solution.npz:
1. **Step-2 spectral dispersion** (snapshot width = 256 + 27*2 = 310). PWM `cassi_gap_tv.py` and `generate_demos.py` use step=1 and width=256.
2. **100 iterations** vs the demo's `CASSI_N_ITERS = 15`.
3. **lam=0.1** TV weight vs the demo's `tv_lambda=0.005`.
4. **Paper's PSNR convention** (clip both arrays to [0,1], peak=1) — earlier per-array max normalization in test_cassi_quality.py was wrong; bright GAP-TV solutions (sol.max ≈ 1.45) got penalized rather than clipped. Switching to the paper's `compute_psnr` (see `papers/inversenet/scripts/validate_cassi_inversenet.py` line 374) lifts sample_01 from 22.14 → 26.49 dB.

To clear the 24 dB target on all 10 KAIST samples, regenerate
`pwm-team/pwm_product/demos/cassi/sample_*/{snapshot,solution}.npz`
using `scripts/regenerate_demos_inversenet.py --only cassi` (which
uses `pwm_core.recon.gap_tv.gap_tv_cassi` with the four corrections).
