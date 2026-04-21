"""Tests for pwm-node sp register command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pwm_node.__main__ import main


@pytest.fixture()
def solver_file(tmp_path) -> Path:
    p = tmp_path / "solver.py"
    p.write_text("# noop")
    return p


def test_sp_register_happy_path(tmp_path, solver_file, capsys):
    """Writes manifest file with all declared fields."""
    out = tmp_path / "manifest.json"
    rc = main([
        "sp", "register",
        "--entry-point", str(solver_file),
        "--share-ratio", "0.5",
        "--min-vram-gb", "8",
        "--framework", "pytorch",
        "--expected-runtime-s", "30",
        "--output", str(out),
    ])
    assert rc == 0
    manifest = json.loads(out.read_text())
    assert manifest["entry_point"] == str(solver_file.resolve())
    assert manifest["share_ratio_p"] == 0.5
    assert manifest["min_vram_gb"] == 8
    assert manifest["framework"] == "pytorch"
    assert manifest["expected_runtime_s"] == 30
    assert manifest["ipfs_cid"] is None


def test_sp_register_share_ratio_too_low(solver_file, capsys):
    rc = main([
        "sp", "register",
        "--entry-point", str(solver_file),
        "--share-ratio", "0.05",
    ])
    assert rc == 1
    assert "must be in [0.10, 0.90]" in capsys.readouterr().out


def test_sp_register_share_ratio_too_high(solver_file, capsys):
    rc = main([
        "sp", "register",
        "--entry-point", str(solver_file),
        "--share-ratio", "0.95",
    ])
    assert rc == 1
    assert "must be in [0.10, 0.90]" in capsys.readouterr().out


def test_sp_register_missing_entry_point(tmp_path, capsys):
    rc = main([
        "sp", "register",
        "--entry-point", str(tmp_path / "nope.py"),
        "--share-ratio", "0.5",
    ])
    assert rc == 1
    assert "file not found" in capsys.readouterr().out


def test_sp_register_default_output_location(tmp_path, solver_file, capsys, monkeypatch):
    """Without --output, writes to $HOME/.pwm-node/sp_manifest.json."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    rc = main([
        "sp", "register",
        "--entry-point", str(solver_file),
        "--share-ratio", "0.5",
    ])
    assert rc == 0
    expected = home / ".pwm-node" / "sp_manifest.json"
    assert expected.is_file()
    manifest = json.loads(expected.read_text())
    assert manifest["share_ratio_p"] == 0.5
