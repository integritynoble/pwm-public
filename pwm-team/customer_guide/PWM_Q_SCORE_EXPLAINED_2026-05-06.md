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

PWM's L3 benchmarks are **P-benchmarks** — rho=50 instances drawn across
the parameter space Ω, scored as a *distribution* not a single PSNR.
So Q is a weighted aggregate of how the solver performs across many
instances, not a normalisation of one reading.

The scoring engine
(`pwm-team/infrastructure/agent-scoring/pwm_scoring/score.py:_compute_q_p`)
mixes three signals:

```
Q_p = 0.40 · coverage + 0.40 · margin + 0.20 · stratum_pass_frac
```

(With Track C cross-bench transfer enabled, the weights shift to
0.35/0.35/0.15/0.15 with `degradation_score` as the fourth term.)

| Term | What it measures |
|---|---|
| **coverage** | Fraction of the rho instances whose `PSNR / epsilon_fn(Ω) ≥ 1.0` — i.e. how many instances cleared the per-instance threshold. |
| **margin** | Mean of `(PSNR/epsilon − 1)` across the *passing* instances, saturated at 1.0. Rewards beating the threshold by a margin, not just barely clearing it. |
| **stratum_pass_frac** | Fraction of Track-A strata (S1_small / S2_medium / S3_large / S4_xlarge) whose worst-case PSNR cleared its centroid epsilon. Penalises solvers that fail entire H×W regimes. |

`epsilon_fn(Ω)` is the per-instance acceptance threshold declared by
the parent L2 spec. For CASSI L2-003 it's
`25.0 + 2.0·log2(H/64) + 1.5·log10(photon_count/50)` — bigger images and
higher-photon scenes raise the bar.

Final clamp + integer conversion:

```python
Q     = max(0.0, min(1.0, Q_p))     # already in [0,1] by construction
Q_int = round(Q * 100)              # uint8 in [0, 100], goes on-chain
```

---

## Quick read of the four reference baselines on L3-003

The `baselines[]` entries in L3-003.json are *authored reference values*
— the benchmark author runs each baseline solver across rho=50 and
records the resulting Q. They're stored as manifest data, not
re-computed from a single PSNR every time the page loads.

| Baseline | Authored PSNR (T1_nominal) | Authored Q | What this means |
|---|---|---|---|
| GAP-TV | 26.0 dB | 0.62 | Classical floor — passes only some instances; modest margin |
| ADMM-CASSI | 28.5 dB | 0.76 | Classical ceiling — most instances pass, larger margin |
| PnP-HSICNN | 31.8 dB | 0.89 | Plug-and-play — nearly all instances pass with comfortable margin |
| MST-L | 35.295 dB | 0.95 | Deep-learning landmark — the current SOTA reference |

The Q values aren't directly derivable from the single PSNR shown — they
embed the author's per-instance + per-stratum results. To verify a
specific Q in production, run the actual solver across rho=50 instances
and call `score_solution()`; that's what `pwm-node mine` does.

---

## Concrete CASSI example — what `mine` reports today

For a CASSI run that scores rho=50 instances, `pwm-node mine` reports
each component before quantising:

```
[mine] Track A: stratum_results — 4 strata × 5 instances each
[mine] Track B: median PSNR vs epsilon_fn(median Ω) → pass/fail
[mine] coverage          = 0.96   (48 of 50 instances cleared epsilon_fn)
[mine] margin            = 0.18   (mean of (PSNR/eps − 1) on passing)
[mine] stratum_pass_frac = 1.00   (4 of 4 strata passed)
[mine] Q_p   = 0.40·0.96 + 0.40·0.18 + 0.20·1.00 = 0.656
[mine] Q     = clip(Q_p, 0, 1)        → 0.656
[mine] Q_int = round(0.656 · 100)     → 66
```

The on-chain `CertificateSubmitted` event then carries `Q_int = 66`
(and not the headline 35.295 dB PSNR you'd read off the off-chain
`cert-meta` row). That's why the leaderboard's `Q` column and the
solver's published PSNR look like different numbers — they
intentionally measure different things:

- **PSNR (off-chain meta)** — single-instance image quality, nice for
  a paper headline.
- **Q_int (on-chain, 0-100)** — aggregate of coverage/margin/stratum
  across the full rho=50 sweep, deterministic across implementations,
  ranking-grade.

The MST-L cert at `0x7c7740…e13` shows `Q_int = 35` because its
production scoring run gave a `Q_p` of about 0.35 against the full
benchmark, even though its headline PSNR on the *one instance the
submitter highlighted* is 35.295 dB. Both numbers are accurate; they
just answer different questions.

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
