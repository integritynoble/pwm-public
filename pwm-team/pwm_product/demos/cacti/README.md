# CACTI demo dataset — `L3-004` (T1_nominal-equivalent)

Canonical, committed-to-repo demo input + reference output. Any external
user or CI job can verify the reference solver works against this
dataset in < 5 seconds.

**⚠ This is NOT the real L3-004 benchmark.** It is a 4-frame 32×32
synthetic problem created by `scripts/generate_demos.py` from a fixed
RNG seed. Use it to verify the pipeline; do NOT submit cert_hashes
computed against it expecting to score on the real leaderboard.

## Files

| File | Purpose | Shape |
|------|---------|-------|
| `snapshot.npz` | Solver input: `y`, `masks` | y: (32, 32) |
| `ground_truth.npz` | True video (for PSNR scoring) | (4, 32, 32) |
| `solution.npz` | Pre-computed output from the reference PnP-ADMM solver | (4, 32, 32) |
| `meta.json` | Provenance + SHA-256 hashes of the three `.npz` files |

## Run the reference solver on this demo

```bash
python3 pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py \
    --input  pwm-team/pwm_product/demos/cacti \
    --output /tmp/cacti_out
cat /tmp/cacti_out/meta.json
```

Expected: `PSNR=14.87 dB`. If your output differs, check numpy version
drift or re-run `scripts/generate_demos.py --cacti`.

## Swap in your own solver

Any solver matching the input contract (reads `snapshot.npz` with keys
`y`, `masks`; writes `solution.npz` with key `video`) can use this
exact input:

```bash
python3 /path/to/your_solver.py \
    --input pwm-team/pwm_product/demos/cacti \
    --output /tmp/your_out
```

Compare PSNR to the 14.87 dB floor; if you beat it, submit via
`pwm-node mine L3-004 --solver /path/to/your_solver.py` against the
real benchmark (not this demo).

## Regenerate

```bash
python3 scripts/generate_demos.py --cacti
```
