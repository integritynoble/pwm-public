"""Per-event handlers: translate decoded log -> DB rows.

Each handler is written to be pure: it takes a connection, an already-decoded
event dict (the `args` of a web3 log or a hand-crafted dict for tests), and an
EventContext, then writes to the database. That keeps tests fast -- no RPC,
no filters -- and keeps `main.py` short.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from . import db
from .events import EventContext, to_addr, to_hex


# PWMCertificate.Status enum (from the Solidity contract).
STATUS_PENDING = 0
STATUS_CHALLENGED = 1
STATUS_FINALIZED = 2
STATUS_INVALID = 3
STATUS_RESOLVED = 4


def handle_artifact_registered(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMRegistry.ArtifactRegistered(hash, layer, creator, timestamp)."""
    db.upsert_artifact(
        conn,
        hash=to_hex(args["hash"]),
        parent_hash=None,  # fetched separately via getArtifact if needed
        layer=int(args["layer"]),
        creator=to_addr(args["creator"]),
        timestamp=int(args["timestamp"]),
        block_number=ctx.block_number,
        tx_hash=ctx.tx_hash,
        artifact_id=None,
    )


def handle_certificate_submitted(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMCertificate.CertificateSubmitted(certHash, benchmarkHash, submitter, Q_int)."""
    db.upsert_certificate(
        conn,
        cert_hash=to_hex(args["certHash"]),
        benchmark_hash=to_hex(args["benchmarkHash"]),
        submitter=to_addr(args["submitter"]),
        q_int=int(args["Q_int"]),
        status=STATUS_PENDING,
        submitted_at=ctx.timestamp,
        block_number=ctx.block_number,
        tx_hash=ctx.tx_hash,
    )


def handle_certificate_challenged(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMCertificate.CertificateChallenged(certHash, challenger, proof)."""
    db.set_certificate_status(
        conn,
        cert_hash=to_hex(args["certHash"]),
        status=STATUS_CHALLENGED,
        challenger=to_addr(args["challenger"]),
    )


def handle_challenge_resolved(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMCertificate.ChallengeResolved(certHash, upheld)."""
    upheld = bool(args["upheld"])
    db.set_certificate_status(
        conn,
        cert_hash=to_hex(args["certHash"]),
        # upheld=True means challenge succeeded -> Invalid; else return to Resolved.
        status=STATUS_INVALID if upheld else STATUS_RESOLVED,
        challenge_upheld=1 if upheld else 0,
    )


def handle_certificate_finalized(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMCertificate.CertificateFinalized(certHash, rank)."""
    db.set_certificate_status(
        conn,
        cert_hash=to_hex(args["certHash"]),
        status=STATUS_FINALIZED,
        finalized_rank=int(args["rank"]),
    )


def handle_draw_settled(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMReward.DrawSettled(certHash, benchmarkHash, rank, drawAmount, rolloverRemaining)."""
    db.insert_draw(
        conn,
        cert_hash=to_hex(args["certHash"]),
        benchmark_hash=to_hex(args["benchmarkHash"]),
        rank=int(args["rank"]),
        draw_amount=str(int(args["drawAmount"])),
        rollover_remaining=str(int(args["rolloverRemaining"])),
        settled_at=ctx.timestamp,
        block_number=ctx.block_number,
        tx_hash=ctx.tx_hash,
    )


def handle_royalties_paid(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMReward.RoyaltiesPaid(certHash, ac, acAmt, cp, cpAmt, treasuryAmt)."""
    db.insert_royalty(
        conn,
        cert_hash=to_hex(args["certHash"]),
        ac_addr=to_addr(args["ac"]),
        ac_amount=str(int(args["acAmt"])),
        cp_addr=to_addr(args["cp"]),
        cp_amount=str(int(args["cpAmt"])),
        treasury_amount=str(int(args["treasuryAmt"])),
        paid_at=ctx.timestamp,
        block_number=ctx.block_number,
    )


def handle_pool_seeded(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMReward.PoolSeeded(benchmarkHash, amount, newBalance, from, kind)."""
    db.insert_pool_event(
        conn,
        benchmark_hash=to_hex(args["benchmarkHash"]),
        amount=str(int(args["amount"])),
        new_balance=str(int(args["newBalance"])),
        from_addr=to_addr(args["from"]),
        kind=str(args["kind"]),
        block_number=ctx.block_number,
        timestamp=ctx.timestamp,
    )


def handle_funds_received(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMTreasury.FundsReceived(principleId, amount, newBalance)."""
    db.insert_treasury_event(
        conn,
        principle_id=str(int(args["principleId"])),
        amount=str(int(args["amount"])),
        new_balance=str(int(args["newBalance"])),
        event_kind="received",
        winner=None,
        block_number=ctx.block_number,
        timestamp=ctx.timestamp,
    )


def handle_bounty_paid(
    conn: sqlite3.Connection, args: dict[str, Any], ctx: EventContext
) -> None:
    """PWMTreasury.BountyPaid(principleId, winner, amount, newBalance)."""
    db.insert_treasury_event(
        conn,
        principle_id=str(int(args["principleId"])),
        amount=str(int(args["amount"])),
        new_balance=str(int(args["newBalance"])),
        event_kind="bounty_paid",
        winner=to_addr(args["winner"]),
        block_number=ctx.block_number,
        timestamp=ctx.timestamp,
    )


# Lookup by (contract_name, event_name) — used by main.py.
HANDLERS = {
    ("PWMRegistry", "ArtifactRegistered"): handle_artifact_registered,
    ("PWMCertificate", "CertificateSubmitted"): handle_certificate_submitted,
    ("PWMCertificate", "CertificateChallenged"): handle_certificate_challenged,
    ("PWMCertificate", "ChallengeResolved"): handle_challenge_resolved,
    ("PWMCertificate", "CertificateFinalized"): handle_certificate_finalized,
    ("PWMReward", "DrawSettled"): handle_draw_settled,
    ("PWMReward", "RoyaltiesPaid"): handle_royalties_paid,
    ("PWMReward", "PoolSeeded"): handle_pool_seeded,
    ("PWMTreasury", "FundsReceived"): handle_funds_received,
    ("PWMTreasury", "BountyPaid"): handle_bounty_paid,
}
