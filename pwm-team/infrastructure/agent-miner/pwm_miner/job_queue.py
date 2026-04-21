"""
job_queue.py — Poll PWMRegistry for benchmark jobs (Layer-3 ArtifactRegistered events).

Polls the PWMRegistry contract on Sepolia testnet for ArtifactRegistered events
where layer == 3 (compute benchmark jobs). For each new event it fetches the
job manifest from IPFS, filters jobs that exceed the local VRAM budget, and
returns the remaining jobs sorted by expected_reward descending.

Environment variables
---------------------
PWM_WEB3_URL      : WebSocket (or HTTP) URL for an Ethereum JSON-RPC provider.
                    Defaults to a placeholder Infura WSS URL.
PWM_LOCAL_VRAM_GB : Integer GB of GPU VRAM available locally.  Defaults to 0
                    (CPU-only — only layer-3 jobs with min_vram_gb == 0 pass).
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from web3 import Web3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contract constants
# ---------------------------------------------------------------------------

REGISTRY_ADDRESS = "0x2375217dd8FeC420707D53C75C86e2258FBaab65"

REGISTRY_ABI = [
    {
        "name": "ArtifactRegistered",
        "type": "event",
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "hash",      "type": "bytes32"},
            {"indexed": False, "name": "layer",     "type": "uint8"},
            {"indexed": True,  "name": "creator",   "type": "address"},
            {"indexed": False, "name": "timestamp", "type": "uint256"},
        ],
    }
]

# Only layer-3 artifacts are benchmark jobs.
BENCHMARK_LAYER = 3

# IPFS HTTP gateway used to fetch job manifests.
IPFS_GATEWAY = "https://ipfs.io/ipfs/{cid}"

# Timeout for IPFS HTTP requests (seconds).
IPFS_FETCH_TIMEOUT = 15

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ComputeManifest:
    """Hardware requirements extracted from the IPFS job manifest."""

    min_vram_gb: int
    memory_mb: int
    timeout_seconds: int
    gpu_spec: str  # "none" | "all" | "device=0" etc.


@dataclass
class Job:
    """A single benchmark job available on the network."""

    job_id: str            # hex of benchmark_hash bytes32 (0x-prefixed)
    benchmark_hash: str    # same as job_id, kept for clarity
    solver_cid: str        # IPFS CID of solver binary
    solver_sha256: str     # expected SHA-256 hex digest of solver binary
    compute_manifest: ComputeManifest
    expected_reward: float  # estimated PWM reward


# ---------------------------------------------------------------------------
# Default manifest used when IPFS fetch fails
# ---------------------------------------------------------------------------

_DEFAULT_MANIFEST: dict[str, Any] = {
    "solver_cid": "",
    "solver_sha256": "",
    "compute_manifest": {
        "min_vram_gb": 0,
        "memory_mb": 2048,
        "timeout_seconds": 300,
        "gpu_spec": "none",
    },
    "expected_reward": 0.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetch_manifest(benchmark_hash_hex: str) -> dict[str, Any]:
    """
    Fetch the JSON manifest for a benchmark job from IPFS.

    The manifest is stored at the IPFS gateway under the benchmark hash
    (without 0x prefix) as the CID-like path segment.  If the fetch fails
    for any reason (network error, bad JSON, timeout) sensible defaults are
    returned so the caller can still create a placeholder Job.

    Parameters
    ----------
    benchmark_hash_hex:
        The bytes32 hash as a hex string (with or without '0x' prefix).
    """
    cid = benchmark_hash_hex.lstrip("0x")
    url = IPFS_GATEWAY.format(cid=cid)
    try:
        with urlopen(url, timeout=IPFS_FETCH_TIMEOUT) as resp:
            raw = resp.read()
        data: dict[str, Any] = json.loads(raw)
        logger.debug("Fetched manifest for %s from %s", cid, url)
        return data
    except (URLError, json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "Failed to fetch IPFS manifest for %s (%s); using defaults.", cid, exc
        )
        return dict(_DEFAULT_MANIFEST)


def _parse_manifest(manifest: dict[str, Any], benchmark_hash_hex: str) -> Job:
    """
    Parse a raw manifest dict into a :class:`Job`.

    Missing keys fall back to the values in ``_DEFAULT_MANIFEST``.
    """
    cm_raw: dict[str, Any] = manifest.get("compute_manifest", {})
    cm = ComputeManifest(
        min_vram_gb=int(cm_raw.get("min_vram_gb", 0)),
        memory_mb=int(cm_raw.get("memory_mb", 2048)),
        timeout_seconds=int(cm_raw.get("timeout_seconds", 300)),
        gpu_spec=str(cm_raw.get("gpu_spec", "none")),
    )

    # Normalise the hash to 0x-prefixed lowercase.
    normalised = benchmark_hash_hex if benchmark_hash_hex.startswith("0x") else "0x" + benchmark_hash_hex

    return Job(
        job_id=normalised,
        benchmark_hash=normalised,
        solver_cid=str(manifest.get("solver_cid", "")),
        solver_sha256=str(manifest.get("solver_sha256", "")),
        compute_manifest=cm,
        expected_reward=float(manifest.get("expected_reward", 0.0)),
    )


def _bytes32_to_hex(value: bytes | str) -> str:
    """Convert a bytes32 value (returned by web3) to a 0x-prefixed hex string."""
    if isinstance(value, (bytes, bytearray)):
        return "0x" + value.hex()
    # Already a hex string — normalise.
    s = str(value)
    return s if s.startswith("0x") else "0x" + s


# ---------------------------------------------------------------------------
# JobQueue
# ---------------------------------------------------------------------------


@dataclass
class JobQueue:
    """
    Poll the PWMRegistry for benchmark (layer-3) jobs and maintain a local
    claimed-job set to prevent double-submission.

    Parameters
    ----------
    web3_url:
        JSON-RPC endpoint URL.  Reads ``PWM_WEB3_URL`` env var when not given.
    local_vram_gb:
        VRAM available on this machine in GB.  Jobs whose manifest specifies
        ``min_vram_gb > local_vram_gb`` are silently dropped.  Reads
        ``PWM_LOCAL_VRAM_GB`` env var when not given; defaults to 0 (CPU-only).
    """

    web3_url: str = field(
        default_factory=lambda: os.environ.get(
            "PWM_WEB3_URL",
            "wss://sepolia.infura.io/ws/v3/<YOUR_INFURA_KEY>",
        )
    )
    local_vram_gb: int = field(
        default_factory=lambda: int(os.environ.get("PWM_LOCAL_VRAM_GB", "0"))
    )

    # Internal state — not part of the public constructor signature.
    _w3: Web3 = field(init=False, repr=False, default=None)
    _contract: Any = field(init=False, repr=False, default=None)
    _last_block: int = field(init=False, repr=False, default=0)
    _claimed: set[str] = field(init=False, repr=False, default_factory=set)

    def __post_init__(self) -> None:
        if self.web3_url.startswith(("wss://", "ws://")):
            self._w3 = Web3(Web3.WebsocketProvider(self.web3_url))
        else:
            self._w3 = Web3(Web3.HTTPProvider(self.web3_url))

        self._contract = self._w3.eth.contract(
            address=Web3.to_checksum_address(REGISTRY_ADDRESS),
            abi=REGISTRY_ABI,
        )
        # Start polling from the current chain head so we only see new events.
        try:
            self._last_block = self._w3.eth.block_number
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch current block number: %s; starting from 0", exc)
            self._last_block = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll(self) -> list[Job]:
        """
        Fetch new ``ArtifactRegistered`` events (layer == 3) since the last
        call to ``poll()``, resolve each job's IPFS manifest, filter by VRAM,
        skip already-claimed jobs, and return the remainder sorted by
        ``expected_reward`` descending.

        Returns
        -------
        list[Job]
            Qualifying jobs sorted highest-reward-first.
        """
        try:
            current_block = self._w3.eth.block_number
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch block number during poll: %s", exc)
            return []

        if current_block < self._last_block:
            # Chain reorg or stale connection — reset to current.
            logger.warning(
                "current_block (%d) < last_block (%d); resetting poll window.",
                current_block,
                self._last_block,
            )
            self._last_block = current_block
            return []

        from_block = self._last_block + 1
        to_block = current_block

        if from_block > to_block:
            return []

        # Fetch all ArtifactRegistered events in [from_block, to_block].
        try:
            raw_events = self._contract.events.ArtifactRegistered.get_logs(
                fromBlock=from_block,
                toBlock=to_block,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error fetching events [%d..%d]: %s", from_block, to_block, exc)
            return []

        # Advance the watermark regardless of filtering results.
        self._last_block = to_block

        jobs: list[Job] = []
        for event in raw_events:
            args = event["args"]
            layer: int = args["layer"]
            if layer != BENCHMARK_LAYER:
                continue  # not a benchmark job

            benchmark_hash_hex = _bytes32_to_hex(args["hash"])

            # Skip already-claimed jobs.
            if benchmark_hash_hex in self._claimed:
                logger.debug("Skipping already-claimed job %s", benchmark_hash_hex)
                continue

            # Fetch and parse the IPFS manifest (tolerates failures).
            manifest = _fetch_manifest(benchmark_hash_hex)
            job = _parse_manifest(manifest, benchmark_hash_hex)

            # Filter by VRAM.
            if job.compute_manifest.min_vram_gb > self.local_vram_gb:
                logger.debug(
                    "Skipping job %s: requires %d GB VRAM, local=%d GB",
                    benchmark_hash_hex,
                    job.compute_manifest.min_vram_gb,
                    self.local_vram_gb,
                )
                continue

            jobs.append(job)

        # Sort highest expected_reward first.
        jobs.sort(key=lambda j: j.expected_reward, reverse=True)
        return jobs

    def claim(self, job_id: str) -> None:
        """
        Mark *job_id* as claimed locally so it will not appear in future
        ``poll()`` results for this process lifetime.

        Parameters
        ----------
        job_id:
            The ``job_id`` field of the :class:`Job` to claim (0x-prefixed
            bytes32 hex).
        """
        normalised = job_id if job_id.startswith("0x") else "0x" + job_id
        self._claimed.add(normalised)
        logger.debug("Claimed job %s", normalised)
