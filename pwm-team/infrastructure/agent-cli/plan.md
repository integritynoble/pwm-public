# agent-cli: Execution Plan

Read `CLAUDE.md` first (your role and all command specs). This file is your step-by-step work order.

---

## Before You Start

- [ ] Read `CLAUDE.md` — all commands and their exact signatures are there.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §CLI Commands, §SP Registration.
- [ ] **Wait for M1.1** (contracts ABI) AND **M1.2** (scoring engine) before implementing chain.py and mine.py.
- [ ] You can implement `verify.py` and `inspect.py` immediately (no chain dependency).
- [ ] Check these are available before proceeding:
  - `../../coordination/agent-coord/interfaces/contracts_abi/` — must contain all 7 ABI JSONs
  - `../../coordination/agent-coord/interfaces/scoring_api.py` — scoring engine stub

---

## Step 1 — Project Setup

- [ ] **1.1** Create `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools"]
  build-backend = "setuptools.backends.legacy:build"

  [project]
  name = "pwm-node"
  version = "1.0.0"
  requires-python = ">=3.11"
  dependencies = ["web3>=6.0", "click>=8.0", "ipfshttpclient", "pwm-scoring"]

  [project.scripts]
  pwm-node = "pwm_node.cli:main"
  ```
- [ ] **1.2** Create `pwm_node/cli.py` — Click group that imports all command groups:
  ```python
  import click
  from .commands import mine, verify, submit, stake, inspect, agent

  @click.group()
  def main(): pass

  main.add_command(mine.mine)
  main.add_command(verify.verify)
  # etc.
  ```
- [ ] **1.3** `pip install -e .` → `pwm-node --help` shows all commands.

---

## Step 2 — verify.py (no chain, start here)

- [ ] **2.1** `pwm-node verify <benchmark_yaml>`:
  - Load benchmark YAML from local path
  - Run `pwm_scoring.gates.check_s1` through `check_s4`
  - Print per-gate result:
    ```
    S1 [PASS] dimensions OK (256×256×28)
    S2 [PASS] iterative solver matches underdetermined system
    S3 [FAIL] convergence rate 1.4 < required 1.8
    S4 [PASS] worst PSNR 24.3 ≥ epsilon 22.0
    ```
- [ ] **2.2** Write `tests/test_verify.py` — mock gates, confirm output formatting.

---

## Step 3 — inspect.py (no chain initially, add chain when M1.1 ready)

- [ ] **3.1** `pwm-node inspect <hash>`:
  - If `--offline`: load from local JSON cache
  - Else: call `PWMRegistry.getArtifact(hash)` via `chain.py`
  - Pretty-print: layer, creator, parent hash, timestamp, children
- [ ] **3.2** `pwm-node balance [--address <wallet>]`:
  - Call ERC20 `balanceOf()` on test PWM token contract
  - Print: `0x1234... balance: 1,234.56 PWM`

---

## Step 4 — chain.py (after M1.1)

- [ ] **4.1** Implement `chain.py`:
  ```python
  from web3 import Web3
  from pathlib import Path
  import json, os

  ABI_DIR = Path(__file__).parent.parent.parent / "agent-coord/interfaces/contracts_abi"
  ADDRESSES_FILE = Path(__file__).parent.parent.parent / "agent-coord/interfaces/addresses.json"

  def get_contract(name: str, network: str = "testnet"):
      w3 = Web3(Web3.HTTPProvider(os.environ["PWM_RPC_URL"]))
      abi = json.load(open(ABI_DIR / f"{name}.json"))["abi"]
      address = json.load(open(ADDRESSES_FILE))[network][name]
      return w3.eth.contract(address=address, abi=abi)
  ```
- [ ] **4.2** Add wrappers for each contract function used by CLI commands:
  - `register_artifact(hash, parent_hash, layer)` → PWMRegistry
  - `submit_certificate(cert_hash, benchmark_hash, Q_int, payload)` → PWMCertificate
  - `stake_artifact(layer, artifact_hash, value_wei)` → PWMStaking
  - `get_artifact(hash)` → PWMRegistry
