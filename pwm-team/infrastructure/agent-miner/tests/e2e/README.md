# End-to-end acceptance tests for `pwm-miner`

The CP mining client's acceptance criteria from `CLAUDE.md`:

> - Successfully completes 100 consecutive job executions on testnet
> - Commit-then-reveal tested under simulated racing (3 CPs competing)
> - Docker sandbox verified: solver cannot read host files, cannot make network calls
> - CP bond staking and slashing tested

This directory hosts the opt-in tests that validate those properties against
real infrastructure (Sepolia RPC, actual Docker daemon). Mocked-unit tests in
the parent `tests/` cover the logic; these e2e tests cover the integration.

## Opt-in gate

Tests are **skipped** unless the `PWM_RUN_E2E=1` env var is set. This mirrors
the agent-cli e2e gating.

## Acceptance procedure (100-job continuous run)

Per bounty spec §4 acceptance criterion 1.

### Prerequisites

1. **Docker daemon** running and accessible: `docker info` returns without error.
2. **Build the sandbox image**:
   ```bash
   cd pwm-team/infrastructure/agent-miner/docker
   docker build -t pwm-sandbox .
   ```
3. **Funded CP wallet on Sepolia** — ≥ 15 PWM (10 for bond + gas headroom).
   Get Sepolia ETH from a faucet; protocol's PWM faucet via `pwm-node stake quote`.
4. **Registered as CP**:
   ```bash
   export PWM_PRIVATE_KEY=0x<64-hex>
   export PWM_WEB3_URL=https://sepolia.infura.io/v3/<key>
   pwm-miner cp register --gpu RTX4090 --vram 24 --region us-east-1
   ```

### Run the continuous mining loop

```bash
# Start miner with --max-jobs 100 to stop after 100 completions
pwm-miner start --vram-gb 24 --max-jobs 100
```

**Expected throughput:** one `JobPosted` → `commit` → `reveal` → `submit` cycle
per ~60 seconds (commit-reveal protocol window). 100 jobs ≈ 100 minutes of
wall-clock if jobs post back-to-back; more likely several hours in practice
as actual SP job posts are irregular.

**Pass criteria:**

- All 100 cycles result in a valid certificate submission (no `VerificationError`,
  no `RegistrationError`).
- No spot-check mismatches (< 1% allowable; see CLAUDE.md §Spot-check).
- CP bond remains ≥ 10 PWM throughout (no slash events).

### Race test — 3 CPs competing

Commit-then-reveal correctness under race conditions:

```bash
# Terminal 1 (CP_A):
export PWM_PRIVATE_KEY=0xAAA...
pwm-miner start --vram-gb 24 --max-jobs 10

# Terminal 2 (CP_B):
export PWM_PRIVATE_KEY=0xBBB...
pwm-miner start --vram-gb 24 --max-jobs 10

# Terminal 3 (CP_C):
export PWM_PRIVATE_KEY=0xCCC...
pwm-miner start --vram-gb 24 --max-jobs 10
```

**Pass criteria:**

- No double-submission: a given `cert_hash` is only finalized once.
- Exactly one CP wins each job (the first valid reveal; block-timestamp tie-break).
- Losers see a "job already settled" info log, no error.

### Docker sandbox verification

The sandbox must deny solver access to:
- Host filesystem (beyond mounted /input /output)
- Network egress

Manual check:
```bash
# Build a test "solver" that tries to escape
cat > /tmp/escape_solver.py <<'EOF'
import pathlib, urllib.request
# Try to read a host file — should fail
try:
    pathlib.Path("/etc/shadow").read_text()
    print("FAIL: host file accessible")
except Exception as e:
    print(f"OK: host file blocked ({type(e).__name__})")
# Try to make a network call — should fail (--network none)
try:
    urllib.request.urlopen("https://example.com", timeout=3)
    print("FAIL: network accessible")
except Exception as e:
    print(f"OK: network blocked ({type(e).__name__})")
EOF

# Run via the sandbox
docker run --rm \
    --network none \
    --read-only \
    --mount type=bind,src=/tmp,dst=/input,readonly \
    --mount type=bind,src=/tmp,dst=/output \
    --memory 1g \
    pwm-sandbox python /input/escape_solver.py
```

**Pass criteria:** both checks print "OK: ... blocked".

### CP bond slashing path

Slashing happens on-chain via `PWMStaking.slashForFraud(artifactHash)` or
`slashForChallenge(artifactHash, challenger)`. The path is exercised by
submitting a provably-wrong solution and observing the slash event. This
requires coordination with the protocol validators and is documented in
`pwm_overview1.md §Spot-check`.

## Common issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Cannot connect to Web3 endpoint` | RPC URL wrong or rate-limited | Use `PWM_WEB3_URL=wss://...infura.io/ws/v3/<key>` |
| `InsufficientBondError: bond below 10 PWM` | Test ran with `bond_amount_pwm=0` | Supply `--bond 10.0` or higher to `pwm-miner cp register` |
| Docker `Permission denied` | User not in docker group | `sudo usermod -aG docker $USER && newgrp docker` |
| `No jobs in queue` for > 5 minutes | No SPs have submitted jobs on this spec | Normal during bootstrap; monitor with `pwm-node benchmarks --domain compressive` |

## Exit codes (for scripting)

`pwm-miner start` runs indefinitely. Use `--max-jobs N` for scripting. On exit:

- `0` — max_jobs reached cleanly
- `1` — configuration error (PWM_PRIVATE_KEY missing, etc.)
- `130` — SIGINT (Ctrl-C); any in-flight job is allowed to finish
