"""PWM REST API — read-only chain+genesis view.

Run directly:  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from . import bounties, genesis, matching, store


app = FastAPI(
    title="PWM Web Explorer API",
    version="0.1.0",
    description="Read-only view of PWM on-chain state joined with genesis artifacts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CACHE_SECONDS = int(os.environ.get("PWM_CACHE_SECONDS", "60"))


def _cached(body: Any) -> Response:
    return Response(
        content=json.dumps(body, default=str),
        media_type="application/json",
        headers={"Cache-Control": f"public, max-age={CACHE_SECONDS}"},
    )


def _load_addresses() -> dict:
    try:
        _default_addr = str(Path(__file__).resolve().parents[3] / "coordination" / "agent-coord" / "interfaces" / "addresses.json")
    except IndexError:
        _default_addr = "/coord/addresses.json"
    p = Path(os.environ.get("PWM_ADDRESSES", _default_addr))
    try:
        return json.loads(p.read_text())
    except OSError:
        return {}


# ---------- routes ----------

@app.get("/api/health")
def health():
    import time
    conn = store.get_conn()
    try:
        last_block_row = conn.execute(
            "SELECT value FROM meta WHERE key='last_block'"
        ).fetchone()
        last_block = int(last_block_row[0]) if last_block_row else None
        # Freshness: the indexer writes `last_block` each scan. If it hasn't
        # been updated for > PWM_STALE_SECONDS (default 10 min = 2x the bounty
        # "updates within <=5 min" criterion), we report degraded.
        latest_event_row = conn.execute(
            "SELECT MAX(timestamp) FROM ("
            " SELECT timestamp FROM artifacts UNION ALL"
            " SELECT submitted_at FROM certificates UNION ALL"
            " SELECT settled_at FROM draws UNION ALL"
            " SELECT timestamp FROM pool_events UNION ALL"
            " SELECT timestamp FROM treasury_events UNION ALL"
            " SELECT timestamp FROM stakes UNION ALL"
            " SELECT timestamp FROM mints"
            ")"
        ).fetchone()
        latest_event_ts = int(latest_event_row[0]) if latest_event_row and latest_event_row[0] else None
        stale_seconds = int(os.environ.get("PWM_STALE_SECONDS", "600"))
        now = int(time.time())
        if last_block is None:
            status = "bootstrapping"
        elif latest_event_ts and (now - latest_event_ts) > stale_seconds:
            status = "degraded"
        else:
            status = "healthy"
        return _cached({
            "ok": True,
            "status": status,
            "last_indexed_block": last_block,
            "latest_event_timestamp": latest_event_ts,
            "counts": store.counts(conn),
            "genesis": {
                "l1": len(genesis.principles()),
                "l2": len(genesis.specs()),
                "l3": len(genesis.benchmarks()),
            },
        })
    finally:
        conn.close()


@app.get("/api/network")
def network():
    """Describe the chain this API is pointed at."""
    addrs = _load_addresses()
    net = os.environ.get("PWM_NETWORK", "testnet")
    return _cached({"network": net, "addresses": addrs.get(net, {})})


@app.get("/api/overview")
def overview():
    """Home-page summary: pool totals, active principles, recent draws."""
    conn = store.get_conn()
    try:
        c = store.counts(conn)
        draws = store.recent_draws(conn, limit=10)
        # Total "pool remaining" = sum of latest pool_event.new_balance per benchmark.
        total_pool = 0
        rows = conn.execute(
            """
            SELECT benchmark_hash,
                   (SELECT new_balance FROM pool_events p2
                    WHERE p2.benchmark_hash = pool_events.benchmark_hash
                    ORDER BY p2.block_number DESC, p2.id DESC LIMIT 1) AS balance
              FROM pool_events
             GROUP BY benchmark_hash
            """
        ).fetchall()
        for r in rows:
            try:
                total_pool += int(r["balance"] or 0)
            except (TypeError, ValueError):
                pass
        activity = store.recent_activity(conn, limit=20)
        return _cached({
            "counts": c,
            "active_principles": len(genesis.principles()),
            "total_pool_wei": str(total_pool),
            "recent_draws": draws,
            "recent_activity": activity,
        })
    finally:
        conn.close()


@app.get("/api/activity")
def activity_feed(limit: int = 50):
    """Chronological feed of every indexed event across contracts."""
    limit = max(1, min(200, int(limit)))
    conn = store.get_conn()
    try:
        return _cached({"activity": store.recent_activity(conn, limit=limit)})
    finally:
        conn.close()


@app.get("/api/principles")
def principles_list():
    chain_principles = []
    conn = store.get_conn()
    try:
        chain_principles = store.artifacts_by_layer(conn, 1)
    finally:
        conn.close()
    body = {
        "genesis": [genesis.summarize_principle(p) for p in genesis.principles()],
        "chain": chain_principles,
        "domains": list(genesis.principle_domains()),
    }
    return _cached(body)


@app.get("/api/principles/{principle_id}")
def principle_detail(principle_id: str):
    p = genesis.by_artifact_id(principle_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"principle not found: {principle_id}")
    specs = [genesis.summarize_spec(s) for s in genesis.specs_for_principle(principle_id)]
    conn = store.get_conn()
    try:
        # PWMMinting indexes principles by unpadded numeric id (e.g. "3" not "003").
        # artifact_id looks like "L1-003" — take the part after the final "-".
        tail = principle_id.rsplit("-", 1)[-1]
        numeric = tail.lstrip("0") or "0"
        treasury = store.treasury_balance(conn, numeric)
        registered = store.benchmarks_for_principle(conn, numeric)
        meta = store.principle_meta(conn, numeric)
        total_minted = store.total_minted_for_principle(conn, numeric)
    finally:
        conn.close()
    return _cached({
        "principle": p,
        "specs": specs,
        "treasury_balance_wei": treasury,
        "registered_benchmarks": registered,
        "chain_meta": meta,
        "total_minted_wei": total_minted,
    })


@app.get("/api/benchmarks")
def benchmarks_list():
    conn = store.get_conn()
    try:
        chain_benchmarks = store.artifacts_by_layer(conn, 3)
        # Attach pool balance + minting linkage per benchmark.
        for b in chain_benchmarks:
            b["pool_balance_wei"] = store.pool_balance(conn, b["hash"])
            meta = store.benchmark_meta(conn, b["hash"])
            b["principle_id"] = meta["principle_id"] if meta else None
            b["rho"] = meta["rho"] if meta else None
            b["registered"] = bool(meta and meta["removed_at"] is None)
    finally:
        conn.close()
    return _cached({
        "genesis": [genesis.summarize_benchmark(b) for b in genesis.benchmarks()],
        "chain": chain_benchmarks,
    })


@app.get("/api/benchmarks/{benchmark_ref}")
def benchmark_detail(benchmark_ref: str):
    # Accept either an artifact_id (L3-003) or an on-chain hash.
    genesis_entry = genesis.by_artifact_id(benchmark_ref) or None
    conn = store.get_conn()
    try:
        chain_row = store.get_artifact(conn, benchmark_ref) if benchmark_ref.startswith("0x") else None
        chain_hash = (chain_row or {}).get("hash")
        leaderboard = []
        pool = None
        if chain_hash:
            leaderboard = store.certificates_for_benchmark(conn, chain_hash)[:10]
            pool = store.pool_balance(conn, chain_hash)
        return _cached({
            "genesis": genesis_entry,
            "chain": chain_row,
            "leaderboard": leaderboard,
            "pool_balance_wei": pool,
        })
    finally:
        conn.close()


@app.get("/api/pools")
def pools_list():
    conn = store.get_conn()
    try:
        rows = conn.execute(
            """
            SELECT benchmark_hash,
                   (SELECT new_balance FROM pool_events p2
                    WHERE p2.benchmark_hash = pool_events.benchmark_hash
                    ORDER BY p2.block_number DESC, p2.id DESC LIMIT 1) AS balance
              FROM pool_events
             GROUP BY benchmark_hash
            """
        ).fetchall()
        treasury_rows = conn.execute(
            """
            SELECT principle_id,
                   (SELECT new_balance FROM treasury_events t2
                    WHERE t2.principle_id = treasury_events.principle_id
                    ORDER BY t2.block_number DESC, t2.id DESC LIMIT 1) AS balance
              FROM treasury_events
             GROUP BY principle_id
            """
        ).fetchall()
        return _cached({
            "pools": [dict(r) for r in rows],
            "treasury": [dict(r) for r in treasury_rows],
        })
    finally:
        conn.close()


@app.get("/api/cert/{cert_hash}")
def cert_detail(cert_hash: str):
    conn = store.get_conn()
    try:
        row = store.certificate(conn, cert_hash)
        if not row:
            raise HTTPException(status_code=404, detail="certificate not found")
        benchmark_genesis = None
        chain_bench = store.get_artifact(conn, row["benchmark_hash"])
        if chain_bench and chain_bench.get("artifact_id"):
            benchmark_genesis = genesis.by_artifact_id(chain_bench["artifact_id"])
        return _cached({
            "certificate": row,
            "benchmark_chain": chain_bench,
            "benchmark_genesis": benchmark_genesis,
            "s_gates": _status_to_gates(row),
        })
    finally:
        conn.close()


@app.get("/api/leaderboard/{benchmark_hash}")
def leaderboard(benchmark_hash: str):
    conn = store.get_conn()
    try:
        rows = store.certificates_for_benchmark(conn, benchmark_hash)[:10]
        return _cached({"benchmark_hash": benchmark_hash.lower(), "entries": rows})
    finally:
        conn.close()


@app.get("/api/bounties")
def bounties_list():
    return _cached({"bounties": bounties.list_bounties()})


@app.get("/api/match")
def match(
    prompt: str | None = None,
    domain: str | None = None,
    modality: str | None = None,
    h: int | None = None,
    w: int | None = None,
    noise: float | None = None,
):
    """Faceted (LLM-free) benchmark matcher — reference implementation.

    Call pattern: /api/match?prompt=...  OR  /api/match?domain=imaging&h=256
    Response shape matches pwm_overview1.md §8.3 + 08-llm-matcher.md wire schema.

    For LLM-routed / natural-language matching, see Bounty #8
    (`interfaces/bounties/08-llm-matcher.md`).
    """
    # Responses are NOT cached — filters are combinatorial; would bloat the cache.
    return matching.match_prompt(
        prompt=prompt, domain=domain, modality=modality,
        h=h, w=w, noise=noise,
    )


# ---------- helpers ----------

def _status_to_gates(row: dict) -> dict:
    """Derive S1-S4 verdict summary from certificate lifecycle.

    Until the scoring engine publishes per-gate verdicts on-chain, we infer a
    simplified view: pending -> all unknown, finalized -> all pass unless
    challenge_upheld -> all fail.
    """
    status = int(row.get("status", 0))
    upheld = row.get("challenge_upheld")
    if status == 2 and not upheld:
        return {"S1": "PASS", "S2": "PASS", "S3": "PASS", "S4": "PASS"}
    if upheld:
        return {"S1": "FAIL", "S2": "FAIL", "S3": "FAIL", "S4": "FAIL"}
    return {"S1": "PENDING", "S2": "PENDING", "S3": "PENDING", "S4": "PENDING"}
