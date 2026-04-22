"""Post-deploy verification for a PWM L2 (or Sepolia) deployment.

After running ``npx hardhat run deploy/l2.js --network <net>``, run this
script to confirm:

  1. All 7 contract addresses are populated in ``addresses.json[<net>]``
     with non-zero bytecode on-chain.
  2. Cross-contract wiring is correct:
       PWMReward     → certificate, staking, minting, treasury
       PWMCertificate→ registry, reward, minting
       PWMMinting    → certificate, reward
       PWMStaking    → reward
       PWMTreasury   → reward
  3. Governance is set (initially to the deployer).
  4. Stake amounts are sensible (per-layer).
  5. The chain's chainId matches what addresses.json declares.

Exits non-zero on any check failure so CI or a shell pipeline can gate
on it.

Usage:
    export PWM_RPC_URL=https://sepolia.base.org
    python3 scripts/verify_l2_deploy.py --network baseSepolia
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("verify_l2")


SUPPORTED_SLOTS = (
    "testnet", "mainnet",
    "base", "baseSepolia",
    "arbitrum", "arbSepolia",
    "optimism",
    "local",
)


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("Cannot find repo root")


def _load_abi(repo_root: Path, name: str) -> list:
    path = repo_root / "pwm-team/coordination/agent-coord/interfaces/contracts_abi" / f"{name}.json"
    raw = json.loads(path.read_text())
    return raw if isinstance(raw, list) else raw.get("abi", [])


def _check(condition: bool, ok_msg: str, fail_msg: str, errors: list) -> bool:
    if condition:
        logger.info(f"  ✓ {ok_msg}")
        return True
    logger.error(f"  ✗ {fail_msg}")
    errors.append(fail_msg)
    return False


def run(args: argparse.Namespace) -> int:
    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed. pip install web3")
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL env var required")
        return 1

    if args.network not in SUPPORTED_SLOTS:
        logger.error(f"--network must be one of: {SUPPORTED_SLOTS}")
        return 1

    repo = _repo_root()
    addresses = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/addresses.json").read_text()
    )
    slot = addresses.get(args.network, {})
    if not slot:
        logger.error(f"addresses.json has no slot for {args.network}")
        return 2
    declared_chain_id = slot.get("chainId")
    logger.info(f"verifying slot {args.network} (declared chainId {declared_chain_id})")

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to RPC {rpc_url}")
        return 2
    live_chain_id = w3.eth.chain_id

    errors: list[str] = []

    # Check 1: chainId matches.
    _check(
        declared_chain_id == live_chain_id,
        f"chainId matches ({live_chain_id})",
        f"chainId mismatch: addresses.json says {declared_chain_id}, RPC reports {live_chain_id}",
        errors,
    )

    # Check 2: all 7 addresses present, and each has bytecode on-chain.
    expected = ("PWMGovernance", "PWMRegistry", "PWMTreasury", "PWMReward",
                "PWMStaking", "PWMCertificate", "PWMMinting")
    contracts = {}
    for name in expected:
        addr = slot.get(name)
        if not (isinstance(addr, str) and addr.startswith("0x") and int(addr, 16) != 0):
            errors.append(f"{name}: address missing or zero in addresses.json[{args.network}]")
            logger.error(f"  ✗ {name}: address missing or zero")
            continue
        code = w3.eth.get_code(w3.to_checksum_address(addr))
        if len(code) < 10:
            errors.append(f"{name}: no bytecode at {addr}")
            logger.error(f"  ✗ {name} @ {addr}: no bytecode on-chain")
            continue
        logger.info(f"  ✓ {name} @ {addr}: {len(code)} bytes of bytecode")
        contracts[name] = w3.eth.contract(
            address=w3.to_checksum_address(addr),
            abi=_load_abi(repo, name),
        )

    if len(contracts) != len(expected):
        logger.error("not all contracts present; skipping wiring checks")
        return 3

    # Check 3: cross-contract wiring.
    logger.info("verifying cross-contract wiring...")
    reward = contracts["PWMReward"]
    cert = contracts["PWMCertificate"]
    minting = contracts["PWMMinting"]
    staking = contracts["PWMStaking"]
    treasury = contracts["PWMTreasury"]
    reg_addr = contracts["PWMRegistry"].address

    def _eq(a: str, b: str) -> bool:
        return a.lower() == b.lower()

    try:
        _check(_eq(reward.functions.certificate().call(), cert.address),
               "PWMReward.certificate = PWMCertificate",
               "PWMReward.certificate mismatch", errors)
    except Exception as e:
        errors.append(f"PWMReward.certificate() call failed: {e}")
    try:
        _check(_eq(reward.functions.staking().call(), staking.address),
               "PWMReward.staking = PWMStaking",
               "PWMReward.staking mismatch", errors)
    except Exception as e:
        errors.append(f"PWMReward.staking() call failed: {e}")
    try:
        _check(_eq(reward.functions.minting().call(), minting.address),
               "PWMReward.minting = PWMMinting",
               "PWMReward.minting mismatch", errors)
    except Exception as e:
        errors.append(f"PWMReward.minting() call failed: {e}")
    try:
        _check(_eq(reward.functions.treasury().call(), treasury.address),
               "PWMReward.treasury = PWMTreasury",
               "PWMReward.treasury mismatch", errors)
    except Exception as e:
        errors.append(f"PWMReward.treasury() call failed: {e}")
    try:
        _check(_eq(cert.functions.registry().call(), reg_addr),
               "PWMCertificate.registry = PWMRegistry",
               "PWMCertificate.registry mismatch", errors)
    except Exception as e:
        errors.append(f"PWMCertificate.registry() call failed: {e}")
    try:
        _check(_eq(cert.functions.reward().call(), reward.address),
               "PWMCertificate.reward = PWMReward",
               "PWMCertificate.reward mismatch", errors)
    except Exception as e:
        errors.append(f"PWMCertificate.reward() call failed: {e}")
    try:
        _check(_eq(cert.functions.minting().call(), minting.address),
               "PWMCertificate.minting = PWMMinting",
               "PWMCertificate.minting mismatch", errors)
    except Exception as e:
        errors.append(f"PWMCertificate.minting() call failed: {e}")
    try:
        _check(_eq(minting.functions.certificate().call(), cert.address),
               "PWMMinting.certificate = PWMCertificate",
               "PWMMinting.certificate mismatch", errors)
    except Exception as e:
        errors.append(f"PWMMinting.certificate() call failed: {e}")
    try:
        _check(_eq(minting.functions.reward().call(), reward.address),
               "PWMMinting.reward = PWMReward",
               "PWMMinting.reward mismatch", errors)
    except Exception as e:
        errors.append(f"PWMMinting.reward() call failed: {e}")
    try:
        _check(_eq(staking.functions.reward().call(), reward.address),
               "PWMStaking.reward = PWMReward",
               "PWMStaking.reward mismatch", errors)
    except Exception as e:
        errors.append(f"PWMStaking.reward() call failed: {e}")
    try:
        _check(_eq(treasury.functions.reward().call(), reward.address),
               "PWMTreasury.reward = PWMReward",
               "PWMTreasury.reward mismatch", errors)
    except Exception as e:
        errors.append(f"PWMTreasury.reward() call failed: {e}")

    # Check 4: governance addresses set + consistent across contracts that have
    # an onlyGovernance modifier.
    logger.info("verifying governance setup...")
    try:
        gov_staking = staking.functions.governance().call()
        gov_reward = reward.functions.governance().call()
        gov_cert = cert.functions.governance().call()
        gov_minting = minting.functions.governance().call()
        gov_treasury = treasury.functions.governance().call()
        logger.info(f"  PWMStaking.governance   = {gov_staking}")
        logger.info(f"  PWMReward.governance    = {gov_reward}")
        logger.info(f"  PWMCertificate.governance = {gov_cert}")
        logger.info(f"  PWMMinting.governance   = {gov_minting}")
        logger.info(f"  PWMTreasury.governance  = {gov_treasury}")
        all_same = len({gov_staking.lower(), gov_reward.lower(), gov_cert.lower(),
                        gov_minting.lower(), gov_treasury.lower()}) == 1
        _check(all_same,
               "all 5 governance-gated contracts agree on governance address",
               "governance addresses diverge across contracts",
               errors)
    except Exception as e:
        errors.append(f"governance() probe failed: {e}")

    # Check 5: stake amounts.
    logger.info("verifying stake amounts (informational)...")
    try:
        for layer, name in [(0, "L1 Principle"), (1, "L2 Spec"), (2, "L3 Benchmark")]:
            amt_wei = staking.functions.stakeAmount(layer).call()
            logger.info(f"  stakeAmount[{layer}] ({name}) = {w3.from_wei(amt_wei, 'ether')} ETH")
    except Exception as e:
        errors.append(f"stakeAmount probe failed: {e}")

    # Result.
    if errors:
        logger.error(f"==== VERIFICATION FAILED: {len(errors)} error(s) ====")
        for e in errors:
            logger.error(f"  - {e}")
        return 1
    logger.info("==== VERIFICATION PASSED ====")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify a PWM L2/testnet deployment on-chain")
    ap.add_argument("--network", required=True, choices=sorted(SUPPORTED_SLOTS),
                    help="Slot in addresses.json to verify against the live RPC")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
