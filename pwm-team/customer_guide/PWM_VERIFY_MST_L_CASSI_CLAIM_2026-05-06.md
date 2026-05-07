# Verifying the MST-L CASSI Claim — Concrete Steps

**Date:** 2026-05-06
**Audience:** Researchers, regulators, paper reviewers, compliance auditors — anyone who wants to verify a published PWM L4 cert claim end-to-end
**Trigger question (Director, 2026-05-06):**
> "How can I verify a published claim — MST-L of CASSI? Please give me the
> detailed steps."

---

## The real claim on-chain (Sepolia, today)

| Field | Value |
|---|---|
| **Cert hash** | `0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13` |
| **Benchmark** | L3-003 CASSI = `0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a` |
| **Submitter** | `0x0c566f0F87cD062C3DE95943E50d572c74A87dEd` |
| **Solver label (off-chain meta)** | MST-L · PyTorch 2.1 + CUDA 12.1 |
| **Q_int (on-chain)** | 35 |
| **PSNR (off-chain meta)** | 35.295 dB |
| **Submitted at block** | 10778856 · tx `0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5` |

There are **5 layers of verification**, from "look at it" (1 min) to
"rebuild the bytes from scratch and re-hash" (1-2 hours on a GPU box).
Pick the depth that matches how hard you want to scrutinize.

---

## Layer 1 — Look at the cert detail page (~30 seconds)

```
https://explorer.pwm.platformai.org/cert/0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13
```

What you should see:
- Cert hash matches the URL
- benchmark_hash = `0xdc8ad0dc…48b4a` (CASSI L3-003)
- submitter = `0x0c566f…7dEd`
- Q_int: **35**
- Solver label: **MST-L**
- A "View on Etherscan" link to the tx

This is the explorer's joined view — on-chain data plus the off-chain
solver-label meta the submitter posted via `POST /api/cert-meta`. The
off-chain meta is convenience labeling; everything that *matters* for
trust is the on-chain part.

---

## Layer 2 — Inspect the on-chain event on Etherscan (~1 minute)

```
https://sepolia.etherscan.io/tx/0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5
```

Click "Logs" in the Etherscan view. Find the `CertificateSubmitted`
event and check its decoded fields:

| Topic | Expected value |
|---|---|
| `certHash` | `0x7c7740faad378c…` |
| `benchmarkHash` | `0xdc8ad0dc…48b4a` |
| `submitter` | `0x0c566f…7dEd` |
| `Q_int` | `35` |

If those four values agree with what the explorer claims, the explorer
is honest. If they disagree — Etherscan is the source of truth. The
explorer is just a UI; Etherscan is reading raw EVM state.

This is **canonical, no UI in between**. There is nothing PWM controls
that can fake an Etherscan log.

---

## Layer 3 — Read PWMCertificate state directly via `cast` (~2 minutes)

For tooling-friendly verification (CI / regulator scripts):

```bash
# Address of the PWMCertificate contract on Sepolia
export CERT_ADDR=0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08
export CERT_HASH=0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13
export RPC=https://ethereum-sepolia-rpc.publicnode.com

# Fetch the on-chain certificate struct
cast call $CERT_ADDR \
  "certificates(bytes32)(bytes32,bytes32,address,uint8,uint8,uint64,uint64)" \
  $CERT_HASH \
  --rpc-url $RPC
```

Expected output (one line, fields separated by newlines in cast):
```
0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a   # benchmarkHash
0x0c566f0F87cD062C3DE95943E50d572c74A87dEd                           # submitter
35                                                                    # Q_int
0                                                                     # status (0 = pending challenge)
1777772748                                                            # submittedAt (unix)
...
```

If `cast` is unavailable, the same lookup via `web3.py`:

```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia-rpc.publicnode.com"))
cert_contract = w3.eth.contract(
    address=Web3.to_checksum_address("0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08"),
    abi=open("pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json").read(),
)
print(cert_contract.functions.certificates(
    bytes.fromhex("7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13")
).call())
```

Whatever the explorer shows, *this* is the truth. If the two disagree,
trust this.

---

## Layer 4 — Reproduce the cert hash from the local payload (~5 minutes)

This proves the cert payload posted by the miner hashes to the cert
hash on-chain. The trick: `cert_hash = keccak256(canonical_json(payload))`
— same function used by `pwm-node mine` and `register_genesis.py`.

If the submitter has shared the cert payload
(`pwm_work_<id>/cert_payload.json` in their working directory), you can
re-derive the hash yourself:

