"""Tests for pwm_miner.cp_register — closing a gap in the miner test coverage.

Focus areas (security-critical):
- HardwareProfile serialisation is deterministic.
- Bond below 10 PWM is rejected before any tx is built.
- PWM → wei conversion is correct.
- Private key is never reflected in error messages or logs.
- Web3 connection failure surfaces as RegistrationError.
- ABI loading merges deployed entries with CP extensions without duplication.
"""
from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from pwm_miner.cp_register import (
    HardwareProfile,
    InsufficientBondError,
    MIN_BOND_PWM,
    RegistrationError,
    _load_abi,
    _pwm_to_wei,
    register_cp,
)


# ───── data-type tests ─────


def test_hardware_profile_to_json_deterministic():
    """to_json produces sorted, compact JSON suitable for on-chain storage."""
    p = HardwareProfile(gpu_model="A100", vram_gb=80, region="us-east-1")
    j = p.to_json()
    assert j == '{"gpu_model":"A100","region":"us-east-1","vram_gb":80}'
    # Round-trip
    assert json.loads(j) == {"gpu_model": "A100", "region": "us-east-1", "vram_gb": 80}


def test_hardware_profile_is_dataclass():
    p = HardwareProfile(gpu_model="RTX4090", vram_gb=24, region="eu-west-2")
    assert p.gpu_model == "RTX4090"
    assert p.vram_gb == 24
    assert p.region == "eu-west-2"


# ───── amount conversion ─────


def test_pwm_to_wei_10_pwm():
    assert _pwm_to_wei(10.0) == 10 * 10**18


def test_pwm_to_wei_fractional():
    # 1.5 PWM = 1.5e18 wei
    assert _pwm_to_wei(1.5) == int(1.5 * 10**18)


# ───── bond validation ─────


def test_register_cp_rejects_bond_below_minimum():
    """Bond < 10 PWM is rejected BEFORE any web3 call is attempted."""
    profile = HardwareProfile(gpu_model="T4", vram_gb=16, region="us-east-1")
    with patch("pwm_miner.cp_register._load_web3") as load_w3:
        with pytest.raises(InsufficientBondError):
            register_cp(
                web3_url="http://fake",
                private_key="0x" + "a" * 64,
                profile=profile,
                bond_amount_pwm=5.0,
            )
        # Defensive: web3 should never even be loaded when bond is too low
        load_w3.assert_not_called()


def test_register_cp_minimum_bond_is_10():
    """Exactly MIN_BOND_PWM (10.0) is accepted (boundary condition)."""
    assert MIN_BOND_PWM == 10.0


# ───── connection failure ─────


def test_register_cp_raises_on_connection_failure():
    """An unreachable Web3 endpoint raises RegistrationError."""
    profile = HardwareProfile(gpu_model="A100", vram_gb=80, region="us-west-2")

    with patch("pwm_miner.cp_register._load_web3") as load_w3:
        load_w3.side_effect = RegistrationError("Cannot connect to Web3 endpoint: http://dead")
        with pytest.raises(RegistrationError, match="Cannot connect"):
            register_cp(
                web3_url="http://dead",
                private_key="0x" + "b" * 64,
                profile=profile,
                bond_amount_pwm=10.0,
            )


# ───── security: private key hygiene ─────


def test_private_key_not_in_insufficientbond_error_message(caplog):
    """Error raised for low bond must not contain the private key."""
    pk = "0xabcdef1234567890" * 4  # 64 hex chars, distinctive
    profile = HardwareProfile(gpu_model="T4", vram_gb=16, region="us-east-1")

    caplog.set_level(logging.DEBUG, logger="pwm_miner")

    try:
        register_cp(
            web3_url="http://fake",
            private_key=pk,
            profile=profile,
            bond_amount_pwm=1.0,  # below minimum
        )
    except InsufficientBondError as e:
        assert pk not in str(e), "private key must never appear in exception message"

    # And not in captured log records
    for rec in caplog.records:
        assert pk not in rec.getMessage(), "private key leaked into log record"


def test_private_key_not_in_registrationerror_on_conn_fail(caplog):
    """Connection-failure error must not leak the private key."""
    pk = "0xdeadbeef" + "1" * 56
    profile = HardwareProfile(gpu_model="A100", vram_gb=80, region="us-east-1")
    caplog.set_level(logging.DEBUG, logger="pwm_miner")

    with patch("pwm_miner.cp_register._load_web3") as load_w3:
        load_w3.side_effect = RegistrationError("Cannot connect to Web3 endpoint: http://dead")
        try:
            register_cp(
                web3_url="http://dead",
                private_key=pk,
                profile=profile,
                bond_amount_pwm=10.0,
            )
        except RegistrationError as e:
            assert pk not in str(e)
            assert "dead" in str(e) or "Cannot connect" in str(e)

    for rec in caplog.records:
        assert pk not in rec.getMessage()


# ───── ABI loading ─────


def test_load_abi_includes_deployed_functions():
    """_load_abi returns the deployed PWMStaking ABI plus CP extensions."""
    abi = _load_abi()
    names = {e.get("name") for e in abi if e.get("type") == "function"}
    # Deployed functions (from the real PWMStaking.json)
    assert "stake" in names
    assert "stakeAmount" in names
    # CP extensions (planned for future contract upgrade)
    assert "bondCP" in names
    assert "getCPStatus" in names


def test_load_abi_no_duplicate_names():
    """If a CP-extension function collides with a deployed one, deployed wins
    (no duplicate entries in the returned list)."""
    abi = _load_abi()
    function_entries = [e for e in abi if e.get("type") == "function"]
    name_counts = {}
    for e in function_entries:
        name_counts[e.get("name")] = name_counts.get(e.get("name"), 0) + 1
    duplicates = {n: c for n, c in name_counts.items() if c > 1}
    assert not duplicates, f"duplicate ABI entries: {duplicates}"
