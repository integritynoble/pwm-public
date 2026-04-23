# CASSI demo dataset — `L3-003` (T1_nominal-equivalent)

Canonical, committed-to-repo demo input + reference output. Any external
user or CI job can verify the reference solver works against this dataset
in < 5 seconds.

**⚠ This is NOT the real L3-003 benchmark.** It is a 32×32×8 synthetic
problem created by `scripts/generate_demos.py` from a fixed RNG seed.
Use it to verify the pipeline; do NOT submit cert_hashes computed against
it expecting to score on the real leaderboard.

## Files

| File | Purpose | Shape |
|------|---------|-------|
| `snapshot.npz` | Solver input: `y`, `mask`, `shifts` | y: (32, 32) |
| `ground_truth.npz` | True HSI cube (for PSNR scoring) | (32, 32, 8) |
| `solution.npz` | Pre-computed output from the reference GAP-TV solver | (32, 32, 8) |
| `meta.json` | Provenance + SHA-256 hashes of the three `.npz` files |

## Run the reference solver on this demo

```bash
python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
    --input  pwm-team/pwm_product/demos/cassi \
    --output /tmp/cassi_out
cat /tmp/cassi_out/meta.json
```

Expected: `PSNR=10.60 dB`. If your output differs, either numpy's math
is drifting between versions or the committed `snapshot.npz` was
corrupted — re-run `scripts/generate_demos.py --cassi` to regenerate.

## Swap in your own solver

Any solver matching the input contract (reads `snapshot.npz` with keys
`y`, `mask`, `shifts`; writes `solution.npz` with key `cube`) can use
this exact input:

```bash
python3 /path/to/your_solver.py \
    --input pwm-team/pwm_product/demos/cassi \
    --output /tmp/your_out
```

Your output goes in `/tmp/your_out/solution.npz`. Compare PSNR to the
10.60 dB floor; if you beat it, submit via
`pwm-node mine L3-003 --solver /path/to/your_solver.py` against the
real benchmark (not this demo).

## Regenerate

If you change the demo parameters (size, seed, noise level):

```bash
python3 scripts/generate_demos.py --cassi
```

The outputs are deterministic at the committed seed; regeneration
produces byte-identical files.