- [ ] **4.3** Signing: read private key from env `PWM_PRIVATE_KEY`; never log or print it.

---

## Step 5 — ipfs.py

- [ ] **5.1** `upload(path: Path) -> str`:
  - Upload file to IPFS daemon (or Pinata API if no local daemon)
  - Return CID
- [ ] **5.2** `download(cid: str, dest: Path)`:
  - Fetch from IPFS
  - Verify SHA-256 matches `dest.stem` if provided
  - Raise `HashMismatchError` on mismatch

---

## Step 6 — mine.py (after M1.1 + M1.2)

- [ ] **6.1** `pwm-node mine <benchmark_id> --solver <solve.py> [--dry-run]`:
  ```
  1. Fetch benchmark manifest from PWMRegistry by benchmark_id
  2. Download instance data from IPFS (manifest.instance_cid)
  3. Run solver: subprocess.run(["python", solve.py, "--input", instance_dir, "--output", out_dir])
  4. Load solver output array from out_dir
  5. Call score_solution(benchmark_manifest, instance_dir, solver_output, omega_params)
  6. Print cert_payload preview
  7. If --dry-run: stop here
  8. Upload cert_payload to IPFS → get CID
  9. Call chain.submit_certificate(...)
  10. Poll for DrawSettled event (timeout 15 days)
  11. Print draw result: rank, amount, SP/CP split
  ```
- [ ] **6.2** Write `tests/test_mine.py` — mock chain + scoring engine; confirm full flow.

---

## Step 7 — submit.py

- [ ] **7.1** `pwm-node submit-benchmark <dir>`:
  - Validate benchmark dir (run scoring validation)
  - Upload benchmark files to IPFS
  - Call `PWMRegistry.register()` for L3 artifact hash
- [ ] **7.2** `pwm-node stake spec --principle-id <id> --spec-file <yaml> --usd-amount <n>`:
  - Compute required PWM from USD + Chainlink TWAP (read from chain)
  - Call `PWMStaking.stake(layer=2, artifactHash)`
- [ ] **7.3** `pwm-node stake benchmark --spec-id <id> --benchmark-file <yaml> --usd-amount <n>`:
  - Same as above with layer=3

---

## Step 8 — stake.py and agent.py

- [ ] **8.1** `pwm-node sp register --entry-point <solve.py> --share-ratio <float> --min-vram-gb <int> --framework <str>`:
  - Register SP profile on-chain
  - Store entry-point hash in PWMRegistry
- [ ] **8.2** `pwm-node agent mine-all --domain <domain> --model <model_id>`:
  - Fetch all benchmarks for domain from PWMRegistry
  - For each benchmark: call `mine()` in a loop
  - Designed for automated agent use (minimal interactive output)
- [ ] **8.3** `pwm-node claim-cross-bench --p-cert <hash> --target <benchmark_id>`:
  - Verify P-cert passed (Q ≥ threshold)
  - Submit cross-benchmark claim for I-benchmarks in same spec

---

## Step 9 — Help Text and Polish

- [ ] **9.1** Every command has `--help` with description, required args, examples.
- [ ] **9.2** Error messages are human-readable (not Python tracebacks by default).
- [ ] **9.3** Confirm works on Linux, macOS (and Windows if possible).

---

## Step 10 — End-to-End Test on Testnet

- [ ] **10.1** Set env vars:
  ```bash
  export PWM_RPC_URL="https://testnet-rpc.pwm.platformai.org"
  export PWM_PRIVATE_KEY="0x..."
  ```
- [ ] **10.2** Run:
  ```bash
  pwm-node mine cassi/t1_nominal --solver gap_tv.py
  ```
  Expected: cert submitted on testnet, draw settled, reward printed.

---

## Step 11 — Signal Completion

- [ ] **11.1** Update `../../coordination/agent-coord/progress.md` — mark M1.3 `DONE`.
- [ ] **11.2** Open PR: `feat/pwm-node-cli-v1`
  - Include: full `pwm_node/` package, `tests/`, `pyproject.toml`
  - PR description: end-to-end testnet result (benchmark_id, Q score, draw rank)
