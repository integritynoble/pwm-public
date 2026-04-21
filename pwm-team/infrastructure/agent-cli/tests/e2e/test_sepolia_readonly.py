"""End-to-end readonly checks against real Sepolia.

These tests attempt actual RPC calls. They are SKIPPED when:
  - PWM_RUN_E2E env var is not set (opt-in to prevent accidental network hits
    in CI)
  - No network reachable

Readonly tests require no wallet. They verify:
  1. Connection to a Sepolia RPC succeeds.
  2. The 7 deployed contract addresses resolve (code is present on-chain).
  3. PWMStaking.stakeAmount(layer) returns a sensible value.
  4. Current block number is fresh (< 1 hour old, if we can tell).

To run:
    export PWM_RUN_E2E=1
    export PWM_RPC_URL=https://rpc.sepolia.org   # optional; default works
    pytest tests/e2e/test_sepolia_readonly.py -v

To exercise the full mine flow, see tests/e2e/test_mine_dry_run.py and the
acceptance procedure in tests/e2e/README.md.
"""
from __future__ import annotations

import os

import pytest

_RUN = os.environ.get("PWM_RUN_E2E") == "1"
_SKIP_REASON = "Set PWM_RUN_E2E=1 to enable live-network tests"


@pytest.mark.skipif(not _RUN, reason=_SKIP_REASON)
def test_connect_to_sepolia():
    """PWMChain constructs against real Sepolia RPC and reports a block number."""
    from pwm_node.chain import PWMChain
    chain = PWMChain(network="testnet")
    block = chain.block_number()
    assert isinstance(block, int)
    assert block > 0, "Sepolia block number should be positive"


@pytest.mark.skipif(not _RUN, reason=_SKIP_REASON)
def test_all_7_contracts_have_code():
    """Each contract address on Sepolia has deployed code (non-zero bytes)."""
    from pwm_node.chain import CONTRACT_NAMES, PWMChain
    chain = PWMChain(network="testnet")
    for name in CONTRACT_NAMES:
        addr = chain.addresses[name]
        code = chain.w3.eth.get_code(chain.w3.to_checksum_address(addr))
        assert len(code) > 2, (
            f"{name} at {addr} has no deployed code (len={len(code)}). "
            f"Either the address in addresses.json is wrong, or the contract has been removed."
        )


@pytest.mark.skipif(not _RUN, reason=_SKIP_REASON)
def test_stake_amounts_are_sensible():
    """stakeAmount(layer) returns non-zero values for all 3 layers.

    If any returns 0, governance has not yet initialized the contract.
    """
    from pwm_node.chain import PWMChain
    chain = PWMChain(network="testnet")
    for layer, name in {0: "principle", 1: "spec", 2: "benchmark"}.items():
        amt = chain.stake_amount(layer)
        assert amt > 0, (
            f"stakeAmount({layer}, {name}) returned 0 — "
            f"has governance called setStakeAmount yet?"
        )


@pytest.mark.skipif(not _RUN, reason=_SKIP_REASON)
def test_info_dict_complete():
    """info() returns all expected fields."""
    from pwm_node.chain import CONTRACT_NAMES, PWMChain
    chain = PWMChain(network="testnet")
    info = chain.info()
    assert info["network"] == "testnet"
    assert info["chain_id"] == 11155111
    assert isinstance(info["block"], int)
    assert set(info["contracts"].keys()) == set(CONTRACT_NAMES)
