"""pwm-node submit-cert — submit a signed L4 certificate to PWMCertificate.

Flow:
1. Load cert_payload from --cert <path> (JSON file).
2. Validate against cert_schema.json (required keys only; strict schema check
   deferred to the scoring engine's own validator).
3. Optionally upload full payload to IPFS (--ipfs-upload).
4. Call chain.submit_certificate(payload).
5. Wait for tx, print tx_hash + block number + gas used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# Minimum keys a cert_payload must have per interfaces/cert_schema.json
# (Full schema validation deferred to pwm_scoring.cert.validate; this is a
# fast local pre-check so users don't burn gas on an obviously-malformed cert.)
_REQUIRED_CERT_KEYS = {
    "cert_hash",
    "h_p",
    "h_s",
    "h_b",
    "h_x",
    "Q",
    "gate_verdicts",
}


def _validate_cert(payload: dict) -> list[str]:
    """Return a list of missing/bad-typed keys. Empty list = valid."""
    errors = []
    for key in _REQUIRED_CERT_KEYS:
        if key not in payload:
            errors.append(f"missing required key: {key!r}")
    if "Q" in payload and not isinstance(payload["Q"], (int, float)):
        errors.append(f"Q must be int or float, got {type(payload['Q']).__name__}")
    if "Q" in payload and isinstance(payload["Q"], (int, float)):
        if not (0.0 <= float(payload["Q"]) <= 1.0):
            errors.append(f"Q must be in [0.0, 1.0], got {payload['Q']}")
    gv = payload.get("gate_verdicts")
    if gv is not None and not isinstance(gv, dict):
        errors.append(f"gate_verdicts must be a dict, got {type(gv).__name__}")
    return errors


def run(args: argparse.Namespace) -> int:
    """Submit cert. Returns 0 on success, non-zero on any failure class."""
    if args.network == "offline":
        print(
            "[pwm-node submit-cert] --network offline cannot submit. "
            "Use --network testnet for first-time submission."
        )
        return 1

    cert_path: Path = args.cert
    if not cert_path.is_file():
        print(f"[pwm-node submit-cert] cert file not found: {cert_path}")
        return 1

    try:
        payload = json.loads(cert_path.read_text())
    except json.JSONDecodeError as e:
        print(f"[pwm-node submit-cert] invalid JSON in {cert_path}: {e}")
        return 1

    errors = _validate_cert(payload)
    if errors:
        print(f"[pwm-node submit-cert] cert payload validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 4

    # Optionally upload the full payload to IPFS for external verifiers
    if args.ipfs_upload:
        try:
            from pwm_node.ipfs import IPFSError, upload
        except ImportError as e:
            print(f"[pwm-node submit-cert] IPFS unavailable: {e}")
            return 1
        try:
            cid = upload(cert_path)
            print(f"[pwm-node submit-cert] uploaded to IPFS: {cid}")
            payload["ipfs_cid"] = cid
        except IPFSError as e:
            print(f"[pwm-node submit-cert] IPFS upload failed: {e}")
            if not args.skip_ipfs_on_failure:
                return 5
            print("[pwm-node submit-cert] continuing without IPFS CID (--skip-ipfs-on-failure)")

    if args.dry_run:
        print("[pwm-node submit-cert] --dry-run: would submit:")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    try:
        from pwm_node.chain import ChainError, PWMChain
    except ImportError as e:
        print(f"[pwm-node submit-cert] chain unavailable: {e}")
        return 1

    try:
        chain = PWMChain(network=args.network)
        if not chain.signer_address():
            print(
                "[pwm-node submit-cert] PWM_PRIVATE_KEY env var required for submission. "
                "Set it, then retry."
            )
            return 1
        print(f"[pwm-node submit-cert] signer: {chain.signer_address()}")
        print(f"[pwm-node submit-cert] submitting to PWMCertificate on {chain.network}...")
        tx_hash = chain.submit_certificate(payload, gas=args.gas)
        print(f"[pwm-node submit-cert] tx submitted: {tx_hash}")
        if not args.no_wait:
            receipt = chain.wait_for_tx(tx_hash, timeout_s=args.timeout)
            print(
                f"[pwm-node submit-cert] confirmed in block {receipt.get('blockNumber')}, "
                f"gas used {receipt.get('gasUsed')}"
            )
        return 0
    except ChainError as e:
        print(f"[pwm-node submit-cert] chain error: {e}")
        return 1
