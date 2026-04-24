# CASSI demo datasets — `L3-003`

Canonical, committed-to-repo inputs + reference outputs for `L3-003`.
**2 independent samples** (different RNG seeds) so external users
can see the reference solver is deterministic and not cherry-picked.

**⚠ These are NOT the real L3-003 benchmark.** They are small
(32×32) synthetic problems created by `scripts/generate_demos.py`.
Use them to verify the pipeline end-to-end; do NOT submit cert_hashes
computed against them.

## Samples

| Sample | Seed | Reference PSNR |
|--------|------|----------------|
| `sample_01/` | 42 | 10.6 dB |
| `sample_02/` | 43 | 10.73 dB |

## Files in each sample

| File | Purpose |
|------|---------|
| `snapshot.npz`     | Solver input |
| `ground_truth.npz` | True cube/video (for PSNR scoring) |
| `solution.npz`     | Pre-computed output from the reference solver |
| `snapshot.png`     | Rendered preview of the input |
| `ground_truth.png` | Rendered preview of the target |
| `meta.json`        | Provenance + SHA-256 hashes |

## Run the reference solver on sample_01

```bash
python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
    --input  pwm-team/pwm_product/demos/cassi/sample_01 \
    --output /tmp/out
cat /tmp/out/meta.json
```

Each sample is byte-stable across runs at the same git SHA.
