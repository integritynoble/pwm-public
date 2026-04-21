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
import re
from pathlib import Path


# 12 struct fields in the ABI-declared order. camelCase keys match
# interfaces/cert_schema.json and the Solidity SubmitArgs struct exactly.
_REQUIRED_CERT_KEYS = (
    "certHash",
    "benchmarkHash",
    "principleId",
    "l1Creator",
    "l2Creator",
    "l3Creator",
    "acWallet",
    "cpWallet",
    "shareRatioP",
    "Q_int",
    "delta",
    "rank",
)

_BYTES32_HEX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_ADDRESS_HEX_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_ZERO_ADDR = "0x" + "0" * 40

_BYTES32_FIELDS = ("certHash", "benchmarkHash")
_ADDRESS_FIELDS = ("l1Creator", "l2Creator", "l3Creator", "acWallet", "cpWallet")
_INT_RANGES = {
    "principleId": (0, 2**256 - 1),
    "shareRatioP": (0, 10_000),
    "Q_int": (0, 100),
    "delta": (0, 255),
    "rank": (0, 255),
}


def _validate_cert(payload: dict) -> list[str]:
    """Return a list of validation errors. Empty list = valid.

    Validates the 12-field SubmitArgs schema (interfaces/cert_schema.json):
    bytes32 hex for certHash/benchmarkHash, address hex for the five wallet
    fields, and non-negative integers within uint range for the rest.

    Extras: rejects zero-address fields (all-zero wallets are a signal that
    the cert was built offline/dry-run without a signer configured, and
    submitting such a cert wastes gas).
    """
    errors: list[str] = []
    for key in _REQUIRED_CERT_KEYS:
        if key not in payload:
            errors.append(f"missing required key: {key!r}")
    if errors:
        return errors

    for f in _BYTES32_FIELDS:
        v = payload[f]
        if not isinstance(v, str) or not _BYTES32_HEX_RE.match(v):
            errors.append(f"{f} must be 0x + 64 hex chars, got {v!r}")

    for f in _ADDRESS_FIELDS:
        v = payload[f]
        if not isinstance(v, str) or not _ADDRESS_HEX_RE.match(v):
            errors.append(f"{f} must be 0x + 40 hex chars, got {v!r}")
            continue
        if v.lower() == _ZERO_ADDR:
            errors.append(
                f"{f} is the zero address — the cert was likely built with no "
                "signer configured. Set PWM_PRIVATE_KEY or pass --sp-wallet and rebuild."
            )

    for f, (lo, hi) in _INT_RANGES.items():
        v = payload[f]
        if not isinstance(v, int) or isinstance(v, bool):
            errors.append(f"{f} must be an integer, got {type(v).__name__}")
            continue
        if not (lo <= v <= hi):
            errors.append(f"{f} must be in [{lo}, {hi}], got {v}")

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

    # Strip the optional human-readable metadata before validating: the chain
    # submission only carries the 12 struct fields, and _meta is additive.
    payload.pop("_meta", None)

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
