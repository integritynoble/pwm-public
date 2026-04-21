"""Tests for pwm_miner.ipfs_fetch.

Covers:
  - Cache hit: returns immediately without any download
  - Successful download via IPFS CLI + hash verification → returns path
  - Hash mismatch → VerificationError raised, temp file deleted
  - CLI failure falls back to HTTP gateway
  - HTTP gateway failure raises RuntimeError
  - Stale cache entry (wrong hash) is re-downloaded
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import textwrap
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_CID = "QmFakeCid0000000000000000000000000000000000000000"
FAKE_CONTENT = b"fake solver binary content"
FAKE_HASH = hashlib.sha256(FAKE_CONTENT).hexdigest()
BAD_CONTENT = b"corrupted data"


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Redirect cache root to a tmp directory for every test."""
    import pwm_miner.ipfs_fetch as mod
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(mod, "_CACHE_ROOT", cache_dir)
    yield mod


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_cache_file(mod, cid: str, content: bytes) -> Path:
    """Write *content* directly into the cache (simulates a prior download)."""
    cache_path = mod._cache_path_for(cid)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)
    return cache_path


def _make_urlopen_response(content: bytes):
    """Return a mock urlopen context manager that yields *content*."""
    response = MagicMock()
    response.read = BytesIO(content).read
    # shutil.copyfileobj calls response.read(length); make it behave like a file.
    response.__enter__ = lambda s: BytesIO(content)
    response.__exit__ = MagicMock(return_value=False)
    return response


# ---------------------------------------------------------------------------
# Test: cache hit
# ---------------------------------------------------------------------------

class TestCacheHit:
    def test_returns_cached_path_without_download(self, isolated_cache):
        mod = isolated_cache
        cache_path = _write_cache_file(mod, FAKE_CID, FAKE_CONTENT)

        with (
            patch("subprocess.run") as mock_run,
            patch("urllib.request.urlopen") as mock_urlopen,
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert result == cache_path
        assert result.read_bytes() == FAKE_CONTENT
        mock_run.assert_not_called()
        mock_urlopen.assert_not_called()

    def test_cache_hit_accepts_uppercase_expected_hash(self, isolated_cache):
        """expected_hash should be normalised to lowercase before comparison."""
        mod = isolated_cache
        _write_cache_file(mod, FAKE_CID, FAKE_CONTENT)

        with patch("subprocess.run"), patch("urllib.request.urlopen"):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH.upper())

        assert result.read_bytes() == FAKE_CONTENT


# ---------------------------------------------------------------------------
# Test: CLI download + successful verification
# ---------------------------------------------------------------------------

class TestCliDownloadSuccess:
    def test_cli_success_returns_verified_path(self, isolated_cache, tmp_path):
        mod = isolated_cache

        def fake_subprocess_run(cmd, **kwargs):
            # Simulate `ipfs get` by writing FAKE_CONTENT to the dest path.
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(FAKE_CONTENT)
            result = MagicMock()
            result.returncode = 0
            return result

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run) as mock_run,
            patch("urllib.request.urlopen") as mock_urlopen,
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert result.exists()
        assert result.read_bytes() == FAKE_CONTENT
        assert result == mod._cache_path_for(FAKE_CID)
        mock_run.assert_called_once()
        mock_urlopen.assert_not_called()

    def test_cached_file_present_after_success(self, isolated_cache):
        mod = isolated_cache

        def fake_subprocess_run(cmd, **kwargs):
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(FAKE_CONTENT)
            r = MagicMock()
            r.returncode = 0
            return r

        with patch("subprocess.run", side_effect=fake_subprocess_run):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        # Second call should be a cache hit — no subprocess call.
        with (
            patch("subprocess.run") as mock_run,
            patch("urllib.request.urlopen") as mock_urlopen,
        ):
            result2 = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert result == result2
        mock_run.assert_not_called()
        mock_urlopen.assert_not_called()


# ---------------------------------------------------------------------------
# Test: hash mismatch
# ---------------------------------------------------------------------------

class TestHashMismatch:
    def test_raises_verification_error_on_mismatch(self, isolated_cache):
        mod = isolated_cache

        def fake_subprocess_run(cmd, **kwargs):
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(BAD_CONTENT)  # wrong content
            r = MagicMock()
            r.returncode = 0
            return r

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run),
            patch("urllib.request.urlopen"),
        ):
            with pytest.raises(mod.VerificationError) as exc_info:
                mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert FAKE_CID in str(exc_info.value)
        assert FAKE_HASH in str(exc_info.value)

    def test_temp_file_deleted_on_mismatch(self, isolated_cache):
        mod = isolated_cache
        cache_dir = mod._cache_path_for(FAKE_CID).parent
        cache_dir.mkdir(parents=True, exist_ok=True)

        def fake_subprocess_run(cmd, **kwargs):
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(BAD_CONTENT)
            r = MagicMock()
            r.returncode = 0
            return r

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run),
            patch("urllib.request.urlopen"),
        ):
            with pytest.raises(mod.VerificationError):
                mod.fetch_solver(FAKE_CID, FAKE_HASH)

        # No tmp files should remain.
        leftover = list(cache_dir.glob(".tmp_*"))
        assert leftover == [], f"Unexpected leftover temp files: {leftover}"

    def test_bad_file_not_cached_on_mismatch(self, isolated_cache):
        mod = isolated_cache

        def fake_subprocess_run(cmd, **kwargs):
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(BAD_CONTENT)
            r = MagicMock()
            r.returncode = 0
            return r

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run),
            patch("urllib.request.urlopen"),
        ):
            with pytest.raises(mod.VerificationError):
                mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert not mod._cache_path_for(FAKE_CID).exists()


