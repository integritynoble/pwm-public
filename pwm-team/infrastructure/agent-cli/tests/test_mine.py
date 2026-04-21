"""Tests for pwm-node mine command.

Uses a tiny real Python-file solver (echo_solver.py written to tmp_path) to
exercise the subprocess flow. pwm_scoring is not required — the command
falls back to a mock Q=0.85 when it's absent.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

from pwm_node.__main__ import main
from pwm_node.commands.mine import _build_cert_payload, _resolve_benchmark_offline, _run_solver


@pytest.fixture()
def fake_l3_dir(tmp_path) -> Path:
    """Build a genesis dir with one L3 artifact that mine can resolve."""
    root = tmp_path / "genesis"
    (root / "l3").mkdir(parents=True)
    art = {
        "artifact_id": "L3-003",
        "layer": "L3",
        "principle_number": "003",
        "title": "CASSI benchmark",
        "principle_ref": "sha256:cassi_principle",
        "spec_ref": "sha256:cassi_spec",
    }
    (root / "l3" / "L3-003.json").write_text(json.dumps(art))
    return root


@pytest.fixture()
def echo_solver(tmp_path) -> Path:
    """Write a trivial solver that just touches an output marker file."""
    p = tmp_path / "echo_solver.py"
    p.write_text(
        textwrap.dedent("""
            import argparse, pathlib, sys
            ap = argparse.ArgumentParser()
            ap.add_argument("--input", type=pathlib.Path)
            ap.add_argument("--output", type=pathlib.Path)
            args = ap.parse_args()
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "result.txt").write_text("ok")
        """).strip()
    )
    return p


@pytest.fixture()
def slow_solver(tmp_path) -> Path:
    """A solver that sleeps longer than any sane timeout."""
    p = tmp_path / "slow_solver.py"
    p.write_text(
        textwrap.dedent("""
            import time, argparse, pathlib
            ap = argparse.ArgumentParser()
            ap.add_argument("--input", type=pathlib.Path)
            ap.add_argument("--output", type=pathlib.Path)
            ap.parse_args()
            time.sleep(300)
        """).strip()
    )
    return p


@pytest.fixture()
def failing_solver(tmp_path) -> Path:
    """A solver that exits with non-zero status."""
    p = tmp_path / "fail_solver.py"
    p.write_text("import sys; sys.exit(13)")
    return p


# ───── unit tests ─────


def test_resolve_benchmark_exact_id(fake_l3_dir):
    hit = _resolve_benchmark_offline(fake_l3_dir, "L3-003")
    assert hit is not None
    art, path = hit
    assert art["artifact_id"] == "L3-003"
    assert path.name == "L3-003.json"


def test_resolve_benchmark_substring(fake_l3_dir):
    """Shorthand like 'cassi' should match against the serialized artifact."""
    hit = _resolve_benchmark_offline(fake_l3_dir, "cassi")
    assert hit is not None


def test_resolve_benchmark_miss(fake_l3_dir):
    assert _resolve_benchmark_offline(fake_l3_dir, "xyz999") is None


def test_build_cert_payload_hash_is_deterministic():
    art = {"artifact_id": "L3-003", "principle_number": "003"}
    p1 = _build_cert_payload(art, Q=0.9, gate_verdicts={"S1": "pass"})
    p2 = _build_cert_payload(art, Q=0.9, gate_verdicts={"S1": "pass"})
    assert p1["cert_hash"] == p2["cert_hash"]
    assert p1["cert_hash"].startswith("sha256:")
    assert len(p1["cert_hash"]) == 7 + 64  # 'sha256:' + 64 hex


def test_build_cert_payload_has_required_keys():
    art = {"artifact_id": "L3-003", "principle_ref": "sha256:abc", "spec_ref": "sha256:def"}
    payload = _build_cert_payload(art, Q=0.92, gate_verdicts={"S1": "pass"})
    for key in ("h_p", "h_s", "h_b", "h_x", "Q", "gate_verdicts", "cert_hash"):
        assert key in payload


def test_run_solver_echo(tmp_path, echo_solver):
    """Echo solver runs successfully; output dir gets result.txt."""
    rc, out_dir, elapsed = _run_solver(echo_solver, tmp_path, timeout_s=10)
    assert rc == 0
    assert (out_dir / "result.txt").read_text() == "ok"
    assert elapsed < 10


def test_run_solver_timeout(tmp_path, slow_solver):
    """Slow solver is killed after timeout; returns code 124."""
    rc, _, elapsed = _run_solver(slow_solver, tmp_path, timeout_s=1)
    assert rc == 124
    assert elapsed < 5  # didn't wait for sleep(300)


def test_run_solver_failure(tmp_path, failing_solver):
    """Solver that exits non-zero is reported."""
    rc, _, _ = _run_solver(failing_solver, tmp_path, timeout_s=5)
    assert rc == 13


# ───── end-to-end command tests ─────


def test_mine_benchmark_not_found(fake_l3_dir, echo_solver, capsys):
    rc = main(
        [
            "--genesis-dir", str(fake_l3_dir),
            "mine", "L3-999",
            "--solver", str(echo_solver),
            "--dry-run",
        ]
    )
    assert rc == 3
    out = capsys.readouterr().out
    assert "benchmark not found" in out


def test_mine_missing_solver(fake_l3_dir, tmp_path, capsys):
    rc = main(
        [
            "--genesis-dir", str(fake_l3_dir),
            "mine", "L3-003",
            "--solver", str(tmp_path / "does_not_exist.py"),
            "--dry-run",
        ]
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "solver path required" in out


def test_mine_solver_timeout_exit_6(fake_l3_dir, slow_solver, capsys):
    rc = main(
        [
            "--genesis-dir", str(fake_l3_dir),
            "mine", "L3-003",
            "--solver", str(slow_solver),
            "--timeout", "1",
            "--dry-run",
        ]
    )
    assert rc == 6
    out = capsys.readouterr().out
    assert "timed out" in out


def test_mine_solver_nonzero_exit_7(fake_l3_dir, failing_solver, capsys):
    rc = main(
        [
            "--genesis-dir", str(fake_l3_dir),
            "mine", "L3-003",
            "--solver", str(failing_solver),
            "--dry-run",
        ]
    )
    assert rc == 7
    out = capsys.readouterr().out
    assert "exited with code 13" in out


def test_mine_dry_run_happy_path(fake_l3_dir, echo_solver, capsys):
    """Echo solver runs, mock Q=0.85, dry-run prints payload, returns 0."""
    rc = main(
        [
            "--genesis-dir", str(fake_l3_dir),
            "mine", "L3-003",
            "--solver", str(echo_solver),
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "resolved L3-003" in out
    assert "Q = 0.850" in out or "Q = 0.8500" in out
    assert "cert_hash" in out
    assert "--dry-run: not submitting" in out
