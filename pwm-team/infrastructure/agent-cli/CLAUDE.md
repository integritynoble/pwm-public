# Agent Role: agent-cli
## pwm-node CLI Developer

You build the `pwm-node` command-line tool — the primary interface for individual miners (SP role). It wraps the scoring engine and contract calls behind human-readable commands. Install with one command; works on Linux, macOS, Windows.

## You own
- `pwm_node/` — Python package, installable as `pwm-node` via pip
- `tests/` — full test suite

## You must NOT modify
- `../agent-contracts/` — contracts (you call them, never edit them)
- `../agent-scoring/` — scoring engine (you import it as a library)
- `../agent-miner/` — mining client (separate component)
- `../agent-web/` — web explorer
- `../agent-*/principles/` — content

## Interfaces you depend on
- `../agent-coord/interfaces/contracts_abi/` — for chain.py contract calls
- `../agent-coord/interfaces/scoring_api.py` — import pwm_scoring.score_solution
- `pwm_overview1.md` §CLI Commands — your specification

## Unblocked at: M1.1 (contracts ABI) + M1.2 (scoring engine)

## Commands to implement

```bash
# Discovery
pwm-node benchmarks [--domain <domain>] [--spec <spec_id>]
pwm-node inspect <cert_hash | benchmark_id | spec_id | principle_id>
pwm-node balance [--address <wallet>]

# Local validation (free — no chain interaction)
pwm-node verify <benchmark_yaml>           # S1-S4 pre-check on your solver
pwm-node validate-benchmark <dir>          # validate benchmark dir before submission

# Mining (SP role)
pwm-node mine <benchmark_id> --solver <solve.py> [--dry-run]

# SP registration
pwm-node sp register \
  --entry-point <solve.py> \
  --share-ratio <float>    \
  --min-vram-gb <int>      \
  --framework <pytorch|jax|numpy>

# Submission (L2/L3)
pwm-node submit-benchmark <dir>
pwm stake spec      --principle-id <id> --spec-file <yaml> --usd-amount <n>
pwm stake benchmark --spec-id <id>      --benchmark-file <yaml> --usd-amount <n>

# Cross-benchmark claim (after P-benchmark pass)
pwm-node claim-cross-bench --p-cert <hash> --target <benchmark_id>

# Agent interface
pwm-node agent mine-all --domain <domain> --model <model_id>
```

## Files to implement

### pwm_node/commands/mine.py
- Parse benchmark_id → fetch manifest from chain (PWMRegistry)
- Call score_solution() from pwm_scoring
- If --dry-run: print cert_payload preview, stop
- Else: sign and submit to PWMCertificate.submit()
- Poll for finalization, print draw result

### pwm_node/commands/verify.py
- Load benchmark_yaml locally
- Run S1-S4 gates (from pwm_scoring.gates) without chain interaction
- Print pass/fail per gate with reason

### pwm_node/commands/submit.py
- validate-benchmark: run pwm_scoring validation on local dir
- submit-benchmark: IPFS upload → PWMRegistry.register()

### pwm_node/commands/stake.py
- Compute required PWM from USD amount + Chainlink TWAP
- Call PWMStaking.stake()

### pwm_node/commands/inspect.py
- Fetch artifact data from PWMRegistry by hash
- Pretty-print: layer, creator, parent, timestamp, children

### pwm_node/commands/agent.py
- mine-all: iterate over benchmarks in domain, call mine.py for each
- Designed to be called by Claude Code or other LLM agents

### pwm_node/chain.py
- Web3 wrappers for each contract function
- Reads from ../agent-coord/interfaces/contracts_abi/ and addresses.json
- Signs transactions with local wallet (private key from env: PWM_PRIVATE_KEY)

### pwm_node/ipfs.py
- `upload(path: Path) -> str` — returns CID
- `download(cid: str, dest: Path)` — fetches and verifies SHA-256

## Definition of done
- `pwm-node mine cassi/t1_nominal --solver gap_tv.py` completes end-to-end on testnet
- Installable: `pip install pwm-node` (or `brew install pwm-node`)
- Works on Linux, macOS, Windows
- All commands have --help text
- Test suite: each command tested with mocked chain + scoring engine

## How to signal completion
1. Update `../agent-coord/progress.md` — mark M1.3 DONE
2. Open PR: `feat/pwm-node-cli-v1`
