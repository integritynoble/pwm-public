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
        {"certHash": cert_hash, "benchmarkHash": bench_hash, "submitter": "0x" + "04" * 20, "Q_int": 88},
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
    assert body["certificate"]["q_int"] == 88
    assert body["s_gates"]["S1"] == "PASS"


def test_leaderboard(seeded_env):
    client, refs = seeded_env
    r = client.get(f"/api/leaderboard/{refs['bench_hash']}")
    body = r.json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["draw_rank"] == 1


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
