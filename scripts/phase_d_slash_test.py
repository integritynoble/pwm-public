"""Phase D §3.7 slashing-path test on Sepolia — artifact-stake proxy.

Exercises PWMStaking's stake → slashForFraud() path end-to-end on the
deployed testnet contracts. The deployed PWMStaking implements
*artifact*-layer staking (L1/L2/L3), not CP-bond staking (a Phase-E
mainnet feature); so this test is a proxy that verifies the slashing
mechanics, not the CP-specific accounting.

Flow (all txs on Sepolia, reversible state changes):
  1. DEPLOYER=governance: setStakeAmount(LAYER_BENCHMARK=2, 0.01 ETH)
  2. FOUNDER_2 stakes 0.01 ETH on a synthetic bytes32 (not a real
     registered artifact — avoids delisting real genesis data).
  3. Verify stakeOf(hash) shows FOUNDER_2 / 0.01 ETH / Active.
  4. DEPLOYER slashForFraud(hash) → 100% burned to BURN_SINK.
  5. Verify stakeOf(hash) status flipped to Fraud.
  6. DEPLOYER restores setStakeAmount(2, 2 ETH).

Net state change: one "Fraud"-status Stake record for the synthetic
hash lives on-chain forever (by design — artifact permanently delisted).
No real genesis artifact is touched; no parameters permanently changed.

Requires env: PWM_RPC_URL, PWM_PRIVATE_KEY (=DEPLOYER=governance),
FOUNDER_2_PRIVATE_KEY.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("phase_d_slash")

LAYER_BENCHMARK = 2
LOW_STAKE_WEI = 10 ** 16  # 0.01 ETH
ORIGINAL_STAKE_WEI = 2 * 10 ** 18  # 2 ETH — matches pre-test value
BURN_SINK = "0x000000000000000000000000000000000000dEaD"


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _send(fn, acct, w3, chain_id: int, value_wei: int = 0,
          gas_ceiling: int = 500_000) -> dict:
    """Send a write tx from `acct` and wait for receipt. Returns receipt dict."""
    try:
        gas = fn.estimate_gas({"from": acct.address, "value": value_wei})
    except Exception as e:
        raise RuntimeError(f"estimate_gas failed (likely revert): {e}")
    tx = fn.build_transaction({
        "from": acct.address,
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": min(gas_ceiling, int(gas * 1.2)),
        "value": value_wei,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    })
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    tx_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    status = receipt.get("status")
    logger.info("  → tx %s  block=%d  gas=%d  status=%s",
                tx_hex, receipt.get("blockNumber"), receipt.get("gasUsed"), status)
    if status != 1:
        raise RuntimeError(f"tx REVERTED: {tx_hex}")
    return dict(receipt, tx_hex=tx_hex)


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("web3 not installed: %s", e)
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL required")
        return 1

    repo = _repo_root()
    addresses = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/addresses.json").read_text()
    )["testnet"]
    staking_abi = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMStaking.json").read_text()
    )
    staking_abi = staking_abi if isinstance(staking_abi, list) else staking_abi.get("abi", [])

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error("cannot connect to RPC")
        return 1
    chain_id = addresses["chainId"]
    staking = w3.eth.contract(
        address=w3.to_checksum_address(addresses["PWMStaking"]),
        abi=staking_abi,
    )

    gov_pk = os.environ.get("PWM_PRIVATE_KEY")
    f2_pk = os.environ.get("FOUNDER_2_PRIVATE_KEY")
    if not (gov_pk and f2_pk):
        logger.error("PWM_PRIVATE_KEY and FOUNDER_2_PRIVATE_KEY required")
        return 1
    gov = Account.from_key(gov_pk if gov_pk.startswith("0x") else "0x" + gov_pk)
    f2 = Account.from_key(f2_pk if f2_pk.startswith("0x") else "0x" + f2_pk)

    on_chain_gov = staking.functions.governance().call()
    if on_chain_gov.lower() != gov.address.lower():
        logger.error("PWM_PRIVATE_KEY (%s) is NOT the governance address (%s)",
                     gov.address, on_chain_gov)
        return 2
    logger.info("governance=%s (matches signer)", gov.address)

    # Synthetic benchmark hash — keccak256("phase-d-slash-test/L3-synthetic/2026-04-21")
    synth_preimage = b"phase-d-slash-test/L3-synthetic/2026-04-21"
    art_hash_bytes = w3.keccak(synth_preimage)
    art_hash_hex = "0x" + art_hash_bytes.hex()
    logger.info("synthetic artifactHash=%s", art_hash_hex)

    # Pre-flight: hash must not already be staked (Status.None == 0).
    before = staking.functions.stakeOf(art_hash_bytes).call()
    if before[3] != 0:
        logger.error("hash already has stake record (status=%d); change preimage", before[3])
        return 3

    burn_bal_before = w3.eth.get_balance(w3.to_checksum_address(BURN_SINK))
    f2_bal_before = w3.eth.get_balance(f2.address)
    gov_bal_before = w3.eth.get_balance(gov.address)

    results: dict = {
        "gov_address": gov.address,
        "staker_address": f2.address,
        "artifact_hash": art_hash_hex,
        "burn_sink": BURN_SINK,
        "burn_sink_bal_before_wei": burn_bal_before,
        "steps": [],
    }

    # Step 1 — lower the benchmark stakeAmount to 0.01 ETH so we can afford it.
    logger.info("[1/4] setStakeAmount(2, 0.01 ETH)")
    r1 = _send(staking.functions.setStakeAmount(LAYER_BENCHMARK, LOW_STAKE_WEI),
               gov, w3, chain_id)
    results["steps"].append({"name": "setStakeAmount_low", "tx": r1["tx_hex"],
                             "block": r1["blockNumber"]})
    sa_now = staking.functions.stakeAmount(LAYER_BENCHMARK).call()
    assert sa_now == LOW_STAKE_WEI, f"stakeAmount mismatch: {sa_now}"

    # Step 2 — F2 stakes on the synthetic hash.
    logger.info("[2/4] FOUNDER_2 stakes %s wei on %s",
                LOW_STAKE_WEI, art_hash_hex)
    r2 = _send(staking.functions.stake(LAYER_BENCHMARK, art_hash_bytes),
               f2, w3, chain_id, value_wei=LOW_STAKE_WEI)
    results["steps"].append({"name": "stake", "tx": r2["tx_hex"],
                             "block": r2["blockNumber"]})
    after_stake = staking.functions.stakeOf(art_hash_bytes).call()
    # Returns: (address staker, uint8 layer, uint256 amount, uint8 status)
    assert after_stake[0].lower() == f2.address.lower(), "wrong staker"
    assert after_stake[2] == LOW_STAKE_WEI, "wrong amount"
    assert after_stake[3] == 1, f"status not Active: {after_stake[3]}"  # Status.Active = 1
    logger.info("  staker=%s amount=%s status=Active",
                after_stake[0], after_stake[2])
    results["stake_verified_active"] = True

    # Step 3 — governance slashForFraud(); 100% goes to BURN_SINK.
    logger.info("[3/4] DEPLOYER (governance) slashForFraud(%s)", art_hash_hex)
    r3 = _send(staking.functions.slashForFraud(art_hash_bytes),
               gov, w3, chain_id)
    results["steps"].append({"name": "slashForFraud", "tx": r3["tx_hex"],
                             "block": r3["blockNumber"]})
    after_slash = staking.functions.stakeOf(art_hash_bytes).call()
    # Status.Fraud = 4 in the Solidity enum
    # (None=0, Active=1, Graduated=2, Slashed=3, Fraud=4)
    assert after_slash[3] == 4, f"status not Fraud: {after_slash[3]}"
    logger.info("  status=Fraud ✓")
    results["slash_verified_fraud"] = True

    burn_bal_after = w3.eth.get_balance(w3.to_checksum_address(BURN_SINK))
    burn_delta = burn_bal_after - burn_bal_before
    logger.info("  BURN_SINK delta=%s wei (%.6f ETH)", burn_delta,
                burn_delta / 1e18)
    assert burn_delta == LOW_STAKE_WEI, \
        f"burn amount mismatch: expected {LOW_STAKE_WEI}, got {burn_delta}"
    results["burn_sink_bal_after_wei"] = burn_bal_after
    results["burn_delta_wei"] = burn_delta

    # Step 4 — restore the original stakeAmount so the contract returns to
    # its pre-test configuration.
    logger.info("[4/4] setStakeAmount(2, 2 ETH) — restore")
    r4 = _send(staking.functions.setStakeAmount(LAYER_BENCHMARK, ORIGINAL_STAKE_WEI),
               gov, w3, chain_id)
    results["steps"].append({"name": "setStakeAmount_restore", "tx": r4["tx_hex"],
                             "block": r4["blockNumber"]})
    sa_final = staking.functions.stakeAmount(LAYER_BENCHMARK).call()
    assert sa_final == ORIGINAL_STAKE_WEI, \
        f"restore failed: {sa_final} != {ORIGINAL_STAKE_WEI}"
    results["stake_amount_restored"] = True

    # Final accounting.
    f2_bal_after = w3.eth.get_balance(f2.address)
    gov_bal_after = w3.eth.get_balance(gov.address)
    f2_spent = f2_bal_before - f2_bal_after
    gov_spent = gov_bal_before - gov_bal_after
    logger.info("==== summary ====")
    logger.info("  F2 spent: %.6f ETH (stake + gas)", f2_spent / 1e18)
    logger.info("  gov spent: %.6f ETH (gas across 3 governance txs)", gov_spent / 1e18)
    logger.info("  burned:   %.6f ETH (to %s)", burn_delta / 1e18, BURN_SINK)
    logger.info("  stake_amount restored to %s ETH", ORIGINAL_STAKE_WEI / 1e18)

    results["f2_spent_wei"] = f2_spent
    results["gov_spent_wei"] = gov_spent

    out = repo / "pwm-team/coordination/agent-coord/reviews/phase_d_slash_test.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True))
    logger.info("wrote receipts to %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