# ---------------------------------------------------------------------------
# Test: CLI failure → HTTP gateway fallback
# ---------------------------------------------------------------------------

class TestHttpFallback:
    def _make_urlopen_cm(self, content: bytes):
        """Return a context-manager mock whose __enter__ returns a BytesIO."""
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=BytesIO(content))
        cm.__exit__ = MagicMock(return_value=False)
        return cm

    def test_cli_nonzero_falls_back_to_http(self, isolated_cache):
        mod = isolated_cache

        cli_result = MagicMock()
        cli_result.returncode = 1
        cli_result.stderr = b"error"

        urlopen_cm = self._make_urlopen_cm(FAKE_CONTENT)

        with (
            patch("subprocess.run", return_value=cli_result) as mock_run,
            patch("urllib.request.urlopen", return_value=urlopen_cm) as mock_urlopen,
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        mock_run.assert_called_once()
        mock_urlopen.assert_called_once()
        assert result.read_bytes() == FAKE_CONTENT

    def test_cli_not_found_falls_back_to_http(self, isolated_cache):
        mod = isolated_cache

        urlopen_cm = self._make_urlopen_cm(FAKE_CONTENT)

        with (
            patch("subprocess.run", side_effect=FileNotFoundError("ipfs not found")),
            patch("urllib.request.urlopen", return_value=urlopen_cm) as mock_urlopen,
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        mock_urlopen.assert_called_once()
        assert result.read_bytes() == FAKE_CONTENT

    def test_cli_timeout_falls_back_to_http(self, isolated_cache):
        mod = isolated_cache

        urlopen_cm = self._make_urlopen_cm(FAKE_CONTENT)

        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="ipfs", timeout=300),
            ),
            patch("urllib.request.urlopen", return_value=urlopen_cm) as mock_urlopen,
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        mock_urlopen.assert_called_once()
        assert result.read_bytes() == FAKE_CONTENT

    def test_http_mismatch_still_raises_verification_error(self, isolated_cache):
        mod = isolated_cache

        cli_result = MagicMock()
        cli_result.returncode = 1
        cli_result.stderr = b""

        urlopen_cm = self._make_urlopen_cm(BAD_CONTENT)  # wrong content via HTTP

        with (
            patch("subprocess.run", return_value=cli_result),
            patch("urllib.request.urlopen", return_value=urlopen_cm),
        ):
            with pytest.raises(mod.VerificationError):
                mod.fetch_solver(FAKE_CID, FAKE_HASH)

        assert not mod._cache_path_for(FAKE_CID).exists()


# ---------------------------------------------------------------------------
# Test: stale cache entry (hash mismatch on cached file)
# ---------------------------------------------------------------------------

class TestStaleCacheEntry:
    def test_stale_cache_triggers_redownload(self, isolated_cache):
        mod = isolated_cache
        # Plant a stale file with the wrong content.
        _write_cache_file(mod, FAKE_CID, BAD_CONTENT)

        def fake_subprocess_run(cmd, **kwargs):
            dest = Path(cmd[cmd.index("-o") + 1])
            dest.write_bytes(FAKE_CONTENT)
            r = MagicMock()
            r.returncode = 0
            return r

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run) as mock_run,
            patch("urllib.request.urlopen"),
        ):
            result = mod.fetch_solver(FAKE_CID, FAKE_HASH)

        mock_run.assert_called_once()
        assert result.read_bytes() == FAKE_CONTENT


# ---------------------------------------------------------------------------
# Test: HTTP gateway error
# ---------------------------------------------------------------------------

class TestHttpGatewayError:
    def test_both_cli_and_http_fail_raises_runtime_error(self, isolated_cache):
        mod = isolated_cache

        cli_result = MagicMock()
        cli_result.returncode = 1
        cli_result.stderr = b""

        with (
            patch("subprocess.run", return_value=cli_result),
            patch(
                "urllib.request.urlopen",
                side_effect=OSError("gateway unreachable"),
            ),
        ):
            with pytest.raises(RuntimeError, match="HTTP gateway download failed"):
                mod.fetch_solver(FAKE_CID, FAKE_HASH)
