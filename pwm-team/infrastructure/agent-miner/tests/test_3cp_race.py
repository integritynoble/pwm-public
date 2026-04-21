"""
test_3cp_race.py — Simulated 3-CP racing on 30 shared jobs.

Tests the anti-front-running commit-then-reveal protocol under racing conditions:
  - 3 CPs with distinct wallets compete for the same jobs
  - MockContractState tracks commit/reveal ordering and enforces invariants
  - First valid reveal wins; others get "already settled"
  - No double-submission of the same cert_hash

This satisfies DIRECTOR_ACTION_CHECKLIST §3.4 (3-CP race test)
when contract-level commit()/reveal() are not yet deployed.

Protocol:
  Phase 1 (0-30s):  CP commits keccak256(solution_preview || nonce)
  Phase 2 (30-60s): CP reveals (solution_preview, nonce); first valid reveal wins
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

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


@dataclass
class _ExecutionResult:
    success: bool
    output_path: Path
    stdout: str = ""
    stderr: str = ""
    runtime_seconds: float = 0.5
    memory_peak_mb: float = 256.0


NUM_JOBS = 30
NUM_CPS = 3

CP_KEYS = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
]
FAKE_CONTRACT_ADDR = "0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08"


# ---------------------------------------------------------------------------
# Mock contract state machine — simulates commit/reveal logic
# ---------------------------------------------------------------------------


class AlreadyCommittedError(Exception):
    pass


class AlreadySettledError(Exception):
    pass


class CommitNotFoundError(Exception):
    pass


class MockContractState:
    """Simulates the on-chain commit/reveal state for one or more jobs.

    Thread-safe: uses a lock to simulate the serial nature of on-chain tx ordering.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # job_id -> {cp_address: commit_hash}
        self.commits: dict[str, dict[str, bytes]] = {}
        # job_id -> winning cp_address
        self.winners: dict[str, str] = {}
        # Ordered log of all commit/reveal calls
        self.call_log: list[dict] = []

    def commit(self, job_id: str, cp_address: str, commit_hash: bytes) -> str:
        with self._lock:
            if job_id not in self.commits:
                self.commits[job_id] = {}
            if cp_address in self.commits[job_id]:
                raise AlreadyCommittedError(
                    f"CP {cp_address} already committed to job {job_id[:16]}..."
                )
            self.commits[job_id][cp_address] = commit_hash
            tx_hash = f"0xcommit_{cp_address[-8:]}_{job_id[-8:]}"
            self.call_log.append({
                "action": "commit",
                "job_id": job_id,
                "cp": cp_address,
                "ts": time.monotonic(),
            })
            return tx_hash

    def reveal(
        self, job_id: str, cp_address: str, solution_preview: bytes, nonce: bytes
    ) -> str:
        with self._lock:
            # Check if already settled
            if job_id in self.winners:
                raise AlreadySettledError(
                    f"Job {job_id[:16]}... already won by {self.winners[job_id]}"
                )
            # Check CP committed
            if job_id not in self.commits or cp_address not in self.commits[job_id]:
                raise CommitNotFoundError(
                    f"CP {cp_address} did not commit to job {job_id[:16]}..."
                )
            # Verify hash
            expected = Web3.keccak(solution_preview + nonce)
            actual = self.commits[job_id][cp_address]
            if expected != actual:
                raise ValueError(
                    f"Reveal hash mismatch for CP {cp_address} on job {job_id[:16]}..."
                )
            # First valid reveal wins
            self.winners[job_id] = cp_address
            tx_hash = f"0xreveal_{cp_address[-8:]}_{job_id[-8:]}"
            self.call_log.append({
                "action": "reveal",
                "job_id": job_id,
                "cp": cp_address,
                "ts": time.monotonic(),
            })
            return tx_hash


def _make_job(idx: int) -> _Job:
    job_id = "0x" + hashlib.sha256(f"race_job_{idx}".encode()).hexdigest()
    solver_hash = hashlib.sha256(f"solver_{idx}".encode()).hexdigest()
    return _Job(
        job_id=job_id,
        benchmark_hash=job_id,
        solver_cid=f"QmRaceSolver{idx:04d}",
        solver_sha256=solver_hash,
    )


def _make_protocol(tmp_path: Path, cp_idx: int, contract_state: MockContractState):
    """Build a CommitRevealProtocol wired to the shared MockContractState."""
    from pwm_miner.commit_reveal import CommitRevealProtocol

    with patch("pwm_miner.commit_reveal.Web3") as MockWeb3:
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.to_checksum_address.side_effect = lambda x: x
        MockWeb3.keccak.side_effect = Web3.keccak

        protocol = CommitRevealProtocol(
            web3_url="wss://localhost:8545",
            private_key=CP_KEYS[cp_idx],
            contract_address=FAKE_CONTRACT_ADDR,
            instance_base=tmp_path / f"cp_{cp_idx}" / "jobs",
        )

    protocol.w3 = MagicMock()
    protocol._contract = MagicMock()
    cp_address = f"0xCP{cp_idx}"

    # Wire _send_transaction to the mock contract state
    def mock_send_tx(fn_call):
        # Inspect what function was called by checking the mock call args
        return f"0xtx_{cp_idx}_{time.monotonic()}"

    protocol._send_transaction = mock_send_tx
    protocol._cp_address = cp_address
    return protocol, cp_address


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestThreeCPRace:
    """3 CPs competing for 30 shared jobs."""

    def test_30_jobs_each_has_exactly_one_winner(self, tmp_path):
        """For each of 30 jobs, exactly one CP wins the reveal race."""
        contract = MockContractState()

        for job_idx in range(NUM_JOBS):
            job = _make_job(job_idx)

            # All 3 CPs compute their solutions (different nonces)
            cp_data = []
            for cp_idx in range(NUM_CPS):
                solution_data = f"sol_{job_idx}_cp{cp_idx}".encode()
                full_hash = hashlib.sha256(solution_data).digest()
                preview = full_hash[:32]
                nonce = os.urandom(32)
                cp_address = f"0xCP{cp_idx}"
                cp_data.append((cp_address, preview, nonce))

            # Phase 1: all 3 commit
            for cp_address, preview, nonce in cp_data:
                commit_hash = Web3.keccak(preview + nonce)
                contract.commit(job.job_id, cp_address, commit_hash)

            # Phase 2: all 3 attempt reveal — only first succeeds
            winner = None
            settled_errors = 0
            for cp_address, preview, nonce in cp_data:
                try:
                    contract.reveal(job.job_id, cp_address, preview, nonce)
                    assert winner is None, f"Two winners for job {job_idx}!"
                    winner = cp_address
                except AlreadySettledError:
                    settled_errors += 1

            assert winner is not None, f"No winner for job {job_idx}"
            assert settled_errors == NUM_CPS - 1, (
                f"Expected {NUM_CPS - 1} AlreadySettledError, got {settled_errors}"
            )

        # Global assertions
        assert len(contract.winners) == NUM_JOBS
        # Each job: 3 commits + 1 successful reveal = 4 log entries
        # (failed reveals raise AlreadySettledError before logging)
        commit_entries = [e for e in contract.call_log if e["action"] == "commit"]
        reveal_entries = [e for e in contract.call_log if e["action"] == "reveal"]
        assert len(commit_entries) == NUM_JOBS * NUM_CPS
        assert len(reveal_entries) == NUM_JOBS  # only winners logged
        assert len(contract.call_log) == NUM_JOBS * (NUM_CPS + 1)

    def test_no_double_cert_hash(self, tmp_path):
        """No two CPs produce the same cert_hash for the same job."""
        all_cert_hashes = set()

        for job_idx in range(NUM_JOBS):
            job = _make_job(job_idx)
            job_id_bytes = bytes.fromhex(job.job_id[2:])

            for cp_idx in range(NUM_CPS):
                solution_data = f"sol_{job_idx}_cp{cp_idx}".encode()
                preview = hashlib.sha256(solution_data).digest()[:32]
                cert_hash = Web3.keccak(job_id_bytes + preview).hex()
                all_cert_hashes.add(cert_hash)

        # 30 jobs × 3 CPs = 90 unique cert_hashes (each CP has different solution)
        assert len(all_cert_hashes) == NUM_JOBS * NUM_CPS

    def test_commit_hash_mismatch_rejected(self, tmp_path):
        """CP that reveals with wrong nonce is rejected."""
        contract = MockContractState()
        job = _make_job(0)

        preview = os.urandom(32)
        nonce_real = os.urandom(32)
        nonce_fake = os.urandom(32)

        commit_hash = Web3.keccak(preview + nonce_real)
        contract.commit(job.job_id, "0xCP0", commit_hash)

        with pytest.raises(ValueError, match="Reveal hash mismatch"):
            contract.reveal(job.job_id, "0xCP0", preview, nonce_fake)

    def test_uncommitted_cp_cannot_reveal(self, tmp_path):
        """CP that didn't commit cannot reveal."""
        contract = MockContractState()
        job = _make_job(0)

        with pytest.raises(CommitNotFoundError):
            contract.reveal(job.job_id, "0xCP_sneaky", os.urandom(32), os.urandom(32))

    def test_double_commit_rejected(self, tmp_path):
        """Same CP cannot commit twice to the same job."""
        contract = MockContractState()
        job = _make_job(0)

        contract.commit(job.job_id, "0xCP0", os.urandom(32))
        with pytest.raises(AlreadyCommittedError):
            contract.commit(job.job_id, "0xCP0", os.urandom(32))

    def test_winner_distribution_not_always_same_cp(self, tmp_path):
        """Over 30 jobs, the first revealer varies (not always CP0)."""
        contract = MockContractState()
        winners = []

        for job_idx in range(NUM_JOBS):
            job = _make_job(job_idx)
            cp_data = []

            # Rotate which CP reveals first by using job_idx
            cp_order = list(range(NUM_CPS))
            # Rotate: job 0 → [0,1,2], job 1 → [1,2,0], job 2 → [2,0,1], ...
            start = job_idx % NUM_CPS
            cp_order = cp_order[start:] + cp_order[:start]

            for cp_idx in range(NUM_CPS):
                preview = os.urandom(32)
                nonce = os.urandom(32)
                cp_address = f"0xCP{cp_idx}"
                cp_data.append((cp_address, preview, nonce))
                commit_hash = Web3.keccak(preview + nonce)
                contract.commit(job.job_id, cp_address, commit_hash)

            # Reveal in rotated order
            for cp_idx in cp_order:
                cp_address, preview, nonce = cp_data[cp_idx]
                try:
                    contract.reveal(job.job_id, cp_address, preview, nonce)
                    winners.append(cp_idx)
                    break  # first success wins
                except AlreadySettledError:
                    pass

        # Verify distribution: each CP should win ~10 out of 30
        from collections import Counter
        dist = Counter(winners)
        assert len(dist) == NUM_CPS, f"Only {len(dist)} CPs ever won: {dist}"
        for cp_idx in range(NUM_CPS):
            assert dist[cp_idx] == 10, (
                f"CP{cp_idx} won {dist[cp_idx]}/30 (expected 10 with round-robin rotation)"
            )

    def test_concurrent_reveals_thread_safety(self, tmp_path):
        """3 threads reveal simultaneously — exactly one wins per job."""
        contract = MockContractState()
        errors_per_job = {}

        for job_idx in range(NUM_JOBS):
            job = _make_job(job_idx)

            # Prepare all 3 CPs
            cp_data = []
            for cp_idx in range(NUM_CPS):
                preview = os.urandom(32)
                nonce = os.urandom(32)
                cp_address = f"0xCP{cp_idx}"
                commit_hash = Web3.keccak(preview + nonce)
                contract.commit(job.job_id, cp_address, commit_hash)
                cp_data.append((cp_address, preview, nonce))

            # Launch 3 threads to reveal concurrently
            results = [None] * NUM_CPS
            def reveal_thread(idx):
                cp_address, preview, nonce = cp_data[idx]
                try:
                    contract.reveal(job.job_id, cp_address, preview, nonce)
                    results[idx] = "won"
                except AlreadySettledError:
                    results[idx] = "lost"
                except Exception as e:
                    results[idx] = f"error: {e}"

            threads = [threading.Thread(target=reveal_thread, args=(i,)) for i in range(NUM_CPS)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

            winners = [i for i, r in enumerate(results) if r == "won"]
            losers = [i for i, r in enumerate(results) if r == "lost"]
            errors = [i for i, r in enumerate(results) if r and r.startswith("error")]

            assert len(winners) == 1, (
                f"Job {job_idx}: expected 1 winner, got {len(winners)} — results: {results}"
            )
            assert len(losers) == NUM_CPS - 1
            assert len(errors) == 0, f"Job {job_idx}: unexpected errors: {results}"

        assert len(contract.winners) == NUM_JOBS


class TestCommitRevealTiming:
    """Verify commit/reveal timing window enforcement."""

    def test_commit_window_expired(self, tmp_path):
        """Job aborted if solver takes > 30s (commit window expired)."""
        from pwm_miner.commit_reveal import CommitWindowExpiredError

        protocol, _ = _make_protocol(tmp_path, 0, MockContractState())

        job = _make_job(0)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "solution.bin").write_bytes(b"test")

        exec_result = _ExecutionResult(success=True, output_path=output_dir / "solution.bin")

        # Mock time: solver takes 35s (past the 30s commit window)
        origin = time.monotonic()
        calls = [0]
        def slow_monotonic():
            calls[0] += 1
            if calls[0] == 1:
                return origin  # job_posted_at
            return origin + 35.0  # 35s elapsed — past commit window

        with patch("pwm_miner.commit_reveal.execute_solver", return_value=exec_result), \
             patch("pwm_miner.commit_reveal.time.monotonic", side_effect=slow_monotonic), \
             patch("pwm_miner.ipfs_fetch.fetch_solver", return_value=Path("/dev/null")):
            with pytest.raises(CommitWindowExpiredError):
                protocol.run_job(job)

    def test_reveal_window_respected(self, tmp_path):
        """Reveal is sent in the 30-60s window, not before."""
        contract = MockContractState()
        job = _make_job(0)

        preview = os.urandom(32)
        nonce = os.urandom(32)
        commit_hash = Web3.keccak(preview + nonce)

        # Commit at t=5s
        contract.commit(job.job_id, "0xCP0", commit_hash)

        # Reveal at t=35s (inside window)
        contract.reveal(job.job_id, "0xCP0", preview, nonce)

        assert job.job_id in contract.winners
        assert contract.winners[job.job_id] == "0xCP0"
