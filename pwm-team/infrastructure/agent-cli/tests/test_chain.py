"""Tests for pwm_node.chain — mocked web3 so no live RPC needed.

Covers:
- PWMChain construction resolves addresses + loads ABIs
- Missing contract addresses raise ChainError with the contract names
- Wallet resolution from PWM_PRIVATE_KEY env var
- get_balance, info read methods go through the mocked web3 interface
- Invalid private key → ChainError
- Mainnet with null addresses → ChainError with actionable message
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pwm_node.chain import CONTRACT_NAMES, ChainError, PWMChain


# ───── test fixtures ─────


@pytest.fixture()
def fake_interfaces(tmp_path, monkeypatch) -> Path:
    """Build a tmp pwm-team/coordination/agent-coord/interfaces/ tree with
    addresses.json + 7 empty-ABI files. Also chdir so auto-detect works."""
    iface = tmp_path / "pwm-team" / "coordination" / "agent-coord" / "interfaces"
    (iface / "contracts_abi").mkdir(parents=True)

    addresses = {
        "testnet": {
            "network": "sepolia",
            "chainId": 11155111,
            "PWMGovernance": "0xf5a061B18455bf4a66441B0B5B84159d69af1286",
            "PWMRegistry": "0x2375217dd8FeC420707D53C75C86e2258FBaab65",
            "PWMTreasury": "0x390eAa7bEa784cFDD17a2Fa4b27e81B097A8c1F9",
            "PWMReward": "0xcCC011Bb4f99A4545E11B8DbFbeAcbb60C374A5f",
            "PWMStaking": "0x17Fc30B22E6d0e683359e3a2D0F75Bded01A2852",
            "PWMCertificate": "0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08",
            "PWMMinting": "0x2516e21861F74D6E133b263c7297fb7c8a9B4F52",
        },
        "mainnet": {name: None for name in CONTRACT_NAMES} | {
            "network": "mainnet", "chainId": 1
        },
    }
    (iface / "addresses.json").write_text(json.dumps(addresses))

    # Minimal fake ABI — empty list is a valid ABI for contract construction
    for name in CONTRACT_NAMES:
        (iface / "contracts_abi" / f"{name}.json").write_text(json.dumps([]))

    monkeypatch.chdir(tmp_path)
    return iface


@pytest.fixture()
def mock_web3(monkeypatch):
    """Patch web3.Web3 to a mock so no real RPC is made."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 123456
    mock_w3.eth.chain_id = 11155111
    mock_w3.to_checksum_address.side_effect = lambda a: a  # pass-through
    mock_w3.from_wei.side_effect = lambda wei, unit: float(wei) / 1e18
    mock_w3.to_wei.side_effect = lambda val, unit: int(val) * int(1e9)
    # contract() returns a generic mock — tests can probe attrs as needed
    mock_w3.eth.contract.return_value = MagicMock()

    with patch("pwm_node.chain.Web3") as web3_cls:
        web3_cls.return_value = mock_w3
        web3_cls.HTTPProvider = MagicMock()
        yield mock_w3


# ───── tests ─────


def test_chain_constructs_testnet(fake_interfaces, mock_web3):
    """PWMChain constructs from fake interfaces/ + mocked web3."""
    chain = PWMChain(network="testnet")
    assert chain.network == "testnet"
    assert chain.chain_id == 11155111
    assert set(chain.contracts.keys()) == set(CONTRACT_NAMES)


def test_chain_mainnet_not_deployed_errors(fake_interfaces, mock_web3):
    """Mainnet has null addresses — should raise ChainError with actionable msg."""
    with pytest.raises(ChainError) as exc_info:
        PWMChain(network="mainnet")
    assert "Mainnet contracts not yet deployed" in str(exc_info.value)


def test_chain_bad_network_errors(fake_interfaces, mock_web3):
    """Network must be testnet or mainnet."""
    with pytest.raises(ChainError, match="must be 'testnet' or 'mainnet'"):
        PWMChain(network="arbitrum")


def test_chain_not_connected_errors(fake_interfaces):
    """When is_connected() is False, construction raises."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = False
    with patch("pwm_node.chain.Web3") as web3_cls:
        web3_cls.return_value = mock_w3
        web3_cls.HTTPProvider = MagicMock()
        with pytest.raises(ChainError, match="Cannot connect to RPC"):
            PWMChain(network="testnet")


def test_signer_address_without_key(fake_interfaces, mock_web3, monkeypatch):
    """signer_address() returns None when PWM_PRIVATE_KEY is unset."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    chain = PWMChain(network="testnet")
    assert chain.signer_address() is None


def test_signer_address_with_key(fake_interfaces, mock_web3, monkeypatch):
    """Valid PWM_PRIVATE_KEY resolves to an address."""
    # Valid test key (do NOT use in production)
    monkeypatch.setenv(
        "PWM_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    chain = PWMChain(network="testnet")
    addr = chain.signer_address()
    assert addr is not None
    assert addr.startswith("0x")
    assert len(addr) == 42


def test_invalid_private_key_errors(fake_interfaces, mock_web3, monkeypatch):
    """Malformed private key raises ChainError."""
    monkeypatch.setenv("PWM_PRIVATE_KEY", "not-a-key")
    chain = PWMChain(network="testnet")
    with pytest.raises(ChainError, match="Invalid private key"):
        chain._get_account()


def test_get_balance_uses_signer(fake_interfaces, mock_web3, monkeypatch):
    """get_balance() with no arg uses the signer address."""
    monkeypatch.setenv(
        "PWM_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    mock_web3.eth.get_balance.return_value = int(0.5 * 1e18)  # 0.5 ETH in wei
    chain = PWMChain(network="testnet")
    bal = chain.get_balance()
    assert bal == 0.5


def test_get_balance_no_address_no_signer_errors(fake_interfaces, mock_web3, monkeypatch):
    """get_balance() raises when both address arg and signer are missing."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    chain = PWMChain(network="testnet")
    with pytest.raises(ChainError, match="No address provided"):
        chain.get_balance()


def test_info_returns_summary(fake_interfaces, mock_web3, monkeypatch):
    """info() returns a dict summary of the connection."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    chain = PWMChain(network="testnet")
    info = chain.info()
    assert info["network"] == "testnet"
    assert info["chain_id"] == 11155111
    assert info["block"] == 123456
    assert info["signer"] is None
    assert set(info["contracts"].keys()) == set(CONTRACT_NAMES)


def test_custom_rpc_url_respected(fake_interfaces, monkeypatch):
    """Explicit rpc_url= overrides PWM_RPC_URL env and DEFAULT_RPCS."""
    monkeypatch.setenv("PWM_RPC_URL", "http://env-rpc")
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 0
    mock_w3.to_checksum_address.side_effect = lambda a: a
    with patch("pwm_node.chain.Web3") as web3_cls:
        web3_cls.return_value = mock_w3
        web3_cls.HTTPProvider = MagicMock()
        PWMChain(network="testnet", rpc_url="http://explicit-rpc")
        called_url = web3_cls.HTTPProvider.call_args[0][0]
        assert called_url == "http://explicit-rpc"
