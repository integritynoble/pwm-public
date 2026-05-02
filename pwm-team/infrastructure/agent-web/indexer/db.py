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


def upsert_cert_meta(conn: sqlite3.Connection, **row) -> None:
    """Off-chain enrichment posted by miners — solver label + PSNR dB.

    Last-write-wins on cert_hash; the cert hash itself is the proof of
    submission so anyone with it can post the meta. Lying doesn't change
    the on-chain Q_int / rank / reward.
    """
    conn.execute(
        """
        INSERT INTO cert_meta(cert_hash, solver_label, psnr_db,
                              runtime_sec, framework, meta_url,
                              posted_at, posted_by)
        VALUES(:cert_hash, :solver_label, :psnr_db,
               :runtime_sec, :framework, :meta_url,
               :posted_at, :posted_by)
        ON CONFLICT(cert_hash) DO UPDATE SET
            solver_label = excluded.solver_label,
            psnr_db      = excluded.psnr_db,
            runtime_sec  = excluded.runtime_sec,
            framework    = excluded.framework,
            meta_url     = excluded.meta_url,
            posted_at    = excluded.posted_at,
            posted_by    = excluded.posted_by
        """,
        row,
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


def upsert_benchmark_meta(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO benchmark_meta(benchmark_hash, principle_id, rho, registered_at, removed_at)
        VALUES(:benchmark_hash, :principle_id, :rho, :registered_at, NULL)
        ON CONFLICT(benchmark_hash) DO UPDATE SET
            principle_id = excluded.principle_id,
            rho = excluded.rho,
            registered_at = excluded.registered_at,
            removed_at = NULL
        """,
        row,
    )


def set_benchmark_rho(conn: sqlite3.Connection, benchmark_hash: str, rho: str) -> None:
    conn.execute(
        "UPDATE benchmark_meta SET rho = ? WHERE benchmark_hash = ?",
        (rho, benchmark_hash),
    )


def mark_benchmark_removed(conn: sqlite3.Connection, benchmark_hash: str, removed_at: int) -> None:
    conn.execute(
        "UPDATE benchmark_meta SET removed_at = ? WHERE benchmark_hash = ?",
        (removed_at, benchmark_hash),
    )


def upsert_principle_meta(
    conn: sqlite3.Connection,
    principle_id: str,
    updated_at: int,
    *,
    delta: str | None = None,
    promoted: int | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO principle_meta(principle_id, delta, promoted, updated_at)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(principle_id) DO UPDATE SET
            delta    = COALESCE(excluded.delta,    principle_meta.delta),
            promoted = COALESCE(excluded.promoted, principle_meta.promoted),
            updated_at = excluded.updated_at
        """,
        (principle_id, delta, promoted, updated_at),
    )


def insert_mint(conn: sqlite3.Connection, **row) -> None:
    conn.execute(
        """
        INSERT INTO mints(principle_id, benchmark_hash, a_k, a_kjb, remaining_after,
                          block_number, timestamp)
        VALUES(:principle_id, :benchmark_hash, :a_k, :a_kjb, :remaining_after,
               :block_number, :timestamp)
        """,
        row,
    )


def insert_stake(conn: sqlite3.Connection, **row) -> None:
    row.setdefault("layer", None)
    row.setdefault("seeded", None)
    row.setdefault("to_challenger", None)
    row.setdefault("burned", None)
    conn.execute(
        """
        INSERT INTO stakes(artifact_hash, layer, staker, amount, event_kind,
                            seeded, to_challenger, burned, block_number, timestamp)
        VALUES(:artifact_hash, :layer, :staker, :amount, :event_kind,
               :seeded, :to_challenger, :burned, :block_number, :timestamp)
        """,
        row,
    )
