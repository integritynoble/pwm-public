# CASSI on PWM — What it does, and how to use it

**Target reader:** a spectroscopist or computational imaging
researcher who has raw CASSI-style data and wants reconstructions,
and is unfamiliar with PWM.

---

## What CASSI is

Coded Aperture Snapshot Spectral Imaging captures a whole
**hyperspectral cube** (x, y, wavelength) in a **single 2D photograph**.

Your camera has a binary coded mask in front of the sensor and a
dispersive element that laterally shifts each wavelength by a
known amount. The sensor reads one exposure — a mosaic of all bands
overlaid with per-band spatial shifts. A reconstruction algorithm
unwinds the mosaic into the underlying 28-band cube.

Applications: medical diagnostics, materials inspection, remote
sensing, microscopy, real-time spectral video.

## What PWM gives you

PWM maintains a public, verifiable **benchmark** for this problem
(`L3-003`) with four difficulty tiers:

| Tier | H × W | Mismatch | Baseline best (PSNR) |
|------|-------|----------|----------------------|
| **T1 nominal** | 256×256 | perfect calibration | PnP-HSICNN: 31.8 dB |
| **T2 low** | 256×256 | ~1% dispersion drift, 0.2 px mask shift | PnP-HSICNN: 28.3 dB |
| **T3 moderate** | 512×512 | ~2.5% dispersion, 0.5 px shift, 0.07 rad rotation | PnP-HSICNN: 25.4 dB |
| **T4 blind** | 1024×1024 | severe drift, no oracle calibration | PnP-HSICNN: 22.5 dB |

Three things come with the benchmark:

1. **A fixed dataset + ground-truth** (subset of KAIST-30, CAVE,
   ICVL, stitched to the required resolutions).
2. **A quality metric** — PSNR dB (primary), SSIM (secondary),
   per-tier thresholds.
3. **A published leaderboard** — any solver submitted and verified
   becomes part of it automatically.

You don't have to adopt PWM to use the dataset or the evaluation
protocol — the benchmark JSON at
`pwm-team/pwm_product/genesis/l3/L3-003.json` is open and
self-contained.

## How to use this if you have your own CASSI data

### Option A — I just want a reconstruction

1. Open the PWM explorer: https://explorer.pwm.platformai.org/
2. Describe your setup in plain English at the `/match` page:
   *"I have a single 2D CASSI snapshot, 256×256, roughly 2% dispersion
   drift, noise ~5%. Reconstruct."*
3. The matcher resolves this to L3-003 T3_moderate.
4. Download the top-ranked solver. Run it on your snapshot.

*Status:* the matcher ships in Phase U1a step 4. Until then, you
can browse benchmarks directly and download solvers from the
leaderboard page.

### Option B — I'm an algorithm author who wants to mine

Follow the `pwm-node` CLI flow (see
`pwm-team/infrastructure/agent-cli/CLAUDE.md`):

```bash
pwm-node benchmarks --domain imaging           # discover
pwm-node verify L3-003                          # local S1-S4 gate check
pwm-node mine L3-003 --solver your_solver.py    # submit a cert
```

If your Q score beats the current Rank 1 on a tier, you get paid from
the benchmark's reward pool. Full economics in
`papers/Proof-of-Solution/pwm_overview1.md §§9-11`.

## When CASSI is NOT the right principle on PWM

| Your situation | Use instead |
|----------------|-------------|
| Single RGB image → hyperspectral (no coded aperture) | Not yet in PWM |
| Video reconstruction from one coded snapshot | **CACTI** — see `cacti.md` |
| 1D spectroscopy (Raman, NMR) | Not yet in PWM |
| Multispectral from a filter wheel (multiple shots) | Not yet in PWM |
| MRI / CT | Not yet in PWM (Phase U1b candidates) |
| 3D point cloud from depth sensors | Not in scope — PWM is imaging-first |

## Status on PWM

- **On-chain registration:** CASSI L1/L2/L3 artifacts registered to
  Sepolia PWMRegistry on 2026-04-21. Mainnet registration happens at
  Phase E launch.
- **Benchmark card:** `pwm-team/pwm_product/benchmark_cards/L3-003.yaml`
  — auto-generated metadata + handwritten summary.
- **Reference solver:** coming in Phase U1a step 5 (a minimal GAP-TV
  baseline, sufficient to exercise the full pipeline). High-quality
  solvers expected from external authors via Bounty #7 or direct
  mining.
- **Demo dataset:** coming in Phase U1a step 6.

## Where to go next

- **Browse:** https://explorer.pwm.platformai.org/principles/3
- **Protocol spec:** `papers/Proof-of-Solution/pwm_overview1.md §§2-6`
- **Canonical reference:** `papers/Proof-of-Solution/mine_example/cassi.md`
  (~1,600-line deep-dive — the source material for this page)
- **Questions or gap requests:** raise a GitHub issue at
  https://github.com/integritynoble/pwm-public/issues with the
  `bounty-07-claim` label to request creation of a new benchmark
  tier or related principle.
