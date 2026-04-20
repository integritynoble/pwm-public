"""Smoke tests for the event handlers and the DB layer.

These tests deliberately avoid the RPC path — they feed event args directly
into the handlers, which is what real logs would look like once decoded.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from indexer import db, handlers
from indexer.events import EventContext


@pytest.fixture()
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_db(c)
    yield c
    c.close()


def _ctx(block: int = 100, ts: int = 1_700_000_000, tx: str = "0xaa") -> EventContext:
    return EventContext(block_number=block, tx_hash=tx, timestamp=ts)


def test_artifact_registered_roundtrip(conn):
    handlers.handle_artifact_registered(
        conn,
        {"hash": b"\x01" * 32, "layer": 1, "creator": "0xABCD" + "0" * 36, "timestamp": 1700000000},
        _ctx(),
    )
    row = conn.execute("SELECT * FROM artifacts").fetchone()
    assert row["layer"] == 1
    assert row["hash"].startswith("0x01")
    assert row["creator"].startswith("0xabcd")


def test_certificate_submit_then_finalize(conn):
    cert_hash = b"\x02" * 32
    bench = b"\x03" * 32
    handlers.handle_certificate_submitted(
        conn,
        {"certHash": cert_hash, "benchmarkHash": bench, "submitter": "0x" + "ab" * 20, "Q_int": 95},
        _ctx(block=200),
    )
    handlers.handle_certificate_finalized(
        conn, {"certHash": cert_hash, "rank": 1}, _ctx(block=201)
    )
    row = conn.execute("SELECT * FROM certificates").fetchone()
    assert row["q_int"] == 95
    assert row["status"] == handlers.STATUS_FINALIZED
    assert row["finalized_rank"] == 1


def test_challenge_lifecycle(conn):
    cert_hash = b"\x04" * 32
    handlers.handle_certificate_submitted(
        conn,
        {"certHash": cert_hash, "benchmarkHash": b"\x05" * 32, "submitter": "0x" + "cd" * 20, "Q_int": 70},
        _ctx(),
    )
    handlers.handle_certificate_challenged(
        conn, {"certHash": cert_hash, "challenger": "0x" + "ef" * 20, "proof": b""}, _ctx()
    )
    handlers.handle_challenge_resolved(
        conn, {"certHash": cert_hash, "upheld": True}, _ctx()
    )
    row = conn.execute("SELECT status, challenge_upheld FROM certificates").fetchone()
    assert row["status"] == handlers.STATUS_INVALID
    assert row["challenge_upheld"] == 1


def test_draw_and_royalties(conn):
    cert_hash = b"\x06" * 32
    bench = b"\x07" * 32
    handlers.handle_draw_settled(
        conn,
        {
            "certHash": cert_hash,
            "benchmarkHash": bench,
            "rank": 2,
            "drawAmount": 10**18,
            "rolloverRemaining": 5 * 10**17,
        },
        _ctx(block=300),
    )
    handlers.handle_royalties_paid(
        conn,
        {
            "certHash": cert_hash,
            "ac": "0x" + "11" * 20,
            "acAmt": 10**17,
            "cp": "0x" + "22" * 20,
            "cpAmt": 10**17,
            "treasuryAmt": 5 * 10**16,
        },
        _ctx(block=300),
    )
    draw = conn.execute("SELECT * FROM draws").fetchone()
    royalty = conn.execute("SELECT * FROM royalties").fetchone()
    assert draw["rank"] == 2
    assert draw["draw_amount"] == str(10**18)
    assert royalty["ac_amount"] == str(10**17)


def test_pool_and_treasury(conn):
    handlers.handle_pool_seeded(
        conn,
        {
            "benchmarkHash": b"\x08" * 32,
            "amount": 10**18,
            "newBalance": 10**18,
            "from": "0x" + "aa" * 20,
            "kind": "A-pool-minting",
        },
        _ctx(),
    )
    handlers.handle_funds_received(
        conn,
        {"principleId": 3, "amount": 10**17, "newBalance": 10**17},
        _ctx(),
    )
    handlers.handle_bounty_paid(
        conn,
        {"principleId": 3, "winner": "0x" + "bb" * 20, "amount": 10**16, "newBalance": 9 * 10**16},
        _ctx(),
    )
    pool = conn.execute("SELECT * FROM pool_events").fetchone()
    treas = conn.execute("SELECT COUNT(*) AS n FROM treasury_events").fetchone()
    assert pool["kind"] == "A-pool-minting"
    assert treas["n"] == 2


def test_minting_benchmark_registration_and_rho(conn):
    bench = b"\xaa" * 32
    handlers.handle_benchmark_registered(
        conn, {"principleId": 3, "benchmarkHash": bench, "rho": 1}, _ctx(block=50, ts=1700)
    )
    row = conn.execute("SELECT * FROM benchmark_meta").fetchone()
    assert row["principle_id"] == "3"
    assert row["rho"] == "1"
    assert row["removed_at"] is None

    handlers.handle_benchmark_rho_updated(
        conn, {"principleId": 3, "benchmarkHash": bench, "rho": 2}, _ctx()
    )
    assert conn.execute("SELECT rho FROM benchmark_meta").fetchone()["rho"] == "2"

    handlers.handle_benchmark_removed(
        conn, {"principleId": 3, "benchmarkHash": bench}, _ctx(ts=1800)
    )
    assert conn.execute("SELECT removed_at FROM benchmark_meta").fetchone()["removed_at"] == 1800


def test_minting_delta_and_promotion(conn):
    handlers.handle_delta_set(conn, {"principleId": 7, "delta": 3}, _ctx())
    handlers.handle_promotion_set(conn, {"principleId": 7, "promoted": True}, _ctx())
    row = conn.execute("SELECT * FROM principle_meta WHERE principle_id = '7'").fetchone()
    assert row["delta"] == "3"
    assert row["promoted"] == 1


def test_minted_insert(conn):
    handlers.handle_minted(
        conn,
        {"principleId": 3, "benchmarkHash": b"\xbb" * 32,
         "A_k": 10**18, "A_kjb": 5 * 10**17, "remainingAfter": 42},
        _ctx(block=60),
    )
    r = conn.execute("SELECT * FROM mints").fetchone()
    assert r["a_k"] == str(10**18)
    assert r["remaining_after"] == "42"


def test_handlers_cover_minting_events():
    expected = {
        "BenchmarkRegistered", "BenchmarkRhoUpdated", "BenchmarkRemoved",
        "DeltaSet", "PromotionSet", "Minted",
    }
    actual = {event for (contract, event) in handlers.HANDLERS if contract == "PWMMinting"}
    assert expected <= actual


def test_schema_is_idempotent(tmp_path):
    c = db.connect(tmp_path / "x.db")
    db.init_db(c)
    db.init_db(c)  # running twice must not error
    # meta round-trip
    db.set_meta(c, "last_block", "42")
    assert db.get_meta(c, "last_block") == "42"
    c.close()