```bash
# Get the payload (in the submitter's working tree, or shared as a gist):
PAYLOAD=cert_payload.json   # the file with Q_int, benchmarkHash, omega, solver_id

python3 <<'PY'
import json
from web3 import Web3

with open("cert_payload.json") as f:
    payload = json.load(f)

# UI_ONLY_FIELDS stripped from canonical hashing — same filter as pwm-node
UI_ONLY = {"display_slug", "display_color", "ui_metadata", "registration_tier"}
canonical = {k: v for k, v in payload.items() if k not in UI_ONLY}
canonical_bytes = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()

cert_hash = "0x" + Web3.keccak(canonical_bytes).hex().lstrip("0x").zfill(64)
print(f"Recomputed cert_hash: {cert_hash}")
print(f"On-chain cert_hash:  0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13")
print(f"Match: {cert_hash.lower() == '0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13'}")
PY
```

If `Match: True`, the payload you have is *exactly* the bytes that
hashed to the on-chain cert. The miner cannot have lied about Q_int,
benchmarkHash, or omega without breaking this hash.

If the submitter hasn't shared the payload publicly, you can still
verify Q_int matches (Layer 3) but not the other fields. This is the ✗
no `solution_uri` case — Q is bound, but reproducibility from raw bytes
requires payload sharing.

---

## Publishing your payload (optional, but high-trust)

Layer 4 only works if the submitter publishes the cert payload bytes.
By default, after running `pwm-node mine`, your `cert_payload.json`
sits in a local working directory (`pwm_work_<timestamp>/`) and stays
on your machine. Third parties can verify Layers 1, 2, 3, and 5 but
not Layer 4 without those bytes.

This section is for submitters who want their certs to be Layer-4-
verifiable by anyone (paper reviewers, regulators, auditors, the
general public).

### When to publish your payload

| Scenario | Publish? |
|---|---|
| You're submitting a routine cert with no external scrutiny | No need — Layer 1-3 + 5 are sufficient |
| You're citing the cert in a paper / FDA submission / grant application | **Yes** — reviewers will want byte-level reproducibility |
| You want the cert to serve as a third-party-verifiable benchmark claim | **Yes** — Layer 4 is the bridge from "the score is locked" to "the score is reproducible from raw bytes" |
| You're competing for a high-value rank-1 spot and want to defuse "did you actually compute this?" challenges | **Yes** — preempts disputes during the 7-day challenge window |

### What's in the payload (and what's NOT)

A `cert_payload.json` contains exactly the 12 fields that the canonical
hash covers — the same fields the chain bound when you submitted:

```json
{
  "Q_int": 35,
  "benchmarkHash": "0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a",
  "principleId": 3,
  "delta": 3,
  "spWallet": "0x0c566f0F87cD062C3DE95943E50d572c74A87dEd",
  "acWallet": "0x0c566f0F87cD062C3DE95943E50d572c74A87dEd",
  "cpWallet": "0x0c566f0F87cD062C3DE95943E50d572c74A87dEd",
  "creatorL1": "0x...",
  "creatorL2": "0x...",
  "creatorL3": "0x...",
  "shareRatioP": 5000,
  "submittedAt": 1777772748,
  "_meta": { ... }   // optional inspection-only sidecar; stripped before hashing
}
```

