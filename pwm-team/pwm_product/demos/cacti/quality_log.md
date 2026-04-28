# CACTI quality log

Per `pwm-team/coordination/MAINNET_DEPLOY_PLAN.md` Stream 1, Director
logs CACTI reference-solver PSNR weekly (Friday).

**Done criterion (Stream 1):** average PSNR over SCI-6 ≥ 24 dB.

## Schema

Each entry: date · solver tag · per-sample PSNR list · average · notes.

## Entries

| Date | Solver tag | Kobe | Traffic | Runner | Drop | Crash | Aerial | avg | notes |
|---|---|---|---|---|---|---|---|---|---|
| 2026-04-28 | baseline (stored solution.npz from `scripts/generate_demos.py`) — naive PSNR (no normalization) | 11.72 | 6.31 | 9.37 | 2.23 | 5.13 | 8.64 | **7.23** | First measured. Heavily affected by scale mismatch: gt in [0, 255], solution in [0, 5.76]. |
| 2026-04-28 | baseline — normalized PSNR (per-array max — matches `generate_demos.py` PSNR convention used at generation time) | 13.90 | 8.42 | 11.86 | 4.69 | 7.34 | 10.99 | **9.53** | This is the metric the demo-generation log uses. 0/6 clear 24 dB. Gap is real, not a normalization artifact. |

## InverseNet paper benchmarks (target reference)

Per `papers/inversenet/RECONSTRUCTION_ALGORITHM_GUIDE.md` and
`papers/inversenet/tables/cacti_results_table.csv`:

| Method | Scenario I (ideal) | Scenario II (mismatch) | Notes |
|---|---|---|---|
| **GAP-TV** (classical) | 26.75 ± 4.48 dB | 15.81 ± 1.98 dB | What our reference solver claims to be |
| **PnP-FFDNet** (classical+denoiser) | 29.28 ± 5.53 dB | 11.43 ± 2.71 dB | |
| **ELP-Unfolding** (deep) | 34.09 ± 4.11 dB | 15.47 ± 1.71 dB | |
| **EfficientSCI** (deep) | **35.39 ± 4.46 dB** | 14.81 ± 2.19 dB | Best for ideal forward model |

Our current 9.53 dB is materially below the GAP-TV Scenario I baseline (26.75 dB) and below even Scenario II baseline (15.81 dB), suggesting the demo generation is using buggy or excessively-mismatched solver parameters. Achieving the 24 dB target via PnP-ADMM alone is plausible under Scenario I; alternatively, integrate EfficientSCI from local `/home/spiritai/EfficientSCI-main/` (or the InverseNet validation pipeline at `papers/inversenet/scripts/validate_cacti_inversenet.py`).
