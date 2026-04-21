"""
tests/test_job_queue.py — Unit tests for pwm_miner.job_queue.

All external dependencies (web3, IPFS HTTP) are fully mocked so the suite
runs without a live Ethereum node or internet access.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from pwm_miner.job_queue import (
    BENCHMARK_LAYER,
    ComputeManifest,
    Job,
    JobQueue,
    _bytes32_to_hex,
    _fetch_manifest,
    _parse_manifest,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_hash(n: int) -> bytes:
    """Return a deterministic 32-byte value for test event hashes."""
    return n.to_bytes(32, "big")


def _make_event(hash_bytes: bytes, layer: int = BENCHMARK_LAYER, creator: str = "0xDEAD") -> dict:
    """
    Build a dict that looks like a decoded web3 log entry for
    ArtifactRegistered.
    """
    return {
        "args": {
            "hash": hash_bytes,
            "layer": layer,
            "creator": creator,
            "timestamp": 1_700_000_000,
        },
        "blockNumber": 1,
        "transactionHash": b"\x00" * 32,
    }


def _make_manifest(
    *,
    min_vram_gb: int = 8,
    memory_mb: int = 4096,
    timeout_seconds: int = 300,
    gpu_spec: str = "all",
    expected_reward: float = 1.5,
    solver_cid: str = "QmXxx",
    solver_sha256: str = "abc123",
) -> dict[str, Any]:
    return {
        "solver_cid": solver_cid,
        "solver_sha256": solver_sha256,
        "compute_manifest": {
            "min_vram_gb": min_vram_gb,
            "memory_mb": memory_mb,
            "timeout_seconds": timeout_seconds,
            "gpu_spec": gpu_spec,
        },
        "expected_reward": expected_reward,
    }


def _make_job_queue(local_vram_gb: int = 8, start_block: int = 100) -> tuple[JobQueue, MagicMock]:
    """
    Create a JobQueue whose web3 internals are fully mocked.

    Returns
    -------
    (queue, mock_contract_events)
        queue               — the JobQueue instance
        mock_contract.events.ArtifactRegistered
                            — the MagicMock on which you can configure
                              get_logs return values
    """
    with patch("pwm_miner.job_queue.Web3") as MockWeb3:
        mock_w3 = MagicMock()
        mock_w3.eth.block_number = start_block
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.WebsocketProvider = MagicMock()
        MockWeb3.to_checksum_address = lambda addr: addr

        queue = JobQueue(web3_url="http://localhost:8545", local_vram_gb=local_vram_gb)

    return queue, mock_w3


# ---------------------------------------------------------------------------
# _bytes32_to_hex
# ---------------------------------------------------------------------------

class TestBytes32ToHex:
    def test_bytes_input(self):
        b = b"\x00" * 31 + b"\x01"
        assert _bytes32_to_hex(b) == "0x" + "00" * 31 + "01"

    def test_hex_string_with_prefix(self):
        assert _bytes32_to_hex("0xdeadbeef") == "0xdeadbeef"

    def test_hex_string_without_prefix(self):
        assert _bytes32_to_hex("deadbeef") == "0xdeadbeef"


# ---------------------------------------------------------------------------
# _fetch_manifest
# ---------------------------------------------------------------------------

class TestFetchManifest:
    def test_successful_fetch(self):
        manifest = _make_manifest(min_vram_gb=4, expected_reward=2.0)
        payload = json.dumps(manifest).encode()

        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = payload

        with patch("pwm_miner.job_queue.urlopen", return_value=mock_resp):
            result = _fetch_manifest("0xabcd1234")

        assert result["expected_reward"] == 2.0
        assert result["compute_manifest"]["min_vram_gb"] == 4

    def test_network_error_returns_defaults(self):
        from urllib.error import URLError

        with patch("pwm_miner.job_queue.urlopen", side_effect=URLError("timeout")):
            result = _fetch_manifest("0xdeadbeef")

        # Should return a dict with the default keys, not raise.
        assert "solver_cid" in result
        assert result["expected_reward"] == 0.0

    def test_bad_json_returns_defaults(self):
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = b"not-json!!!"

        with patch("pwm_miner.job_queue.urlopen", return_value=mock_resp):
            result = _fetch_manifest("0xbadcafe")

        assert result["expected_reward"] == 0.0


# ---------------------------------------------------------------------------
# _parse_manifest
# ---------------------------------------------------------------------------

class TestParseManifest:
    def test_full_manifest(self):
        manifest = _make_manifest(
            min_vram_gb=16,
            memory_mb=8192,
            timeout_seconds=600,
            gpu_spec="device=0",
            expected_reward=3.0,
            solver_cid="QmSolver",
            solver_sha256="sha256abc",
        )
        job = _parse_manifest(manifest, "0xdeadbeef")

        assert job.job_id == "0xdeadbeef"
        assert job.benchmark_hash == "0xdeadbeef"
        assert job.solver_cid == "QmSolver"
        assert job.solver_sha256 == "sha256abc"
        assert job.compute_manifest.min_vram_gb == 16
        assert job.compute_manifest.memory_mb == 8192
        assert job.compute_manifest.timeout_seconds == 600
        assert job.compute_manifest.gpu_spec == "device=0"
        assert job.expected_reward == 3.0

    def test_missing_keys_use_defaults(self):
        job = _parse_manifest({}, "cafebabe")

        # Hash should be 0x-prefixed.
        assert job.job_id == "0xcafebabe"
        assert job.compute_manifest.min_vram_gb == 0
        assert job.compute_manifest.gpu_spec == "none"
        assert job.expected_reward == 0.0

    def test_hash_without_prefix_gets_normalised(self):
        job = _parse_manifest({}, "aabbcc")
        assert job.job_id.startswith("0x")


# ---------------------------------------------------------------------------
# JobQueue — construction
# ---------------------------------------------------------------------------

class TestJobQueueInit:
    def test_last_block_set_to_current_head(self):
        queue, mock_w3 = _make_job_queue(start_block=500)
        assert queue._last_block == 500

    def test_claimed_set_is_empty_on_init(self):
        queue, _ = _make_job_queue()
        assert len(queue._claimed) == 0

    def test_block_number_failure_defaults_to_zero(self):
        with patch("pwm_miner.job_queue.Web3") as MockWeb3:
            mock_w3 = MagicMock()
            mock_w3.eth.block_number = PropertyError()  # attribute raises
            MockWeb3.return_value = mock_w3
            MockWeb3.HTTPProvider = MagicMock()
            MockWeb3.to_checksum_address = lambda a: a

            # Simulate an exception on block_number access.
            type(mock_w3.eth).block_number = property(
                lambda self: (_ for _ in ()).throw(Exception("rpc error"))
            )

            queue = JobQueue(web3_url="http://localhost:8545", local_vram_gb=0)

        assert queue._last_block == 0


# ---------------------------------------------------------------------------
# JobQueue.poll — core filtering and sorting behaviour
# ---------------------------------------------------------------------------

class TestJobQueuePoll:
    """
    All tests use a pre-built JobQueue whose internal Web3 objects are mocked
    via direct attribute injection after construction, which avoids re-patching
    the class on every test.
    """

    # ---- helpers --------------------------------------------------------

    def _queue_with_events(
        self,
        events: list[dict],
        local_vram_gb: int = 8,
        current_block: int = 110,
        start_block: int = 100,
        manifests: dict[str, dict] | None = None,
    ) -> JobQueue:
        """
        Return a JobQueue whose next poll() call will return *events* and
        whose IPFS manifest fetches are mocked using *manifests* (keyed by
        the 0x-hex job id).  Any hash not in *manifests* falls back to a
        default manifest with min_vram_gb=0 and expected_reward=0.
        """
        queue, mock_w3 = _make_job_queue(
            local_vram_gb=local_vram_gb, start_block=start_block
        )

        # After construction, wire up the per-test stubs.
        type(mock_w3.eth).block_number = property(lambda self: current_block)

        mock_event_class = MagicMock()
        mock_event_class.get_logs.return_value = events
        mock_w3.eth.contract.return_value.events.ArtifactRegistered = mock_event_class

        # Re-attach the contract so poll() uses our stubbed version.
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        manifests = manifests or {}

        def fake_fetch(hash_hex: str) -> dict:
            return manifests.get(hash_hex, _make_manifest(min_vram_gb=0, expected_reward=0.0))

        queue._fetch_manifest_fn = fake_fetch  # stored for use below
        return queue

    def _poll_with_mock_fetch(self, queue: JobQueue, manifests: dict[str, dict]) -> list[Job]:
        """Invoke queue.poll() with _fetch_manifest patched to use *manifests*."""
        def fake_fetch(hash_hex: str) -> dict:
            return manifests.get(hash_hex, _make_manifest(min_vram_gb=0, expected_reward=0.0))

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=fake_fetch):
            return queue.poll()

    # ---- tests ----------------------------------------------------------

    def test_poll_empty_when_no_new_blocks(self):
        queue, mock_w3 = _make_job_queue(start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 100)
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest"):
            result = queue.poll()

        assert result == []

    def test_poll_skips_non_layer3_events(self):
        queue, mock_w3 = _make_job_queue(start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 105)

        events = [
            _make_event(_make_hash(1), layer=1),  # content artifact — skip
            _make_event(_make_hash(2), layer=2),  # skip
        ]
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = events
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest") as mock_fetch:
            result = queue.poll()

        mock_fetch.assert_not_called()
        assert result == []

    def test_poll_filters_high_vram_jobs(self):
        """Job requiring 16 GB is dropped when local VRAM is 8 GB."""
        hash_hi = _make_hash(10)
        hash_lo = _make_hash(11)

        hash_hi_hex = _bytes32_to_hex(hash_hi)
        hash_lo_hex = _bytes32_to_hex(hash_lo)

        manifests = {
            hash_hi_hex: _make_manifest(min_vram_gb=16, expected_reward=5.0),
            hash_lo_hex: _make_manifest(min_vram_gb=4,  expected_reward=2.0),
        }

        queue, mock_w3 = _make_job_queue(local_vram_gb=8, start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 105)

        events = [
            _make_event(hash_hi, layer=BENCHMARK_LAYER),
            _make_event(hash_lo, layer=BENCHMARK_LAYER),
        ]
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = events
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda h: manifests.get(h, {})):
            result = queue.poll()

        assert len(result) == 1
        assert result[0].job_id == hash_lo_hex
        assert result[0].compute_manifest.min_vram_gb == 4

    def test_poll_returns_jobs_sorted_by_reward_descending(self):
        """poll() must return jobs highest-reward-first."""
        hashes = [_make_hash(i) for i in range(3)]
        hex_ids = [_bytes32_to_hex(h) for h in hashes]
        rewards = [1.0, 3.5, 2.0]

        manifests = {
            hid: _make_manifest(min_vram_gb=0, expected_reward=r)
            for hid, r in zip(hex_ids, rewards)
        }

        queue, mock_w3 = _make_job_queue(local_vram_gb=0, start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 105)

        events = [_make_event(h, layer=BENCHMARK_LAYER) for h in hashes]
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = events
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda h: manifests.get(h, {})):
            result = queue.poll()

        assert len(result) == 3
        assert result[0].expected_reward == 3.5
        assert result[1].expected_reward == 2.0
        assert result[2].expected_reward == 1.0

    def test_poll_advances_last_block_watermark(self):
        queue, mock_w3 = _make_job_queue(start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 150)

        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = []
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest"):
            queue.poll()

        assert queue._last_block == 150

    def test_poll_does_not_return_same_block_events_twice(self):
        """After one poll, same events should NOT re-appear on the next poll."""
        h = _make_hash(99)
        h_hex = _bytes32_to_hex(h)
        manifests = {h_hex: _make_manifest(min_vram_gb=0, expected_reward=1.0)}

        call_count = 0

        def block_number_side_effect(self_):
            nonlocal call_count
            call_count += 1
            return 105 if call_count <= 2 else 105  # always 105

        queue, mock_w3 = _make_job_queue(local_vram_gb=0, start_block=100)
        type(mock_w3.eth).block_number = property(block_number_side_effect)

        mock_event_class = mock_w3.eth.contract.return_value.events.ArtifactRegistered
        mock_event_class.get_logs.return_value = [_make_event(h, layer=BENCHMARK_LAYER)]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            first = queue.poll()
            # On the second call, block number hasn't advanced — from_block > to_block.
            mock_event_class.get_logs.return_value = []  # no new events
            second = queue.poll()

        assert len(first) == 1
        assert second == []


# ---------------------------------------------------------------------------
# JobQueue.claim
# ---------------------------------------------------------------------------

class TestJobQueueClaim:
    def test_claim_adds_to_claimed_set(self):
        queue, _ = _make_job_queue()
        queue.claim("0xdeadbeef")
        assert "0xdeadbeef" in queue._claimed

    def test_claim_normalises_missing_prefix(self):
        queue, _ = _make_job_queue()
        queue.claim("cafebabe")
        assert "0xcafebabe" in queue._claimed

    def test_claimed_job_absent_from_next_poll(self):
        """
        After claim(job_id), a subsequent poll() must NOT include that job,
        even if the underlying contract emits it again.
        """
        h = _make_hash(42)
        h_hex = _bytes32_to_hex(h)
        manifests = {h_hex: _make_manifest(min_vram_gb=0, expected_reward=9.9)}

        queue, mock_w3 = _make_job_queue(local_vram_gb=0, start_block=100)

        # First poll: block advances to 105, event present.
        type(mock_w3.eth).block_number = property(lambda self: 105)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(h, layer=BENCHMARK_LAYER)
        ]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            first = queue.poll()

        assert len(first) == 1
        assert first[0].job_id == h_hex

        # Claim the job.
        queue.claim(h_hex)

        # Second poll: block advances to 110, same event emitted again.
        type(mock_w3.eth).block_number = property(lambda self: 110)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(h, layer=BENCHMARK_LAYER)
        ]

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            second = queue.poll()

        assert second == [], "Claimed job must not re-appear after claim()"

    def test_claim_does_not_affect_other_jobs(self):
        h1 = _make_hash(1)
        h2 = _make_hash(2)
        h1_hex = _bytes32_to_hex(h1)
        h2_hex = _bytes32_to_hex(h2)

        manifests = {
            h1_hex: _make_manifest(min_vram_gb=0, expected_reward=1.0),
            h2_hex: _make_manifest(min_vram_gb=0, expected_reward=2.0),
        }

        queue, mock_w3 = _make_job_queue(local_vram_gb=0, start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 105)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(h1, layer=BENCHMARK_LAYER),
            _make_event(h2, layer=BENCHMARK_LAYER),
        ]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        # Claim h1 before polling.
        queue.claim(h1_hex)

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            result = queue.poll()

        # Only h2 should remain.
        assert len(result) == 1
        assert result[0].job_id == h2_hex


# ---------------------------------------------------------------------------
# Integration-style: parse ArtifactRegistered event end-to-end
# ---------------------------------------------------------------------------

class TestEventParsing:
    """Verify the full path from a raw ABI event to a Job struct."""

    def test_parse_layer3_event_to_job(self):
        raw_hash = _make_hash(7)
        raw_hex = _bytes32_to_hex(raw_hash)

        manifest = _make_manifest(
            min_vram_gb=8,
            memory_mb=4096,
            timeout_seconds=300,
            gpu_spec="all",
            expected_reward=1.5,
            solver_cid="QmSolver7",
            solver_sha256="deadbeef1234",
        )

        queue, mock_w3 = _make_job_queue(local_vram_gb=16, start_block=200)
        type(mock_w3.eth).block_number = property(lambda self: 205)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(raw_hash, layer=BENCHMARK_LAYER)
        ]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", return_value=manifest):
            jobs = queue.poll()

        assert len(jobs) == 1
        job = jobs[0]

        assert job.job_id == raw_hex
        assert job.benchmark_hash == raw_hex
        assert job.solver_cid == "QmSolver7"
        assert job.solver_sha256 == "deadbeef1234"
        assert job.compute_manifest.min_vram_gb == 8
        assert job.compute_manifest.memory_mb == 4096
        assert job.compute_manifest.timeout_seconds == 300
        assert job.compute_manifest.gpu_spec == "all"
        assert job.expected_reward == 1.5


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_vram_exact_match_is_accepted(self):
        """A job requiring exactly local_vram_gb should not be filtered."""
        h = _make_hash(55)
        h_hex = _bytes32_to_hex(h)
        manifests = {h_hex: _make_manifest(min_vram_gb=8, expected_reward=1.0)}

        queue, mock_w3 = _make_job_queue(local_vram_gb=8, start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 101)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(h, layer=BENCHMARK_LAYER)
        ]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            result = queue.poll()

        assert len(result) == 1

    def test_zero_vram_job_accepted_on_cpu_node(self):
        """A job with min_vram_gb=0 must be accepted on a CPU-only node."""
        h = _make_hash(66)
        h_hex = _bytes32_to_hex(h)
        manifests = {h_hex: _make_manifest(min_vram_gb=0, gpu_spec="none", expected_reward=0.5)}

        queue, mock_w3 = _make_job_queue(local_vram_gb=0, start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 101)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.return_value = [
            _make_event(h, layer=BENCHMARK_LAYER)
        ]
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest", side_effect=lambda hh: manifests.get(hh, {})):
            result = queue.poll()

        assert len(result) == 1
        assert result[0].compute_manifest.gpu_spec == "none"

    def test_rpc_error_during_poll_returns_empty_list(self):
        """If get_logs raises, poll() must return [] and not propagate the exception."""
        queue, mock_w3 = _make_job_queue(start_block=100)
        type(mock_w3.eth).block_number = property(lambda self: 110)
        mock_w3.eth.contract.return_value.events.ArtifactRegistered.get_logs.side_effect = (
            Exception("RPC timeout")
        )
        queue._contract = mock_w3.eth.contract.return_value
        queue._w3 = mock_w3

        with patch("pwm_miner.job_queue._fetch_manifest"):
            result = queue.poll()

        assert result == []


# Suppress the unused helper used only inside a property lambda.
class PropertyError(Exception):
    pass
