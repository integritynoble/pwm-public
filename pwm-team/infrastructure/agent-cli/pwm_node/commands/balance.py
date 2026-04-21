"""pwm-node balance — show native ETH balance on the target network.

Uses ``PWMChain.get_balance``. Read-only, no wallet required (address can
be passed explicitly via --address). When no address is passed and no
signer is configured, prints an actionable message.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> int:
    """Print balance. Returns 0 on success, 1 on error."""
    if args.network == "offline":
        print(
            "[pwm-node balance] --network offline cannot query balances. "
            "Retry with --network testnet or mainnet."
        )
        return 1

    try:
        from pwm_node.chain import ChainError, PWMChain
    except ImportError as e:
        print(f"[pwm-node balance] chain support not available: {e}")
        return 1

    try:
        chain = PWMChain(network=args.network)
        info = chain.info()
        addr = args.address or info["signer"]
        if not addr:
            print(
                "[pwm-node balance] no --address given and no PWM_PRIVATE_KEY set. "
                "Provide one: pwm-node balance --address 0x<40hex>"
            )
            return 1
        bal = chain.get_balance(addr)
        print(f"Network: {info['network']} (chainId {info['chain_id']}, block {info['block']})")
        print(f"Address: {addr}")
        print(f"Balance: {bal:.6f} ETH")
        return 0
    except ChainError as e:
        print(f"[pwm-node balance] {e}")
        return 1
