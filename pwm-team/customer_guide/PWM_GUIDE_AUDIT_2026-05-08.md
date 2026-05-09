# Audit: PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md

**Date:** 2026-05-08
**Scope:** Pre-mainnet review of `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` (refreshed 2026-05-08)
**Methodology:** Cross-checked every claim against repo state — ran each documented CLI command against the live Sepolia testnet, verified every cross-referenced file path resolves, compared `addresses.json` to in-doc contract addresses, recounted L1 manifests by `registration_tier`.
**Verdict:** **Do not ship the guide as-is on mainnet day.** Two blockers, six bugs, four nits — all fixable in <1 hour of edits except the contract deployment itself.

---

## 🚫 Mainnet-deploy blockers

### B1. `addresses.json:mainnet` is null — guide assumes it isn't
Every `--network mainnet` example in the guide (lines 1041, 825, 976, 1192) presumes mainnet contract addresses exist. They don't:

```json
"mainnet": { "network": "base", "chainId": 8453,
             "PWMRegistry": null, "PWMCertificate": null,
             "PWMReward": null, "PWMTreasury": null,
             "PWMGovernance": null, "PWMStaking": null,
             "PWMMinting": null, "deployedAt": null }
```

**You cannot ship the guide to mainnet without deploying contracts and populating these fields first.** Until that lands, every `--network mainnet` command in the guide fails. The doc acknowledges this in two places (lines 825, 1041) but those caveats are buried — readers running through Journey E would hit it cold.

### B2. Repo-visibility paragraph (lines 31–38) is now actively misleading

> "**Repo visibility status (current):** pwm-public is currently a private repo during the pre-mainnet preparation window. Anonymous browsers see a GitHub 404."

The repo has been cloned anonymously without auth (verified 2026-05-08). It flipped public ahead of D9 Step 12. Either delete this paragraph or replace it with a "now public" note. As written, it tells external collaborators they need a per-engagement invite — they don't.

---

## 🐛 Bugs (factually wrong claims)

### Bug 1. Cardinality table says 533, the catalog has 531

| Where | Claim | Actual |
|---|---|---|
| Line 327 | "L1 Principle &#124; 533" | **531** |
| Line 328 | "L2 Spec &#124; 533" | **531** (1:1 with L1) |
| Line 329 | "L3 Benchmark &#124; 533" | **531** (1:1 with L2) |
| Line 408 | "Cataloged in repo &#124; 531" | ✓ matches |
| Line 433 | "Total: 531 cataloged" | ✓ matches |
| Line 858 | "529 of 531 cataloged manifests" | ✓ matches |

The `533` in the cardinality table contradicts the rest of the doc (which consistently says `531`). Direct count: **529 stubs + 2 founder_vetted = 531 total L1 manifests.** Fix: change the cardinality table to read `531`.

### Bug 2. Per-domain counts are off by one in two places

Line 428 says `# 165 medical imaging` for `agent-imaging/principles`. Two errors:

- Actual count of `L1-*.json` under `agent-imaging/principles/` is **164**, not 165.
- The label is wrong — `agent-imaging` is *all imaging* (10 sub-clusters: microscopy, compressive, medical, coherent, photography, etc.), not just medical.

Same story for physics: the comment claims 148, actual is **147**.

| Domain | Guide says | Actual | Off by |
|---|---|---|---|
| agent-imaging | 165 | 164 | −1 |
| agent-physics | 148 | 147 | −1 |
| agent-applied | 112 | 112 | 0 ✓ |
| agent-chemistry | 67 | 67 | 0 ✓ |
| agent-signal | 39 | 39 | 0 ✓ |

### Bug 3. The `L3-026b` example on line 238 doesn't work

```bash
pwm-node inspect L3-026b         # works for Tier-3 stubs too (content tree)
```

This errors out: `[pwm-node inspect] no offline match for 'L3-026b'`. The Phase B renumbering (described 60 lines later in the same doc, lines 277–298) renamed `L3-026b` → `L3-026-002-001`. The example didn't get updated.

