"""Smoke tests for pwm-node CLI offline commands."""
from __future__ import annotations

from pathlib import Path

import pytest

from pwm_node.__main__ import build_parser, main


def test_parser_builds():
    """Parser constructs without error and has the mandatory subcommands."""
    p = build_parser()
    help_text = p.format_help()
    for cmd in ("benchmarks", "principles", "inspect", "verify", "mine", "submit-cert"):
        assert cmd in help_text, f"missing subcommand: {cmd}"


def test_benchmarks_lists_l3_artifacts(fake_genesis, capsys):
    """Per smoke-test F1: `benchmarks` walks genesis/l3/ and lists L3
    artifacts with parent L1/L2 IDs and tier/baseline data."""
    rc = main(["--genesis-dir", str(fake_genesis), "benchmarks"])
    assert rc == 0
    out = capsys.readouterr().out
    # L3 IDs are the headline content for `benchmarks`.
    assert "L3-003" in out
    assert "L3-004" in out
    # Parent L1 IDs surface in the `L1` column.
    assert "L1-003" in out
    assert "L1-004" in out
    # T1 epsilon and baseline data appear.
    assert "28.0" in out  # CASSI L3-003 T1 epsilon
    assert "GAP-TV" in out  # CASSI T1 baseline name
    # NOT listing the L1-only widefield principle.
    assert "L1-001" not in out


def test_benchmarks_filters_by_substring(fake_genesis, capsys):
    """`benchmarks --domain <sub>` filters L3s by title/slug substring."""
    rc = main(["--genesis-dir", str(fake_genesis), "benchmarks", "--domain", "cassi"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "L3-003" in out  # CASSI matches
    assert "L3-004" not in out  # CACTI excluded


def test_principles_lists_l1_artifacts(fake_genesis, capsys):
    """The new `principles` subcommand inherits the historical `benchmarks`
    behaviour — walks genesis/l1/ and prints L1 artifacts. Smoke-test F1."""
    rc = main(["--genesis-dir", str(fake_genesis), "principles"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "L1-001" in out  # widefield
    assert "L1-003" in out  # CASSI
    assert "L1-004" in out  # CACTI
    # Domain column shows L1 fields.
    assert "Compressive Imaging" in out
    assert "Microscopy" in out


def test_principles_filters_by_domain(fake_genesis, capsys):
    """`principles --domain compressive` filters by L1 domain field."""
    rc = main(["--genesis-dir", str(fake_genesis), "principles", "--domain", "compressive"])
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


def test_inspect_l3_renders_l3_specific_fields(fake_genesis, capsys):
    """Regression for smoke-test finding F3 (2026-05-03):
    `inspect L3-003` must surface the L3-specific fields, not just the
    universal title block. Specifically it must print:
      - parent_l1, parent_l2 references
      - dataset_registry.primary
      - first ibenchmarks tier with its epsilon
    Smoke-test success criteria from
    PWM_PUBLIC_REPO_SMOKE_TEST_2026-05-03.md.
    """
    rc = main(["--genesis-dir", str(fake_genesis), "inspect", "L3-003"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "L1-003" in out, "parent_l1 not rendered for L3 inspect"
    assert "L2-003" in out, "parent_l2 not rendered for L3 inspect"
    assert "KAIST" in out, "dataset_registry.primary not rendered"
    assert "T1_nominal" in out, "ibenchmarks[0].tier not rendered"
    assert "28.0" in out, "ibenchmarks[0].epsilon not rendered"


def test_inspect_l3_does_not_print_l1_only_fields_as_question_marks(fake_genesis, capsys):
    """L3 manifests don't have `domain` / `difficulty_tier` / `difficulty_delta` —
    the renderer must NOT print them as bare '?' for L3 (or any non-L1) artifacts.
    This is the second half of F3 from the smoke-test results.
    """
    rc = main(["--genesis-dir", str(fake_genesis), "inspect", "L3-003"])
    assert rc == 0
    out = capsys.readouterr().out
    # The Difficulty line should not appear for L3 (or should not contain '?').
    assert "Difficulty:   ? (δ=?)" not in out, (
        "L3 manifest is missing L1-only difficulty fields, but the renderer "
        "still printed them as '?'. Expected: skip the Difficulty line for L3."
    )


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


def test_main_reconfigures_stdio_to_utf8_when_needed(capsys, monkeypatch):
    """Per smoke-test finding F2: Windows shells default to cp1252/charmap
    and crash on non-Latin-1 chars (Greek delta, em-dashes). The CLI must
    install a UTF-8 stdio shim early so first-line output never crashes.

    We can't actually flip the terminal encoding inside pytest (capsys uses
    its own capture), but we can call the helper directly and confirm it
    runs without raising and leaves an encoding the right shape.
    """
    from pwm_node.__main__ import _ensure_utf8_stdio
    import sys as _sys

    # Calling the helper a second time on top of pytest's capture should be
    # a no-op (capsys already captures via UTF-8-friendly buffer); shouldn't raise.
    _ensure_utf8_stdio()

    # Verify any installed shim accepts non-Latin-1 chars without exception.
    print("delta-sign-test: \u03b4 dash:\u2014 done")
    out = capsys.readouterr().out
    assert "\u03b4" in out
    assert "\u2014" in out


def test_all_commands_live(capsys):
    """All 8 CLI commands are now real (no stubs remain). The _chain_stub
    handler is vestigial and not reachable via any command as of Phase C session 7."""
    p = build_parser()
    help_text = p.format_help()
    # Sanity: none of the mandatory commands advertise a '[Phase C stub]' label
    assert "[Phase C stub]" not in help_text
