"""Tests for pwm_miner/executor.py.

All Docker and IPFS interactions are mocked so no real containers or network
calls are made during the test run.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pwm_miner.ipfs_fetch import VerificationError
from pwm_miner.executor import (
    ExecutionResult,
    ResourceLimits,
    execute_solver,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FAKE_CID = "QmFakeCID123"
FAKE_HASH = "abcdef1234567890" * 4  # 64 hex chars
FAKE_SOLVER_PATH = Path("/tmp/cache/solve.py")


@pytest.fixture()
def instance_dir(tmp_path: Path) -> Path:
    d = tmp_path / "instance"
    d.mkdir()
    return d


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


def _make_completed_process(returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout="solution=[1,2,3]",
        stderr="",
    )


# ---------------------------------------------------------------------------
# Helper: common patch context
# ---------------------------------------------------------------------------

def _patch_fetch(side_effect=None, return_value=FAKE_SOLVER_PATH):
    """Patch fetch_solver inside the executor module."""
    if side_effect is not None:
        return patch(
            "pwm_miner.executor.fetch_solver",
            side_effect=side_effect,
        )
    return patch(
        "pwm_miner.executor.fetch_solver",
        return_value=return_value,
    )


# ---------------------------------------------------------------------------
# Test: successful execution
# ---------------------------------------------------------------------------

class TestSuccessfulExecution:
    def test_returns_execution_result(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert isinstance(result, ExecutionResult)
        mock_run.assert_called_once()

    def test_success_true_on_zero_returncode(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)):
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert result.success is True

    def test_success_false_on_nonzero_returncode(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(1)):
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert result.success is False

    def test_stdout_captured(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)):
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert result.stdout == "solution=[1,2,3]"

    def test_output_path_is_output_dir(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)):
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert result.output_path == output_dir

    def test_runtime_seconds_is_positive(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)):
            result = execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

        assert result.runtime_seconds >= 0.0


# ---------------------------------------------------------------------------
# Test: VerificationError propagation
# ---------------------------------------------------------------------------

class TestVerificationErrorPropagation:
    def test_raises_verification_error(self, instance_dir, output_dir):
        with _patch_fetch(side_effect=VerificationError("hash mismatch")), \
             patch("subprocess.run") as mock_run:
            with pytest.raises(VerificationError):
                execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)

            # Container must NEVER be started when verification fails
            mock_run.assert_not_called()

    def test_container_never_runs_on_bad_hash(self, instance_dir, output_dir):
        """Explicit confirmation that subprocess.run is not called."""
        mock_run = MagicMock()
        with _patch_fetch(side_effect=VerificationError("bad hash")):
            try:
                with patch("subprocess.run", mock_run):
                    execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)
            except VerificationError:
                pass

        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Test: --network none is always present
# ---------------------------------------------------------------------------

class TestNetworkNone:
    def _get_cmd(self, instance_dir, output_dir, limits=None):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir, limits)
        return mock_run.call_args[0][0]  # positional arg: the cmd list

    def test_network_none_present(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir)
        assert "--network" in cmd
        network_idx = cmd.index("--network")
        assert cmd[network_idx + 1] == "none"

    def test_network_none_present_with_gpu(self, instance_dir, output_dir):
        limits = ResourceLimits(gpu_spec="all")
        cmd = self._get_cmd(instance_dir, output_dir, limits)
        assert "--network" in cmd
        network_idx = cmd.index("--network")
        assert cmd[network_idx + 1] == "none"

    def test_network_none_present_with_default_limits(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir, ResourceLimits())
        assert "--network" in cmd
        network_idx = cmd.index("--network")
        assert cmd[network_idx + 1] == "none"


# ---------------------------------------------------------------------------
# Test: --user 1000:1000 is always present
# ---------------------------------------------------------------------------

class TestUserFlag:
    def _get_cmd(self, instance_dir, output_dir, limits=None):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir, limits)
        return mock_run.call_args[0][0]

    def test_user_flag_present(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir)
        assert "--user" in cmd
        user_idx = cmd.index("--user")
        assert cmd[user_idx + 1] == "1000:1000"

    def test_user_flag_present_with_gpu(self, instance_dir, output_dir):
        limits = ResourceLimits(gpu_spec="device=0")
        cmd = self._get_cmd(instance_dir, output_dir, limits)
        assert "--user" in cmd
        user_idx = cmd.index("--user")
        assert cmd[user_idx + 1] == "1000:1000"


# ---------------------------------------------------------------------------
# Test: GPU spec handling
# ---------------------------------------------------------------------------

class TestGPUSpec:
    def _get_cmd(self, gpu_spec: str, instance_dir, output_dir):
        limits = ResourceLimits(gpu_spec=gpu_spec)
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir, limits)
        return mock_run.call_args[0][0]

    def test_gpu_all_adds_gpus_flag(self, instance_dir, output_dir):
        cmd = self._get_cmd("all", instance_dir, output_dir)
        assert "--gpus" in cmd
        gpus_idx = cmd.index("--gpus")
        assert cmd[gpus_idx + 1] == "all"

    def test_gpu_device_adds_gpus_flag(self, instance_dir, output_dir):
        cmd = self._get_cmd("device=0", instance_dir, output_dir)
        assert "--gpus" in cmd
        gpus_idx = cmd.index("--gpus")
        assert cmd[gpus_idx + 1] == "device=0"

    def test_gpu_none_omits_gpus_flag(self, instance_dir, output_dir):
        cmd = self._get_cmd("none", instance_dir, output_dir)
        assert "--gpus" not in cmd

    def test_default_limits_omit_gpus_flag(self, instance_dir, output_dir):
        """Default ResourceLimits has gpu_spec='none', so --gpus must be absent."""
        cmd = self._get_cmd("none", instance_dir, output_dir)
        assert "--gpus" not in cmd


# ---------------------------------------------------------------------------
# Test: container image is pwm-sandbox
# ---------------------------------------------------------------------------

class TestSandboxImage:
    def test_image_is_pwm_sandbox(self, instance_dir, output_dir):
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)
        cmd = mock_run.call_args[0][0]
        assert "pwm-sandbox" in cmd

    def test_pwm_sandbox_is_last_before_solver_args(self, instance_dir, output_dir):
        """pwm-sandbox must be the image name (last positional arg in docker run)."""
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)
        cmd = mock_run.call_args[0][0]
        assert cmd[-1] == "pwm-sandbox"


# ---------------------------------------------------------------------------
# Test: memory limits
# ---------------------------------------------------------------------------

class TestMemoryLimits:
    def test_memory_flag_uses_limits_value(self, instance_dir, output_dir):
        limits = ResourceLimits(memory_mb=2048)
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir, limits)
        cmd = mock_run.call_args[0][0]
        assert "--memory" in cmd
        mem_idx = cmd.index("--memory")
        assert cmd[mem_idx + 1] == "2048m"

    def test_memory_swap_equals_memory(self, instance_dir, output_dir):
        """--memory-swap == --memory disables swap inside the container."""
        limits = ResourceLimits(memory_mb=1024)
        with _patch_fetch(), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir, limits)
        cmd = mock_run.call_args[0][0]
        swap_idx = cmd.index("--memory-swap")
        assert cmd[swap_idx + 1] == "1024m"


# ---------------------------------------------------------------------------
# Test: volume mounts
# ---------------------------------------------------------------------------

class TestVolumeMounts:
    def _get_cmd(self, instance_dir, output_dir):
        with _patch_fetch(return_value=FAKE_SOLVER_PATH), \
             patch("subprocess.run", return_value=_make_completed_process(0)) as mock_run:
            execute_solver(FAKE_CID, FAKE_HASH, instance_dir, output_dir)
        return mock_run.call_args[0][0]

    def test_solver_mounted_readonly(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir)
        solver_mount = f"{FAKE_SOLVER_PATH}:/input/solve.py:ro"
        assert solver_mount in cmd

    def test_instance_dir_mounted_readonly(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir)
        instance_mount = f"{instance_dir}:/input:ro"
        assert instance_mount in cmd

    def test_output_dir_mounted_readwrite(self, instance_dir, output_dir):
        cmd = self._get_cmd(instance_dir, output_dir)
        output_mount = f"{output_dir}:/output"
        assert output_mount in cmd
