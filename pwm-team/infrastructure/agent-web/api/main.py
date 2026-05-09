"""PWM REST API — read-only chain+genesis view (plus a single write-side
endpoint at POST /api/cert-meta/{cert_hash} for off-chain enrichment of
certificate metadata: solver name + PSNR-as-dB).

Run directly:  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import bounties, demos, genesis, matching, store


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
        # Freshness signal: the indexer writes a `last_scan_at` heartbeat
        # every poll iteration regardless of whether new events arrive. We
        # call the indexer "degraded" only when *that* heartbeat is stale,
        # not when the chain is quiet — a quiet chain (Sepolia at idle, or
        # mainnet between events) should still report healthy. Falls back
        # to latest_event_ts only if the indexer predates the heartbeat
        # write (legacy DBs), so the upgrade is backward-compatible.
        last_scan_row = conn.execute(
            "SELECT value FROM meta WHERE key='last_scan_at'"
        ).fetchone()
        last_scan_at = int(last_scan_row[0]) if last_scan_row else None
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
        # Pick the freshness signal: prefer indexer heartbeat; fall back to
        # latest event for legacy DBs that have no heartbeat yet.
        freshness_ts = last_scan_at if last_scan_at is not None else latest_event_ts
        if last_block is None:
            status = "bootstrapping"
        elif freshness_ts and (now - freshness_ts) > stale_seconds:
            status = "degraded"
        else:
            status = "healthy"
        return _cached({
            "ok": True,
            "status": status,
            "last_indexed_block": last_block,
            "last_scan_at": last_scan_at,
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
def principles_list(
    tier: str = "mineable",
    carrier: str | None = None,
    problem_class: str | None = None,
    noise_model: str | None = None,
):
    """List L1 principles. ?tier=mineable (default) returns founder_vetted +
    community_proposed; ?tier=stub returns the claim-board inventory only;
    ?tier=all returns everything across both buckets.

    Faceted filters (each independent, AND-combined):
      ?carrier=photon|electron|mechanical|acoustic|x_ray|...
      ?problem_class=linear_inverse|nonlinear_inverse|parameter_estimation|...
      ?noise_model=gaussian|shot_poisson|poisson|...

    Returns `tier_counts` (always) and `facet_counts` (per-value counts
    on the post-tier set, so the UI can show "20 photon / 5 electron"
    even while another facet is selected).
    """
    buckets = genesis.all_principles_by_tier()
    counts = {k: len(v) for k, v in buckets.items()}
    counts["total"] = sum(counts.values())

    mineable = buckets.get("founder_vetted", []) + buckets.get("community_proposed", [])
    mineable_ids = {p.get("artifact_id") for p in mineable}

    if tier == "stub":
        selected_raw = buckets.get("stub", [])
    elif tier == "all":
        selected_raw = mineable + buckets.get("stub", [])
    else:  # "mineable"
        selected_raw = mineable

    def matches(p: dict) -> bool:
        pf = p.get("physics_fingerprint") or {}
        if carrier and pf.get("carrier") != carrier:
            return False
        if problem_class and pf.get("problem_class") != problem_class:
            return False
        if noise_model and pf.get("noise_model") != noise_model:
            return False
        return True

    filtered = [p for p in selected_raw if matches(p)]

    # Facet counts computed on the post-tier set (BEFORE applying facets)
    # so the UI can show how many entries each value has within the
    # current tier scope, even while other facets are active.
    facet_counts: dict[str, dict[str, int]] = {
        "carrier": {}, "problem_class": {}, "noise_model": {},
    }
    for p in selected_raw:
        pf = p.get("physics_fingerprint") or {}
        for axis in facet_counts:
            v = pf.get(axis)
            if v:
                facet_counts[axis][v] = facet_counts[axis].get(v, 0) + 1

    summaries = [
        genesis.summarize_principle(p) if p.get("artifact_id") in mineable_ids
        else genesis.summarize_stub_principle(p)
        for p in filtered
    ]

    chain_principles = []
    conn = store.get_conn()
    try:
        chain_principles = store.artifacts_by_layer(conn, 1)
    finally:
        conn.close()
    body = {
        "genesis": summaries,
        "chain": chain_principles,
        "domains": list(genesis.principle_domains(include_stubs=(tier in ("stub", "all")))),
        "tier_counts": counts,
        "tier": tier,
        "facet_counts": facet_counts,
        "active_facets": {
            "carrier": carrier,
            "problem_class": problem_class,
            "noise_model": noise_model,
        },
    }
    return _cached(body)


@app.get("/api/principles/{principle_id}")
def principle_detail(principle_id: str):
    p = genesis.principle_by_artifact_id_any(principle_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"principle not found: {principle_id}")

    is_stub = (p.get("registration_tier") or "stub") == "stub"
    specs = [genesis.summarize_spec(s) for s in genesis.specs_for_principle(principle_id)]

    if is_stub:
        # Stubs have no on-chain footprint — skip the chain queries entirely.
        return _cached({
            "principle": p,
            "specs": specs,
            "treasury_balance_wei": None,
            "registered_benchmarks": [],
            "chain_meta": None,
            "total_minted_wei": "0",
            "is_stub": True,
        })

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
        "is_stub": False,
    })


@app.get("/api/specs/{spec_id}")
def spec_detail(spec_id: str):
    """L2 spec detail page — covers the six-tuple contract + child L3 list.

    Accepts artifact_id (`L2-003`, `L2-026-002`), legacy alias (`L2-003-001`
    auto-resolves to `L2-003`), or display_slug (`spc` → L2-026-002).
    """
    s = genesis.spec_by_artifact_id_any(spec_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"spec not found: {spec_id}")

    aid = s.get("artifact_id") or spec_id
    parent_l1_id = s.get("parent_l1")
    parent_l1 = genesis.principle_by_artifact_id_any(parent_l1_id) if parent_l1_id else None

    # Sibling specs (other L2s under the same L1) — useful for discoverability
    siblings = []
    if parent_l1_id:
        siblings = [
            genesis.summarize_spec(x)
            for x in genesis._load_content_layer("l2")
            if x.get("parent_l1") == parent_l1_id and x.get("artifact_id") != aid
        ]
        # Also include genesis-tree siblings (e.g., L2-003 alongside any future L2-003-002)
        siblings.extend(
            genesis.summarize_spec(x)
            for x in genesis.specs()
            if x.get("parent_l1") == parent_l1_id and x.get("artifact_id") != aid
            and x.get("artifact_id") not in {sb.get("artifact_id") for sb in siblings}
        )

    children = [genesis.summarize_benchmark(b) for b in genesis.benchmarks_for_spec_any(aid)]

    return _cached({
        "spec": s,
        "parent_principle": (
            genesis.summarize_principle(parent_l1) if parent_l1 else None
        ),
        "siblings": siblings,
        "child_benchmarks": children,
        "is_stub": (s.get("registration_tier") or "stub") == "stub",
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


_BENCHMARK_TO_DEMO = {
    "L3-003": "cassi",
    "L3-004": "cacti",
}


def _demo_for_benchmark(benchmark_ref: str) -> dict | None:
    """Return the demo record (samples + metadata) for a benchmark id, or None."""
    demo_name = _BENCHMARK_TO_DEMO.get(benchmark_ref)
    if not demo_name:
        return None
    return demos.find_demo(demo_name)


@app.get("/api/benchmarks/{benchmark_ref}")
def benchmark_detail(benchmark_ref: str):
    # Accept artifact_id (L3-003), display_slug (cassi), or on-chain hash.
    # resolve_ref tries artifact_id first, then display_slug.
    genesis_entry = genesis.resolve_ref(benchmark_ref, prefer_layer="l3")
    conn = store.get_conn()
    try:
        # Resolve the on-chain row in this order:
        #   1. The ref is already a 0x… hash → look up by hash.
        #   2. The ref is an artifact_id (e.g. "L3-003") → look up by the
        #      artifact_id column (populated by the indexer's genesis-JSON
        #      enrichment step).
        #   3. The matching genesis JSON carries an explicit `chain_hash`
        #      → look up by that hash. Forward-compatible with future
        #      genesis-JSON enrichment that records the on-chain hash.
        if benchmark_ref.startswith("0x"):
            chain_row = store.get_artifact(conn, benchmark_ref)
        else:
            # If the input is a slug, resolve_ref already mapped it to the
            # genesis entry; use its artifact_id for the chain lookup.
            artifact_id_for_chain = (
                (genesis_entry or {}).get("artifact_id") or benchmark_ref
            )
            chain_row = store.get_artifact_by_artifact_id(conn, artifact_id_for_chain)
            if chain_row is None and genesis_entry and genesis_entry.get("chain_hash"):
                chain_row = store.get_artifact(conn, genesis_entry["chain_hash"])
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
            "demo": _demo_for_benchmark(benchmark_ref),
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


def _resolve_benchmark_ref(conn, benchmark_ref: str):
    """Convert a customer-facing benchmark reference to (chain_hash, artifact_id, genesis_entry).

    Accepts:
      - on-chain hex hash (0x…)        → look up by hash
      - artifact_id (L3-003)           → look up by artifact_id column
      - display_slug (cassi)           → resolve via genesis lookup, then artifact_id

    Returns (chain_hash, artifact_id, genesis_entry) where any field may be None.
    """
    chain_row = None
    artifact_id: str | None = None
    genesis_entry: dict | None = None

    if benchmark_ref.startswith("0x"):
        chain_row = store.get_artifact(conn, benchmark_ref)
        artifact_id = (chain_row or {}).get("artifact_id")
        if artifact_id:
            genesis_entry = genesis.by_artifact_id(artifact_id)
    else:
        # Try artifact_id first (L3-003), then slug (cassi).
        chain_row = store.get_artifact_by_artifact_id(conn, benchmark_ref)
        artifact_id = benchmark_ref
        genesis_entry = genesis.by_artifact_id(benchmark_ref)
        if genesis_entry is None:
            # Slug path: resolve cassi → L3-003 → look up chain row by artifact_id.
            slug_hit = genesis.by_slug(benchmark_ref, layer="l3")
            if slug_hit:
                genesis_entry = slug_hit
                artifact_id = slug_hit.get("artifact_id") or benchmark_ref
                if chain_row is None:
                    chain_row = store.get_artifact_by_artifact_id(conn, artifact_id)
        if chain_row is None and genesis_entry and genesis_entry.get("chain_hash"):
            chain_row = store.get_artifact(conn, genesis_entry["chain_hash"])

    chain_hash = (chain_row or {}).get("hash")
    return chain_hash, artifact_id, genesis_entry


@app.get("/api/leaderboard/{benchmark_ref}")
def leaderboard(benchmark_ref: str):
    """Leaderboard for one benchmark, enriched with metadata for UI display.

    Accepts either an on-chain hash (0x…) or an artifact_id form (L3-003)
    so customers don't have to paste raw hashes into URLs.

    Response shape (per `PWM_LEADERBOARD_DISPLAY_DESIGN_2026-05-03.md`):
        benchmark_hash       on-chain hex; lower-cased
        benchmark_id         artifact_id like "L3-003" if resolvable
        benchmark_title      from genesis JSON if resolvable
        reference            off-chain reference baseline
                                {label, score_q, psnr_db, source}
                             or null if no genesis baseline available
        current_sota         the top-rank entry surfaced as a first-class
                             field; null when no certs exist
                                {cert_hash, label, score_q, psnr_db,
                                 submitter, rank, status, ...}
        improvement_db       psnr_db(SOTA) - psnr_db(reference);
                             null if either side missing
        ranks                same entries as `entries` but with explicit
                             `rank` int (1-indexed)
        entries              kept for backward-compatibility with the
                             pre-enrichment client

    The reference floor is read from the L3 manifest's first
    ibenchmarks-tier first baseline (typically the GAP-TV / classical
    reference). Empty-leaderboard fallback: the page still has reference
    + benchmark_title to render even before the first cert lands.
    """
    conn = store.get_conn()
    try:
        chain_hash, artifact_id, genesis_entry = _resolve_benchmark_ref(conn, benchmark_ref)
        title = genesis_entry.get("title") if genesis_entry else None

        all_rows: list[dict] = []
        if chain_hash:
            all_rows = store.certificates_for_benchmark(conn, chain_hash)

        # Filter D5 stress-test / synthetic-Q entries from the public
        # leaderboard. They were authored to exercise indexer + draw
        # plumbing, not to represent real solver runs, and their
        # synthetic Q values (often Q_int > 100, i.e. Q > 1.0 — outside
        # the protocol's [0, 1] convention) drown out genuine certs.
        # See PWM_DIRECTOR_NEXT_ACTIONS_2026-05-04 § leaderboard polish.
        real_rows = [r for r in all_rows if not _is_synthetic_cert(r)]
        synthetic_filtered = len(all_rows) - len(real_rows)
        rows = real_rows[:10]

        # Enrich each row with an explicit rank (1-indexed). The store
        # already orders by draw_rank ASC then q_int DESC, so the row
        # order IS the rank order.
        ranks: list[dict] = []
        for i, row in enumerate(rows):
            r = dict(row)
            # Prefer the on-chain finalized rank when present; otherwise
            # provisional rank from sort order.
            r["rank"] = r.get("draw_rank") or (i + 1)
            ranks.append(r)

        current_sota = ranks[0] if ranks else None

        # Reference floors: classical (deliberate weak floor everyone can
        # beat) + optional deep-learning (the harder named landmark).
        # Tolerate missing fields — every level is optional.
        reference = _extract_reference_baseline(genesis_entry)
        reference_advanced = _extract_advanced_baseline(genesis_entry)

        improvement_db = None
        if (
            current_sota is not None
            and current_sota.get("psnr_db") is not None
            and reference is not None
            and reference.get("psnr_db") is not None
        ):
            improvement_db = round(
                float(current_sota["psnr_db"]) - float(reference["psnr_db"]), 3
            )

        return _cached({
            "benchmark_hash": (chain_hash or "").lower(),
            "benchmark_id": artifact_id,
            "benchmark_title": title,
            "reference": reference,
            "reference_advanced": reference_advanced,
            "current_sota": current_sota,
            "improvement_db": improvement_db,
            "ranks": ranks,
            "entries": rows,
            "synthetic_filtered": synthetic_filtered,
        })
    finally:
        conn.close()


# Cert rows emitted by the D5 stress-test harness in
# `pwm-team/infrastructure/agent-web/scripts/d5_stress_test.py`. Their
# `solver_label` is set on the cert_meta row at fixture time. The
# Q-value side covers the case where meta wasn't (yet) posted.
_SYNTHETIC_SOLVER_LABELS = frozenset({"D5-stress-test"})


_UNLABELED_HIGH_Q_THRESHOLD = 40  # PSNR≥40 dB without a posted label is suspicious
                                  # on these benchmarks: GAP-TV ≈ 26, EfficientSCI ≈ 33,
                                  # MST-L ≈ 35. Real submitters above 40 should post a
                                  # solver_label so their work surfaces with attribution.


def _is_synthetic_cert(row: dict) -> bool:
    """True if a cert row should be hidden from the public leaderboard.

    Three independent signals — any one is sufficient:

    1. solver_label matches a known synthetic harness label (explicit).
    2. q_int > 100 (defense-in-depth). Real solver Q values are normalised
       to [0, 1] (`Q = PSNR_dB / 100` in `mine.py:_compute_q`), so q_int
       above 100 is structurally impossible for a real cert.
    3. q_int >= 50 AND no solver_label posted via cert-meta. Reasoning:
       a real PSNR ≥ 50 dB on these benchmarks is rare; if a submitter
       achieved it, they have every incentive to post a solver_label so
       the leaderboard shows their work properly. Unlabeled certs in
       that range are therefore much more likely to be unlabeled test
       fixtures or harness leftovers than real submissions worth
       advertising. A real solver running ~30-40 dB without a label
       still appears (q_int < 50), and any labeled cert at any q_int
       below 100 still appears.
    """
    label = (row.get("solver_label") or "").strip()
    if label in _SYNTHETIC_SOLVER_LABELS:
        return True
    q_int = row.get("q_int")
    if q_int is not None and q_int > 100:
        return True
    if q_int is not None and q_int >= _UNLABELED_HIGH_Q_THRESHOLD and not label:
        return True
    return False


def _format_baseline(b: dict, tier: str | None) -> dict:
    return {
        "label": b.get("name"),
        "category": b.get("category"),
        "score_q": b.get("Q"),
        "psnr_db": b.get("score") if b.get("metric") == "PSNR_dB" else None,
        "metric": b.get("metric"),
        "tier": tier,
        "source": "off-chain reference (genesis manifest baseline)",
    }


def _extract_reference_baseline(genesis_entry: dict | None) -> dict | None:
    """Pull the first baseline of the first ibenchmarks tier as the
    classical reference floor for leaderboard display.

    Schema (from a real L3 manifest):
        ibenchmarks: [
          {tier: T1_nominal, baselines: [
              {name: "GAP-TV", category: "classical",
               metric: "PSNR_dB", score: 26.0, Q: 0.62}, ...
          ]}, ...
        ]

    Returns the first entry whose `category` is "classical" if any
    baseline declares categories; otherwise falls back to the first
    baseline (legacy manifests without categories).
    """
    if not genesis_entry:
        return None
    ibench = genesis_entry.get("ibenchmarks") or []
    if not ibench:
        return None
    tier = (ibench[0] or {}).get("tier")
    baselines = (ibench[0] or {}).get("baselines") or []
    if not baselines:
        return None
    classical = next((b for b in baselines if b.get("category") == "classical"), None)
    chosen = classical or baselines[0]
    return _format_baseline(chosen, tier)


def _extract_advanced_baseline(genesis_entry: dict | None) -> dict | None:
    """Pull the first deep-learning sidecar baseline.

    Looks in two places, in priority order:

    1. The top-level `display_baselines` array — UI-only sidecar entries
       (in UI_ONLY_FIELDS, so they don't affect the manifest's keccak256
       hash). This is the canonical place to add a deep-learning landmark
       like MST-L without breaking the on-chain registration.
    2. Fallback: any `ibenchmarks[0].baselines[]` entry tagged
       `category: "deep_learning"`. Tagging baselines this way DOES
       change the manifest hash, so it should only be used on
       not-yet-registered manifests.

    Returns None when no deep-learning baseline is declared. Pages
    render this alongside the classical reference floor as the
    "deep-learning floor" — a harder gate that surfaces the SOTA
    deep-learning method as a known landmark for new contributors.
    """
    if not genesis_entry:
        return None

    # Priority 1: hash-invariant sidecar
    sidecar = genesis_entry.get("display_baselines") or []
    advanced = next((b for b in sidecar if b.get("category") == "deep_learning"), None)
    if advanced:
        return _format_baseline(advanced, advanced.get("tier"))

    # Priority 2: legacy in-baselines tag (changes the manifest hash)
    ibench = genesis_entry.get("ibenchmarks") or []
    if not ibench:
        return None
    tier = (ibench[0] or {}).get("tier")
    baselines = (ibench[0] or {}).get("baselines") or []
    advanced = next((b for b in baselines if b.get("category") == "deep_learning"), None)
    return _format_baseline(advanced, tier) if advanced else None


# ---------- write path: certificate-meta enrichment ----------

class CertMetaPayload(BaseModel):
    """Off-chain enrichment of an on-chain L4 certificate.

    The on-chain CertificateSubmitted event carries only
    (certHash, benchmarkHash, submitter, Q_int). This payload adds the
    human-meaningful labels — solver name, PSNR-as-dB — that the leaderboard
    UI displays alongside the cert hash.
    """
    solver_label: str = Field(..., min_length=1, max_length=64,
                              description="e.g. 'MST-L', 'EfficientSCI', 'GAP-TV (ref)'")
    psnr_db: float | None = Field(None, ge=0.0, le=200.0,
                                  description="PSNR in dB; e.g. 34.13")
    runtime_sec: float | None = Field(None, ge=0.0,
                                      description="solver runtime in seconds")
    framework: str | None = Field(None, max_length=128,
                                  description="e.g. 'PyTorch 2.1 + CUDA 12.1'")
    meta_url: str | None = Field(None, max_length=512,
                                 description="optional pointer to full meta.json (IPFS / GCS / etc.)")


_CERT_HASH_RE_LEN = 66  # 0x + 64 hex chars


@app.post("/api/cert-meta/{cert_hash}")
def upsert_cert_meta(cert_hash: str, payload: CertMetaPayload):
    """Upsert off-chain enrichment for a previously-submitted certificate.

    Auth model: the cert hash itself is proof of submission. Anyone with
    it can post; lying about solver_label or psnr_db doesn't change the
    on-chain Q_int / rank / reward (those are determined by
    PWMCertificate.submit() and PWMReward.distribute()).

    Rejects cert hashes not yet in the indexer DB — must already be on-chain
    AND indexed before enrichment can land.

    Rate-limit at the reverse-proxy layer (~10 req/min/IP is plenty).
    """
    cert_hash = cert_hash.lower().strip()
    if not cert_hash.startswith("0x") or len(cert_hash) != _CERT_HASH_RE_LEN:
        raise HTTPException(
            status_code=400,
            detail="cert_hash must be 0x-prefixed 64-hex (32 bytes)",
        )
    try:
        bytes.fromhex(cert_hash[2:])
    except ValueError:
        raise HTTPException(status_code=400, detail="cert_hash is not valid hex")

    conn = store.get_writable_conn()
    try:
        submitter = store.certificate_submitter(conn, cert_hash)
        if submitter is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"cert {cert_hash} not in indexer DB — either not yet on-chain "
                    "or the indexer hasn't caught up. Wait 1-2 min and retry."
                ),
            )
        store.upsert_cert_meta_via_api(
            conn,
            cert_hash=cert_hash,
            solver_label=payload.solver_label,
            psnr_db=payload.psnr_db,
            runtime_sec=payload.runtime_sec,
            framework=payload.framework,
            meta_url=payload.meta_url,
            posted_at=int(time.time()),
            posted_by=submitter,
        )
        conn.commit()
        return {
            "ok": True,
            "cert_hash": cert_hash,
            "submitter": submitter,
            "solver_label": payload.solver_label,
            "psnr_db": payload.psnr_db,
        }
    finally:
        conn.close()


@app.get("/api/bounties")
def bounties_list():
    return _cached({"bounties": bounties.list_bounties()})


@app.get("/api/demos")
def demos_list():
    """List canonical demo datasets (CASSI, CACTI anchors — plus U1b additions later)."""
    return _cached({"demos": demos.list_demos()})


def _demo_mime(filename: str) -> str:
    if filename.endswith(".json"):
        return "application/json"
    if filename.endswith(".md"):
        return "text/markdown"
    if filename.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


@app.get("/api/demos/{demo_name}/{filename}")
def demo_benchmark_file(demo_name: str, filename: str):
    """Stream a benchmark-level file (README.md only)."""
    path = demos.resolve_benchmark_file(demo_name, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="demo file not found")
    return Response(content=path.read_bytes(), media_type=_demo_mime(filename),
                    headers={"Cache-Control": "public, max-age=3600"})


def _default_walkthroughs_dir() -> str:
    """Fall back to the dev-tree path; the Docker image sets PWM_WALKTHROUGHS_DIR."""
    try:
        return str(Path(__file__).resolve().parents[3] / "pwm_product" / "walkthroughs")
    except IndexError:
        return "/app/walkthroughs"


_WALKTHROUGH_DIR = Path(os.environ.get("PWM_WALKTHROUGHS_DIR", _default_walkthroughs_dir()))
_WALKTHROUGH_ALLOWED = frozenset({"cassi", "cacti"})


@app.get("/api/walkthrough/{anchor}")
def walkthrough(anchor: str):
    """Return the markdown body of one anchor's complete 4-layer walkthrough.

    Source: papers/Proof-of-Solution/mine_example/<anchor>.md, mirrored to
    pwm-team/pwm_product/walkthroughs/<anchor>.md and copied into the image.
    """
    if anchor not in _WALKTHROUGH_ALLOWED:
        raise HTTPException(status_code=404, detail="unknown walkthrough")
    path = _WALKTHROUGH_DIR / f"{anchor}.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="walkthrough not found")
    return Response(
        content=path.read_bytes(),
        media_type="text/markdown",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/demos/{demo_name}/{sample_name}/{filename}")
def demo_sample_file(demo_name: str, sample_name: str, filename: str):
    """Stream one file from a demo sample dir.

    Allowed filenames: snapshot.npz, ground_truth.npz, solution.npz,
    snapshot.png, ground_truth.png, solution.png, meta.json. Anything else → 404.
    """
    path = demos.resolve_sample_file(demo_name, sample_name, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="demo sample file not found")
    return Response(content=path.read_bytes(), media_type=_demo_mime(filename),
                    headers={"Cache-Control": "public, max-age=3600"})


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
    (`pwm-team/bounties/08-llm-matcher.md`).
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
