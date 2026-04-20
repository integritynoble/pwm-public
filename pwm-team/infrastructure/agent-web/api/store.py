"""Read-only helpers over the indexer's SQLite DB.

All queries are simple enough that we hand-write them. No ORM.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


DEFAULT_DB = Path(__file__).resolve().parents[1] / "indexer" / "pwm_index.db"


def _db_path() -> Path:
    return Path(os.environ.get("PWM_DB", str(DEFAULT_DB)))


def get_conn() -> sqlite3.Connection:
    """Return a read-only connection if the DB exists; empty connection otherwise.

    The API must still return JSON skeletons when the indexer hasn't populated the
    DB yet (e.g. fresh deploys). We create the DB if missing so endpoints don't
    fail; it'll simply be empty.
    """
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        conn = sqlite3.connect(path)
        schema = Path(__file__).resolve().parents[1] / "indexer" / "schema.sql"
        if schema.exists():
            conn.executescript(schema.read_text())
            conn.commit()
        conn.row_factory = sqlite3.Row
        return conn
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- queries ----------

def artifacts_by_layer(conn: sqlite3.Connection, layer: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE layer = ? ORDER BY block_number DESC",
        (layer,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_artifact(conn: sqlite3.Connection, artifact_hash: str) -> dict | None:
    r = conn.execute("SELECT * FROM artifacts WHERE hash = ?", (artifact_hash.lower(),)).fetchone()
    return dict(r) if r else None


def certificates_for_benchmark(conn: sqlite3.Connection, benchmark_hash: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.*, d.rank AS draw_rank, d.draw_amount
          FROM certificates c
          LEFT JOIN draws d ON d.cert_hash = c.cert_hash
         WHERE c.benchmark_hash = ?
         ORDER BY (CASE WHEN d.rank IS NULL THEN 9999 ELSE d.rank END) ASC,
                  c.q_int DESC
        """,
        (benchmark_hash.lower(),),
    ).fetchall()
    return [dict(r) for r in rows]


def certificate(conn: sqlite3.Connection, cert_hash: str) -> dict | None:
    r = conn.execute(
        """
        SELECT c.*,
               d.rank AS draw_rank,
               d.draw_amount,
               d.rollover_remaining,
               d.settled_at,
               r.ac_addr, r.ac_amount,
               r.cp_addr, r.cp_amount,
               r.treasury_amount
          FROM certificates c
          LEFT JOIN draws     d ON d.cert_hash = c.cert_hash
          LEFT JOIN royalties r ON r.cert_hash = c.cert_hash
         WHERE c.cert_hash = ?
        """,
        (cert_hash.lower(),),
    ).fetchone()
    return dict(r) if r else None


def recent_draws(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM draws ORDER BY settled_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def pool_balance(conn: sqlite3.Connection, benchmark_hash: str) -> str | None:
    r = conn.execute(
        "SELECT new_balance FROM pool_events WHERE benchmark_hash = ? "
        "ORDER BY block_number DESC, id DESC LIMIT 1",
        (benchmark_hash.lower(),),
    ).fetchone()
    return r["new_balance"] if r else None


def treasury_balance(conn: sqlite3.Connection, principle_id: str) -> str | None:
    r = conn.execute(
        "SELECT new_balance FROM treasury_events WHERE principle_id = ? "
        "ORDER BY block_number DESC, id DESC LIMIT 1",
        (principle_id,),
    ).fetchone()
    return r["new_balance"] if r else None


def counts(conn: sqlite3.Connection) -> dict:
    def c(q: str, *args) -> int:
        row = conn.execute(q, args).fetchone()
        return int(row[0]) if row else 0
    return {
        "principles": c("SELECT COUNT(*) FROM artifacts WHERE layer = 1"),
        "specs": c("SELECT COUNT(*) FROM artifacts WHERE layer = 2"),
        "benchmarks": c("SELECT COUNT(*) FROM artifacts WHERE layer = 3"),
        "certificates": c("SELECT COUNT(*) FROM certificates"),
        "draws": c("SELECT COUNT(*) FROM draws"),
    }
