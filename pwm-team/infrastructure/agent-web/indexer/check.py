"""One-shot indexer health check.

Prints a compact summary of DB counts and cursor position. Exits 0 if the
indexer appears healthy (data rows present OR cursor recorded), 1 otherwise.

Run from infrastructure/agent-web/:
    PYTHONPATH=. python -m indexer.check
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

from . import config as config_mod
from . import db as db_mod


TABLES = (
    "artifacts",
    "certificates",
    "draws",
    "royalties",
    "pool_events",
    "treasury_events",
    "benchmark_meta",
    "principle_meta",
    "mints",
    "stakes",
)


def collect(conn: sqlite3.Connection) -> dict:
    def count(tbl: str) -> int:
        row = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
        return int(row[0]) if row else 0

    last_block = db_mod.get_meta(conn, "last_block")
    return {
        "last_block": int(last_block) if last_block else None,
        "counts": {t: count(t) for t in TABLES},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit as JSON")
    args = ap.parse_args()

    cfg = config_mod.load_config()
    conn = db_mod.connect(cfg.db_path)
    db_mod.init_db(conn)

    state = collect(conn)
    conn.close()

    if args.json:
        json.dump(state, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"db: {cfg.db_path}")
        print(f"network: {cfg.network}")
        print(f"last_block: {state['last_block'] if state['last_block'] is not None else '— (not yet indexed)'}")
        print("counts:")
        for tbl, n in state["counts"].items():
            print(f"  {tbl:20s} {n:>8d}")

    # "Healthy" = cursor recorded (indexer has run) OR some data present.
    any_rows = any(v > 0 for v in state["counts"].values())
    healthy = state["last_block"] is not None or any_rows
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
