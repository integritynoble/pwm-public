"""Runtime configuration for the PWM indexer."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


try:
    REPO_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    REPO_ROOT = Path("/repo")  # Docker fallback — repo mounted at /repo
INTERFACES_DIR = REPO_ROOT / "coordination" / "agent-coord" / "interfaces"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "pwm_index.db"
DEFAULT_ADDRESSES = INTERFACES_DIR / "addresses.json"
DEFAULT_ABI_DIR = INTERFACES_DIR / "contracts_abi"


# Per-network default RPC endpoints. Used when PWM_RPC_URL env var is unset.
# Keys match slots in addresses.json. Unknown networks require PWM_RPC_URL
# explicitly — we raise rather than fall through to a wrong default.
DEFAULT_RPCS: dict[str, str] = {
    "local":       "http://127.0.0.1:8545",
    "testnet":     "https://ethereum-sepolia-rpc.publicnode.com",  # Sepolia
    "mainnet":     "https://eth.llamarpc.com",
    "base":        "https://mainnet.base.org",
    "baseSepolia": "https://sepolia.base.org",
    "arbitrum":    "https://arb1.arbitrum.io/rpc",
    "arbSepolia":  "https://sepolia-rollup.arbitrum.io/rpc",
    "optimism":    "https://mainnet.optimism.io",
}


@dataclass(frozen=True)
class IndexerConfig:
    rpc_url: str
    # Slot name in addresses.json. One of: local, testnet, mainnet, base,
    # baseSepolia, arbitrum, arbSepolia, optimism.
    network: str
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
    addresses_all = json.loads(addresses_file.read_text(encoding="utf-8"))
    network_addresses = addresses_all.get(network, {})

    rpc_from_env = os.environ.get("PWM_RPC_URL")
    if rpc_from_env:
        rpc_url = rpc_from_env
    elif network in DEFAULT_RPCS:
        rpc_url = DEFAULT_RPCS[network]
    else:
        raise ValueError(
            f"PWM_NETWORK={network!r} is not a known slot and PWM_RPC_URL "
            f"is not set. Known slots: {sorted(DEFAULT_RPCS)}. Set PWM_RPC_URL "
            "or pick a known network."
        )

    return IndexerConfig(
        rpc_url=rpc_url,
        network=network,
        db_path=Path(os.environ.get("PWM_DB", str(DEFAULT_DB_PATH))),
        abi_dir=Path(os.environ.get("PWM_ABI_DIR", str(DEFAULT_ABI_DIR))),
        addresses=network_addresses,
        poll_interval_seconds=int(os.environ.get("PWM_POLL_SECONDS", "12")),
        backfill_chunk=int(os.environ.get("PWM_BACKFILL_CHUNK", "5000")),
        start_block=int(os.environ["PWM_START_BLOCK"]) if os.environ.get("PWM_START_BLOCK") else None,
    )


def load_abi(abi_dir: Path, name: str) -> list[dict]:
    data = json.loads((abi_dir / f"{name}.json").read_text(encoding="utf-8"))
    return data["abi"]
