"""pwm-node stake — stake on a principle / spec / benchmark artifact.

Sub-commands:
  stake quote <layer>                 — show required stake in ETH (view)
  stake principle <artifact_hash>     — stake on a principle
  stake spec <artifact_hash>          — stake on a spec
  stake benchmark <artifact_hash>     — stake on a benchmark

The on-chain PWMStaking contract uses a flat layer-indexed stake model:
layer 0 = principle, 1 = spec, 2 = benchmark. Amount per layer is configured
by governance via `setStakeAmount(uint8 layer, uint256 amount)`. This CLI
reads the required amount from the contract before sending the tx, so
users can't accidentally underfund.
"""
from __future__ import annotations

import argparse


_LAYER_MAP = {"principle": 0, "spec": 1, "benchmark": 2}


def run(args: argparse.Namespace) -> int:
    """Dispatch stake subcommands. Returns 0 on success."""
    if args.network == "offline":
        print("[pwm-node stake] --network offline cannot read stake contract.")
        return 1

    try:
        from pwm_node.chain import ChainError, PWMChain
    except ImportError as e:
        print(f"[pwm-node stake] chain unavailable: {e}")
        return 1

    sub = args.stake_sub

    try:
        chain = PWMChain(network=args.network)
    except ChainError as e:
        print(f"[pwm-node stake] {e}")
        return 1

    if sub == "quote":
        return _cmd_quote(chain, args)
    if sub in _LAYER_MAP:
        return _cmd_stake(chain, args, layer=_LAYER_MAP[sub])

    print(f"[pwm-node stake] unknown sub-command: {sub}")
    return 1


def _cmd_quote(chain, args: argparse.Namespace) -> int:
    """Print required stake per layer (or just one if --layer given)."""
    from pwm_node.chain import ChainError

    try:
        layers = [args.layer] if args.layer is not None else [0, 1, 2]
        print(f"Network: {chain.network} (chainId {chain.chain_id}, block {chain.block_number()})")
        print("Required stake per layer:")
        for layer in layers:
            wei = chain.stake_amount(layer)
            eth = float(chain.w3.from_wei(wei, "ether"))
            print(f"  layer {layer} ({chain._LAYER_NAMES[layer]:10}): {eth:.6f} ETH ({wei} wei)")
        return 0
    except ChainError as e:
        print(f"[pwm-node stake quote] {e}")
        return 1


def _cmd_stake(chain, args: argparse.Namespace, *, layer: int) -> int:
    """Stake on a specific artifact."""
    from pwm_node.chain import ChainError

    h = args.artifact_hash
    if not h:
        print("[pwm-node stake] --artifact-hash required.")
        return 1
    if not chain.signer_address():
        print(
            "[pwm-node stake] PWM_PRIVATE_KEY env var required for staking. "
            "Set it, then retry."
        )
        return 1

    try:
        required = chain.stake_amount(layer)
        required_eth = float(chain.w3.from_wei(required, "ether"))
        print(f"[pwm-node stake] layer {layer} ({chain._LAYER_NAMES[layer]}) requires {required_eth:.6f} ETH")
        print(f"[pwm-node stake] signer: {chain.signer_address()}")
        print(f"[pwm-node stake] artifact: {h}")

        if args.dry_run:
            print("[pwm-node stake] --dry-run: not broadcasting.")
            return 0

        tx_hash = chain.stake(layer, h, gas=args.gas)
        print(f"[pwm-node stake] tx submitted: {tx_hash}")
        if not args.no_wait:
            receipt = chain.wait_for_tx(tx_hash, timeout_s=args.timeout)
            print(
                f"[pwm-node stake] confirmed in block {receipt.get('blockNumber')}, "
                f"gas used {receipt.get('gasUsed')}"
            )
        return 0
    except ChainError as e:
        print(f"[pwm-node stake] {e}")
        return 1
