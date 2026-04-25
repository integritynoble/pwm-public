# CACTI — `L3-004` — InverseNet SCI Video Benchmark

6 standard coded-aperture temporal imaging videos from the SCI
Video Benchmark (Kobe, Traffic, Runner, Drop, Crash, Aerial). Each sample
is one 256×256×8 block reconstructed from a single coded snapshot by the
reference PnP-ADMM solver with 12 iterations.


## Samples

| Sample | Scene | Reference PSNR | Solver time |
|--------|-------|----------------|-------------|
| `sample_01/` | kobe | 13.9 dB | 1.4s |
| `sample_02/` | traffic | 8.42 dB | 1.4s |
| `sample_03/` | runner | 11.86 dB | 1.3s |
| `sample_04/` | drop | 4.69 dB | 1.3s |
| `sample_05/` | crash | 7.34 dB | 1.4s |
| `sample_06/` | aerial | 10.99 dB | 1.4s |

## Files per sample

| File | Purpose |
|------|---------|
| `snapshot.npz`     | Solver input: 2D coded-aperture measurement |
| `ground_truth.npz` | Full hyperspectral cube (CASSI) / 8-frame video (CACTI) |
| `solution.npz`     | Reference-solver reconstruction |
| `snapshot.png`     | Rendered preview of the snapshot |
| `ground_truth.png` | Rendered preview of the target (mean bands / middle frame) |
| `solution.png`     | Rendered preview of the reconstruction |
| `meta.json`        | Provenance, SHA-256 hashes, PSNR |

## Attribution

Source datasets are widely-redistributed academic benchmarks used in every
major CASSI/CACTI paper. See each sample's `meta.json` for the canonical
citation. Redistribution here follows standard academic-comparison practice.
