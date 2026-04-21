"""Smoke tests for pwm-node CLI offline commands."""
from __future__ import annotations

from pathlib import Path

import pytest

from pwm_node.__main__ import build_parser, main


def test_parser_builds():
    """Parser constructs without error and has the mandatory subcommands."""
    p = build_parser()
    help_text = p.format_help()
    for cmd in ("benchmarks", "inspect", "verify", "mine", "submit-cert"):
        assert cmd in help_text, f"missing subcommand: {cmd}"


def test_benchmarks_lists_all(fake_genesis, capsys):
    """benchmarks command prints all L1 artifacts by default."""
    rc = main(["--genesis-dir", str(fake_genesis), "benchmarks"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "L1-001" in out
    assert "L1-003" in out
    assert "L1-004" in out
    assert "CASSI" in out
    assert "CACTI" in out


def test_benchmarks_filters_by_domain(fake_genesis, capsys):
    """--domain filter matches substring against domain + sub_domain (case-insensitive)."""
    rc = main(["--genesis-dir", str(fake_genesis), "benchmarks", "--domain", "compressive"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "L1-003" in out  # CASSI
    assert "L1-004" in out  # CACTI
    assert "L1-001" not in out  # widefield (Microscopy domain)


def test_inspect_finds_cassi(fake_genesis, capsys):
    """inspect resolves L1-003 and prints title + L_DAG."""
    rc = main(["--genesis-dir", str(fake_genesis), "inspect", "L1-003"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CASSI" in out
    assert "Compressive Imaging" in out
    assert "3.7" in out  # L_DAG
    assert "5000" in out  # κ_sys
    assert "triple-verified" in out


def test_inspect_finds_cacti(fake_genesis, capsys):
    """inspect resolves L1-004 and prints CACTI's distinct primitives + L_DAG 1.4."""
    rc = main(["--genesis-dir", str(fake_genesis), "inspect", "L1-004"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CACTI" in out
    assert "1.4" in out
    assert "S.temporal.coded" in out


def test_inspect_miss_returns_3(fake_genesis, capsys):
    """Unknown target returns exit code 3 and prints hint."""
    rc = main(["--genesis-dir", str(fake_genesis), "inspect", "L1-999"])
    assert rc == 3
    out = capsys.readouterr().out
    assert "no offline match" in out


def test_verify_missing_file_returns_1(tmp_path, capsys):
    """verify with a non-existent benchmark yaml returns exit 1."""
    rc = main(["verify", str(tmp_path / "does_not_exist.yaml")])
    assert rc == 1


def test_verify_minimal_yaml_returns_0(tmp_path, capsys):
    """verify with a yaml containing the required 5 fields returns 0 (structural pass)."""
    bench = tmp_path / "minimal.yaml"
    bench.write_text(
        "principle_ref: sha256:<test>\n"
        "omega:\n  H: 512\nE:\n  forward: y = x\n"
        "O: [PSNR]\n"
        "epsilon_fn: '25.0'\n"
    )
    rc = main(["verify", str(bench)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PASS" in out


def test_verify_missing_fields_returns_4(tmp_path, capsys):
    """verify with a yaml missing required fields returns 4."""
    bench = tmp_path / "incomplete.yaml"
    bench.write_text("omega:\n  H: 512\n")  # missing principle_ref, E, O, epsilon_fn
    rc = main(["verify", str(bench)])
    assert rc == 4


def test_chain_stub_returns_2(capsys):
    """Chain-dependent commands (mine, submit-cert) print deferral notice and return 2."""
    rc = main(["mine", "cassi/t1_nominal"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "not implemented yet" in err
