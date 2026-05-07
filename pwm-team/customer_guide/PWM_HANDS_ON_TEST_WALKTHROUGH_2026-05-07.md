# Hands-on Test Walkthrough — All 4 Layers

**Date:** 2026-05-07
**Audience:** First-time PWM tester who wants to validate every claim in `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` by hand
**Trigger question (Director, 2026-05-07):**
> "I want to test this file with my hand. Please give me detailed examples
> to test. Each layer should have one example. For principle, I think I
> can use the single pixel camera."

---

## Plan

Run each block in your terminal. The `Expected output` row tells you what
to look for; check ✓ when you see it.

Single-pixel imaging exists only as a **Tier 3 stub** in the catalog (no
reference solver, no dataset, not registered on-chain). So:

- **L1 uses single-pixel** (where stubs work fine for browsing/inspection)
- **L2-L4 use CASSI** (the founder-vetted Tier 1 path — only place where actual mining works end-to-end)
- **Bonus** at the end: try mining a stub to see what "stubs are inert" looks like

---

## Pre-flight (one-time, ~1 min)

```bash
cd /home/spiritai/pwm/Physics_World_Model/pwm

# Verify CLI is on the path
pwm-node --version
```

| | |
|---|---|
| **Goal** | Confirm `pwm-node` CLI is installed |
| **Expected** | A version string like `pwm-node 0.x.x` |
| **Pass** | ✓ no `command not found` |

---

## L1 — Single-Pixel Imaging (consumer browse)

### L1-Test-1: Read the principle JSON directly

```bash
cat pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026_single_pixel.json | python3 -m json.tool | head -25
```

| | |
|---|---|
| **Goal** | See the raw L1 manifest for single-pixel imaging |
| **Expected** | JSON starting with `"artifact_id": "L1-026"`, `"title": "Single-Pixel Imaging..."`, `"registration_tier": "stub"`, and `"forward_model": "y = Phi * vec(x) + n..."` |
| **Pass** | ✓ you can see all 4 fields |

### L1-Test-2: Inspect via CLI

```bash
pwm-node inspect L1-026
```

| | |
|---|---|
| **Goal** | Pretty-printed view of the L1 (no chain calls) |
| **Expected** | A panel showing title `Single-Pixel Imaging…`, domain `Compressive Imaging`, the forward model `y = Phi * vec(x) + n`, the DAG primitives, and difficulty info |
| **Pass** | ✓ inspect output renders without error |

> Note: this command currently walks `pwm_product/genesis/` only and may
> say "not found" — if so, fall back to the JSON read above. The
> `inspect` CLI hooking up to the content tree is a follow-up TODO.

### L1-Test-3: Find single-pixel via match

```bash
pwm-node match "I have a compressive sensing problem with random binary masks measured by a single detector"
```

| | |
|---|---|
| **Goal** | The faceted matcher should surface single-pixel as a top match |
| **Expected** | Result list naming L1-026 / L1-026b in the top 3 (or — if the matcher only walks registered artifacts — surfacing CASSI L1-003 instead, with a note about how few entries it has to match against) |
| **Pass** | ✓ either single-pixel surfaces, or the matcher returns CASSI as nearest-mineable |

### L1-Test-4: Browse on the live web explorer

Open in your browser:

```
https://explorer.pwm.platformai.org/principles?tier=all
```

Then click "Compressive Imaging" domain filter and look for
`L1-026 — Single-Pixel Imaging`.

| | |
|---|---|
| **Goal** | Confirm Option B exposes the stub on the web |
| **Expected** | Three tabs at top: **Mineable (2)**, **Claim Board (529)**, **All (531)**. Click "All" → search for "single pixel" → row appears with 📋 `Stub — not mineable` badge, opacity-60 muted styling |
| **Pass** | ✓ row visible, with stub badge |

### L1-Test-5: Open the stub detail page

Click the row, or go directly to:

```
https://explorer.pwm.platformai.org/principles/L1-026
```

| | |
|---|---|
| **Goal** | See the stub-specific UI |
| **Expected** | Page header has `📋 Stub — not mineable` badge. An amber **"Unclaimed Principle — open for contribution"** card with two buttons: "Read the contribution guide" and "Open a claim issue". The Treasury / Minting / Registered benchmarks sections are hidden. |
| **Pass** | ✓ amber card visible, no chain-only sections |

---

## L2 — CASSI Spec (read the math contract)

Single-pixel L2 is a stub too, so for realistic L2 testing we use the
**registered CASSI L2**.

### L2-Test-1: Inspect L2-003

```bash
pwm-node inspect L2-003
```

