# agent-cli: Validation Checklist

Run every check below before merging the CLI PR. All commands reference `pwm_overview1.md` §CLI Commands and agent-cli CLAUDE.md.

---

## V1 — Files Exist

- [ ] `pyproject.toml` — name = "pwm-node", dependencies include web3, click, ipfshttpclient, pwm-scoring
- [ ] `pwm_node/__init__.py`
- [ ] `pwm_node/cli.py` — Click group entry point
- [ ] `pwm_node/chain.py` — Web3 contract wrappers
- [ ] `pwm_node/ipfs.py` — upload/download with hash verification
- [ ] `pwm_node/commands/mine.py`
- [ ] `pwm_node/commands/verify.py`
- [ ] `pwm_node/commands/submit.py`
- [ ] `pwm_node/commands/stake.py`
- [ ] `pwm_node/commands/inspect.py`
- [ ] `pwm_node/commands/agent.py`
- [ ] `tests/test_verify.py`
- [ ] `tests/test_mine.py`

**Verify:**
```bash
pip install -e .
pwm-node --help  # shows all command groups
```

---

## V2 — All Commands Exist with --help

### Discovery commands (pwm-node prefix):
```bash
pwm-node benchmarks --help        # [ ] exists
pwm-node inspect --help           # [ ] exists
pwm-node balance --help           # [ ] exists
```

### Local validation (pwm-node prefix, no chain):
```bash
pwm-node verify --help            # [ ] exists
pwm-node validate-benchmark --help # [ ] exists
```

### Mining (pwm-node prefix):
```bash
pwm-node mine --help              # [ ] exists
pwm-node sp register --help       # [ ] exists (NOT "ac register")
```

### Submission (mixed prefixes):
```bash
pwm-node submit-benchmark --help  # [ ] exists
pwm stake spec --help             # [ ] exists (pwm prefix)
pwm stake benchmark --help        # [ ] exists (pwm prefix)
pwm stake quote --help            # [ ] exists
```

### Solution management (pwm prefix):
```bash
pwm register solution --help      # [ ] exists
pwm upgrade solution --help       # [ ] exists
pwm pause solution --help         # [ ] exists
pwm resume solution --help        # [ ] exists
```

### CP operations (pwm prefix):
```bash
pwm register cp --help            # [ ] exists
pwm jobs list --help              # [ ] exists
pwm jobs submit --help            # [ ] exists
```

### Cross-benchmark and challenges:
```bash
pwm-node claim-cross-bench --help # [ ] exists
pwm challenge file --help         # [ ] exists
pwm challenge status --help       # [ ] exists
```

### Status checks:
```bash
pwm status principle --help       # [ ] exists
pwm status spec --help            # [ ] exists
pwm status benchmark --help       # [ ] exists
```

### Agent interface:
```bash
pwm-node agent mine-all --help    # [ ] exists
pwm-node agent mine-l1 --help     # [ ] exists
pwm-node agent mine-l3 --help     # [ ] exists
```

---

## V3 — verify.py (No Chain Interaction)

```bash
pwm-node verify <benchmark_yaml>
```

- [ ] Loads benchmark YAML from local path (no network call)
- [ ] Runs `pwm_scoring.gates.check_s1` through `check_s4`
- [ ] Prints per-gate result in this format:
  ```
  S1 [PASS] dimensions OK (256×256×28)
  S2 [PASS] iterative solver matches underdetermined system
  S3 [FAIL] convergence rate 1.4 < required 1.8
  S4 [PASS] worst PSNR 24.3 ≥ epsilon 22.0
  ```
- [ ] Exit code 0 if all gates pass, non-zero if any fail
- [ ] Works completely offline (no env vars needed)

---

## V4 — inspect.py

```bash
pwm-node inspect <hash>
pwm-node inspect <hash> --offline
pwm-node balance
pwm-node balance --address 0x1234...
```

- [ ] `inspect`: fetches from PWMRegistry via chain.py by default
- [ ] `inspect --offline`: loads from local JSON cache
- [ ] Pretty-prints: layer, creator, parent hash, timestamp, children
- [ ] `balance`: calls ERC20 `balanceOf()` on test PWM token
- [ ] `balance` output format: `0x1234... balance: 1,234.56 PWM`

---

## V5 — chain.py

- [ ] `ABI_DIR` points to `../../coordination/agent-coord/interfaces/contracts_abi/`
- [ ] `ADDRESSES_FILE` points to `../../coordination/agent-coord/interfaces/addresses.json`
- [ ] `get_contract(name, network="testnet")` returns Web3 contract instance
- [ ] Reads RPC URL from env `PWM_RPC_URL`
- [ ] Reads private key from env `PWM_PRIVATE_KEY`
- [ ] **NEVER** logs or prints the private key (grep for it)
- [ ] Wrapper functions exist:
  - [ ] `register_artifact(hash, parent_hash, layer)` → PWMRegistry
  - [ ] `submit_certificate(cert_hash, benchmark_hash, Q_int, payload)` → PWMCertificate
  - [ ] `stake_artifact(layer, artifact_hash, value_wei)` → PWMStaking
  - [ ] `get_artifact(hash)` → PWMRegistry

