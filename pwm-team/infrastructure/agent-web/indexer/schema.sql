-- PWM Web Indexer schema
-- One SQLite DB captures all on-chain activity needed by the API.

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Artifacts: L1 principles, L2 specs, L3 benchmarks (layer=1,2,3).
-- hash = bytes32 (stored as 0x-prefixed hex).
CREATE TABLE IF NOT EXISTS artifacts (
    hash TEXT PRIMARY KEY,
    parent_hash TEXT,
    layer INTEGER NOT NULL,
    creator TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    block_number INTEGER NOT NULL,
    tx_hash TEXT NOT NULL,
    -- Off-chain linkage: artifact_id like "L1-003" once resolved from genesis JSON.
    artifact_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_artifacts_layer ON artifacts(layer);
CREATE INDEX IF NOT EXISTS idx_artifacts_parent ON artifacts(parent_hash);

-- Certificates: solutions submitted against a benchmark.
-- status: 0=Pending, 1=Challenged, 2=Finalized, 3=Invalid, 4=Resolved.
CREATE TABLE IF NOT EXISTS certificates (
    cert_hash TEXT PRIMARY KEY,
    benchmark_hash TEXT NOT NULL,
    submitter TEXT NOT NULL,
    q_int INTEGER NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    submitted_at INTEGER NOT NULL,
    finalized_rank INTEGER,
    challenger TEXT,
    challenge_upheld INTEGER,
    block_number INTEGER NOT NULL,
    tx_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_certificates_benchmark ON certificates(benchmark_hash);
CREATE INDEX IF NOT EXISTS idx_certificates_submitter ON certificates(submitter);
CREATE INDEX IF NOT EXISTS idx_certificates_status ON certificates(status);

-- Draws: reward settlement events (one row per DrawSettled).
CREATE TABLE IF NOT EXISTS draws (
    cert_hash TEXT PRIMARY KEY,
    benchmark_hash TEXT NOT NULL,
    rank INTEGER NOT NULL,
    draw_amount TEXT NOT NULL,
    rollover_remaining TEXT NOT NULL,
    settled_at INTEGER NOT NULL,
    block_number INTEGER NOT NULL,
    tx_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_draws_benchmark ON draws(benchmark_hash);

-- Royalty payouts: AC/CP/treasury per certificate.
CREATE TABLE IF NOT EXISTS royalties (
    cert_hash TEXT PRIMARY KEY,
    ac_addr TEXT NOT NULL,
    ac_amount TEXT NOT NULL,
    cp_addr TEXT NOT NULL,
    cp_amount TEXT NOT NULL,
    treasury_amount TEXT NOT NULL,
    paid_at INTEGER NOT NULL,
    block_number INTEGER NOT NULL
);

-- Pool state: current balance per benchmark (Pool_k).
CREATE TABLE IF NOT EXISTS pool_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_hash TEXT NOT NULL,
    amount TEXT NOT NULL,
    new_balance TEXT NOT NULL,
    from_addr TEXT NOT NULL,
    kind TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    timestamp INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pool_events_benchmark ON pool_events(benchmark_hash);

-- Treasury receipts: per-principle treasury balance (T_k).
CREATE TABLE IF NOT EXISTS treasury_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    principle_id TEXT NOT NULL,
    amount TEXT NOT NULL,
    new_balance TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    winner TEXT,
    block_number INTEGER NOT NULL,
    timestamp INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_treasury_events_principle ON treasury_events(principle_id);
