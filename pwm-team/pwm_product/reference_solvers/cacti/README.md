# CACTI reference solver — PnP-ADMM + 2D TV (numpy only)

**Purpose.** Minimal, self-contained reference reconstruction that
external CP submissions can compete against on L3-004. NOT a
state-of-the-art solver.

**Expected quality.** ~12-17 dB PSNR on T1_nominal synthetic inputs.
State-of-the-art solvers (EfficientSCI, BIRNAT, DUN-3D) reach ~30 dB+
on the equivalent problem. The ~15 dB gap is expected and intentional
— a reference floor should be obviously beatable.

## Run it

```bash
# Auto-synthetic input (CI smoke test):
python3 cacti_pnp_admm.py --input /tmp/empty_dir --output /tmp/out --verbose

# Real input:
python3 cacti_pnp_admm.py --input /path/to/benchmark_input --output /tmp/out
```

## Input contract

The script reads `<input>/snapshot.npz` which must contain:

- `y`: shape `(H, W)`, float32 — compressive temporal snapshot
- `masks`: shape `(T, H, W)`, float32 (binary 0/1) — per-frame coded apertures

Optional `<input>/ground_truth.npz` with key `x` — if present, PSNR is
computed and logged in the output meta.

If `snapshot.npz` is missing, the solver generates a tiny 4-frame
32×32 synthetic problem (moving Gaussian blob) so the binary runs for
CI. The synthetic problem is NOT the L3-004 benchmark.

## Output contract

Writes two files to `<output>`:

- `solution.npz` with key `video`, shape `(T, H, W)`, float32
- `meta.json` — solver name, version, ADMM parameters, PSNR if available

## How to beat this

1. **Learned denoiser.** Replace the 2D TV prox with BM3D (scikit-image
   ships this) or a learned CNN denoiser. Order-of-magnitude PSNR gain
   expected. Most published CACTI solvers take this path.
2. **3D prior.** The reference applies TV per-frame, ignoring temporal
   coherence. Using a spatiotemporal prior (3D TV, optical-flow-regularized
   TV, learned temporal prior) is where the biggest wins come from.
3. **Exact x-update.** The reference uses a diagonal Jacobi approximation
   for the (Phi^T Phi + rho I)^{-1} step. The exact inverse is tractable
   (diagonal per-pixel after Fourier or direct linear system) and
   improves convergence.
4. **Unrolled networks.** DUN-3D, BIRNAT, EfficientSCI — all unrolled
   deep networks that dominate the leaderboard on realistic tiers.

Submit via `pwm-node mine L3-004 --solver your_solver.py`.

## File layout

```
cacti_pnp_admm.py  # the solver (single file, no pwm-* imports)
README.md          # this file
```

Self-contained — copy this directory and modify freely.
