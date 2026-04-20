"""PWM chain indexer entry point.

Backfills all historical events from the deployment block, then polls new blocks
at `poll_interval_seconds` (12s default = one Ethereum block).

Run directly:  python -m indexer.main
Env vars:
  PWM_RPC_URL        HTTP RPC endpoint (WebSocket not required for polling)
  PWM_NETWORK        local|testnet|mainnet (selects addresses.json entry)
  PWM_DB             SQLite path (default: indexer/pwm_index.db)
  PWM_START_BLOCK    Starting block (default: latest_indexed+1 or deploy block)
"""
from __future__ import annotations

import logging
import sqlite3
import sys
import time
from pathlib import Path

# Allow running as a script *or* a module.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from indexer import config as config_mod  # type: ignore
    from indexer import db as db_mod  # type: ignore
    from indexer.events import EventContext  # type: ignore
    from indexer.handlers import HANDLERS  # type: ignore
else:
    from . import config as config_mod
    from . import db as db_mod
    from .events import EventContext
    from .handlers import HANDLERS

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:  # pragma: no cover — import guard for envs without web3
    Web3 = None  # type: ignore
    ExtraDataToPOAMiddleware = None  # type: ignore


log = logging.getLogger("pwm-indexer")


# Contracts that emit the events we care about.
CONTRACTS = ("PWMRegistry", "PWMCertificate", "PWMReward", "PWMTreasury")


class Indexer:
    def __init__(self, cfg: config_mod.IndexerConfig, conn: sqlite3.Connection):
        if Web3 is None:
            raise RuntimeError("web3 package is required to run the indexer")
        self.cfg = cfg
        self.conn = conn
        self.w3 = Web3(Web3.HTTPProvider(cfg.rpc_url, request_kwargs={"timeout": 30}))
        if ExtraDataToPOAMiddleware is not None:
            # Sepolia/goerli include >32-byte extraData; POA middleware tolerates it.
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.contracts = {}
        self.event_signatures = {}  # (contract, event_name) -> signature_hash
        for name in CONTRACTS:
            addr = cfg.addresses.get(name)
            if not addr:
                log.warning("No address for %s on %s; skipping", name, cfg.network)
                continue
            abi = config_mod.load_abi(cfg.abi_dir, name)
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
            self.contracts[name] = contract

    # ---- public loop ----
    def run(self) -> None:
        latest = self.w3.eth.block_number
        from_block = self._resolve_start_block()
        log.info("Indexing from block %d to head %d", from_block, latest)
        head = self._backfill(from_block, latest)
        while True:
            time.sleep(self.cfg.poll_interval_seconds)
            new_head = self.w3.eth.block_number
            if new_head <= head:
                continue
            head = self._backfill(head + 1, new_head)

    # ---- internals ----
    def _resolve_start_block(self) -> int:
        if self.cfg.start_block is not None:
            return self.cfg.start_block
        last = db_mod.get_meta(self.conn, "last_block")
        if last:
            return int(last) + 1
        return 0

    def _backfill(self, from_block: int, to_block: int) -> int:
        chunk = self.cfg.backfill_chunk
        cursor = from_block
        while cursor <= to_block:
            chunk_end = min(cursor + chunk - 1, to_block)
            self._scan_range(cursor, chunk_end)
            with db_mod.transaction(self.conn):
                db_mod.set_meta(self.conn, "last_block", str(chunk_end))
            cursor = chunk_end + 1
        return to_block

    def _scan_range(self, from_block: int, to_block: int) -> None:
        for (contract_name, event_name), handler in HANDLERS.items():
            contract = self.contracts.get(contract_name)
            if contract is None:
                continue
            event = getattr(contract.events, event_name, None)
            if event is None:
                continue
            try:
                logs = event.get_logs(from_block=from_block, to_block=to_block)
            except Exception as exc:  # RPC can fail on large ranges; shrink and retry.
                log.warning("get_logs failed for %s.%s (%d-%d): %s",
                            contract_name, event_name, from_block, to_block, exc)
                if to_block > from_block:
                    mid = (from_block + to_block) // 2
                    self._scan_range(from_block, mid)
                    self._scan_range(mid + 1, to_block)
                    return
                raise
            if not logs:
                continue
            log.info("%s.%s: %d logs in [%d,%d]", contract_name, event_name, len(logs), from_block, to_block)
            with db_mod.transaction(self.conn):
                for entry in logs:
                    block = self.w3.eth.get_block(entry.blockNumber)
                    ctx = EventContext(
                        block_number=int(entry.blockNumber),
                        tx_hash=entry.transactionHash.hex() if hasattr(entry.transactionHash, "hex") else str(entry.transactionHash),
                        timestamp=int(block.timestamp),
                    )
                    handler(self.conn, dict(entry["args"]), ctx)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = config_mod.load_config()
    conn = db_mod.connect(cfg.db_path)
    db_mod.init_db(conn)
    indexer = Indexer(cfg, conn)
    try:
        indexer.run()
    except KeyboardInterrupt:
        log.info("Indexer stopped")


if __name__ == "__main__":
    main()