| | |
|---|---|
| **Goal** | Read the six-tuple math contract |
| **Expected** | Output showing `Ω` = parameter space (mask types, dispersions, photon levels), `E` = forward operator + DAG, `B` = boundary constraints, `I` = init strategy, `O` = observable list (PSNR, SSIM), `ε` = epsilon function. Plus `gate_class: analytical`. |
| **Pass** | ✓ all six tuple fields visible |

### L2-Test-2: Compare to the JSON

```bash
cat pwm-team/pwm_product/genesis/l2/L2-003.json | python3 -m json.tool | head -40
```

| | |
|---|---|
| **Goal** | Cross-check that the inspect view matches the underlying manifest |
| **Expected** | JSON with `"artifact_id": "L2-003"`, `"parent_l1": "L1-003"`, `"registration_tier": "founder_vetted"`, the same six-tuple fields |
| **Pass** | ✓ artifact_id and parent_l1 both resolve correctly |

### L2-Test-3: View on web

```
https://explorer.pwm.platformai.org/principles/L1-003
```

Scroll to the "Specs" section.

| | |
|---|---|
| **Goal** | See L2-003 listed as a spec under its parent L1-003 |
| **Expected** | A row with spec_id `L2-003`, title, type, d_spec value |
| **Pass** | ✓ row present |

---

## L3 — CASSI Benchmark (download data, compare locally)

### L3-Test-1: Inspect L3-003

```bash
pwm-node inspect L3-003
```

| | |
|---|---|
| **Goal** | Read the benchmark spec |
| **Expected** | Output showing rho (=50), ω parameters, scoring metric (PSNR_dB), dataset registry references, and "Compressive Imaging" domain |
| **Pass** | ✓ rho + scoring visible |

### L3-Test-2: List bundled samples

```bash
ls pwm-team/pwm_product/demos/cassi/sample_01/
```

| | |
|---|---|
| **Goal** | See the demo dataset that ships with the repo |
| **Expected** | Files: `ground_truth.npz`, `ground_truth.png`, `snapshot.npz`, `snapshot.png`, `solution.npz`, `solution.png`, `meta.json` |
| **Pass** | ✓ all 7 files present |

### L3-Test-3: Inspect sample meta

```bash
cat pwm-team/pwm_product/demos/cassi/sample_01/meta.json | python3 -m json.tool
```

| | |
|---|---|
| **Goal** | See SHA-256 fingerprints + scoring metadata |
| **Expected** | `reference_solver_psnr_db: 26.49`, three SHA-256 hashes (one per `.npz`), `solver: pwm_core.recon.gap_tv.gap_tv_cassi`, scene_id `scene01` |
| **Pass** | ✓ fingerprints visible |

### L3-Test-4: Verify the bundled samples haven't been tampered with

```bash
python3 <<'PY'
import json, hashlib
meta = json.load(open("pwm-team/pwm_product/demos/cassi/sample_01/meta.json"))
for fname, expected in meta["sha256"].items():
    actual = hashlib.sha256(open(f"pwm-team/pwm_product/demos/cassi/sample_01/{fname}", "rb").read()).hexdigest()
    status = "✓" if actual == expected else "✗ MISMATCH"
    print(f"  {status}  {fname}: {actual[:20]}…")
PY
```