**Safe to publish:** all 12 chain-bound fields above are already public
(they're on-chain or derived from on-chain values).

**Never publish:**
- Your private key (`PWM_PRIVATE_KEY`) — this is **not** in the payload, but check no `.env` file or environment dump leaks alongside the payload.
- The reconstruction `.npz` itself, unless you separately want IPFS-pinning. The `.npz` is what Layer 5 verifies; the payload is just the cert metadata.

### Two publishing options

**Option A — commit to the public repo (recommended for permanent claims)**

```bash
# On the machine where mining ran (the GPU box for MST-L):
cd <your-pwm-checkout>/pwm-team/infrastructure/agent-cli

# Find the working dir for the cert you want to publish
ls pwm_work_*/cert_payload.json | xargs grep -l '"Q_int": 35'
# pwm_work_1777772700/cert_payload.json    <-- the MST-L one

# Stage it under a public-facing path
mkdir -p ../../proof_certs/mst_l_l3_003/
cp pwm_work_1777772700/cert_payload.json ../../proof_certs/mst_l_l3_003/cert_payload.json

# Optional: also include a README pointing at the on-chain cert
cat > ../../proof_certs/mst_l_l3_003/README.md <<'EOF'
# MST-L L3-003 cert payload

On-chain cert: 0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13
Tx:            0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5
Submitter:     0x0c566f0F87cD062C3DE95943E50d572c74A87dEd
Q_int:         35
PSNR:          35.30 dB

Verify byte-exactness:
  python3 scripts/verify_cert_payload.py proof_certs/mst_l_l3_003/cert_payload.json
EOF

git add ../../proof_certs/mst_l_l3_003/
git commit -m "proof: publish MST-L L3-003 cert payload for Layer 4 verification"
git push
```

After the next pwm-public mirror sync, anyone can clone the repo and
re-derive the hash:

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
python3 scripts/verify_cert_payload.py proof_certs/mst_l_l3_003/cert_payload.json
# Recomputed cert_hash: 0x7c7740faad378c…
# On-chain cert_hash:  0x7c7740faad378c…
# Match: True
```

**Option B — paste as a GitHub Gist (good for one-off publication)**

```bash
# Authenticate gh once: gh auth login
gh gist create pwm_work_1777772700/cert_payload.json \
  --public \
  --desc "MST-L cert payload for L3-003 (cert 0x7c7740faad378c…)"

# Output: a gist URL like https://gist.github.com/…/abc123
# Paste that URL into your paper / FDA submission alongside the cert hash
```

The Gist is git-tracked too, so its content can't be silently edited
without leaving a revision history.

### A `verify_cert_payload.py` helper script (suggested)

Adding a one-line CLI wrapper to the public repo would let any third
party run the recipe without copy-pasting Python. Suggested file:
`scripts/verify_cert_payload.py`:

```python
#!/usr/bin/env python3
"""Verify a published cert_payload.json against the on-chain cert hash.

Usage:
    python3 scripts/verify_cert_payload.py path/to/cert_payload.json [expected_cert_hash]

If expected_cert_hash is omitted, just prints the recomputed hash so
the caller can compare to whichever on-chain hash they expected.
"""
import json, sys
from pathlib import Path
from web3 import Web3

# Must match scripts/register_genesis.py::UI_ONLY_FIELDS exactly
UI_ONLY = {"display_slug", "display_color", "ui_metadata", "registration_tier", "display_baselines"}

def main():
    if len(sys.argv) < 2:
        print("Usage: verify_cert_payload.py <cert_payload.json> [expected_hash]")
        sys.exit(2)
    payload = json.loads(Path(sys.argv[1]).read_text())
    chain_payload = {k: v for k, v in payload.items() if not k.startswith("_")}
    canonical = {k: v for k, v in chain_payload.items() if k not in UI_ONLY}
    canonical_bytes = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    recomputed = "0x" + Web3.keccak(canonical_bytes).hex().lstrip("0x").zfill(64)
    print(f"Recomputed cert_hash: {recomputed}")
    if len(sys.argv) >= 3:
        expected = sys.argv[2].lower()
        if not expected.startswith("0x"):
            expected = "0x" + expected
        match = recomputed.lower() == expected
        print(f"Expected cert_hash:  {expected}")
        print(f"Match: {match}")
        sys.exit(0 if match else 1)

if __name__ == "__main__":
    main()
```

### Privacy tradeoff

Publishing the payload exposes a few extra bits not strictly required
by the on-chain cert:

- **Wallet associations:** if `acWallet ≠ cpWallet ≠ spWallet`, you reveal the team's role split. Most miners use the same wallet for all three (single-wallet mining), in which case nothing extra leaks.
- **shareRatioP:** the AC/CP split percentage. Already on-chain via the cert struct, so no real leakage.
- **submittedAt:** identical to the block timestamp; on-chain.
- **_meta block** (if present): can include solver runtime, framework version, GPU model. Strip the `_meta` key before publishing if you'd rather keep your hardware setup private.

Most submitters can publish freely. If you have a reason to keep wallet
associations private, switch to a single-wallet mining setup before
mining the cert you plan to publish.

### Summary

| If you... | Then... |
|---|---|
| Want maximum third-party trust | Publish the payload (Option A or B). Layer 4 becomes available to everyone. |
| Want the cert to be tamper-resistant but private | Just submit the cert. Layers 1-3 (and Layer 5 for anyone with GPU + dataset) still apply. |
| Cite the cert in a paper / regulator submission | **Publish.** Reviewers expect byte-level reproducibility for high-stakes claims. |

---

## Layer 5 — Re-run MST-L on the benchmark dataset (~1-2 hours, GPU required)

The deepest check: actually re-run the solver and confirm the PSNR
claim of 35.30 dB.

### Setup (one-time, ~30 min)

```bash
# 1. Clone the public repo (with git-lfs for pretrained weights)
git lfs install
git clone --recursive https://github.com/integritynoble/pwm-public.git
cd pwm-public
git -C public lfs pull

# 2. Verify MST-L weights landed (~750 MB)
bash scripts/download_weights.sh
ls -la public/packages/pwm_core/weights/mst/mst_l.pth
# expected: regular file ~750 MB, NOT a 2-byte symlink

# 3. Install pwm_core + CUDA torch (adjust cu128 to your CUDA version)
pip install -e public/packages/pwm_core
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -e pwm-team/infrastructure/agent-cli   # for pwm-node CLI
```

### Run the dry-run mining flow (~5-30 min on GPU)

```bash
# Mine L3-003 with MST-L; --dry-run computes Q without submitting another cert
pwm-node --network testnet mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py \
  --dry-run

# Expected stdout:
#   [mine] runtime=~30s  PSNR=35.30 dB  Q=0.35  Q_int=35
#   [mine] cert_hash: 0x... (would-be hash, --dry-run prevents submission)
```

The `Q_int=35` and `PSNR=35.30 dB` should match the on-chain cert. The
would-be `cert_hash` will differ because your wallet address differs
from the submitter's — the miner's address is part of the canonical
payload.

### Confirm Q_int matches across runs

If your dry-run gives Q_int=35 and the cert says Q_int=35, that closes
the verification loop:

1. Same benchmark dataset (proven by Layer 4: payload's `benchmarkHash` matches L3-003's on-chain hash)
2. Same scoring formula (open source in `pwm_core.scoring`)
3. Same solver weights (deterministic — MST-L `.pth` is one bit-exact file)
4. Same input bytes (deterministic — InverseNet KAIST-10 datasets pinned)
5. Therefore, same Q_int = honest claim.

If you're missing the GPU and can only run Layers 1-4, that's still
strong evidence — the on-chain hash binding (Layer 3 + 4) prevents
tampering with the *claim*; Layer 5 is the optional "trust through
reproduction" step.

---

## What if a verification step fails?

| Failure mode | What it means |
|---|---|
| Layer 1 explorer ✓ but Layer 2 Etherscan ✗ | Explorer UI is wrong/stale — file an issue; trust Etherscan |
| Layer 2 ✓ but Layer 3 `cast` ✗ | Etherscan UI bug — extremely rare; treat both as evidence |
| Layer 4 hash mismatch | Submitter posted a payload that doesn't match what they registered. Either you have the wrong file, or they're lying. |
| Layer 5 re-run gives ≤30 dB | Either the weights file is corrupt (re-pull LFS), the dataset isn't bit-exact (re-pull from IPFS), or the solver code path was changed since the cert was submitted. Check `git log pwm_core/recon/mst.py` for changes since the cert's block timestamp. |

---

## Quick verification script (Layers 1-3 in 30 seconds)

```bash
#!/usr/bin/env bash
# verify-mst-l-claim.sh
CERT=0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13
echo "=== Explorer view ==="
curl -sS https://explorer.pwm.platformai.org/api/cert/$CERT \
  | jq '{q_int, solver_label, psnr_db, benchmark_hash, submitter}'
echo
echo "=== On-chain (cast call) ==="
cast call 0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08 \
  "certificates(bytes32)(bytes32,address,uint8,uint8,uint64,uint64)" $CERT \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
echo
echo "=== Etherscan tx (open in browser): https://sepolia.etherscan.io/tx/0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5"
```

Run that script → 30 seconds → you have on-chain Q_int=35 + benchmark
binding + submitter address confirmed three independent ways. That's
enough for most verification needs (FDA submission, paper review,
compliance audit).

For "I want to *fully* re-run their work" — Layer 5 is required and is
the gold standard.

---

## Cross-references

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full mining + cert lifecycle
- `pwm-team/customer_guide/PWM_Q_SCORE_EXPLAINED_2026-05-06.md` — what Q_int means + how it's computed
- `pwm-team/customer_guide/PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` — what binds Q_int to the cert hash on-chain
- `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol` — on-chain `uint8 Q_int` storage + `CertificateSubmitted` event
- `pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json` — ABI used by `web3.py` examples above
- `https://explorer.pwm.platformai.org/cert/0x7c7740faad378c…` — live cert detail page for the MST-L claim
- `https://sepolia.etherscan.io/tx/0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5` — Sepolia tx that minted the cert
