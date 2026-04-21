"""Tests for pwm-node stake command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pwm_node.__main__ import main


@pytest.fixture()
def fake_interfaces(tmp_path, monkeypatch):
    """Minimal testnet interfaces tree."""
    from pwm_node.chain import CONTRACT_NAMES

    iface = tmp_path / "pwm-team" / "coordination" / "agent-coord" / "interfaces"
    (iface / "contracts_abi").mkdir(parents=True)
    addresses = {
        "testnet": {
            "network": "sepolia", "chainId": 11155111,
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
def mock_chain_with_stake(fake_interfaces, monkeypatch):
    """Mock PWMChain with stake_amount returning known wei values."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 100
    mock_w3.to_checksum_address.side_effect = lambda a: a
    mock_w3.from_wei.side_effect = lambda wei, unit: float(wei) / 1e18
    mock_w3.to_wei.side_effect = lambda val, unit: int(val) * int(1e9)

    # PWMStaking.stakeAmount returns: layer 0 → 0.1 ETH, layer 1 → 0.05 ETH, layer 2 → 0.02 ETH
    staking_contract = MagicMock()
    stake_amt_fn = MagicMock()
    stake_amt_fn.call.side_effect = lambda: None  # never called directly
    # More realistic: functions.stakeAmount(layer).call()
    staking_contract.functions.stakeAmount.side_effect = lambda layer: MagicMock(
        call=MagicMock(return_value={0: int(0.1 * 1e18), 1: int(0.05 * 1e18), 2: int(0.02 * 1e18)}[layer])
    )

    # Other contracts can just be generic mocks
    def _contract_factory(*args, **kwargs):
        addr = kwargs.get("address", "0x")
        from pwm_node.chain import CONTRACT_NAMES  # noqa
        # Treat the PWMStaking address specially
        # The test fixture assigns the same 0xaa... to all 7 contracts, so we can't distinguish
        # by address here. Instead return a wrapper that exposes stakeAmount always.
        c = MagicMock()
        c.functions = staking_contract.functions
        return c

    mock_w3.eth.contract.side_effect = _contract_factory

    with patch("pwm_node.chain.Web3") as web3_cls:
        web3_cls.return_value = mock_w3
        web3_cls.HTTPProvider = MagicMock()
        yield mock_w3


# ───── tests ─────


def test_stake_offline_network_refuses(capsys):
    rc = main(["--network", "offline", "stake", "quote"])
    assert rc == 1
    assert "cannot read stake contract" in capsys.readouterr().out


def test_stake_quote_all_layers(mock_chain_with_stake, capsys, monkeypatch):
    """stake quote → prints all 3 layers."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    rc = main(["--network", "testnet", "stake", "quote"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "layer 0 (principle" in out
    assert "layer 1 (spec" in out
    assert "layer 2 (benchmark" in out
    assert "0.100000 ETH" in out  # principle
    assert "0.050000 ETH" in out  # spec
    assert "0.020000 ETH" in out  # benchmark


def test_stake_quote_single_layer(mock_chain_with_stake, capsys, monkeypatch):
    """stake quote --layer 1 → prints just spec layer."""
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    rc = main(["--network", "testnet", "stake", "quote", "--layer", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "layer 1 (spec" in out
    assert "layer 0" not in out
    assert "layer 2" not in out


def test_stake_spec_no_signer_errors(mock_chain_with_stake, capsys, monkeypatch):
    monkeypatch.delenv("PWM_PRIVATE_KEY", raising=False)
    rc = main(["--network", "testnet", "stake", "spec", "0x" + "b" * 64])
    assert rc == 1
    assert "PWM_PRIVATE_KEY" in capsys.readouterr().out


def test_stake_spec_dry_run(mock_chain_with_stake, capsys, monkeypatch):
    """dry-run prints plan and returns 0 without calling stake()."""
    monkeypatch.setenv(
        "PWM_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    rc = main(
        [
            "--network", "testnet",
            "stake", "spec", "0x" + "c" * 64,
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "layer 1 (spec)" in out
    assert "0.050000 ETH" in out
    assert "not broadcasting" in out
