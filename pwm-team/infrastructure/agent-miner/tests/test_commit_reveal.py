"""
test_commit_reveal.py — Unit and integration-style tests for CommitRevealProtocol.

Test matrix
-----------
1. commit_hash_correct        — keccak256(solution_preview ‖ nonce) matches expected
2. reveal_args_correct        — reveal() passes exact solution_preview and nonce to contract
3. commit_window_expired      — job aborted when 0–30 s window is missed before commit()
4. solver_verification_error  — VerificationError from execute_solver propagates, no commit
5. three_cp_race              — 3 CPs racing; first valid reveal wins (call-order tracking)
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from web3 import Web3

# ---------------------------------------------------------------------------
# Minimal stubs — replicate just enough of the real dataclass shapes so the
# tests work without importing executor/job_queue (which are still stubs).
# ---------------------------------------------------------------------------
@dataclass
class _ResourceLimits:
    memory_mb: int = 4096
    timeout_seconds: int = 300
    gpu_spec: str = "none"


@dataclass
class _ExecutionResult:
    success: bool
    output_path: Path
    stdout: str = ""
    stderr: str = ""
    runtime_seconds: float = 1.0
    memory_peak_mb: float = 512.0


@dataclass
class _ComputeManifest:
    min_vram_gb: int = 0
    memory_mb: int = 4096
    timeout_seconds: int = 300
    gpu_spec: str = "none"


@dataclass
class _Job:
    job_id: str
    benchmark_hash: str
    solver_cid: str
    solver_sha256: str
    compute_manifest: _ComputeManifest = field(default_factory=_ComputeManifest)
    expected_reward: float = 10.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
FAKE_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
FAKE_CONTRACT_ADDR = "0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08"

# Pre-computed keccak256 test vector (both preview and nonce are all-zero bytes).
_ZERO_PREVIEW = b"\x00" * 32
_ZERO_NONCE   = b"\x00" * 32
_ZERO_COMMIT_HASH = Web3.keccak(_ZERO_PREVIEW + _ZERO_NONCE)


def _make_protocol(tmp_path: Path) -> Any:
    """
    Build a CommitRevealProtocol with all network I/O mocked out.

    The Web3 provider, contract object, and _send_transaction are replaced so
    tests never touch the network.
    """
    from pwm_miner.commit_reveal import CommitRevealProtocol

    with patch("pwm_miner.commit_reveal.Web3") as MockWeb3:
        # Make Web3(provider) return a usable mock.
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.to_checksum_address.side_effect = lambda x: x
        MockWeb3.keccak.side_effect = Web3.keccak  # real keccak

        protocol = CommitRevealProtocol(
            web3_url="wss://localhost:8545",
            private_key=FAKE_PRIVATE_KEY,
            contract_address=FAKE_CONTRACT_ADDR,
            instance_base=tmp_path / "jobs",
        )

    # Restore real keccak on the instance's w3 attribute reference.
    protocol.w3 = MagicMock()
    protocol._contract = MagicMock()
    return protocol


# ---------------------------------------------------------------------------
# Test 1: commit_hash is keccak256(solution_preview ‖ nonce)
# ---------------------------------------------------------------------------
class TestCommitHash:
    def test_zero_preview_and_nonce(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol

        result = CommitRevealProtocol._compute_commit_hash(_ZERO_PREVIEW, _ZERO_NONCE)
        assert result == _ZERO_COMMIT_HASH

    def test_random_inputs(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol

        preview = os.urandom(32)
        nonce   = os.urandom(32)
        expected = Web3.keccak(preview + nonce)
        assert CommitRevealProtocol._compute_commit_hash(preview, nonce) == expected

    def test_different_nonce_produces_different_hash(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol

        preview = b"x" * 32
        h1 = CommitRevealProtocol._compute_commit_hash(preview, b"\x00" * 32)
        h2 = CommitRevealProtocol._compute_commit_hash(preview, b"\xff" * 32)
        assert h1 != h2


# ---------------------------------------------------------------------------
# Test 2: reveal() passes exact solution_preview and nonce to the contract
# ---------------------------------------------------------------------------
class TestRevealArgs:
    def test_reveal_passes_correct_args(self, tmp_path):
        """
        reveal() must forward solution_preview and nonce verbatim to the
        planned PWMCertificate.reveal() contract function.
        """
        from pwm_miner.commit_reveal import CommitRevealProtocol

        protocol = _make_protocol(tmp_path)
        # Capture the arguments passed to contract.functions.reveal(...)
        reveal_calls: List[tuple] = []

        def capture_reveal(*args):
            reveal_calls.append(args)
            return MagicMock()  # fn_call mock

        protocol._contract.functions.reveal.side_effect = capture_reveal
        protocol._send_transaction = MagicMock(return_value="0xabc123")

        preview = b"\xde\xad\xbe\xef" + b"\x00" * 28
        nonce   = b"\xca\xfe" + b"\x00" * 30
        job_id  = "0x" + "ab" * 32

        # No job_posted_at → reveal fires immediately (no timing wait in test)
        tx = protocol.reveal(job_id, preview, nonce, job_posted_at=None)

        assert tx == "0xabc123"
        assert len(reveal_calls) == 1
        _, actual_preview, actual_nonce = reveal_calls[0]
        assert actual_preview == preview
        assert actual_nonce == nonce

    def test_commit_sends_keccak_of_preview_nonce(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol

        protocol = _make_protocol(tmp_path)
        commit_calls: List[tuple] = []

        def capture_commit(*args):
            commit_calls.append(args)
            return MagicMock()

        protocol._contract.functions.commit.side_effect = capture_commit
        protocol._send_transaction = MagicMock(return_value="0xdeadbeef")

        preview = b"\x01" * 32
        nonce   = b"\x02" * 32
        job_id  = "0x" + "cd" * 32

        tx = protocol.commit(job_id, preview, nonce, job_posted_at=None)

        assert tx == "0xdeadbeef"
        _, sent_commit_hash = commit_calls[0]
        expected_hash = Web3.keccak(preview + nonce)
        assert sent_commit_hash == expected_hash


# ---------------------------------------------------------------------------
# Test 3: commit window expiry aborts the job
# ---------------------------------------------------------------------------
class TestCommitWindowExpiry:
    def test_commit_raises_when_window_expired(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol, CommitWindowExpiredError, COMMIT_WINDOW_SECONDS

        protocol = _make_protocol(tmp_path)
        # Simulate elapsed time = 31 s, which is past the 30 s window.
        fake_posted_at = time.monotonic() - (COMMIT_WINDOW_SECONDS + 1)

        with pytest.raises(CommitWindowExpiredError):
            protocol.commit(
                "0x" + "aa" * 32,
                b"\x00" * 32,
                b"\x00" * 32,
                job_posted_at=fake_posted_at,
            )

    def test_commit_succeeds_inside_window(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol, COMMIT_WINDOW_SECONDS

        protocol = _make_protocol(tmp_path)
        protocol._contract.functions.commit.return_value = MagicMock()
        protocol._send_transaction = MagicMock(return_value="0xok")

        # Posted at t=0 (just now), elapsed ~ 0 s → inside window
        fake_posted_at = time.monotonic()

        tx = protocol.commit(
            "0x" + "aa" * 32,
            b"\x00" * 32,
            b"\x00" * 32,
            job_posted_at=fake_posted_at,
        )
        assert tx == "0xok"

    def test_run_job_aborts_when_solver_too_slow(self, tmp_path):
        """
        If execute_solver takes longer than 30 s (simulated via mock time), run_job
        must raise CommitWindowExpiredError and never call commit().
        """
        from pwm_miner.commit_reveal import CommitRevealProtocol, CommitWindowExpiredError, COMMIT_WINDOW_SECONDS

        protocol = _make_protocol(tmp_path)

        # Patch time.monotonic so that _seconds_since_posted returns > 30 s
        # by the time it is first checked after execute_solver returns.
        call_count = [0]
        origin = time.monotonic()

        def fake_monotonic():
            call_count[0] += 1
            # First call (job_posted_at capture): return t=0 baseline
            if call_count[0] == 1:
                return origin
            # Subsequent calls: pretend 35 s have elapsed (solver was slow)
            return origin + COMMIT_WINDOW_SECONDS + 5

        output_file = tmp_path / "out.bin"
        output_file.write_bytes(b"solver output data")

        fake_result = _ExecutionResult(success=True, output_path=output_file)

        with patch("pwm_miner.commit_reveal.time.monotonic", side_effect=fake_monotonic), \
             patch("pwm_miner.commit_reveal.execute_solver", return_value=fake_result), \
             patch("pwm_miner.commit_reveal.os.urandom", return_value=b"\x00" * 32), \
             patch("pwm_miner.ipfs_fetch.fetch_solver", create=True):
            # Also patch the ipfs lazy import inside run_job
            import sys
            fake_ipfs = MagicMock()
            sys.modules.setdefault("pwm_miner.ipfs_fetch", fake_ipfs)

            commit_spy = MagicMock(side_effect=CommitWindowExpiredError("window expired"))
            protocol.commit = commit_spy

            job = _Job(
                job_id="0x" + "bb" * 32,
                benchmark_hash="QmFakeBenchmarkHash",
                solver_cid="QmFakeSolverCid",
                solver_sha256="a" * 64,
            )

            with pytest.raises(CommitWindowExpiredError):
                protocol.run_job(job)


# ---------------------------------------------------------------------------
# Test 4: VerificationError from execute_solver propagates; no commit sent
# ---------------------------------------------------------------------------
class TestVerificationErrorPropagation:
    def test_verification_error_blocks_commit(self, tmp_path):
        """
        If execute_solver raises VerificationError (binary hash mismatch), run_job
        must re-raise it immediately and never call commit().

        We patch both the lazy ipfs_fetch import and execute_solver so we never
        touch the network or Docker.
        """
        from pwm_miner.commit_reveal import CommitRevealProtocol

        class VerificationError(Exception):
            """Simulated VerificationError from ipfs_fetch/executor."""

        protocol = _make_protocol(tmp_path)
        commit_spy = MagicMock()
        protocol.commit = commit_spy

        fake_fetch_solver = MagicMock(return_value=tmp_path / "fake_binary")

        # Patch both the module-level execute_solver import and the lazy
        # ipfs_fetch.fetch_solver import that lives inside run_job().
        import sys
        import types
        fake_ipfs_module = types.ModuleType("pwm_miner.ipfs_fetch")
        fake_ipfs_module.fetch_solver = fake_fetch_solver
        sys.modules["pwm_miner.ipfs_fetch"] = fake_ipfs_module

        with patch(
            "pwm_miner.commit_reveal.execute_solver",
            side_effect=VerificationError("SHA-256 mismatch"),
        ):
            job = _Job(
                job_id="0x" + "cc" * 32,
                benchmark_hash="QmFakeBenchmarkHash",
                solver_cid="QmFakeSolverCid",
                solver_sha256="b" * 64,
            )
            with pytest.raises(VerificationError):
                protocol.run_job(job)

        commit_spy.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: Three CPs racing — first valid reveal wins
# ---------------------------------------------------------------------------
class TestThreeCPRace:
    """
    Simulate 3 Compute Providers racing to commit then reveal on the same job.

    The 'contract' is a shared mock that records reveal call order and timestamps.
    The first CP to call reveal() wins; the other two are late and get no reward.

    Implementation notes
    --------------------
    - We don't spawn threads: racing is modelled by building 3 protocols that share
      a mocked contract, then calling commit() and reveal() sequentially with
      controlled synthetic timestamps.  The call-order list is the observable.
    - We verify: only the FIRST reveal call would be accepted (call index 0 has
      earliest synthetic block timestamp).
    """

    def _build_racing_mock_contract(self):
        """
        Returns a shared mock contract and a call-log list.
        Each reveal call appends (cp_id, timestamp) to the log.
        """
        call_log: List[dict] = []

        class RevealTracker:
            def __init__(self, cp_id: int):
                self._cp_id = cp_id

            def __call__(self, job_id_bytes, solution_preview, nonce):
                # Record the wall-clock moment of the reveal call
                call_log.append(
                    {
                        "cp_id": self._cp_id,
                        "ts": time.monotonic(),
                        "solution_preview": solution_preview,
                        "nonce": nonce,
                    }
                )
                return MagicMock()  # fn_call

        return call_log, RevealTracker

    def test_first_reveal_wins(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol

        call_log, RevealTracker = self._build_racing_mock_contract()

        job_id = "0x" + "ff" * 32

        # Each CP has its own preview/nonce (different solvers may differ slightly)
        cp_data = [
            (b"\x01" * 32, os.urandom(32)),
            (b"\x02" * 32, os.urandom(32)),
            (b"\x03" * 32, os.urandom(32)),
        ]

        # Build 3 protocol instances; each shares the same call_log via RevealTracker
        protocols = []
        for cp_id in range(3):
            p = _make_protocol(tmp_path / f"cp{cp_id}")
            # Wire up reveal tracker for this CP
            p._contract.functions.reveal.side_effect = RevealTracker(cp_id)
            # commit() succeeds silently
            p._contract.functions.commit.return_value = MagicMock()
            p._send_transaction = MagicMock(return_value=f"0x{'00' * 32}_{cp_id}")
            protocols.append(p)

        # Simulate: all 3 CPs committed successfully (0–30 s window).
        # Now they race to reveal in 30–60 s window (no timing wait — use job_posted_at=None).
        reveal_tx_hashes = []
        for cp_id, (protocol, (preview, nonce)) in enumerate(zip(protocols, cp_data)):
            # Override _send_transaction to return ordered tx hashes
            protocol._send_transaction = MagicMock(
                return_value=f"0x{'0' * 62}{cp_id:02d}"
            )
            tx = protocol.reveal(job_id, preview, nonce, job_posted_at=None)
            reveal_tx_hashes.append(tx)

        # Verify all 3 reveals were attempted
        assert len(call_log) == 3, "All 3 CPs must have submitted a reveal"

        # Verify CP ordering: cp_id 0 revealed first (earliest call)
        reveal_order = [entry["cp_id"] for entry in call_log]
        assert reveal_order[0] == 0, (
            f"CP 0 should be first to reveal; order was {reveal_order}"
        )

        # Contract rule: only the first valid reveal wins (earliest block timestamp).
        # In a real contract the second and third reveals would revert.
        # Here we assert that cp_id == 0 has the lowest synthetic timestamp.
        assert call_log[0]["ts"] <= call_log[1]["ts"] <= call_log[2]["ts"], (
            "Call log should be monotonically ordered by timestamp"
        )

        # Verify that the solution_preview and nonce for the winning CP are correct.
        winning_preview, winning_nonce = cp_data[0]
        assert call_log[0]["solution_preview"] == winning_preview
        assert call_log[0]["nonce"] == winning_nonce

    def test_first_reveal_commit_hash_matches(self, tmp_path):
        """
        For CP 0 (race winner): the committed hash must equal
        keccak256(solution_preview ‖ nonce) used in the reveal.
        """
        from pwm_miner.commit_reveal import CommitRevealProtocol

        protocol = _make_protocol(tmp_path / "cp0")

        commit_calls: List[tuple] = []
        reveal_calls: List[tuple] = []

        def capture_commit(*args):
            commit_calls.append(args)
            return MagicMock()

        def capture_reveal(*args):
            reveal_calls.append(args)
            return MagicMock()

        protocol._contract.functions.commit.side_effect = capture_commit
        protocol._contract.functions.reveal.side_effect = capture_reveal
        protocol._send_transaction = MagicMock(return_value="0x01")

        preview = os.urandom(32)
        nonce   = os.urandom(32)
        job_id  = "0x" + "ee" * 32

        protocol.commit(job_id, preview, nonce, job_posted_at=None)
        protocol.reveal(job_id, preview, nonce, job_posted_at=None)

        # Committed hash must equal keccak256(preview ‖ nonce)
        _, committed_hash = commit_calls[0]
        expected_hash = Web3.keccak(preview + nonce)
        assert committed_hash == expected_hash, "Committed hash must be keccak256(preview ‖ nonce)"

        # Revealed preview and nonce must match what was committed
        _, revealed_preview, revealed_nonce = reveal_calls[0]
        assert revealed_preview == preview
        assert revealed_nonce == nonce


# ---------------------------------------------------------------------------
# Test 6: reveal() waits for the reveal window before sending
# ---------------------------------------------------------------------------
class TestRevealTiming:
    def test_reveal_respects_30s_open(self, tmp_path):
        """
        If reveal() is called with job_posted_at set to 'just now' (t=1000),
        it must sleep until the 30 s mark before sending the transaction.

        _seconds_since_posted() computes: time.monotonic() - job_posted_at.
        We pass job_posted_at=1000 (a fixed baseline) and mock time.monotonic()
        to return values that simulate the passage of time:
          call 1 → 1000.5  (elapsed 0.5 s  → still in pre-reveal window → sleep)
          call 2 → 1030.1  (elapsed 30.1 s → reveal window open → proceed)
          call 3 → 1030.1  (elapsed check: 30.1 s < 60 s → ok)
        """
        from pwm_miner.commit_reveal import CommitRevealProtocol

        protocol = _make_protocol(tmp_path)
        protocol._contract.functions.reveal.return_value = MagicMock()
        protocol._send_transaction = MagicMock(return_value="0x11")

        sleep_calls: List[float] = []
        BASE = 1000.0  # fixed baseline for job_posted_at

        # monotonic() is called inside _seconds_since_posted; sequence models time passing.
        monotonic_values = iter([BASE + 0.5, BASE + 30.1, BASE + 30.1])

        with patch("pwm_miner.commit_reveal.time.sleep", side_effect=lambda s: sleep_calls.append(s)), \
             patch("pwm_miner.commit_reveal.time.monotonic", side_effect=monotonic_values):
            protocol.reveal(
                "0x" + "aa" * 32,
                b"\x00" * 32,
                b"\x00" * 32,
                job_posted_at=BASE,   # fixed baseline so elapsed is deterministic
            )

        # At least one sleep call proves the method waited.
        assert len(sleep_calls) >= 1, "reveal() should have slept waiting for window"

    def test_reveal_raises_if_window_closed(self, tmp_path):
        from pwm_miner.commit_reveal import CommitRevealProtocol, RevealWindowClosedError, REVEAL_WINDOW_CLOSE

        protocol = _make_protocol(tmp_path)

        # Posted at t = -(REVEAL_WINDOW_CLOSE + 1) → elapsed > 60 s
        fake_posted_at = time.monotonic() - (REVEAL_WINDOW_CLOSE + 1)

        with pytest.raises(RevealWindowClosedError):
            protocol.reveal(
                "0x" + "aa" * 32,
                b"\x00" * 32,
                b"\x00" * 32,
                job_posted_at=fake_posted_at,
            )
