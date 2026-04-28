# CACTI quality log

Per `pwm-team/coordination/MAINNET_DEPLOY_PLAN.md` Stream 1, Director
logs CACTI reference-solver PSNR weekly (Friday).

**Done criterion (Stream 1):** average PSNR over SCI-6 ≥ 24 dB.

## Schema

Each entry: date · solver tag · per-sample PSNR list · average · notes.

## Entries

| Date | Solver tag | Kobe | Traffic | Runner | Drop | Crash | Aerial | avg | notes |
|---|---|---|---|---|---|---|---|---|---|
| 2026-04-28 | baseline (stored solution.npz from `scripts/generate_demos.py`) | 11.72 | 6.31 | 9.37 | 2.23 | 5.13 | 8.64 | **7.23** | First measured baseline. 0/6 samples meet 24 dB. Massive gap (~17 dB). **Suspected scale mismatch:** ground_truth.npz is in [0, 255] (uint8-like) but solution.npz is in [0, 5.76]. Either solver output normalization is wrong or generate_demos.py forgot to denormalize before saving. Fixing the scale alone should close most of the gap. |
