# CASSI reference solver — GAP-TV (numpy only)

**Purpose.** A minimal, self-contained reference reconstruction that
external CP submissions can compete against. NOT a state-of-the-art
solver.

**Expected quality.** ~10-15 dB PSNR on T1_nominal, materially worse on
higher tiers. State-of-the-art solvers (PnP-HSICNN) reach ~31.8 dB on
T1_nominal. A factor-of-2 dB gap is expected and intentional — this
file exists so the pipeline works end-to-end and so the Rank-1
leaderboard slot for L3-003 sits at a genuinely-beatable number from
day one.

## Run it

```bash
# Auto-synthetic input (CI smoke test):
python3 cassi_gap_tv.py --input /tmp/empty_dir --output /tmp/out --verbose

# Real input:
python3 cassi_gap_tv.py --input /path/to/benchmark_input --output /tmp/out
```

## Input contract

The script reads `<input>/snapshot.npz` which must contain three
arrays:

- `y`: shape `(H, W)`, float32 — coded-aperture snapshot
- `mask`: shape `(H, W)`, float32 (binary 0/1) — coded aperture
- `shifts`: shape `(N_bands,)`, int32 — per-band lateral shift (pixels)

Optional: `<input>/ground_truth.npz` with key `x` — if present, PSNR
against ground truth is computed and reported in the output meta.

If `snapshot.npz` is missing, the solver generates a tiny 32×32×8
synthetic problem so the binary still runs for CI smoke tests. The
synthetic problem is NOT the L3-003 benchmark.

## Output contract

Writes two files to `<output>`:

- `solution.npz` with key `cube`, shape `(H, W, N_bands)`, float32
- `meta.json` — solver name, version, iterations, PSNR (if ground-truth
  available), source (input vs. synthetic)

Both files are what `pwm-node mine` expects downstream; the scoring
engine reads them and produces a Q score.

## How to beat this

Obvious improvements any competing CP can make:

1. **Better prior** — swap the TV prox for BM3D, NLM, or a learned
   denoiser (PnP-CNN). Order-of-magnitude PSNR gain likely.
2. **Better forward model** — the reference assumes a pure per-band
   pixel shift, which is an approximation. Using the actual continuous
   dispersion with sub-pixel interpolation improves T2-T4 tiers.
3. **Better optimization** — learned unrolled networks (e.g.,
   DGSMP, ADMM-net) outperform handcrafted GAP-TV materially.
4. **Spectral correlation** — the current prox acts per-band; a prior
   that correlates across the spectral axis (3D TV, cross-channel
   sparsity) uses the structure GAP-TV ignores.

Submit via `pwm-node mine L3-003 --solver your_solver.py`.

## Why these choices

- **Numpy only, no scipy/torch** — external contributors can read the
  code without installing anything beyond what they'd use to mine
  anyway.
- **30 iterations + decaying TV weight** — enough to get past the
  trivial-floor reconstruction in most cases while keeping the
  smoke-test run under 5 seconds.
- **Per-band 2D TV (not 3D)** — 3D TV is a real win but adds code
  complexity that obscures the algorithm for readers. Left as a
  deliberate competing-solver target.

## File layout

```
cassi_gap_tv.py    # the solver (single file, no imports from pwm-*)
README.md          # this file
```

No external pwm_* dependencies; this directory is a drop-in for any
external CP to copy and modify.
