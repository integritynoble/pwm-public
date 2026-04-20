"""Runtime configuration for the PWM indexer."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INTERFACES_DIR = REPO_ROOT / "coordination" / "agent-coord" / "interfaces"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "pwm_index.db"
DEFAULT_ADDRESSES = INTERFACES_DIR / "addresses.json"
DEFAULT_ABI_DIR = INTERFACES_DIR / "contracts_abi"


@dataclass(frozen=True)
class IndexerConfig:
    rpc_url: str
    network: str  # 'local' | 'testnet' | 'mainnet'
    db_path: Path
    abi_dir: Path
    addresses: dict
    poll_interval_seconds: int
    backfill_chunk: int
    start_block: int | None

    @property
    def contract_addresses(self) -> dict[str, str]:
        return {k: v for k, v in self.addresses.items() if isinstance(v, str) and v.startswith("0x")}


def load_config() -> IndexerConfig:
    network = os.environ.get("PWM_NETWORK", "testnet")
    addresses_file = Path(os.environ.get("PWM_ADDRESSES", str(DEFAULT_ADDRESSES)))
    addresses_all = json.loads(addresses_file.read_text())
    network_addresses = addresses_all.get(network, {})

    default_rpc = {
        "local": "http://127.0.0.1:8545",
        "testnet": "https://rpc.sepolia.org",
        "mainnet": "https://eth.llamarpc.com",
    }[network]

    return IndexerConfig(
        rpc_url=os.environ.get("PWM_RPC_URL", default_rpc),
        network=network,
        db_path=Path(os.environ.get("PWM_DB", str(DEFAULT_DB_PATH))),
        abi_dir=Path(os.environ.get("PWM_ABI_DIR", str(DEFAULT_ABI_DIR))),
        addresses=network_addresses,
        poll_interval_seconds=int(os.environ.get("PWM_POLL_SECONDS", "12")),
        backfill_chunk=int(os.environ.get("PWM_BACKFILL_CHUNK", "5000")),
        start_block=int(os.environ["PWM_START_BLOCK"]) if os.environ.get("PWM_START_BLOCK") else None,
    )


def load_abi(abi_dir: Path, name: str) -> list[dict]:
    data = json.loads((abi_dir / f"{name}.json").read_text())
    return data["abi"]
