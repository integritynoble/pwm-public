"""End-to-end mine flow using the REAL repo genesis artifacts, --dry-run.

This test runs without any network call — it:
  1. Locates the repo's pwm-team/pwm_product/genesis/ directory.
  2. Uses the examples/demo_solver.py as the --solver.
  3. Invokes `pwm-node mine L3-003 --dry-run` against the actual CASSI
     L3 artifact in the repo.
  4. Verifies that a cert_payload is produced with a deterministic cert_hash.

If the repo structure changes (genesis moved, L3-003 deleted), this test
catches it. Opt-in via PWM_RUN_E2E env var — shares the same gate as
test_sepolia_readonly.py.

This test is the closest we can get to the bounty acceptance criterion
  "pwm-node mine cassi/t1_nominal --solver demo.py completes in ≤ 5 min"
without broadcasting a transaction (which would require gas ETH and an
on-chain-registered benchmark).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_RUN = os.environ.get("PWM_RUN_E2E") == "1"
_SKIP_REASON = "Set PWM_RUN_E2E=1 to enable e2e tests"


def _find_repo_root() -> Path | None:
    """Walk up looking for pwm-team/pwm_product/genesis/l3/L3-003.json."""
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        probe = p / "pwm-team" / "pwm_product" / "genesis" / "l3" / "L3-003.json"
        if probe.is_file():
            return p
    return None


@pytest.fixture()
def repo_root() -> Path:
    root = _find_repo_root()
    if root is None:
        pytest.skip("Cannot find pwm-team/pwm_product/genesis/l3/L3-003.json from test dir")
    return root


@pytest.fixture()
def demo_solver_path() -> Path:
    """Path to examples/demo_solver.py next to the tests directory."""
    here = Path(__file__).resolve()
    # tests/e2e/ → ../../examples/demo_solver.py
    p = here.parent.parent.parent / "examples" / "demo_solver.py"
    if not p.is_file():
        pytest.skip(f"demo_solver.py not found at {p}")
    return p


@pytest.mark.skipif(not _RUN, reason=_SKIP_REASON)
def test_mine_cassi_dry_run(repo_root, demo_solver_path, tmp_path):
    """pwm-node mine L3-003 --dry-run against real genesis produces a cert_hash."""
    genesis_dir = repo_root / "pwm-team" / "pwm_product" / "genesis"
    work_dir = tmp_path / "work"

    cmd = [
        sys.executable, "-m", "pwm_node",
        "--genesis-dir", str(genesis_dir),
        "mine", "L3-003",
        "--solver", str(demo_solver_path),
        "--work-dir", str(work_dir),
        "--dry-run",
        "--timeout", "60",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    stdout = result.stdout + result.stderr

    assert result.returncode == 0, f"mine dry-run failed:\n{stdout}"
    assert "resolved L3-003" in stdout, f"missing 'resolved L3-003' in output:\n{stdout}"
    assert "certHash" in stdout, f"missing 'certHash' in output:\n{stdout}"
    assert "not submitting to chain" in stdout or "--dry-run" in stdout

    # Cert payload file must exist in work_dir
    cert_file = work_dir / "cert_payload.json"
    assert cert_file.is_file(), f"cert_payload.json not written under {work_dir}"

    import json
    payload = json.loads(cert_file.read_text())
    for key in (
        "certHash", "benchmarkHash", "principleId",
        "l1Creator", "l2Creator", "l3Creator", "acWallet", "cpWallet",
        "shareRatioP", "Q_int", "delta", "rank",
    ):
        assert key in payload, f"cert payload missing struct field: {key}"

    # Determinism: same inputs → same certHash
    import shutil
    shutil.rmtree(work_dir)
    result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    stdout2 = result2.stdout + result2.stderr
    assert result2.returncode == 0
    cert_file2 = work_dir / "cert_payload.json"
    payload2 = json.loads(cert_file2.read_text())
    assert payload["certHash"] == payload2["certHash"], (
        "certHash is not deterministic across runs:\n"
        f"first : {payload['certHash']}\n"
        f"second: {payload2['certHash']}"
    )
