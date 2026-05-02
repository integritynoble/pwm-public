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
        SELECT c.*, d.rank AS draw_rank, d.draw_amount,
               m.solver_label, m.psnr_db, m.runtime_sec, m.framework,
               m.meta_url, m.posted_at AS meta_posted_at
          FROM certificates c
          LEFT JOIN draws     d ON d.cert_hash = c.cert_hash
          LEFT JOIN cert_meta m ON m.cert_hash = c.cert_hash
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
               r.treasury_amount,
               m.solver_label, m.psnr_db, m.runtime_sec, m.framework,
               m.meta_url, m.posted_at AS meta_posted_at
          FROM certificates c
          LEFT JOIN draws     d ON d.cert_hash = c.cert_hash
          LEFT JOIN royalties r ON r.cert_hash = c.cert_hash
          LEFT JOIN cert_meta m ON m.cert_hash = c.cert_hash
         WHERE c.cert_hash = ?
        """,
        (cert_hash.lower(),),
    ).fetchone()
    return dict(r) if r else None


# ---------- write path: cert meta enrichment ----------

def upsert_cert_meta_via_api(
    conn: sqlite3.Connection,
    *,
    cert_hash: str,
    solver_label: str,
    psnr_db: float | None,
    runtime_sec: float | None,
    framework: str | None,
    meta_url: str | None,
    posted_at: int,
    posted_by: str,
) -> None:
    """Inserts/updates a row in cert_meta. Caller has already validated that
    cert_hash exists in certificates (i.e. is on-chain via the indexer).

    NOTE: this opens a writable connection on the same DB the indexer uses.
    Both writers (indexer + API) coexist via SQLite's WAL journal mode set
    in indexer/db.py."""
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
        {
            "cert_hash": cert_hash,
            "solver_label": solver_label,
            "psnr_db": psnr_db,
            "runtime_sec": runtime_sec,
            "framework": framework,
            "meta_url": meta_url,
            "posted_at": posted_at,
            "posted_by": posted_by,
        },
    )


def certificate_submitter(conn: sqlite3.Connection, cert_hash: str) -> str | None:
    """Lookup helper for the cert-meta endpoint: returns the on-chain
    submitter address, or None if the cert isn't in the indexer DB."""
    r = conn.execute(
        "SELECT submitter FROM certificates WHERE cert_hash = ?",
        (cert_hash.lower(),),
    ).fetchone()
    return r["submitter"] if r else None


def get_writable_conn() -> sqlite3.Connection:
    """Return a writable connection (read/write) — the regular get_conn() is
    read-only after the indexer has populated the DB. Used only by the
    cert-meta POST endpoint."""
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    # Ensure schema exists (idempotent IF NOT EXISTS).
    schema = Path(__file__).resolve().parents[1] / "indexer" / "schema.sql"
    if schema.exists():
        conn.executescript(schema.read_text())
        conn.commit()
    return conn


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
        "registered_benchmarks": c(
            "SELECT COUNT(*) FROM benchmark_meta WHERE removed_at IS NULL"
        ),
        "mints": c("SELECT COUNT(*) FROM mints"),
        "stakes": c("SELECT COUNT(*) FROM stakes"),
    }


# ---- PWMMinting-side queries ----

def benchmark_meta(conn: sqlite3.Connection, benchmark_hash: str) -> dict | None:
    r = conn.execute(
        "SELECT * FROM benchmark_meta WHERE benchmark_hash = ?",
        (benchmark_hash.lower(),),
    ).fetchone()
    return dict(r) if r else None


def benchmarks_for_principle(conn: sqlite3.Connection, principle_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM benchmark_meta WHERE principle_id = ? AND removed_at IS NULL "
        "ORDER BY registered_at DESC",
        (principle_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def principle_meta(conn: sqlite3.Connection, principle_id: str) -> dict | None:
    r = conn.execute(
        "SELECT * FROM principle_meta WHERE principle_id = ?",
        (principle_id,),
    ).fetchone()
    return dict(r) if r else None


def total_minted_for_principle(conn: sqlite3.Connection, principle_id: str) -> str:
    r = conn.execute(
        "SELECT COALESCE(SUM(CAST(a_k AS INTEGER)), 0) FROM mints WHERE principle_id = ?",
        (principle_id,),
    ).fetchone()
    return str(int(r[0])) if r else "0"


def counts_include_stakes(conn: sqlite3.Connection) -> int:
    r = conn.execute("SELECT COUNT(*) FROM stakes").fetchone()
    return int(r[0]) if r else 0


def recent_activity(conn: sqlite3.Connection, limit: int = 30) -> list[dict]:
    """Unified chronological feed across artifact / cert / draw / pool / stake tables.

    Each row returns a normalised shape:
        {kind, timestamp, block_number, ...event-specific fields}
    UNION ALL is deliberate — we want every event once; DISTINCT isn't needed.
    """
    rows = conn.execute(
        """
        SELECT * FROM (
          SELECT 'artifact_registered' AS kind, timestamp, block_number,
                 hash AS primary_hash, creator AS actor, layer, NULL AS amount,
                 NULL AS secondary_hash, NULL AS extra
            FROM artifacts
          UNION ALL
          SELECT 'benchmark_registered', registered_at, 0,
                 benchmark_hash, NULL, 3, rho, NULL, principle_id
            FROM benchmark_meta
          UNION ALL
          SELECT 'certificate_submitted', submitted_at, block_number,
                 cert_hash, submitter, NULL, q_int, benchmark_hash, status
            FROM certificates
          UNION ALL
          SELECT 'draw_settled', settled_at, block_number,
                 cert_hash, NULL, rank, draw_amount, benchmark_hash, NULL
            FROM draws
          UNION ALL
          SELECT 'pool_seeded', timestamp, block_number,
                 benchmark_hash, from_addr, NULL, amount, NULL, kind
            FROM pool_events
          UNION ALL
          SELECT 'treasury_' || event_kind, timestamp, block_number,
                 principle_id, winner, NULL, amount, NULL, new_balance
            FROM treasury_events
          UNION ALL
          SELECT 'stake_' || event_kind, timestamp, block_number,
                 artifact_hash, staker, layer, amount, NULL, burned
            FROM stakes
          UNION ALL
          SELECT 'minted', timestamp, block_number,
                 benchmark_hash, NULL, NULL, a_k, NULL, principle_id
            FROM mints
        ) ORDER BY timestamp DESC, block_number DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
