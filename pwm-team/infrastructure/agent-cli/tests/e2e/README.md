# End-to-end acceptance tests for `pwm-node`

These tests validate `pwm-node` against real infrastructure (Sepolia RPC,
the repo's genesis artifacts). They are **opt-in** — disabled by default so
that `pytest` from a fresh checkout runs cleanly without hitting the network.

## Enabling e2e tests

```bash
export PWM_RUN_E2E=1
pytest tests/e2e/ -v
```

## Test inventory

| File | Needs network? | Needs wallet? | Purpose |
|------|---------------|---------------|---------|
| `test_sepolia_readonly.py` | yes | no | Real Sepolia RPC checks: block number, contract code presence, stakeAmount sanity |
| `test_mine_dry_run.py` | no | no | Full mine flow end-to-end against real repo genesis, `--dry-run` (no tx) |

## Full Sepolia mine (acceptance criterion from bounty spec)

The bounty spec's hardest acceptance test is:

> `pwm-node mine cassi/t1_nominal --solver demo_solver.py` completes end-to-end on Sepolia testnet from a clean install in **≤ 5 minutes**.

This requires:

1. **A funded wallet on Sepolia.** Get Sepolia ETH from a faucet (e.g.
   `sepoliafaucet.com`). Minimum ~0.05 ETH for gas headroom.

2. **The L3-003 CASSI benchmark registered on-chain.** Check with:
   ```bash
   pwm-node --network testnet inspect L3-003
   ```
   If the L3 benchmark hash is not yet registered in `PWMRegistry` by
   `agent-contracts`, submission will fail at the chain level. Wait for
   the `GENESIS_REGISTERED` signal in `progress.md`.

3. **An IPFS daemon** (for dataset fetch; stub-tolerant in Phase C but
   needed for Phase D miner integration).

### Run procedure

```bash
# 1. Configure
export PWM_RUN_E2E=1
export PWM_RPC_URL=https://rpc.sepolia.org   # or Infura/Alchemy key
export PWM_PRIVATE_KEY=0x...                 # 64-hex testnet key
cd pwm-team/infrastructure/agent-cli

# 2. Verify readonly first (no gas needed)
pytest tests/e2e/test_sepolia_readonly.py -v

# 3. Dry-run mine (no tx, validates flow)
pytest tests/e2e/test_mine_dry_run.py -v

# 4. Live mine against testnet (this costs gas):
pwm-node --network testnet mine L3-003 \
    --solver examples/demo_solver.py \
    --timeout 300
```

### Expected output for a successful live mine

```
[pwm-node mine] resolved L3-003 → L3-003 (L3-003.json)
[pwm-node mine] work dir: /.../pwm_work_1713654321
[pwm-node mine] running solver: examples/demo_solver.py
[pwm-node mine] solver completed in 0.3s, output: /.../pwm_work_.../output
[pwm-node mine] Q = 0.850, gates: {'S1': 'pass', 'S2': 'pass', 'S3': 'pass', 'S4': 'pass'}
[pwm-node mine] cert payload written to: /.../pwm_work_.../cert_payload.json
[pwm-node mine] cert_hash: sha256:...
[pwm-node mine] submitting cert to testnet...
[pwm-node submit-cert] signer: 0x<you>
[pwm-node submit-cert] submitting to PWMCertificate on testnet...
[pwm-node submit-cert] tx submitted: 0x<hash>
[pwm-node submit-cert] confirmed in block <N>, gas used <G>
```

Total wall-clock: **< 60 seconds** for the demo solver + submit tx. The
bounty spec's ≤ 5-minute budget gives headroom for real solvers and
slow Sepolia blocks.

### Exit codes (for scripting)

```
0  success
1  configuration failure (RPC unreachable, key missing, etc.)
3  benchmark_id not found in registry
4  S1-S4 gates did not all PASS (epsilon not cleared)
5  IPFS dataset fetch failure
6  solver timeout
7  solver exited non-zero
```

## When live tests fail on Sepolia

Common causes:

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Cannot connect to RPC` | RPC URL wrong or rate-limited | Set `PWM_RPC_URL` to an Infura/Alchemy endpoint |
| `Mainnet contracts not yet deployed` | `--network mainnet` without deployment | Use `--network testnet` |
| `PWMStaking.stakeAmount(0) returned 0` | Contract initialized but governance hasn't set stake amounts | Wait for `SETUP_STAKE_AMOUNTS = true` in `progress.md` |
| `no offline match for 'L3-003'` | Running without `--network` flag in chain-lookup mode | Pass `--network testnet` |
| `tx reverted on-chain` | Benchmark hash not registered, or signer unauthorized | Check with `pwm-node --network testnet inspect <hash>` |
