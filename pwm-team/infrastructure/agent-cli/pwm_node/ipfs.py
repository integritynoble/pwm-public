"""IPFS upload/download with SHA-256 verification.

Uses a simple HTTP-gateway-first approach:
- Upload: POST to the local IPFS node's /api/v0/add endpoint (localhost:5001
  by default). Returns the CID.
- Download: fetch from ``https://{gateway}/ipfs/{cid}``; the default gateway
  is ``cloudflare-ipfs.com`` (public, no API key). Verifies SHA-256 after
  download if ``expected_sha256`` is provided.

Design notes:
- No global state; one function call = one IPFS operation.
- Gateway is overridable via ``PWM_IPFS_GATEWAY`` env var.
- Local node (for uploads) is overridable via ``PWM_IPFS_API`` env var.
- SHA-256 verification is always-on for downloads when expected hash is
  provided — failure raises ``IPFSError`` with the expected vs actual hash.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


class IPFSError(RuntimeError):
    """Raised for any IPFS failure (network, CID, hash mismatch)."""


def _default_api() -> str:
    """Local IPFS node API endpoint (kubo default port 5001)."""
    return os.environ.get("PWM_IPFS_API", "http://127.0.0.1:5001")


def _default_gateway() -> str:
    """Public IPFS gateway used for downloads when no local node available."""
    return os.environ.get("PWM_IPFS_GATEWAY", "https://cloudflare-ipfs.com")


def _require_requests() -> None:
    if not _REQUESTS_AVAILABLE:
        raise IPFSError(
            "requests library not installed. "
            "Run: pip install 'pwm-node' (which pulls in requests)"
        )


def _sha256_file(path: Path, *, chunk: int = 65536) -> str:
    """Compute hex-encoded SHA-256 of a file streamed in ``chunk``-byte blocks."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Hex SHA-256 of a byte buffer."""
    return hashlib.sha256(data).hexdigest()


def upload(path: Path, *, api_url: str | None = None, timeout_s: int = 120) -> str:
    """Upload a file to the local IPFS node. Returns the CID (hex string).

    Requires a running kubo (go-ipfs) daemon on PWM_IPFS_API. Falls back to
    localhost:5001 if unset. Files are pinned automatically (default kubo
    behavior).
    """
    _require_requests()
    path = Path(path)
    if not path.is_file():
        raise IPFSError(f"upload source not found or not a file: {path}")

    base = api_url or _default_api()
    url = urljoin(base.rstrip("/") + "/", "api/v0/add")

    try:
        with path.open("rb") as f:
            resp = requests.post(
                url,
                files={"file": (path.name, f)},
                params={"pin": "true", "cid-version": "1"},
                timeout=timeout_s,
            )
    except requests.exceptions.RequestException as e:
        raise IPFSError(
            f"cannot reach IPFS API at {url}: {e}. "
            f"Is a kubo daemon running? Try: ipfs daemon"
        )

    if resp.status_code != 200:
        raise IPFSError(f"IPFS add failed ({resp.status_code}): {resp.text}")

    try:
        meta = resp.json()
    except ValueError:
        raise IPFSError(f"IPFS add returned non-JSON: {resp.text[:200]}")

    cid = meta.get("Hash") or meta.get("Cid", {}).get("/")
    if not cid:
        raise IPFSError(f"IPFS add returned no Hash/Cid: {meta}")
    return cid


def download(
    cid: str,
    dest: Path,
    *,
    expected_sha256: str | None = None,
    gateway_url: str | None = None,
    timeout_s: int = 120,
) -> Path:
    """Fetch ``cid`` from an IPFS gateway to ``dest``. Returns the dest path.

    When ``expected_sha256`` is provided, verifies the downloaded file and
    raises ``IPFSError`` on mismatch (deleting the bad download).
    """
    _require_requests()
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    base = gateway_url or _default_gateway()
    url = f"{base.rstrip('/')}/ipfs/{cid}"

    try:
        with requests.get(url, stream=True, timeout=timeout_s) as resp:
            if resp.status_code != 200:
                raise IPFSError(
                    f"IPFS fetch failed ({resp.status_code}) for {cid} via {base}: "
                    f"{resp.text[:200]}"
                )
            with dest.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise IPFSError(f"cannot fetch {cid} from {url}: {e}")

    if expected_sha256:
        got = _sha256_file(dest)
        if got.lower() != expected_sha256.lower().removeprefix("0x"):
            try:
                dest.unlink()
            except OSError:
                pass
            raise IPFSError(
                f"SHA-256 mismatch for {cid}:\n"
                f"  expected: {expected_sha256}\n"
                f"  got:      {got}\n"
                f"  (bad file deleted)"
            )

    return dest
