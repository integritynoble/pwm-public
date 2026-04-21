"""
commit_reveal.py — Anti-front-running commit-then-reveal protocol for PWM mining.

Protocol timing (relative to job_posted_at):
  Phase 1 (0–30 s): CP runs solver, commits keccak256(solution_preview ‖ nonce) on-chain.
  Phase 2 (30–60 s): CP reveals (solution_preview, nonce). Contract verifies commit matches.
                     First valid reveal wins (1-p)*55% of job reward.
  Tie-breaking: earlier block timestamp wins.

Security invariants:
  - NEVER commit or reveal if the solver's SHA-256 failed verification (VerificationError
    propagates immediately from execute_solver, blocking both phases).
  - Commit MUST be sent within 0–30 s of job_posted_at; if the window is missed the job
    is silently aborted (log warning, no reveal sent).
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import web3 as _web3_module
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from pwm_miner.executor import ResourceLimits, execute_solver
from pwm_miner.job_queue import Job

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timing constants
# ---------------------------------------------------------------------------
COMMIT_WINDOW_SECONDS: int = 30   # job is available from t=0 → t=30 s
REVEAL_WINDOW_OPEN: int = 30      # reveal window opens at t=30 s
REVEAL_WINDOW_CLOSE: int = 60     # reveal window closes at t=60 s
REVEAL_POLL_INTERVAL: float = 0.5  # seconds between "is reveal window open?" polls

# ---------------------------------------------------------------------------
# Planned ABI fragment — commit() and reveal() do not yet exist in the deployed
# PWMCertificate contract.  They are defined here as a forward-looking extension.
# The fragment is used to build the contract object; calls will revert with
# "function not found" until the contract is upgraded on-chain.
#
# Planned contract function - requires PWMCertificate.commit()/reveal() extension
# ---------------------------------------------------------------------------
_COMMIT_REVEAL_ABI_FRAGMENT = [
    # Planned contract function - requires PWMCertificate.commit()/reveal() extension
    {
        "inputs": [
            {"internalType": "bytes32", "name": "jobId",      "type": "bytes32"},
            {"internalType": "bytes32", "name": "commitHash", "type": "bytes32"},
        ],
        "name": "commit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Planned contract function - requires PWMCertificate.commit()/reveal() extension
    {
        "inputs": [
            {"internalType": "bytes32",  "name": "jobId",           "type": "bytes32"},
            {"internalType": "bytes",    "name": "solutionPreview", "type": "bytes"},
            {"internalType": "bytes32",  "name": "nonce",           "type": "bytes32"},
        ],
        "name": "reveal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # jobPostedAt(bytes32 jobId) → uint256  (also planned, used to fetch reference time)
    # Planned contract function - requires PWMCertificate.commit()/reveal() extension
    {
        "inputs": [
            {"internalType": "bytes32", "name": "jobId", "type": "bytes32"},
        ],
        "name": "jobPostedAt",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class CommitWindowExpiredError(Exception):
    """Raised when the 30-second commit window has already passed."""


class RevealWindowClosedError(Exception):
    """Raised when the 60-second reveal window has already closed."""


# ---------------------------------------------------------------------------
# CommitRevealProtocol
# ---------------------------------------------------------------------------
class CommitRevealProtocol:
    """
    Implements the PWM anti-front-running commit-then-reveal protocol.

    Usage::

        protocol = CommitRevealProtocol(
            web3_url="wss://sepolia.infura.io/ws/v3/...",
            private_key="0x...",
            contract_address="0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08",
            instance_base=Path("/tmp/pwm_jobs"),
        )
        cert_hash = protocol.run_job(job)
    """

    def __init__(
        self,
        web3_url: str,
        private_key: str,
        contract_address: str,
        instance_base: Path,
    ) -> None:
        self.w3 = Web3(Web3.WebsocketProvider(web3_url))
        # POA middleware needed for testnets such as Sepolia
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self._private_key = private_key
        self._account = self.w3.eth.account.from_key(private_key)
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.instance_base = instance_base
        self.instance_base.mkdir(parents=True, exist_ok=True)

        # Build contract object with the planned ABI extension.
        # Planned contract function - requires PWMCertificate.commit()/reveal() extension
        self._contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=_COMMIT_REVEAL_ABI_FRAGMENT,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_commit_hash(solution_preview: bytes, nonce: bytes) -> bytes:
        """Return keccak256(solution_preview ‖ nonce) as a 32-byte value."""
        return Web3.keccak(solution_preview + nonce)

    def _job_id_to_bytes32(self, job_id: str) -> bytes:
        """Convert a hex or UTF-8 job_id string to a 32-byte value."""
        # Accept "0x…" hex strings or plain strings that we keccak into 32 bytes.
        if job_id.startswith("0x") or job_id.startswith("0X"):
            raw = bytes.fromhex(job_id[2:])
            if len(raw) != 32:
                raise ValueError(f"job_id hex must be 32 bytes, got {len(raw)}")
            return raw
        # Treat as a UTF-8 label and hash it down to 32 bytes.
        return Web3.keccak(text=job_id)

    def _send_transaction(self, fn_call) -> str:
        """
        Build, sign, and broadcast a contract function call.
        Returns the transaction hash as a hex string (0x-prefixed).
        """
        nonce = self.w3.eth.get_transaction_count(self._account.address)
        tx = fn_call.build_transaction(
            {
                "from": self._account.address,
                "nonce": nonce,
                "gas": 200_000,
                "maxFeePerGas": self.w3.eth.max_priority_fee + (2 * self.w3.eth.gas_price),
                "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, self._private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.debug("Sent tx %s", tx_hash.hex())
        return "0x" + tx_hash.hex()

    def _seconds_since_posted(self, job_posted_at: float) -> float:
        """Wall-clock seconds elapsed since job_posted_at."""
        return time.monotonic() - job_posted_at

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def commit(
        self,
        job_id: str,
        solution_preview: bytes,
        nonce: bytes,
        *,
        job_posted_at: Optional[float] = None,
    ) -> str:
        """
        Compute keccak256(solution_preview ‖ nonce) and submit to the contract.

        Planned contract function - requires PWMCertificate.commit()/reveal() extension

        Parameters
        ----------
        job_id:
            Identifier for the job (hex bytes32 string or plain label).
        solution_preview:
            First 32 bytes of the SHA-256 hash of the solver output.
        nonce:
            32 random bytes generated by the caller.
        job_posted_at:
            monotonic timestamp when the job was observed (time.monotonic()).
            If supplied, the method will raise CommitWindowExpiredError if more
            than COMMIT_WINDOW_SECONDS have elapsed.

        Returns
        -------
        str
            Transaction hash (0x-prefixed hex).
        """
        if job_posted_at is not None:
            elapsed = self._seconds_since_posted(job_posted_at)
            if elapsed >= COMMIT_WINDOW_SECONDS:
                raise CommitWindowExpiredError(
                    f"Commit window expired: {elapsed:.1f}s >= {COMMIT_WINDOW_SECONDS}s"
                )

        job_id_bytes = self._job_id_to_bytes32(job_id)
        commit_hash = self._compute_commit_hash(solution_preview, nonce)

        logger.info(
            "Committing job=%s commit_hash=%s",
            job_id,
            commit_hash.hex(),
        )

        # Planned contract function - requires PWMCertificate.commit()/reveal() extension
        fn_call = self._contract.functions.commit(
            job_id_bytes,
            commit_hash,
        )
        tx_hash = self._send_transaction(fn_call)
        logger.info("Commit tx sent: %s", tx_hash)
        return tx_hash

    def reveal(
        self,
        job_id: str,
        solution_preview: bytes,
        nonce: bytes,
        *,
        job_posted_at: Optional[float] = None,
    ) -> str:
        """
        Wait until the reveal window opens (t >= 30 s) then submit the reveal.

        Planned contract function - requires PWMCertificate.commit()/reveal() extension

        Parameters
        ----------
        job_id:
            Same identifier used in commit().
        solution_preview:
            Exact bytes passed to commit().
        nonce:
            Exact bytes passed to commit().
        job_posted_at:
            monotonic timestamp when the job was observed.  Used to wait for the
            reveal window.  If None, reveal is sent immediately (useful in tests).

        Returns
        -------
        str
            Transaction hash (0x-prefixed hex).
        """
        if job_posted_at is not None:
            # Wait until reveal window opens.
            while True:
                elapsed = self._seconds_since_posted(job_posted_at)
                if elapsed >= REVEAL_WINDOW_OPEN:
                    break
                remaining = REVEAL_WINDOW_OPEN - elapsed
                logger.debug(
                    "Waiting %.1f s for reveal window on job=%s", remaining, job_id
                )
                time.sleep(min(REVEAL_POLL_INTERVAL, remaining))

            # Guard: reveal window must not have closed.
            elapsed = self._seconds_since_posted(job_posted_at)
            if elapsed >= REVEAL_WINDOW_CLOSE:
                raise RevealWindowClosedError(
                    f"Reveal window closed before reveal could be sent: {elapsed:.1f}s"
                )

        job_id_bytes = self._job_id_to_bytes32(job_id)

        logger.info(
            "Revealing job=%s solution_preview=%s nonce=%s",
            job_id,
            solution_preview.hex(),
            nonce.hex(),
        )

        # Planned contract function - requires PWMCertificate.commit()/reveal() extension
        fn_call = self._contract.functions.reveal(
            job_id_bytes,
            solution_preview,
            nonce,
        )
        tx_hash = self._send_transaction(fn_call)
        logger.info("Reveal tx sent: %s", tx_hash)
        return tx_hash

    def run_job(self, job: Job) -> str:
        """
        Execute the full commit-reveal flow for a single job.

        Steps
        -----
        1. Record job_posted_at (wall-clock reference for window timing).
        2. Create a temporary instance directory and download benchmark input from
           IPFS using job.benchmark_hash.
        3. Run the solver: execute_solver(job.solver_cid, job.solver_sha256, …).
           If execute_solver raises VerificationError it propagates immediately —
           no commit is attempted.
        4. Derive solution_preview = first 32 bytes of SHA-256(output file bytes).
        5. Generate nonce = os.urandom(32).
        6. Call self.commit() inside the 0–30 s window; abort if window expired.
        7. Wait for the reveal window (30–60 s) then call self.reveal().
        8. Return cert_hash = keccak256(job_id_bytes ‖ solution_preview).

        Parameters
        ----------
        job: Job
            Job descriptor obtained from the job queue.

        Returns
        -------
        str
            cert_hash as a 0x-prefixed hex string.

        Raises
        ------
        VerificationError
            If the solver binary's SHA-256 does not match the on-chain hash.
        CommitWindowExpiredError
            If solver execution took longer than 30 s and the commit window closed.
        """
        job_posted_at = time.monotonic()

        with tempfile.TemporaryDirectory(
            prefix=f"pwm_job_{job.job_id}_", dir=self.instance_base
        ) as tmp_dir:
            instance_dir = Path(tmp_dir) / "input"
            output_dir = Path(tmp_dir) / "output"
            instance_dir.mkdir()
            output_dir.mkdir()

            # Step 2: download benchmark input from IPFS.
            # ipfs_fetch is imported lazily to avoid circular imports and to allow
            # the module to be mocked independently in tests.
            from pwm_miner.ipfs_fetch import fetch_solver as _fetch_ipfs  # noqa: PLC0415

            benchmark_input_path = instance_dir / "benchmark_input"
            # benchmark_hash doubles as the IPFS CID for the input data.
            # We do not verify the hash of the input (it is publicly known), only
            # the solver binary SHA-256 is security-critical.
            # Signature: fetch_solver(cid, expected_hash) -> Path
            # Input data hash is public/untrusted; security-critical hash is solver_sha256.
            _fetch_ipfs(job.benchmark_hash, "")

            # Step 3: run solver (raises VerificationError if binary hash mismatch).
            limits = ResourceLimits(
                memory_mb=job.compute_manifest.memory_mb,
                timeout_seconds=job.compute_manifest.timeout_seconds,
                gpu_spec=job.compute_manifest.gpu_spec,
            )
            result = execute_solver(
                solver_cid=job.solver_cid,
                expected_hash=job.solver_sha256,
                instance_dir=instance_dir,
                output_dir=output_dir,
                limits=limits,
            )

            if not result.success:
                raise RuntimeError(
                    f"Solver execution failed for job {job.job_id}: {result.stderr}"
                )

            # Step 4: derive solution_preview from output.
            output_bytes = result.output_path.read_bytes()
            full_hash = hashlib.sha256(output_bytes).digest()
            solution_preview: bytes = full_hash[:32]

            # Step 5: generate nonce.
            nonce: bytes = os.urandom(32)

            # Step 6: commit (must be inside 0–30 s window).
            elapsed_before_commit = self._seconds_since_posted(job_posted_at)
            if elapsed_before_commit >= COMMIT_WINDOW_SECONDS:
                logger.warning(
                    "Solver took %.1f s — commit window already closed for job %s; aborting.",
                    elapsed_before_commit,
                    job.job_id,
                )
                raise CommitWindowExpiredError(
                    f"Solver elapsed {elapsed_before_commit:.1f}s >= commit window "
                    f"{COMMIT_WINDOW_SECONDS}s for job {job.job_id}"
                )

            self.commit(
                job.job_id,
                solution_preview,
                nonce,
                job_posted_at=job_posted_at,
            )

            # Step 7: reveal (waits for 30 s mark, then sends).
            self.reveal(
                job.job_id,
                solution_preview,
                nonce,
                job_posted_at=job_posted_at,
            )

        # Step 8: return cert_hash = keccak256(job_id_bytes ‖ solution_preview).
        job_id_bytes = self._job_id_to_bytes32(job.job_id)
        cert_hash: bytes = Web3.keccak(job_id_bytes + solution_preview)
        cert_hash_hex = "0x" + cert_hash.hex()
        logger.info("Job %s completed; cert_hash=%s", job.job_id, cert_hash_hex)
        return cert_hash_hex
