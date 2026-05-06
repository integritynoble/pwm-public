# Q Score — The Quality Measure That Ranks Every Solver

**Date:** 2026-05-06
**Audience:** Researchers, students, miners, regulators — anyone who sees `Q: 85` on a cert detail page
**Trigger question (Director, 2026-05-06):**
> "What is meaning of Q score?"

---

## TL;DR

**Q = normalized quality score in [0, 1]. Q_int = `round(Q × 100)` ∈ [0, 100],
the integer that goes on-chain. Higher Q_int = higher rank = bigger payout.
Each benchmark declares its own floor/ceiling/metric so Q is comparable across
solvers on the *same* benchmark, but not across different benchmarks.**

In a cert detail like `Q score: 85`, that means: the solver hit ~85% of the
way from the benchmark's metric-floor to its metric-ceiling — a credible
result, with room to improve toward Q_int=100 (which would require clearing
or exceeding the declared ceiling).

---

## Two forms: Q (continuous) vs Q_int (on-chain)

| Form | Range | Where it lives | Why |
|---|---|---|---|
| **Q** | `[0.00, 1.00]` (float) | Computed locally by the scoring function | Continuous quality measure — what your solver actually produces |
| **Q_int** | `[0, 100]` (uint8) | Stored on-chain in the cert | Solidity has no floats; we quantize to a single byte for cheap storage and gas |

The conversion is just `Q_int = round(Q * 100)`, clamped to `[0, 100]`.

Source: `pwm-team/infrastructure/agent-cli/pwm_node/commands/mine.py:213`
> `Quality score in [0, 1]; rounded × 100 to get Q_int.`

Source: `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol:54`
> `uint8   Q_int;`

---

## How Q is derived from the actual reconstruction

Different benchmarks use different primary metrics, but the pattern is the
same: take the raw scientific metric, normalize it against the benchmark's
epsilon-threshold function, clip to [0, 1].

```
                              raw metric                  Q (in [0,1])              Q_int
                              ──────────                  ────────────              ─────
CASSI / CACTI:           PSNR_dB (e.g. 26.5 dB)    ───→   normalize vs eps   ───→   85
Chest CT severity:       AUROC (e.g. 0.92)          ───→   already in [0,1]   ───→   92
QSM:                     SSIM (e.g. 0.78)           ───→   already in [0,1]   ───→   78
```

For PSNR-based benchmarks the typical formula:

```
Q = clip( (PSNR_dB - PSNR_floor) / (PSNR_ceiling - PSNR_floor), 0, 1 )
```

`PSNR floor` is "the bar you must clear to get any credit" and `PSNR ceiling`
is "where Q saturates at 1.0". Each L3 manifest declares its own
floor/ceiling/metric in the `scoring` field.

---

## Concrete CASSI example

For CASSI L3-003 with the GAP-TV reference solver:

```
raw PSNR        = 26.49 dB        (your reconstruction's quality)
PSNR floor      = 24.00 dB        (declared in benchmark — minimum)
PSNR ceiling    = 26.94 dB        (declared in benchmark — saturates at this)

Q   = (26.49 - 24.00) / (26.94 - 24.00) = 2.49 / 2.94 = 0.847
Q_int = round(0.847 × 100) = 85    ← this is what goes on-chain
```

That `85` shows up in your cert payload
(`pwm_work_*/cert_payload.json:Q_int: 85`) and on the explorer's leaderboard
column labeled `Q`.

---

## What happens with Q_int on-chain

```
PWMCertificate.submit(certHash, benchmarkHash, Q_int=85, payload)
                                                 │
                                                 ▼
                               Stored on-chain in CertificateSubmitted event
                                                 │
                                                 ▼
                           After 7-day challenge period clean:
                           PWMReward.distribute() ranks all certs
                           for this benchmark by Q_int descending
                                                 │
                                                 ▼
                           Rank 1 (highest Q_int) wins 40% of pool
                           Rank 2 wins 5%, Rank 3 wins 2%,
                           Ranks 4-10 win 1% each
```

---

## Why integer (not float)

Three reasons:

1. **Solidity has no floats.** Storing 0.847 means storing it as a
   fixed-point or string — both are gas-expensive.
2. **`uint8` = 1 byte** vs 32 bytes for a struct-encoded float. Massive
   gas savings on every cert.
3. **Cross-implementation safety.** Floats compare differently across
   languages (Python vs Rust vs JS); integers don't. Two miners running
   the same algorithm in different runtimes get the same Q_int, so ranks
   are deterministic.

The tradeoff is granularity — you can't differentiate between Q = 0.853
and Q = 0.857 (both round to 85). For ranking purposes that's fine because
PWM uses tiebreakers (timestamp, then deterministic hash) when Q_int
collides.

---

## What Q does NOT measure

- **Speed.** A solver that hits Q_int=90 in 5 minutes ranks the same as
  one that takes 5 hours. Speed is a runtime field on the cert but not
  used for ranking.
- **Code quality / elegance.** Just the output number.
- **Generalization across benchmarks.** Q is per-benchmark — your Q=85
  on CASSI says nothing about your CACTI Q.
- **Reproducibility.** Q is a claim; verifying it requires the dataset
  CIDs + your solver. The chain doesn't re-run your code.

---

## Cross-references

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full mining flow that produces Q
- `pwm-team/customer_guide/PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` — what binds Q_int to the cert hash on-chain
- `pwm-team/infrastructure/agent-cli/pwm_node/commands/mine.py` — `Q_int = int(round(float(Q) * 100))` conversion
- `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol` — on-chain `uint8 Q_int` storage
- `pwm-team/infrastructure/agent-contracts/contracts/PWMReward.sol` — ranked-draw payout that consumes Q_int
- `https://explorer.pwm.platformai.org/cert/<hash>` — live cert detail page that displays the Q column