**Security check:**
```bash
# Must return zero matches for private key logging
grep -rn "print.*PRIVATE_KEY\|log.*PRIVATE_KEY\|PRIVATE_KEY.*print\|PRIVATE_KEY.*log" pwm_node/
# Should return nothing
```

---

## V6 — ipfs.py

- [ ] `upload(path: Path) -> str` — returns CID string
- [ ] `download(cid: str, dest: Path)` — fetches from IPFS
- [ ] SHA-256 verification on download
- [ ] Raises `HashMismatchError` if hash doesn't match expected
- [ ] Falls back to Pinata API if no local IPFS daemon

---

## V7 — mine.py

```bash
pwm-node mine <benchmark_id> --solver <solve.py> [--dry-run]
```

Full flow (10 steps):
1. [ ] Fetch benchmark manifest from PWMRegistry by benchmark_id
2. [ ] Download instance data from IPFS (manifest.instance_cid)
3. [ ] Run solver: `subprocess.run(["python", solve.py, "--input", instance_dir, "--output", out_dir])`
4. [ ] Load solver output array from out_dir
5. [ ] Call `score_solution(benchmark_manifest, instance_dir, solver_output, omega_params)`
6. [ ] Print cert_payload preview
7. [ ] If `--dry-run`: stop here, exit
8. [ ] Upload cert_payload to IPFS → get CID
9. [ ] Call `chain.submit_certificate(...)`
10. [ ] Poll for DrawSettled event (timeout 15 days)
11. [ ] Print draw result: rank, amount, SP/CP split

### --dry-run behavior:
- [ ] No chain interaction occurs
- [ ] No IPFS upload occurs
- [ ] cert_payload preview printed to stdout
- [ ] Exit code 0

---

## V8 — stake.py

### Staking formula (MUST match canonical):
```
S = max(PWM_floor, ceil(USD_target / TWAP_30d))
```

| Layer | USD Target | PWM Floor |
|-------|-----------|-----------|
| L1 | $50 | 10 PWM |
| L2 | $5 | 2 PWM |
| L3 | $1 | 1 PWM |

- [ ] `pwm stake spec` computes required PWM from USD + on-chain TWAP
- [ ] `pwm stake benchmark` same computation with L3 values
- [ ] `pwm stake quote` shows current TWAP and required PWM per tier (read-only)
- [ ] Calls `PWMStaking.stake(layer, artifactHash)` with correct value

---

## V9 — SP Registration

```bash
pwm-node sp register \
  --entry-point <solve.py> \
  --share-ratio <float> \
  --min-vram-gb <int> \
  --framework <pytorch|jax|numpy>
```

- [ ] Command name is `sp register` (NOT `ac register`)
- [ ] `--share-ratio` enforced: p ∈ [0.10, 0.90]
- [ ] Rejects p < 0.10 or p > 0.90 with clear error
- [ ] Registers SP profile on-chain
- [ ] Stores entry-point hash in PWMRegistry

---

## V10 — Error Handling

- [ ] S-gate failures show specific gate number and reason:
  ```
  Error: Gate S3 failed — convergence rate 1.4 < required 1.8
  ```
- [ ] Chain errors show human-readable message (not raw Python traceback)
- [ ] Missing env vars (`PWM_RPC_URL`, `PWM_PRIVATE_KEY`) show clear instructions
- [ ] Invalid benchmark_id shows available benchmarks

---

## V11 — Cross-Platform

- [ ] Works on Linux (test with Python 3.11+)
- [ ] Works on macOS
- [ ] Works on Windows (path separators, subprocess calls)
- [ ] `pip install -e .` creates `pwm-node` entry point on all platforms

---

## V12 — End-to-End Test on Testnet

```bash
export PWM_RPC_URL="https://testnet-rpc.pwm.platformai.org"
export PWM_PRIVATE_KEY="0x..."  # test wallet

pwm-node mine cassi/t1_nominal --solver gap_tv.py
```

- [ ] Completes end-to-end in ≤ 5 minutes (excluding solver runtime)
- [ ] Certificate submitted on testnet
- [ ] Draw settled and result printed
- [ ] Output shows: benchmark_id, Q score, rank, draw amount, SP/CP split

---

## V13 — Test Suite

```bash
pytest tests/ -v
```

- [ ] `test_verify.py` — mock gates, confirm output formatting
- [ ] `test_mine.py` — mock chain + scoring engine, confirm full flow
- [ ] All tests pass
- [ ] No tests require live chain connection (all mocked)
