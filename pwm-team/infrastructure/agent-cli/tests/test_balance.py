"""Tests for pwm-node balance command — uses the mocked web3 fixture from test_chain."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pwm_node.__main__ import main


# Reuse fixtures from test_chain.py by importing them via conftest isn't possible
# across files without re-declaring. Duplicate the essentials here, minimally.


@pytest.fixture()
def fake_interfaces(tmp_path, monkeypatch):
    """Minimal fake interfaces tree for testnet only."""
    import json

    from pwm_node.chain import CONTRACT_NAMES

    iface = tmp_path / "pwm-team" / "coordination" / "agent-coord" / "interfaces"
    (iface / "contracts_abi").mkdir(parents=True)
    addresses = {
        "testnet": {
            "network": "sepolia",
            "chainId": 11155111,
            **{name: f"0x{'a' * 40}" for name in CONTRACT_NAMES},
        },
        "mainnet": {name: None for name in CONTRACT_NAMES} | {"network": "mainnet", "chainId": 1},
    }
    (iface / "addresses.json").write_text(json.dumps(addresses))
    for name in CONTRACT_NAMES:
        (iface / "contracts_abi" / f"{name}.json").write_text("[]")
    monkeypatch.chdir(tmp_path)
    return iface


@pytest.fixture()
def mock_web3(monkeypatch):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 777888
    mock_w3.eth.chain_id = 11155111
    mock_w3.to_checksum_address.side_effect = lambda a: a
    mock_w3.from_wei.side_effect = lambda wei, unit: float(wei) / 1e18
    mock_w3.to_wei.side_effect = lambda val, unit: int(val) * int(1e9)
    mock_w3.eth.contract.return_value = MagicMock()

    with patch("pwm_node.chain.Web3") as web3_cls:
        web3_cls.return_value = mock_w3
        web3_cls.HTTPProvider = MagicMock()
        yield mock_w3


def test_balance_offline_network_refuses(capsys, monkeypatch):
    """balance --network offline should refuse clearly."""
    rc = main(["--network", "offline", "balance", "--address", "0x" + "a" * 40])
    assert rc == 1
    out = capsys.readouterr().out
    assert "cannot query balances" in out


def test_balance_with_address(fake_interfaces, mock_web3, capsys, monkeypatch):
    """balance --network testnet --address <x> → prints ETH."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    mock_web3.eth.get_balance.return_value = int(1.25 * 1e18)  # 1.25 ETH
    rc = main(
        ["--network", "testnet", "balance", "--address", "0x" + "b" * 40]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Network: testnet" in out
    assert "chainId 11155111" in out
    assert "block 777888" in out
    assert "1.250000 ETH" in out


def test_balance_no_signer_no_address_errors(fake_interfaces, mock_web3, capsys, monkeypatch):
    """balance without --address and without PWM_PRIVATE_KEY → error."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    rc = main(["--network", "testnet", "balance"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "no --address" in out


def test_balance_uses_signer_when_no_address(fake_interfaces, mock_web3, capsys, monkeypatch):
    """With PWM_PRIVATE_KEY set and no --address, uses signer address."""
    monkeypatch.setenv(
        "PWM_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    mock_web3.eth.get_balance.return_value = int(0.02 * 1e18)
    rc = main(["--network", "testnet", "balance"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "0.020000 ETH" in out
