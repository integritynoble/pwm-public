"""ipfs_fetch: Download solver binaries from IPFS with SHA-256 verification.

Security guarantee: a Path is NEVER returned until the file's SHA-256 has
been confirmed to match `expected_hash`.  Mismatched or partially-downloaded
files are deleted before raising VerificationError.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

# Default gateway used for HTTP fallback.
_IPFS_GATEWAY = os.environ.get("PWM_IPFS_GATEWAY", "https://ipfs.io/ipfs")

# Root cache directory (overridable for tests via env var).
_CACHE_ROOT = Path(os.environ.get("PWM_MINER_CACHE", Path.home() / ".pwm_miner" / "cache"))

# subprocess timeout for `ipfs get` (seconds).
_CLI_TIMEOUT = int(os.environ.get("PWM_IPFS_CLI_TIMEOUT", "300"))


class VerificationError(Exception):
    """Raised when a downloaded file's SHA-256 does not match the expected hash."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_solver(cid: str, expected_hash: str) -> Path:
    """Download a solver binary from IPFS, verify its SHA-256, and cache it.

    Parameters
    ----------
    cid:
        IPFS content identifier (e.g. ``"QmXyz..."``)
    expected_hash:
        Lowercase hex SHA-256 digest that the downloaded file must match.

    Returns
    -------
    Path
        Absolute path to the verified, cached binary.

    Raises
    ------
    VerificationError
        If the downloaded file's SHA-256 does not match *expected_hash*.
        The bad file is deleted before this exception is raised.
    RuntimeError
        If both the CLI and the HTTP gateway fail to download the file.
    """
    expected_hash = expected_hash.lower().strip()
    cache_path = _cache_path_for(cid)

    # --- Cache hit ---
    if cache_path.exists():
        cached_digest = _sha256(cache_path)
        if cached_digest == expected_hash:
            logger.debug("Cache hit for CID %s", cid)
            return cache_path
        # Stale / corrupt cache entry — remove and re-download.
        logger.warning(
            "Cached file for CID %s has unexpected hash %s (expected %s); re-downloading.",
            cid,
            cached_digest,
            expected_hash,
        )
        cache_path.unlink()

    # --- Download to a temp file, then verify before caching ---
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a sibling temp file so the final rename is atomic (same filesystem).
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=cache_path.parent, prefix=f".tmp_{cid}_")
    os.close(tmp_fd)
    tmp_path = Path(tmp_path_str)

    try:
        _download(cid, tmp_path)
        _verify_and_promote(cid, tmp_path, cache_path, expected_hash)
    except Exception:
        _safe_delete(tmp_path)
        raise

    return cache_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cache_path_for(cid: str) -> Path:
    """Return the canonical cache path for a given CID."""
    return _CACHE_ROOT / cid


def _sha256(path: Path) -> str:
    """Return the lowercase hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(cid: str, dest: Path) -> None:
    """Download CID to *dest*, trying the IPFS CLI first then HTTP fallback."""
    if _try_cli_download(cid, dest):
        return
    logger.info("IPFS CLI unavailable or failed for %s; falling back to HTTP gateway.", cid)
    _http_download(cid, dest)


def _try_cli_download(cid: str, dest: Path) -> bool:
    """Attempt ``ipfs get -o <dest> <cid>``.

    Returns True on success, False if the CLI is not available or exits
    non-zero.  Exceptions from the subprocess itself propagate only for
    genuine unexpected errors (not for a missing binary).
    """
    try:
        result = subprocess.run(
            ["ipfs", "get", "-o", str(dest), cid],
            capture_output=True,
            timeout=_CLI_TIMEOUT,
        )
        if result.returncode == 0:
            logger.debug("ipfs CLI download succeeded for CID %s", cid)
            return True
        logger.debug(
            "ipfs CLI exited %d for CID %s: %s",
            result.returncode,
            cid,
            result.stderr.decode(errors="replace"),
        )
        return False
    except FileNotFoundError:
        # `ipfs` binary not on PATH.
        logger.debug("ipfs CLI not found on PATH.")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("ipfs CLI timed out after %ds for CID %s.", _CLI_TIMEOUT, cid)
        return False


def _http_download(cid: str, dest: Path) -> None:
    """Download via HTTP gateway using only the stdlib ``urllib``."""
    url = f"{_IPFS_GATEWAY}/{cid}"
    logger.debug("HTTP download: %s -> %s", url, dest)
    try:
        with urllib.request.urlopen(url, timeout=_CLI_TIMEOUT) as response:
            with dest.open("wb") as fh:
                shutil.copyfileobj(response, fh)
    except Exception as exc:
        raise RuntimeError(
            f"HTTP gateway download failed for CID {cid} (url={url}): {exc}"
        ) from exc


def _verify_and_promote(
    cid: str, tmp_path: Path, cache_path: Path, expected_hash: str
) -> None:
    """Verify *tmp_path* SHA-256 and atomically rename to *cache_path*.

    Raises VerificationError (and cleans up *tmp_path*) on mismatch.
    """
    actual_hash = _sha256(tmp_path)
    if actual_hash != expected_hash:
        _safe_delete(tmp_path)
        raise VerificationError(
            f"Hash mismatch for CID {cid}: "
            f"expected={expected_hash} actual={actual_hash}. "
            "File deleted — refusing to cache unverified binary."
        )
    tmp_path.rename(cache_path)
    logger.info("Verified and cached solver for CID %s at %s", cid, cache_path)


def _safe_delete(path: Path) -> None:
    """Delete *path* without raising if it is already gone."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass
