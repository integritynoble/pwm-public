"""Event decoding utilities.

Separated from main.py so tests can drive decoding without a live RPC.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def to_hex(x: Any) -> str:
    """Normalize a bytes/HexBytes/str into a 0x-prefixed lowercase hex string."""
    if isinstance(x, (bytes, bytearray, memoryview)):
        return "0x" + bytes(x).hex()
    if isinstance(x, str):
        return x.lower() if x.startswith("0x") else "0x" + x.lower()
    raise TypeError(f"not hex-convertible: {type(x)!r}")


def to_addr(x: Any) -> str:
    """Checksum-less lower-case address string, for indexing keys."""
    if isinstance(x, str):
        return x.lower()
    if isinstance(x, (bytes, bytearray)):
        return "0x" + bytes(x).hex()
    raise TypeError(f"not address-convertible: {type(x)!r}")


@dataclass(frozen=True)
class EventContext:
    block_number: int
    tx_hash: str
    timestamp: int  # seconds
