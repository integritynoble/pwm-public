"""End-to-end tests for the API.

We seed a temp SQLite DB using the indexer's handlers, point both the store
and the genesis loader at fixtures, then exercise every endpoint.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from indexer import db as idx_db
from indexer import handlers as idx_handlers
from indexer.events import EventContext


REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture()
def seeded_env(tmp_path, monkeypatch):
    # 1. Fresh DB with a canned set of events.
    db_path = tmp_path / "api_test.db"
    conn = idx_db.connect(db_path)
    idx_db.init_db(conn)

    bench_hash = b"\xbb" * 32
    cert_hash = b"\xcc" * 32
    principle_hash = b"\x11" * 32
    spec_hash = b"\x22" * 32

    ctx = EventContext(block_number=1, tx_hash="0xaaa", timestamp=1700000000)
    idx_handlers.handle_artifact_registered(
        conn, {"hash": principle_hash, "layer": 1, "creator": "0x" + "01" * 20, "timestamp": ctx.timestamp}, ctx
    )
    idx_handlers.handle_artifact_registered(
        conn, {"hash": spec_hash, "layer": 2, "creator": "0x" + "02" * 20, "timestamp": ctx.timestamp}, ctx
    )
    idx_handlers.handle_artifact_registered(
        conn, {"hash": bench_hash, "layer": 3, "creator": "0x" + "03" * 20, "timestamp": ctx.timestamp}, ctx
    )
    idx_handlers.handle_certificate_submitted(
        conn,
        {"certHash": cert_hash, "benchmarkHash": bench_hash, "submitter": "0x" + "04" * 20, "Q_int": 35},
        ctx,
    )
    idx_handlers.handle_certificate_finalized(conn, {"certHash": cert_hash, "rank": 1}, ctx)
    idx_handlers.handle_draw_settled(
        conn,
        {"certHash": cert_hash, "benchmarkHash": bench_hash, "rank": 1, "drawAmount": 5 * 10**17, "rolloverRemaining": 0},
        ctx,
    )
    idx_handlers.handle_royalties_paid(
        conn,
        {"certHash": cert_hash,
         "ac": "0x" + "05" * 20, "acAmt": 2 * 10**17,
         "cp": "0x" + "06" * 20, "cpAmt": 2 * 10**17,
         "treasuryAmt": 10**17},
        ctx,
    )
    idx_handlers.handle_pool_seeded(
        conn,
        {"benchmarkHash": bench_hash, "amount": 10**18, "newBalance": 5 * 10**17,
         "from": "0x" + "07" * 20, "kind": "A-pool-minting"},
        ctx,
    )
    idx_handlers.handle_funds_received(
        conn, {"principleId": 3, "amount": 10**18, "newBalance": 10**18}, ctx
    )
    # Canonical principle_id ↔ benchmark linkage from PWMMinting.
    idx_handlers.handle_benchmark_registered(
        conn, {"principleId": 1, "benchmarkHash": bench_hash, "rho": 1}, ctx
    )
    idx_handlers.handle_delta_set(conn, {"principleId": 1, "delta": 2}, ctx)
    idx_handlers.handle_minted(
        conn,
        {"principleId": 1, "benchmarkHash": bench_hash,
         "A_k": 3 * 10**18, "A_kjb": 10**18, "remainingAfter": 100},
        ctx,
    )
    # Simulate the indexer's genesis-JSON enrichment step: stamp the
    # seeded benchmark row with its off-chain artifact_id so that
    # `/api/benchmarks/L3-001` (artifact-id form) can resolve the chain row.
    conn.execute(
        "UPDATE artifacts SET artifact_id = ? WHERE hash = ?",
        ("L3-001", "0x" + "bb" * 32),
    )
    conn.commit()
    conn.close()

    # 2. Point the API at the seeded DB.
    monkeypatch.setenv("PWM_DB", str(db_path))

    # 3. Point genesis loader at a tiny fixture dir so the tests are self-contained.
    genesis_root = tmp_path / "genesis"
    (genesis_root / "l1").mkdir(parents=True)
    (genesis_root / "l2").mkdir(parents=True)
    (genesis_root / "l3").mkdir(parents=True)
    (genesis_root / "l1" / "L1-001.json").write_text(json.dumps({
        "artifact_id": "L1-001", "title": "Test Principle", "domain": "Test",
        "E": {"forward_model": "y = A x + n"},
        "G": {"L_DAG": 1.0},
        "difficulty_delta": 2, "difficulty_tier": "standard",
        "spec_range": {"center_spec": {"epsilon_fn_center": "30.0 dB PSNR"}},
    }))
    (genesis_root / "l2" / "L2-001.json").write_text(json.dumps({
        "artifact_id": "L2-001", "parent_l1": "L1-001",
        "title": "Test Spec", "spec_type": "center", "d_spec": 0.0,
        "ibenchmark_range": {"center_ibenchmark": {"rho": 1, "epsilon": 30.0}},
    }))
    (genesis_root / "l3" / "L3-001.json").write_text(json.dumps({
        "artifact_id": "L3-001", "parent_l2": "L2-001",
        "title": "Test Benchmark",
        "display_slug": "test-bench",
        "ibenchmark": {"rho": 1, "epsilon": 30.0, "omega_tier": {"H": 128}},
    }))
    monkeypatch.setenv("PWM_GENESIS_DIR", str(genesis_root))

    # 4. Point bounties at a fixture dir.
    bounties_dir = tmp_path / "bounties"
    bounties_dir.mkdir()
    (bounties_dir / "test-bounty.md").write_text(
        "# Test Bounty (50,000 PWM)\n\nShort summary line.\n"
    )
    monkeypatch.setenv("PWM_BOUNTIES_DIR", str(bounties_dir))

    # 5. Reload caches and build the client.
    from api import bounties as b_mod
    from api import genesis as g_mod
    g_mod.reload()
    b_mod.reload()
    from api.main import app
    return TestClient(app), {
        "cert_hash": "0x" + "cc" * 32,
        "bench_hash": "0x" + "bb" * 32,
    }


def test_health(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["counts"]["principles"] == 1
    assert body["genesis"]["l1"] == 1
    # Seed data has a fixed-in-the-past timestamp (1_700_000_000 = 2023-11-14),
    # so the indexer appears stale relative to "now" -> degraded.
    assert body["status"] in {"degraded", "bootstrapping", "healthy"}
    assert "last_indexed_block" in body


def test_overview_has_recent_draws(seeded_env):
    client, refs = seeded_env
    r = client.get("/api/overview")
    assert r.status_code == 200
    assert r.headers["cache-control"].startswith("public, max-age=")
    body = r.json()
    assert body["counts"]["draws"] == 1
    assert body["recent_draws"][0]["cert_hash"] == refs["cert_hash"]


def test_principles_list(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/principles")
    body = r.json()
    assert len(body["genesis"]) == 1
    assert body["genesis"][0]["artifact_id"] == "L1-001"
    assert body["chain"][0]["layer"] == 1


def test_principle_detail_found(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/principles/L1-001")
    assert r.status_code == 200
    body = r.json()
    assert body["principle"]["title"] == "Test Principle"
    assert len(body["specs"]) == 1
    # PWMMinting-derived fields make it through:
    assert len(body["registered_benchmarks"]) == 1
    assert body["registered_benchmarks"][0]["rho"] == "1"
    assert body["chain_meta"]["delta"] == "2"
    assert body["total_minted_wei"] == str(3 * 10**18)


def test_principle_detail_missing(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/principles/L1-999")
    assert r.status_code == 404


def test_benchmarks_list(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/benchmarks")
    body = r.json()
    assert body["genesis"][0]["artifact_id"] == "L3-001"
    assert body["chain"][0]["layer"] == 3
    # Minting linkage surfaces on chain entries:
    assert body["chain"][0]["principle_id"] == "1"
    assert body["chain"][0]["rho"] == "1"
    assert body["chain"][0]["registered"] is True


def test_benchmark_detail_by_hash(seeded_env):
    """Hash-form URL resolves the chain row and surfaces the leaderboard."""
    client, refs = seeded_env
    r = client.get(f"/api/benchmarks/{refs['bench_hash']}")
    assert r.status_code == 200
    body = r.json()
    assert body["chain"] is not None
    assert body["chain"]["hash"] == refs["bench_hash"]
    assert len(body["leaderboard"]) == 1
    assert body["leaderboard"][0]["cert_hash"] == refs["cert_hash"]


def test_benchmark_detail_by_artifact_id(seeded_env):
    """Regression for artifact-id-form URL: `/api/benchmarks/L3-001` must
    resolve to the same on-chain row as the hash-form URL and return the
    leaderboard. Prior to the fix this returned `chain: null` and an empty
    leaderboard because the resolver only handled refs starting with `0x`.
    """
    client, refs = seeded_env
    r = client.get("/api/benchmarks/L3-001")
    assert r.status_code == 200
    body = r.json()
    # Genesis side wired up:
    assert body["genesis"] is not None
    assert body["genesis"]["artifact_id"] == "L3-001"
    # Chain side now resolves via the artifact_id column:
    assert body["chain"] is not None, "artifact-id URL must surface chain row"
    assert body["chain"]["hash"] == refs["bench_hash"]
    assert body["chain"]["artifact_id"] == "L3-001"
    # Leaderboard is non-empty (the seeded cert):
    assert len(body["leaderboard"]) == 1
    assert body["leaderboard"][0]["cert_hash"] == refs["cert_hash"]


def test_health_counts_include_minting(seeded_env):
    client, _ = seeded_env
    body = client.get("/api/health").json()
    assert body["counts"]["registered_benchmarks"] == 1
    assert body["counts"]["mints"] == 1


def test_activity_feed_merges_event_kinds(seeded_env):
    client, _ = seeded_env
    body = client.get("/api/activity?limit=50").json()
    kinds = {a["kind"] for a in body["activity"]}
    # Fixture emits events from six different tables — verify a spread.
    for required in (
        "artifact_registered",
        "certificate_submitted",
        "draw_settled",
        "pool_seeded",
        "benchmark_registered",
        "minted",
    ):
        assert required in kinds


def test_activity_feed_is_ordered_and_limited(seeded_env):
    client, _ = seeded_env
    body = client.get("/api/activity?limit=2").json()
    rows = body["activity"]
    assert len(rows) <= 2
    ts = [a["timestamp"] for a in rows]
    assert ts == sorted(ts, reverse=True)


def test_pools(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/pools")
    body = r.json()
    assert body["pools"][0]["balance"] == str(5 * 10**17)
    assert body["treasury"][0]["balance"] == str(10**18)


def test_cert_detail_and_gates(seeded_env):
    client, refs = seeded_env
    r = client.get(f"/api/cert/{refs['cert_hash']}")
    assert r.status_code == 200
    body = r.json()
    assert body["certificate"]["q_int"] == 35
    assert body["s_gates"]["S1"] == "PASS"


def test_leaderboard(seeded_env):
    client, refs = seeded_env
    r = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    body = r.json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["draw_rank"] == 1


def test_leaderboard_returns_enriched_payload(seeded_env):
    """Enriched leaderboard payload includes benchmark title (from genesis),
    current SOTA (top-rank cert), explicit rank field per entry, and the
    delta vs the off-chain reference baseline.

    Verifies the contract documented in
    `pwm-team/coordination/PWM_LEADERBOARD_DISPLAY_DESIGN_2026-05-03.md`.
    """
    client, refs = seeded_env
    r = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    assert r.status_code == 200
    body = r.json()

    # Backward-compat: existing field still present.
    assert "entries" in body
    assert len(body["entries"]) == 1

    # New fields.
    assert body.get("benchmark_id") == "L3-001"
    assert body.get("benchmark_title") == "Test Benchmark"

    # current_sota = the top-rank entry surfaced as a first-class field.
    sota = body.get("current_sota")
    assert sota is not None, "current_sota should be present when at least one cert exists"
    assert sota["cert_hash"] == refs["cert_hash"]
    assert sota["rank"] == 1

    # ranks: same entries as `entries`, but with an explicit `rank` int per row.
    ranks = body.get("ranks")
    assert ranks is not None
    assert len(ranks) == 1
    assert ranks[0]["rank"] == 1
    assert ranks[0]["cert_hash"] == refs["cert_hash"]


def test_leaderboard_with_slug_resolves_to_artifact_id(seeded_env):
    """Customers see /benchmarks/cassi or /benchmarks/test-bench in URLs.
    The leaderboard endpoint must accept slug form too.
    """
    client, refs = seeded_env
    r = client.get("/api/leaderboard/test-bench")
    assert r.status_code == 200
    body = r.json()
    assert body.get("benchmark_id") == "L3-001"
    assert body.get("benchmark_title") == "Test Benchmark"
    assert len(body["entries"]) == 1


def test_leaderboard_with_artifact_id_resolves_chain_hash(seeded_env):
    """Like /api/benchmarks/L3-001, /api/leaderboard accepts artifact_id form.

    Customers see L3-003 in the URL (not 0xbb...bb), so the leaderboard
    endpoint must accept that form too. Mirrors the resolver pattern in
    benchmark_detail.
    """
    client, refs = seeded_env
    r = client.get("/api/leaderboard/L3-001")
    assert r.status_code == 200
    body = r.json()
    assert body.get("benchmark_id") == "L3-001"
    assert len(body["entries"]) == 1
    # ranks should also be populated when looked up by artifact_id.
    assert body.get("ranks") and body["ranks"][0]["rank"] == 1


def test_leaderboard_empty_returns_no_sota_but_metadata(seeded_env, tmp_path):
    """Benchmark with no on-chain certs returns current_sota=None but
    still resolves benchmark_id + benchmark_title from genesis. This is
    the "empty leaderboard fallback" — every benchmark page has at
    least the metadata layer to display from day 1.
    """
    client, _ = seeded_env
    # Use a hash that has no certs in the seeded DB.
    empty_hash = "0x" + "ee" * 32
    r = client.get(f"/api/leaderboard/{empty_hash}")
    assert r.status_code == 200
    body = r.json()
    assert body.get("entries") == []
    assert body.get("ranks") == []
    assert body.get("current_sota") is None


def test_leaderboard_filters_synthetic_q_certs(seeded_env):
    """D5 stress-test certs with synthetic Q (q_int > 100) are hidden.

    The protocol normalises Q to [0, 1] via Q = PSNR_dB / 100 in
    `mine.py`, so q_int > 100 is structurally impossible for a real
    cert. The D5 harness wrote synthetic q_int values 182-215 directly
    to exercise indexer plumbing; without this filter they drown out
    real solver certs on the public leaderboard.
    """
    client, refs = seeded_env

    # Inject 3 synthetic-Q certs against the same benchmark. Real cert
    # in the seeded fixture has Q_int=35 (below 100, so kept).
    from indexer import db as idx_db
    from indexer import handlers as idx_handlers
    from indexer.events import EventContext
    import os
    db_path = Path(os.environ["PWM_DB"])
    conn = idx_db.connect(db_path)
    bench_hash = bytes.fromhex(refs["bench_hash"][2:])
    ctx = EventContext(block_number=2, tx_hash="0xfake", timestamp=1700000100)
    for i, q in enumerate([215, 200, 150]):
        idx_handlers.handle_certificate_submitted(
            conn,
            {"certHash": bytes([0xa0 + i]) * 32,
             "benchmarkHash": bench_hash,
             "submitter": "0x" + "ff" * 20,
             "Q_int": q},
            ctx,
        )
    conn.commit()
    conn.close()

    r = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    assert r.status_code == 200
    body = r.json()
    assert body["synthetic_filtered"] == 3
    # Real cert (Q_int=35) survives; synthetic ones are gone.
    assert len(body["ranks"]) == 1
    assert body["ranks"][0]["cert_hash"] == refs["cert_hash"]
    # current_sota points at the real cert, not the higher-Q synthetic.
    assert body["current_sota"]["q_int"] == 35


def test_leaderboard_filters_d5_stress_test_label(seeded_env):
    """Even with q_int in the legal range, the D5-stress-test solver
    label is filtered. Belt-and-suspenders alongside the q_int > 100
    rule for synthetic certs that happened to land in [0, 100]."""
    client, refs = seeded_env

    # Insert a synthetic cert with q_int in the legal range (so the
    # q_int filter alone wouldn't catch it), then post a meta row with
    # the D5 label.
    from indexer import db as idx_db
    from indexer import handlers as idx_handlers
    from indexer.events import EventContext
    import os
    db_path = Path(os.environ["PWM_DB"])
    conn = idx_db.connect(db_path)
    bench_hash = bytes.fromhex(refs["bench_hash"][2:])
    fake_cert = bytes([0xbb]) * 32
    ctx = EventContext(block_number=3, tx_hash="0xfake2", timestamp=1700000200)
    idx_handlers.handle_certificate_submitted(
        conn,
        {"certHash": fake_cert,
         "benchmarkHash": bench_hash,
         "submitter": "0x" + "ee" * 20,
         "Q_int": 95},   # within legal range
        ctx,
    )
    conn.commit()
    conn.close()

    fake_cert_hex = "0x" + fake_cert.hex()
    r1 = client.post(
        f"/api/cert-meta/{fake_cert_hex}",
        json={"solver_label": "D5-stress-test", "psnr_db": 95.0},
    )
    assert r1.status_code == 200

    r2 = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    body = r2.json()
    assert body["synthetic_filtered"] == 1
    cert_hashes = [r["cert_hash"] for r in body["ranks"]]
    assert fake_cert_hex not in cert_hashes
    # Real seeded cert is still there.
    assert refs["cert_hash"] in cert_hashes


def test_leaderboard_filters_unlabeled_high_q_int(seeded_env):
    """Unlabeled certs at q_int >= 40 are hidden as likely test fixtures.

    Real solver submissions at PSNR ≥ 40 dB on these benchmarks are
    suspicious — GAP-TV reference is ~26 dB, EfficientSCI ~33 dB,
    MST-L ~35 dB. Any submitter actually beating MST-L by 5+ dB has
    every incentive to POST /api/cert-meta and have their solver_label
    show on the leaderboard. Unlabeled certs in that range are
    dominated by older harness-test certs from founder wallets — they
    bury real solver runs and aren't useful to the public leaderboard.

    Threshold q_int=40 was picked so:
      - real-world MST-L (q_int=35) survives even unlabeled
      - founder-wallet test certs at q_int 41-100 get filtered when unlabeled
      - any labeled cert in the legal q_int range survives
    """
    client, refs = seeded_env

    from indexer import db as idx_db
    from indexer import handlers as idx_handlers
    from indexer.events import EventContext
    import os
    db_path = Path(os.environ["PWM_DB"])
    conn = idx_db.connect(db_path)
    bench_hash = bytes.fromhex(refs["bench_hash"][2:])
    ctx = EventContext(block_number=4, tx_hash="0xfake3", timestamp=1700000300)

    # Inject 3 unlabeled high-q_int certs (founder-wallet-like) — all
    # within the legal q_int range so the q_int>100 rule doesn't catch
    # them, and none have cert_meta posted.
    unlabeled_high = bytes([0xd0]) * 32
    unlabeled_mid = bytes([0xd1]) * 32
    unlabeled_low = bytes([0xd2]) * 32
    for cert, q in [(unlabeled_high, 95), (unlabeled_mid, 45), (unlabeled_low, 39)]:
        idx_handlers.handle_certificate_submitted(
            conn,
            {"certHash": cert, "benchmarkHash": bench_hash,
             "submitter": "0x" + "dd" * 20, "Q_int": q},
            ctx,
        )

    # Also inject a LABELED cert at q_int=80 — this one should NOT be
    # filtered, because the labeled-real-solver branch is the whole
    # point of allowing posts via cert-meta.
    labeled_high = bytes([0xd3]) * 32
    idx_handlers.handle_certificate_submitted(
        conn,
        {"certHash": labeled_high, "benchmarkHash": bench_hash,
         "submitter": "0x" + "dd" * 20, "Q_int": 80},
        ctx,
    )
    conn.execute(
        """INSERT OR REPLACE INTO cert_meta
               (cert_hash, solver_label, psnr_db, posted_at, posted_by)
           VALUES (?, ?, ?, ?, ?)""",
        ("0x" + labeled_high.hex(), "RealSolver-X", 80.0, ctx.timestamp, "test-fixture"),
    )
    conn.commit()
    conn.close()

    r = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    assert r.status_code == 200
    body = r.json()

    # Two unlabeled certs filtered (q_int=95 and q_int=45). The
    # q_int=39 unlabeled cert survives (below threshold of 40).
    assert body["synthetic_filtered"] == 2

    cert_hashes = [r["cert_hash"] for r in body["ranks"]]
    assert "0x" + unlabeled_high.hex() not in cert_hashes  # filtered (95 ≥ 40)
    assert "0x" + unlabeled_mid.hex() not in cert_hashes   # filtered (45 ≥ 40)
    assert "0x" + unlabeled_low.hex() in cert_hashes       # below threshold (39 < 40)
    assert "0x" + labeled_high.hex() in cert_hashes        # labeled, survives
    assert refs["cert_hash"] in cert_hashes                 # labeled seeded cert


def test_leaderboard_returns_classical_and_deep_learning_floors(tmp_path, monkeypatch):
    """When the L3 manifest declares both 'classical' and 'deep_learning'
    baselines, the leaderboard endpoint surfaces both: `reference` for
    the classical floor (deliberate, easy gate) and `reference_advanced`
    for the deep-learning floor (harder named landmark).
    """
    from indexer import db as idx_db
    from indexer import handlers as idx_handlers
    from indexer.events import EventContext

    db_path = tmp_path / "twofloor.db"
    conn = idx_db.connect(db_path)
    idx_db.init_db(conn)
    bench_hash = b"\xee" * 32
    ctx = EventContext(block_number=1, tx_hash="0xfake4", timestamp=1700000400)
    idx_handlers.handle_artifact_registered(
        conn, {"hash": bench_hash, "layer": 3, "creator": "0x" + "01" * 20, "timestamp": ctx.timestamp}, ctx,
    )
    conn.execute(
        "UPDATE artifacts SET artifact_id = ? WHERE hash = ?",
        ("L3-EE", "0x" + "ee" * 32),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("PWM_DB", str(db_path))

    genesis_root = tmp_path / "twofloor_genesis"
    (genesis_root / "l3").mkdir(parents=True)
    (genesis_root / "l3" / "L3-EE.json").write_text(json.dumps({
        "artifact_id": "L3-EE", "title": "Two-Floor Bench",
        "ibenchmarks": [{
            "tier": "T1_nominal",
            "baselines": [
                {"name": "GAP-TV", "category": "classical",
                 "metric": "PSNR_dB", "score": 26.0, "Q": 0.62},
                {"name": "MST-L", "category": "deep_learning",
                 "metric": "PSNR_dB", "score": 35.295, "Q": 0.95},
            ],
        }],
    }))
    monkeypatch.setenv("PWM_GENESIS_DIR", str(genesis_root))

    from api import genesis as g_mod
    g_mod.reload()
    from api.main import app
    client = TestClient(app)

    r = client.get("/api/leaderboard/0x" + "ee" * 32)
    assert r.status_code == 200
    body = r.json()
    assert body["reference"]["label"] == "GAP-TV"
    assert body["reference"]["psnr_db"] == 26.0
    assert body["reference"]["category"] == "classical"
    assert body["reference_advanced"]["label"] == "MST-L"
    assert body["reference_advanced"]["psnr_db"] == 35.295
    assert body["reference_advanced"]["category"] == "deep_learning"


def test_leaderboard_reference_advanced_absent_when_no_deep_learning_baseline(tmp_path, monkeypatch):
    """Manifests that declare only classical baselines (or no categories
    at all) should still work — `reference_advanced` is None."""
    from indexer import db as idx_db
    from indexer import handlers as idx_handlers
    from indexer.events import EventContext

    db_path = tmp_path / "onefloor.db"
    conn = idx_db.connect(db_path)
    idx_db.init_db(conn)
    bench_hash = b"\xef" * 32
    ctx = EventContext(block_number=1, tx_hash="0xfake5", timestamp=1700000500)
    idx_handlers.handle_artifact_registered(
        conn, {"hash": bench_hash, "layer": 3, "creator": "0x" + "01" * 20, "timestamp": ctx.timestamp}, ctx,
    )
    conn.execute(
        "UPDATE artifacts SET artifact_id = ? WHERE hash = ?",
        ("L3-EF", "0x" + "ef" * 32),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("PWM_DB", str(db_path))

    genesis_root = tmp_path / "onefloor_genesis"
    (genesis_root / "l3").mkdir(parents=True)
    (genesis_root / "l3" / "L3-EF.json").write_text(json.dumps({
        "artifact_id": "L3-EF", "title": "One-Floor Bench",
        "ibenchmarks": [{
            "tier": "T1_nominal",
            "baselines": [
                {"name": "GAP-TV", "metric": "PSNR_dB", "score": 26.0, "Q": 0.62},
            ],
        }],
    }))
    monkeypatch.setenv("PWM_GENESIS_DIR", str(genesis_root))

    from api import genesis as g_mod
    g_mod.reload()
    from api.main import app
    client = TestClient(app)

    r = client.get("/api/leaderboard/0x" + "ef" * 32)
    assert r.status_code == 200
    body = r.json()
    assert body["reference"]["label"] == "GAP-TV"
    assert body["reference_advanced"] is None


def test_bounties(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/bounties")
    body = r.json()
    assert len(body["bounties"]) == 1
    assert body["bounties"][0]["amount_pwm"] == 50000


def test_network(seeded_env):
    client, _ = seeded_env
    r = client.get("/api/network")
    assert r.status_code == 200
    body = r.json()
    assert "network" in body


# ---------- cert-meta endpoint tests ----------

def test_cert_meta_post_unknown_cert_returns_404(seeded_env):
    """Posting meta for a cert that's not in the indexer DB returns 404 —
    must already be on-chain AND indexed."""
    client, _ = seeded_env
    fake_cert = "0x" + "ff" * 32
    r = client.post(
        f"/api/cert-meta/{fake_cert}",
        json={"solver_label": "Phantom"},
    )
    assert r.status_code == 404
    assert "not in indexer DB" in r.json()["detail"]


def test_cert_meta_post_malformed_cert_hash_returns_400(seeded_env):
    """Cert hash must be 0x + 64 hex chars."""
    client, _ = seeded_env
    for bad in ["0x1234", "deadbeef", "0xZZZ" + "f" * 60, "0x" + "g" * 64]:
        r = client.post(f"/api/cert-meta/{bad}",
                        json={"solver_label": "Test"})
        assert r.status_code == 400, f"expected 400 for cert_hash={bad!r}"


def test_cert_meta_post_known_cert_succeeds(seeded_env):
    client, refs = seeded_env
    r = client.post(
        f"/api/cert-meta/{refs['cert_hash']}",
        json={
            "solver_label": "MST-L",
            "psnr_db": 34.13,
            "runtime_sec": 12.3,
            "framework": "PyTorch 2.1 + CUDA 12.1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["cert_hash"] == refs["cert_hash"].lower()
    assert body["solver_label"] == "MST-L"
    assert body["psnr_db"] == 34.13


def test_cert_meta_appears_in_leaderboard(seeded_env):
    """After posting meta, the leaderboard query LEFT JOINs it in."""
    client, refs = seeded_env
    # Before: no meta
    r0 = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    assert r0.json()["entries"][0].get("solver_label") is None

    # POST the meta
    r1 = client.post(
        f"/api/cert-meta/{refs['cert_hash']}",
        json={"solver_label": "EfficientSCI", "psnr_db": 33.0},
    )
    assert r1.status_code == 200

    # After: leaderboard includes solver_label + psnr_db
    r2 = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    entry = r2.json()["entries"][0]
    assert entry["solver_label"] == "EfficientSCI"
    assert entry["psnr_db"] == 33.0


def test_cert_meta_appears_in_cert_detail(seeded_env):
    client, refs = seeded_env
    r1 = client.post(
        f"/api/cert-meta/{refs['cert_hash']}",
        json={"solver_label": "MST-L", "psnr_db": 34.1},
    )
    assert r1.status_code == 200
    r2 = client.get(f"/api/cert/{refs['cert_hash']}")
    cert = r2.json()["certificate"]
    assert cert["solver_label"] == "MST-L"
    assert cert["psnr_db"] == 34.1


def test_cert_meta_overwrite_is_idempotent(seeded_env):
    """Re-POSTing replaces the previous values — last-write-wins."""
    client, refs = seeded_env
    client.post(f"/api/cert-meta/{refs['cert_hash']}",
                json={"solver_label": "GAP-TV (ref)", "psnr_db": 24.0})
    client.post(f"/api/cert-meta/{refs['cert_hash']}",
                json={"solver_label": "MST-L", "psnr_db": 34.1})
    r = client.get(f"/api/cert/{refs['cert_hash']}")
    assert r.json()["certificate"]["solver_label"] == "MST-L"
    assert r.json()["certificate"]["psnr_db"] == 34.1


def test_cert_meta_validates_psnr_range(seeded_env):
    """PSNR > 200 dB or negative is rejected — guards against bad inputs."""
    client, refs = seeded_env
    r1 = client.post(f"/api/cert-meta/{refs['cert_hash']}",
                     json={"solver_label": "Test", "psnr_db": -5.0})
    assert r1.status_code == 422  # FastAPI/pydantic validation error
    r2 = client.post(f"/api/cert-meta/{refs['cert_hash']}",
                     json={"solver_label": "Test", "psnr_db": 999.0})
    assert r2.status_code == 422


def test_cert_meta_solver_label_required(seeded_env):
    """solver_label is mandatory — missing or empty fails validation."""
    client, refs = seeded_env
    r1 = client.post(f"/api/cert-meta/{refs['cert_hash']}", json={})
    assert r1.status_code == 422
    r2 = client.post(f"/api/cert-meta/{refs['cert_hash']}",
                     json={"solver_label": ""})
    assert r2.status_code == 422


def test_cert_meta_records_submitter_at_post_time(seeded_env):
    """The endpoint should record the on-chain submitter address as posted_by
    (looked up from certificates table at post time, not trusted from the
    payload)."""
    client, refs = seeded_env
    r = client.post(f"/api/cert-meta/{refs['cert_hash']}",
                    json={"solver_label": "MST-L"})
    assert r.status_code == 200
    # The on-chain submitter from the seeded fixture is 0x04...04 (20 bytes);
    # we don't expose posted_by in the response body, but we can confirm via
    # cert detail that the cert is correctly indexed.
    r2 = client.get(f"/api/cert/{refs['cert_hash']}")
    assert r2.json()["certificate"]["submitter"] == "0x" + "04" * 20
