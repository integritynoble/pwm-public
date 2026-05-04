# CACTI on PWM — What it does, and how to use it

**Target reader:** a computational imaging or computer vision
researcher who has raw CACTI-style data (compressive temporal video
snapshots) and wants reconstructions, and is unfamiliar with PWM.

---

## What CACTI is

Coded Aperture Compressive Temporal Imaging captures a **short video
sequence** (typically 8 to 32+ frames) in a **single 2D photograph**.

During one exposure, a high-speed binary mask (e.g., a DMD) modulates
incoming light frame-by-frame. Each underlying video frame passes
through a *different* mask pattern before summing on the sensor. The
single readout encodes all frames. A reconstruction algorithm unwinds
the sum into the individual frames.

Applications: high-speed video for scientific imaging, motion capture
under low light, fluorescence microscopy with temporal dynamics, LIDAR
time-gating, monitoring of fast mechanical or biological events.

## What PWM gives you

PWM maintains a public, verifiable **benchmark** for this problem
(`L3-004`) with four difficulty tiers:

| Tier | H × W | Frames | Mismatch | Baseline best (PSNR) |
|------|-------|--------|----------|----------------------|
| **T1 nominal** | 256×256 | ~8 | ideal calibration | EfficientSCI: ~31 dB |
| **T2 low** | 256×256 | ~16 | mild exposure drift, small mask shift | EfficientSCI: ~28 dB |
| **T3 moderate** | 512×512 | ~32 | real-world mismatch, rotation, noise | EfficientSCI: ~25 dB |
| **T4 blind** | 1024×1024 | ~32 | severe drift, no oracle calibration | EfficientSCI: ~22 dB |

Three things come with the benchmark:

1. **A fixed dataset + ground-truth** (synthetic video drawn from
   public motion corpora, encoded through PWM's canonical CACTI
   forward model).
2. **A quality metric** — PSNR dB (primary), SSIM (secondary),
   per-tier thresholds.
3. **A public leaderboard** — any verified solver submission is
   listed and ranked automatically.

The benchmark JSON at `pwm-team/pwm_product/genesis/l3/L3-004.json`
is open and self-contained — you can use the dataset and evaluation
protocol without engaging with PWM's economic layer at all.

## How to use this if you have your own CACTI data

### Option A — I just want a reconstruction

1. Open the PWM explorer: https://explorer.pwm.platformai.org/
2. Describe your setup in plain English at `/match`:
   *"I have a single 2D snapshot that encodes 16 video frames, 512×512,
   minor exposure-window drift. Need to recover the video."*
3. The matcher resolves this to L3-004 T2_low.
4. Download the top-ranked solver. Run it on your snapshot.

*Status:* the matcher ships in Phase U1a step 4. Until then, browse
`L3-004` directly on the explorer.

### Option B — I'm an algorithm author who wants to mine

```bash
pwm-node benchmarks --domain imaging
pwm-node verify L3-004
pwm-node mine L3-004 --solver your_solver.py
```

If your Q score beats the current Rank 1 on a tier, you get paid from
the benchmark's reward pool. See
`papers/Proof-of-Solution/pwm_overview1.md §§9-11` for the full
economics.

## When CACTI is NOT the right principle on PWM

| Your situation | Use instead |
|----------------|-------------|
| Hyperspectral reconstruction from one snapshot | **CASSI** — see `cassi.md` |
| Normal (uncompressed) video denoising or deblurring | Not in PWM |
| 3D geometry from multi-view video | Not in PWM |
| Motion capture from external sensors (IMU, tracking markers) | Out of scope |
| MRI / CT dynamic imaging | Not yet in PWM (Phase U1b candidates) |

## Common sources of confusion

- **"Video SCI" vs "CACTI":** CACTI is one specific member of the SCI
  (snapshot compressive imaging) family. Some papers use "SCI" loosely
  to mean either the compressive temporal setting or compressive
  spectral; on PWM, CASSI is the spectral variant and CACTI is the
  temporal one. Same general forward model form
  (`y = Σ mask_t · x_t + n`), different physical axis.
- **Frame count is not part of the principle, but the tier.** T1
  nominal uses ~8 frames; T4 blind stretches to ~32 frames at
  1024×1024 resolution. Pick the tier that matches your deployed
  compression ratio.

## Status on PWM

- **On-chain registration:** CACTI L1/L2/L3 artifacts registered to
  Sepolia PWMRegistry on 2026-04-21. Mainnet at Phase E launch.
- **Benchmark card:** `pwm-team/pwm_product/benchmark_cards/L3-004.yaml`
  — auto-generated metadata + handwritten summary.
- **Reference solver:** coming in Phase U1a step 5 (a minimal
  PnP-ADMM baseline). Higher-quality solvers (EfficientSCI-class)
  expected from external authors via Bounty #7 or direct mining.
- **Demo dataset:** coming in Phase U1a step 6.

## Where to go next

- **Browse:** https://explorer.pwm.platformai.org/principles/4
- **Protocol spec:** `papers/Proof-of-Solution/pwm_overview1.md §§2-6`
- **Canonical reference:** `papers/Proof-of-Solution/mine_example/cacti.md`
  (deep-dive; source material for this page)
- **Questions or gap requests:** open a GitHub issue at
  https://github.com/integritynoble/pwm-public/issues with the
  `bounty-07-claim` label to request creation of a new benchmark
  tier or related principle.
