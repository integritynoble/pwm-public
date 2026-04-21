"""Tests for pwm_node.ipfs — mocked HTTP so no live IPFS node required.

Covers:
- upload calls POST /api/v0/add, returns Hash from response
- upload of missing file raises IPFSError
- upload HTTP failure raises IPFSError with actionable message
- download fetches via gateway
- download verifies SHA-256 when expected hash given
- download deletes bad file on SHA mismatch
- sha256_bytes helper
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pwm_node.ipfs import IPFSError, download, sha256_bytes, upload


def test_sha256_bytes_hex():
    assert sha256_bytes(b"hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_upload_missing_file_errors(tmp_path):
    missing = tmp_path / "nope.bin"
    with pytest.raises(IPFSError, match="not found"):
        upload(missing)


def test_upload_http_unreachable_errors(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"x")
    # Point at a definitely-unreachable port so requests raises
    with pytest.raises(IPFSError, match="cannot reach IPFS API"):
        upload(f, api_url="http://127.0.0.1:1")


def test_upload_happy_path(tmp_path):
    """Mock requests.post to return {Hash: <cid>}; upload should return the cid."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"some bytes")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"Name": "data.bin", "Hash": "bafy123test", "Size": "10"}

    with patch("pwm_node.ipfs.requests.post", return_value=mock_resp) as post_mock:
        cid = upload(f, api_url="http://fake:5001")
    assert cid == "bafy123test"
    # Called with pin=true, cid-version=1
    call = post_mock.call_args
    assert call.kwargs["params"] == {"pin": "true", "cid-version": "1"}


def test_upload_non_200_errors(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"x")
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "internal error"
    with patch("pwm_node.ipfs.requests.post", return_value=mock_resp):
        with pytest.raises(IPFSError, match="IPFS add failed.*500"):
            upload(f, api_url="http://fake:5001")


def test_upload_no_hash_in_response_errors(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"x")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"not_a_hash": "xyz"}
    with patch("pwm_node.ipfs.requests.post", return_value=mock_resp):
        with pytest.raises(IPFSError, match="no Hash/Cid"):
            upload(f, api_url="http://fake:5001")


def test_download_happy_path_no_verify(tmp_path):
    """Mock requests.get to stream bytes; download should write to dest."""
    content = b"downloaded content"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = iter([content])
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    dest = tmp_path / "out.bin"
    with patch("pwm_node.ipfs.requests.get", return_value=mock_resp):
        result = download("bafy1", dest, gateway_url="http://fake")
    assert result == dest
    assert dest.read_bytes() == content


def test_download_verifies_sha256_pass(tmp_path):
    """SHA-256 match on provided expected_sha256 → download succeeds."""
    content = b"verified content"
    expected = hashlib.sha256(content).hexdigest()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = iter([content])
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    dest = tmp_path / "verified.bin"
    with patch("pwm_node.ipfs.requests.get", return_value=mock_resp):
        download("bafy2", dest, expected_sha256=expected, gateway_url="http://fake")
    assert dest.exists()


def test_download_verifies_sha256_fail_deletes_file(tmp_path):
    """SHA-256 mismatch → IPFSError raised AND bad file deleted."""
    content = b"actual content"
    wrong_hash = "0" * 64  # definitely not the actual sha256
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = iter([content])
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    dest = tmp_path / "bad.bin"
    with patch("pwm_node.ipfs.requests.get", return_value=mock_resp):
        with pytest.raises(IPFSError, match="SHA-256 mismatch"):
            download("bafy3", dest, expected_sha256=wrong_hash, gateway_url="http://fake")
    assert not dest.exists(), "bad-download file should be deleted"


def test_download_non_200_errors(tmp_path):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "not found"
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    dest = tmp_path / "x.bin"
    with patch("pwm_node.ipfs.requests.get", return_value=mock_resp):
        with pytest.raises(IPFSError, match="IPFS fetch failed.*404"):
            download("bafy4", dest, gateway_url="http://fake")
    assert not dest.exists()
