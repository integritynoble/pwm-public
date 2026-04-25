# CASSI — `L3-003` — InverseNet KAIST-10 benchmark

10 standard hyperspectral scenes from the KAIST-10 benchmark
(used in MST, HDNet, CST, DAUHST, and the InverseNet paper).
Each 256×256×28 scene is reconstructed from a coded-aperture snapshot
by the reference GAP-TV solver with 15 iterations.


## Samples

| Sample | Scene | Reference PSNR | Solver time |
|--------|-------|----------------|-------------|
| `sample_01/` | scene01 | 19.86 dB | 7.0s |
| `sample_02/` | scene02 | 17.25 dB | 6.1s |
| `sample_03/` | scene03 | 12.34 dB | 5.7s |
| `sample_04/` | scene04 | 14.6 dB | 5.6s |
| `sample_05/` | scene05 | 15.47 dB | 5.8s |
| `sample_06/` | scene06 | 18.75 dB | 7.3s |
| `sample_07/` | scene07 | 13.46 dB | 7.3s |
| `sample_08/` | scene08 | 18.46 dB | 5.9s |
| `sample_09/` | scene09 | 11.66 dB | 5.5s |
| `sample_10/` | scene10 | 14.68 dB | 5.6s |

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