**Fix:** change to `pwm-node inspect L3-026-002-001` (or `pwm-node inspect spc --layer L3`, which does work).

### Bug 4. `pwm-node match` example score is wrong

Line 209: `→ #1 L3-003 (CASSI)  score 12.5`. Actual:

```
#1 L3-003 (tier: T1_nominal): … (score 17.50)
```

Minor, but in a doc where users will run the example verbatim, the disagreement looks bad. Either update to `17.50` or use a softer phrasing ("score in the high teens").

### Bug 5. `rho` displays as `?` in `pwm-node benchmarks` and `pwm-node benchmarks --spec`

The CLI's column-formatter doesn't find the `rho` field where expected. Reproducible:

```
$ pwm-node benchmarks
Title                                            ID         L1       rho   T1_eps   T1 baseline
----------------------------------------------------------------------------------------------------------------
CASSI Mismatch-Only Benchmark Suite (P-benchmark L3-003     L1-003   ?     28.0     GAP-TV = 26.0 PSNR_dB
```

Not a doc bug per se, but the *guide promises* `rho=50` benchmarks (lines 597, 706) and the listing UI shows `?`. Trivially confusing for first-time users. Fix in `agent-cli` before mainnet onboarding starts.

### Bug 6. Bash-only commands across the entire guide; no Windows hint

Every example uses bash idioms that fail on PowerShell verbatim:

| Bash | PowerShell equivalent |
|---|---|
| `python3 -m venv .venv && source .venv/bin/activate` | `python -m venv .venv; .\.venv\Scripts\Activate.ps1` |
| `export PWM_PRIVATE_KEY=…` | `$env:PWM_PRIVATE_KEY = "…"` (or `[Environment]::SetEnvironmentVariable(…, "User")` for persistence) |
| `find pwm-team/...` | `Get-ChildItem -Recurse -Filter L1-*.json` |
| `cat > file <<'JSON'` | (no direct equivalent — needs heredoc or `Set-Content`) |
| `bash scripts/testnet_mine_walkthrough.sh` | needs Git-Bash / WSL on Windows |
| `jq`, `cast`, `curl -sX POST` | each needs separate Windows install |

A founder using a Windows dev box hits this on line 87 of the guide. The friction is real — verified empirically in this audit session.

**Fix options:**
- **(a)** Add a one-paragraph "Windows users" callout near pre-flight pointing to PowerShell equivalents.
- **(b)** Ship a `scripts\setup.ps1` companion to the bash walkthrough.
- **(c)** Add a 1-page `customer_guide/PWM_WINDOWS_QUICKSTART.md`.

The lightest-touch fix is (a).

---

## 🔧 Minor / nits

### N1. `find` glob doesn't quite count what the guide says

Line 433 claims `Total: 531`. The find expression returns L1 files under all 5 agent subfolders, which equals **529** (the stubs). The 2 founder-vetted Principles live under `pwm-team/pwm_product/genesis/l1/`, not under `pwm-team/content/`. So the find command + the "Total: 531" comment disagree about whether the 2 founder_vetted entries are counted.

**Fix:** change the comment to `# 529 cataloged stubs; +2 founder_vetted in pwm_product/genesis/l1 = 531 total`.

### N2. Internal-only docs section (line 1169) lists references no public reader can open

That's a fine thing to keep for cross-session memory, but the framing — "Listed here for cross-session continuity only; public-repo readers don't need any of them" — could be tighter. Suggest moving this to an HTML comment so it doesn't render to public readers at all.

### N3. Memory-anchors section (line 1186) talks about "Director" — internal team language

Public readers will wonder who Director is. Either define on first use or strip the section before mainnet (these anchors are for next-conversation continuity, not customer onboarding).

### N4. Sepolia faucet recommendations (line 142) lead with `https://sepoliafaucet.com` (Alchemy)

This faucet now requires `0.001 ETH on mainnet` as an anti-bot gate, which **kills the funding flow for anyone starting from zero** (verified 2026-05-08). Reorder the faucet list to lead with one that has no mainnet-balance gate:

