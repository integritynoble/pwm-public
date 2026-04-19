# Agent Role: agent-miner
## Mining Client Developer (Compute Provider Role)

You build the CP mining client — the infrastructure that lets any GPU operator earn PWM by running other people's solvers. This makes PWM scalable: no physics knowledge required to be a CP.

## You own
- `pwm_miner/` — Python package
- `docker/Dockerfile` — sandboxed execution environment

## You must NOT modify
- `../agent-contracts/` — contracts
- `../agent-scoring/` — scoring engine
- `../agent-cli/` — CLI (different role: SP vs CP)
- `../agent-web/` — web explorer
- `../agent-*/principles/` — content

## Interfaces you depend on
- `../agent-coord/interfaces/contracts_abi/` — PWMCertificate event stream
- `pwm_overview1.md` §Compute Provider, §Commit-then-Reveal — your specification

## Unblocked at: M1.1 (contracts ABI)

## Files to implement

### pwm_miner/job_queue.py
- Poll `PWMCertificate` event stream for `JobPosted` events
- Filter by hardware requirements: skip if `compute_manifest.min_vram_gb > local_vram`
- Maintain local queue of available jobs sorted by expected reward

### pwm_miner/commit_reveal.py
Implements the anti-front-running commit-then-reveal protocol:
```
Phase 1 (0–30s after job appears):
  CP commits: PWMCertificate.commit(hash(solution_preview + nonce))

Phase 2 (30–60s):
  CP reveals: PWMCertificate.reveal(solution_preview, nonce)
  Contract verifies commit matches; first valid reveal wins

Race winner: first valid Phase 2 reveal earns (1-p) × 55%
Tie-breaking: block timestamp; earlier reveal wins
```

### pwm_miner/executor.py
- Fetch solver binary from IPFS (CID from compute_manifest)
- Verify SHA-256 of binary matches on-chain registered hash BEFORE executing
- Run solver inside Docker container (never execute unverified code on host)
- Enforce resource limits: memory, GPU, runtime from compute_manifest
- Capture stdout/stderr; return solution array + execution metrics

### pwm_miner/ipfs_fetch.py
- `fetch_solver(cid: str, expected_hash: str) -> Path`
- Download binary, verify hash, cache locally
- Raise VerificationError if hash mismatch (never run unverified binaries)

### pwm_miner/cp_register.py
- `pwm-node cp register --gpu <model> --vram <gb> --region <code>`
- Stake ≥10 PWM as CP bond (slashable on provably incorrect output)
- Register hardware profile on-chain

### docker/Dockerfile
```dockerfile
FROM python:3.11-slim
# GPU support via nvidia-docker or CPU fallback
# No network access inside container (solver cannot exfiltrate data)
# /input and /output mount points only
# Memory and GPU limits enforced via docker run flags
```

## Security requirements
- NEVER execute a solver binary whose SHA-256 does not match the on-chain registered hash
- NEVER give solver container network access or host filesystem access
- NEVER run as root inside container
- CP bond is slashed if CP submits provably incorrect solution

## Definition of done
- Successfully completes 100 consecutive job executions on testnet
- Commit-then-reveal tested under simulated racing (3 CPs competing)
- Docker sandbox verified: solver cannot read host files, cannot make network calls
- CP bond staking and slashing tested
- Test suite: unit + integration tests

## How to signal completion
1. Update `../agent-coord/progress.md` — mark M1.4 DONE
2. Open PR: `feat/mining-client-v1`