| | |
|---|---|
| **Goal** | Layer-B fingerprint check on bundled data (matches the architecture doc's 3-layer hash chain) |
| **Expected** | Three lines, all `✓` |
| **Pass** | ✓ all three pass |

### L3-Test-5: View benchmark detail on web

```
https://explorer.pwm.platformai.org/benchmarks/L3-003
```

| | |
|---|---|
| **Goal** | See the public benchmark page with leaderboard |
| **Expected** | "InverseNet KAIST-10" benchmark title; leaderboard with rank 1 = MST-L Q_int=35 / 35.30 dB; "Get this benchmark" download card; sample image rows |
| **Pass** | ✓ leaderboard rank 1 says MST-L |

---

## L4 — Mine + Verify CASSI Cert

### L4-Test-1: Dry-run mine with the GAP-TV reference solver (CPU works!)

```bash
cd /home/spiritai/pwm/Physics_World_Model/pwm
pwm-node mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
  --dry-run
```

| | |
|---|---|
| **Goal** | Compute Q without submitting a tx (no wallet needed) |
| **Expected** | After ~30 sec on CPU: `[mine] PSNR=26.5 dB  Q=0.85  Q_int=85`, plus a would-be `cert_hash` printed. No tx broadcast. |
| **Pass** | ✓ Q_int=85 (or close) appears |

### L4-Test-2: Look at the cert payload it would have submitted

```bash
ls -t pwm_work_*/cert_payload.json | head -1 | xargs cat | python3 -m json.tool | head -20
```

| | |
|---|---|
| **Goal** | See the 12-field cert struct that mining produces |
| **Expected** | JSON with `Q_int: 85`, `benchmarkHash: "0xdc8ad0dc…"`, `principleId: 3`, the 5 wallet addresses, `submittedAt`, etc. |
| **Pass** | ✓ Q_int + benchmarkHash visible |

### L4-Test-3: Verify the existing MST-L cert (Layer 1)

Open in browser:

```
https://explorer.pwm.platformai.org/cert/0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13
```

| | |
|---|---|
| **Goal** | Confirm the on-chain MST-L cert via the explorer |
| **Expected** | Cert detail page shows: rank 1, Q_int=35, solver=MST-L, PSNR=35.30 dB, submitter=`0x0c566f…7dEd`, status=pending (3-4 days remaining on challenge window) |
| **Pass** | ✓ all fields render |

### L4-Test-4: Verify same cert via Etherscan (Layer 2)

```
https://sepolia.etherscan.io/tx/0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5
```

Click "Logs" tab → find `CertificateSubmitted` event.

| | |
|---|---|
| **Goal** | Confirm via canonical EVM (no PWM UI involved) |
| **Expected** | Event topics: certHash=`0x7c7740fa…`, benchmarkHash=`0xdc8ad0dc…`, submitter=`0x0c566f…`, Q_int=`35` |
| **Pass** | ✓ all four fields match what the explorer claimed |

### L4-Test-5: Verify same cert via web3.py (Layer 3 — direct RPC)

```bash
python3 <<'PY'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia-rpc.publicnode.com"))
r = w3.eth.get_transaction_receipt("0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5")
log = r.logs[0]
print(f"  certHash:      0x{log.topics[1].hex().lstrip('0x').zfill(64)}")
print(f"  benchmarkHash: 0x{log.topics[2].hex().lstrip('0x').zfill(64)}")
print(f"  submitter:     0x{log.topics[3].hex()[-40:]}")
print(f"  Q_int:         {int((log.data.hex().lstrip('0x') if isinstance(log.data, bytes) else log.data.lstrip('0x')), 16)}")
PY
```

| | |
|---|---|
| **Goal** | Pull the raw event from Sepolia ourselves |
| **Expected** | Same 4 values as Etherscan (certHash, benchmarkHash, submitter, Q_int=35) |
| **Pass** | ✓ all 4 match |

---

## Bonus — what happens if you try to mine a STUB?

This is the proof that stubs really are inert. Try:

```bash
pwm-node mine L3-026 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
  --dry-run
```

| | |
|---|---|
| **Goal** | Confirm Tier 3 stubs can't be mined |
| **Expected** | Either (a) "L3-026 not found" if the CLI only walks genesis, or (b) the dry-run completes but produces a benchmarkHash that has *no* on-chain registration → if you then drop `--dry-run` and try to actually submit, the contract reverts with "PWMCertificate: benchmark not registered". Either way, no payout is possible. |
| **Pass** | ✓ confirms stubs are inert (no economic exposure to bad authoring) |

---

## Pass-criteria summary

If you run all 22 tests above, you'll have personally verified:

| Layer | Tests | What it proves |
|---|---|---|
| L1 single-pixel | 5 | Stubs are visible (Option B works) but inert; consumers can browse the catalog |
| L2 CASSI | 3 | Six-tuple math contracts are readable from CLI + web |
| L3 CASSI | 5 | Benchmarks ship with bundled, fingerprint-verified sample data |
| L4 CASSI | 5 | Mining produces certs (CPU-only via GAP-TV); existing on-chain certs are verifiable through 3 independent paths (explorer / Etherscan / direct web3.py) |
| Bonus | 1 | Stubs structurally cannot drain mainnet |

If any test fails, paste the error to the founding team and we'll
diagnose. Most likely failure modes are environmental (PWM CLI not on
PATH, web3 not installed, internet down) — none are protocol bugs.

---

## Cross-references

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — the canonical guide this walkthrough tests
- `pwm-team/customer_guide/PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md` — deeper 5-layer verification flow used by L4-Test-3 to L4-Test-5
- `pwm-team/customer_guide/PWM_Q_SCORE_EXPLAINED_2026-05-06.md` — what Q_int means (used by L4-Test-1)
- `pwm-team/customer_guide/PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` — explains the 3-layer hash chain L3-Test-4 verifies
- `pwm-team/coordination/PWM_REGISTRATION_TIERS_AND_ECONOMIC_PROTECTION_2026-05-06.md` — internal memo behind the tier system the Bonus test demonstrates