- `https://sepolia-faucet.pk910.de/` — PoW, no signup, no mainnet gate
- `https://cloud.google.com/application/web3/faucet/ethereum/sepolia` — Google account, no mainnet gate
- `https://www.infura.io/faucet/sepolia` — Infura signup, no mainnet gate

Add a one-line note about the Alchemy gate so future readers don't burn time on it.

---

## ✅ What's correct (worth noting)

- **All 16 cross-referenced file paths resolve.** Every guide reference to `customer_guide/...md`, `bounties/...md`, `infrastructure/...`, `pwm_product/reference_solvers/...py`, and `scripts/...` exists in the repo.
- **Sepolia contract addresses match `addresses.json`** exactly: `PWMRegistry 0x2375217dd8FeC420707D53C75C86e2258FBaab65` and `PWMCertificate 0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08`.
- **All 8 new CLI features documented in the 2026-05-08 refresh actually shipped:** slug lookup (`inspect cassi`), `--layer` flag, legacy alias resolution (`L2-003-001` → `L2-003`), `pwm-node specs --principle`, `pwm-node benchmarks --spec`, `pwm-node match`, slug-based stub access (`spc`, `qsm`). The only gap is the stale `L3-026b` literal example (Bug 3).
- **Registration tier model + `UI_ONLY_FIELDS` hash invariance** described correctly.
- **Reward distribution table** matches `PWMReward.sol` constitutional invariants per the playbook.

---

## Suggested fix order before mainnet ship

1. **B1** — deploy contracts + populate `addresses.json:mainnet`. This is the actual blocker, not the guide. Until done, the guide cannot be fully accurate.
2. **B2** — delete or rewrite the visibility paragraph. 30-second edit.
3. **Bug 1** — `533` → `531` in the cardinality table. 30-second edit, three lines.
4. **Bug 3** — `L3-026b` → `L3-026-002-001` in the slug-aware-browse example. 30-second edit.
5. **Bug 6** — Windows callout in pre-flight. 10-minute edit, one paragraph.
6. **Bug 2** — `164` / `147` counts in the `find` examples. 60-second edit.
7. **N4** — reorder faucets, add Alchemy-gate note. 60-second edit.
8. **Bug 4** (match score), **Bug 5** (rho display), **N1**, **N2**, **N3** — polish, not blockers.

Total time to address everything except B1: under one hour.

---

## Verification commands run during this audit

For reproducibility — these were the commands used to validate each finding:

```powershell
# CLI feature audit (bugs 3, 4, 5; positive confirmations of 8 features)
pwm-node inspect cassi
pwm-node inspect cassi --layer L2
pwm-node inspect L2-003-001
pwm-node specs --principle L1-003
pwm-node benchmarks --spec L2-003
pwm-node match "hyperspectral inverse problem with coded aperture and dispersion"
pwm-node inspect L3-026b        # Bug 3 — fails
pwm-node inspect spc            # works (resolves to L2-026-002)
pwm-node inspect qsm            # works (resolves to L1-503)

# Address verification (B1, positive Sepolia confirmation)
Get-Content pwm-team\infrastructure\agent-contracts\addresses.json

# Catalog count (Bug 1, Bug 2)
Get-ChildItem pwm-team\content\agent-imaging\principles -Filter L1-*.json -Recurse | Measure-Object
# Repeat for agent-physics, agent-applied, agent-chemistry, agent-signal

# Tier breakdown (Bug 1)
Get-ChildItem pwm-team\content -Filter L1-*.json -Recurse |
  ForEach-Object { (Get-Content $_.FullName -Raw | ConvertFrom-Json).registration_tier } |
  Group-Object | Sort-Object Count -Descending
# Output: stub 529, founder_vetted 2 (the 2 are under pwm_product/genesis/l1, not content/)

# Cross-reference path resolution (positive — all 16 OK)
@('pwm-team\customer_guide\plan.md',
  'pwm-team\customer_guide\PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md',
  ...) | ForEach-Object { if (Test-Path $_) { "OK $_" } else { "MISS $_" } }
```
