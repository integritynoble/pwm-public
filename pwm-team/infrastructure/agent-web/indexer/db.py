"""SQLite persistence for the indexer."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def upsert_artifact(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO artifacts(hash, parent_hash, layer, creator, timestamp, block_number, tx_hash, artifact_id)
        VALUES(:hash, :parent_hash, :layer, :creator, :timestamp, :block_number, :tx_hash, :artifact_id)
        ON CONFLICT(hash) DO UPDATE SET
            parent_hash = excluded.parent_hash,
            layer = excluded.layer,
            creator = excluded.creator,
            timestamp = excluded.timestamp,
            block_number = excluded.block_number,
            tx_hash = excluded.tx_hash,
            artifact_id = COALESCE(excluded.artifact_id, artifacts.artifact_id)
        """,
        row,
    )


def upsert_certificate(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO certificates(cert_hash, benchmark_hash, submitter, q_int, status,
                                  submitted_at, block_number, tx_hash)
        VALUES(:cert_hash, :benchmark_hash, :submitter, :q_int, :status,
               :submitted_at, :block_number, :tx_hash)
        ON CONFLICT(cert_hash) DO UPDATE SET
            benchmark_hash = excluded.benchmark_hash,
            submitter = excluded.submitter,
            q_int = excluded.q_int,
            submitted_at = excluded.submitted_at,
            block_number = excluded.block_number,
            tx_hash = excluded.tx_hash
        """,
        row,
    )


def set_certificate_status(
    conn: sqlite3.Connection,
    cert_hash: str,
    status: int,
    *,
    finalized_rank: int | None = None,
    challenger: str | None = None,
    challenge_upheld: int | None = None,
) -> None:
    conn.execute(
        """
        UPDATE certificates
           SET status = ?,
               finalized_rank = COALESCE(?, finalized_rank),
               challenger = COALESCE(?, challenger),
               challenge_upheld = COALESCE(?, challenge_upheld)
         WHERE cert_hash = ?
        """,
        (status, finalized_rank, challenger, challenge_upheld, cert_hash),
    )


def insert_draw(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO draws(cert_hash, benchmark_hash, rank, draw_amount, rollover_remaining,
                          settled_at, block_number, tx_hash)
        VALUES(:cert_hash, :benchmark_hash, :rank, :draw_amount, :rollover_remaining,
               :settled_at, :block_number, :tx_hash)
        ON CONFLICT(cert_hash) DO UPDATE SET
            rank = excluded.rank,
            draw_amount = excluded.draw_amount,
            rollover_remaining = excluded.rollover_remaining,
            settled_at = excluded.settled_at
        """,
        row,
    )


def insert_royalty(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO royalties(cert_hash, ac_addr, ac_amount, cp_addr, cp_amount,
                              treasury_amount, paid_at, block_number)
        VALUES(:cert_hash, :ac_addr, :ac_amount, :cp_addr, :cp_amount,
               :treasury_amount, :paid_at, :block_number)
        ON CONFLICT(cert_hash) DO UPDATE SET
            ac_amount = excluded.ac_amount,
            cp_amount = excluded.cp_amount,
            treasury_amount = excluded.treasury_amount,
            paid_at = excluded.paid_at
        """,
        row,
    )


def insert_pool_event(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO pool_events(benchmark_hash, amount, new_balance, from_addr, kind,
                                block_number, timestamp)
        VALUES(:benchmark_hash, :amount, :new_balance, :from_addr, :kind,
               :block_number, :timestamp)
        """,
        row,
    )


def insert_treasury_event(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO treasury_events(principle_id, amount, new_balance, event_kind, winner,
                                     block_number, timestamp)
        VALUES(:principle_id, :amount, :new_balance, :event_kind, :winner,
               :block_number, :timestamp)
        """,
        row,
    )
