"""Tests for pwm-node submit-cert command — 12-field SubmitArgs schema."""
from __future__ import annotations

import json

import pytest

from pwm_node.__main__ import main
from pwm_node.commands.submit import _validate_cert


_VALID_ADDR = "0x0c566f0F87cD062C3DE95943E50d572c74A87dEd"
_ZERO_ADDR = "0x" + "0" * 40
_BH = "0x" + "dc" * 32  # 0xdcdc... — valid bytes32
_CH = "0x" + "ff" * 32


def _valid_payload() -> dict:
    return {
        "certHash": _CH,
        "benchmarkHash": _BH,
        "principleId": 3,
        "l1Creator": _VALID_ADDR,
        "l2Creator": _VALID_ADDR,
        "l3Creator": _VALID_ADDR,
        "acWallet": _VALID_ADDR,
        "cpWallet": _VALID_ADDR,
        "shareRatioP": 5000,
        "Q_int": 85,
        "delta": 3,
        "rank": 0,
    }


# ───── validator unit tests ─────


def test_validate_cert_complete_payload():
    assert _validate_cert(_valid_payload()) == []


def test_validate_cert_missing_keys_reports_each():
    errors = _validate_cert({"certHash": _CH})
    # 11 of the 12 fields are missing
    assert len(errors) == 11
    assert any("benchmarkHash" in e for e in errors)
    assert any("shareRatioP" in e for e in errors)


def test_validate_cert_bytes32_rejects_wrong_length():
    p = _valid_payload()
    p["certHash"] = "0xabc"  # too short
    errors = _validate_cert(p)
    assert any("certHash" in e and "64 hex" in e for e in errors)


def test_validate_cert_address_rejects_wrong_shape():
    p = _valid_payload()
    p["l1Creator"] = "not-an-address"
    errors = _validate_cert(p)
    assert any("l1Creator" in e and "40 hex" in e for e in errors)


def test_validate_cert_rejects_zero_address():
    p = _valid_payload()
    p["cpWallet"] = _ZERO_ADDR
    errors = _validate_cert(p)
    assert any("cpWallet" in e and "zero address" in e for e in errors)


def test_validate_cert_share_ratio_out_of_range():
    """shareRatioP must be within the contract-enforced [1000, 9000] band."""
    for bad in (0, 500, 999, 9001, 10_000, 20_000):
        p = _valid_payload()
        p["shareRatioP"] = bad
        errors = _validate_cert(p)
        assert any("shareRatioP" in e and "[1000, 9000]" in e for e in errors), \
            f"expected rejection for shareRatioP={bad}, got {errors}"


def test_validate_cert_q_int_out_of_range():
    p = _valid_payload()
    p["Q_int"] = 150
    errors = _validate_cert(p)
    assert any("Q_int" in e and "[0, 100]" in e for e in errors)


def test_validate_cert_rejects_bool_for_int_field():
    p = _valid_payload()
    p["delta"] = True  # bool is an instance of int in Python — must be rejected
    errors = _validate_cert(p)
    assert any("delta" in e and "integer" in e for e in errors)


# ───── end-to-end command tests ─────


def test_submit_offline_network_refuses(tmp_path, capsys):
    cert = tmp_path / "cert.json"
    cert.write_text("{}")
    rc = main(["--network", "offline", "submit-cert", "--cert", str(cert)])
    assert rc == 1
    assert "cannot submit" in capsys.readouterr().out


def test_submit_missing_file_errors(tmp_path, capsys):
    rc = main(
        ["--network", "testnet", "submit-cert", "--cert", str(tmp_path / "missing.json")]
    )
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_submit_invalid_json_errors(tmp_path, capsys):
    cert = tmp_path / "broken.json"
    cert.write_text("{not valid json")
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert)])
    assert rc == 1
    assert "invalid JSON" in capsys.readouterr().out


def test_submit_validation_fail_returns_4(tmp_path, capsys):
    """Missing required cert keys → exit 4."""
    cert = tmp_path / "incomplete.json"
    cert.write_text(json.dumps({"certHash": _CH}))
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert)])
    assert rc == 4
    out = capsys.readouterr().out
    assert "validation failed" in out
    assert "benchmarkHash" in out


def test_submit_dry_run_no_chain_call(tmp_path, capsys):
    """--dry-run validates the 12-field payload and exits 0 without touching chain."""
    cert = tmp_path / "full.json"
    cert.write_text(json.dumps(_valid_payload()))
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--dry-run: would submit" in out
    assert _CH in out  # certHash echoed


def test_submit_drops_meta_before_validation(tmp_path):
    """Payloads from `mine` include a _meta block; submit must strip it."""
    cert = tmp_path / "with_meta.json"
    payload = _valid_payload() | {"_meta": {"artifact_id": "L3-003", "Q_float": 0.85}}
    cert.write_text(json.dumps(payload))
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert), "--dry-run"])
    assert rc == 0
