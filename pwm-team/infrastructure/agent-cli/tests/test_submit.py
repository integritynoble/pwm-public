"""Tests for pwm-node submit-cert command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pwm_node.__main__ import main
from pwm_node.commands.submit import _validate_cert


# ───── unit tests on validator ─────


def test_validate_cert_complete_payload():
    """Valid payload returns empty error list."""
    payload = {
        "cert_hash": "sha256:abc",
        "h_p": "sha256:p",
        "h_s": "sha256:s",
        "h_b": "sha256:b",
        "h_x": "sha256:x",
        "Q": 0.95,
        "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"},
    }
    assert _validate_cert(payload) == []


def test_validate_cert_missing_keys():
    """Missing required keys are reported individually."""
    payload = {"cert_hash": "sha256:abc", "Q": 0.9}
    errors = _validate_cert(payload)
    assert len(errors) >= 5  # 5+ missing keys
    assert any("h_p" in e for e in errors)
    assert any("gate_verdicts" in e for e in errors)


def test_validate_cert_bad_q_type():
    """Q must be numeric."""
    payload = {
        "cert_hash": "a", "h_p": "b", "h_s": "c", "h_b": "d", "h_x": "e",
        "Q": "high", "gate_verdicts": {},
    }
    errors = _validate_cert(payload)
    assert any("Q must be int or float" in e for e in errors)


def test_validate_cert_q_out_of_range():
    """Q must be in [0, 1]."""
    payload = {
        "cert_hash": "a", "h_p": "b", "h_s": "c", "h_b": "d", "h_x": "e",
        "Q": 1.5, "gate_verdicts": {},
    }
    errors = _validate_cert(payload)
    assert any("Q must be in [0.0, 1.0]" in e for e in errors)


def test_validate_cert_bad_gate_verdicts():
    """gate_verdicts must be dict."""
    payload = {
        "cert_hash": "a", "h_p": "b", "h_s": "c", "h_b": "d", "h_x": "e",
        "Q": 0.5, "gate_verdicts": ["S1", "S2"],
    }
    errors = _validate_cert(payload)
    assert any("gate_verdicts must be a dict" in e for e in errors)


# ───── end-to-end command tests ─────


def test_submit_offline_network_refuses(tmp_path, capsys):
    cert = tmp_path / "cert.json"
    cert.write_text("{}")
    rc = main(["--network", "offline", "submit-cert", "--cert", str(cert)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "cannot submit" in out


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
    """Missing required cert keys → exit 4 (matches verify convention)."""
    cert = tmp_path / "incomplete.json"
    cert.write_text(json.dumps({"cert_hash": "x"}))
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert)])
    assert rc == 4
    out = capsys.readouterr().out
    assert "validation failed" in out
    assert "h_p" in out


def test_submit_dry_run_no_chain_call(tmp_path, capsys):
    """--dry-run prints payload and returns 0 without touching chain."""
    cert = tmp_path / "full.json"
    cert.write_text(
        json.dumps({
            "cert_hash": "sha256:abc",
            "h_p": "sha256:p",
            "h_s": "sha256:s",
            "h_b": "sha256:b",
            "h_x": "sha256:x",
            "Q": 0.92,
            "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"},
        })
    )
    rc = main(["--network", "testnet", "submit-cert", "--cert", str(cert), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--dry-run: would submit" in out
    assert "sha256:abc" in out
