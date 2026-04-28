# CASSI quality log

Per `pwm-team/coordination/MAINNET_DEPLOY_PLAN.md` Stream 1, Director
logs CASSI reference-solver PSNR weekly (Friday).

**Done criterion (Stream 1):** average PSNR over KAIST-10 ≥ 24 dB.

## Schema

Each entry: date · solver tag · per-sample PSNR list · average · notes.

## Entries

| Date | Solver tag | sample_01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | avg | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-04-28 | baseline (stored solution.npz from `scripts/generate_demos.py`) | 24.85 | 18.04 | 14.54 | 21.48 | 19.81 | 21.82 | 14.46 | 22.05 | 17.34 | 20.89 | **19.53** | First measured baseline. 1/10 samples meet 24 dB. Gap to target ≈ 4.5 dB. Driven by samples 03, 07 which sit at ~14 dB. Investigate per-scene priors / TV-weight tuning. |
