"""Read-only access to off-chain genesis JSON artifacts.

The chain only carries hashes; the rich metadata (L_DAG, forward_model, omega
bounds, baselines, etc.) lives in `pwm-team/pwm_product/genesis/l{1,2,3}/*.json`.
This module loads them lazily and exposes simple lookup helpers.
"""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable


# __file__ = .../pwm-team/infrastructure/agent-web/api/genesis.py
# .parents[3] = .../pwm-team (local); Docker: /repo/pwm-team
try:
    PWM_TEAM_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    PWM_TEAM_ROOT = Path("/repo/pwm-team")
DEFAULT_GENESIS_DIR = PWM_TEAM_ROOT / "pwm_product" / "genesis"


def genesis_dir() -> Path:
    return Path(os.environ.get("PWM_GENESIS_DIR", str(DEFAULT_GENESIS_DIR)))


def _canonical_hash(artifact: dict) -> str:
    """Deterministic content hash used to link a JSON file to an on-chain hash.

    We canonicalize (sorted keys, no whitespace) and keccak-like hash with SHA-256.
    Contracts use keccak256; until genesis JSONs are re-hashed with the same scheme
    the lookup is best-effort. This helper still lets the UI show JSONs in a
    stable order and serves as a stand-in.
    """
    canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    return "0x" + hashlib.sha256(canonical).hexdigest()


@lru_cache(maxsize=1)
def load_all() -> dict[str, list[dict]]:
    """Return all genesis JSON artifacts bucketed by layer."""
    root = genesis_dir()
    result: dict[str, list[dict]] = {"l1": [], "l2": [], "l3": []}
    for layer in ("l1", "l2", "l3"):
        layer_dir = root / layer
        if not layer_dir.exists():
            continue
        for path in sorted(layer_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            data.setdefault("_source_path", str(path.relative_to(root)))
            data.setdefault("_content_hash", _canonical_hash({k: v for k, v in data.items() if not k.startswith("_")}))
            result[layer].append(data)
    return result


def reload() -> None:
    load_all.cache_clear()


def principles() -> list[dict]:
    return load_all()["l1"]


def specs() -> list[dict]:
    return load_all()["l2"]


def benchmarks() -> list[dict]:
    return load_all()["l3"]


def by_artifact_id(artifact_id: str) -> dict | None:
    for layer in ("l1", "l2", "l3"):
        for item in load_all()[layer]:
            if item.get("artifact_id") == artifact_id:
                return item
    return None


def by_slug(slug: str, layer: str | None = None) -> dict | None:
    """Resolve a manifest by its `display_slug` field.

    Used by URL-routing: `/benchmarks/cassi` → look up the L3 manifest with
    display_slug="cassi" → return its artifact_id "L3-003" → resolve the
    chain row.

    If `layer` is given (l1, l2, or l3), only search that layer; otherwise
    search L3 first (the most-common consumer-facing layer), then L2, then L1.
    """
    if not slug:
        return None
    layers = (layer,) if layer else ("l3", "l2", "l1")
    for la in layers:
        for item in load_all().get(la, []):
            if item.get("display_slug") == slug:
                return item
    return None


def resolve_ref(ref: str, prefer_layer: str | None = None) -> dict | None:
    """Universal benchmark/spec/principle resolver.

    Tries in order:
      1. exact artifact_id match (L1-003, L2-003, L3-003)
      2. exact display_slug match (cassi, cacti)

    Used by API endpoints that accept either form of reference.
    """
    if not ref:
        return None
    hit = by_artifact_id(ref)
    if hit is not None:
        return hit
    return by_slug(ref, layer=prefer_layer)


def specs_for_principle(l1_id: str) -> list[dict]:
    return [s for s in specs() if s.get("parent_l1") == l1_id]


def benchmarks_for_spec(l2_id: str) -> list[dict]:
    return [b for b in benchmarks() if b.get("parent_l2") == l2_id]


def summarize_principle(p: dict) -> dict:
    """Flatten the pieces the /principles list view wants."""
    g = p.get("G") or {}
    spec_range = p.get("spec_range") or {}
    active_specs = specs_for_principle(p.get("artifact_id", ""))
    return {
        "artifact_id": p.get("artifact_id"),
        "title": p.get("title"),
        "domain": p.get("domain"),
        "sub_domain": p.get("sub_domain"),
        "difficulty_delta": p.get("difficulty_delta"),
        "difficulty_tier": p.get("difficulty_tier"),
        "L_DAG": g.get("L_DAG"),
        "forward_model": (p.get("E") or {}).get("forward_model"),
        "active_spec_count": len(active_specs),
        "active_benchmark_count": sum(len(benchmarks_for_spec(s.get("artifact_id", ""))) for s in active_specs),
        "epsilon_center": (spec_range.get("center_spec") or {}).get("epsilon_fn_center"),
    }


def summarize_benchmark(b: dict) -> dict:
    spec_id = b.get("parent_l2")
    spec = by_artifact_id(spec_id) if spec_id else None
    principle_id = spec.get("parent_l1") if spec else None
    ibench = (b.get("ibenchmark") or {})
    return {
        "artifact_id": b.get("artifact_id"),
        "parent_l2": spec_id,
        "parent_l1": principle_id,
        "title": b.get("title") or (spec.get("title") if spec else None),
        "rho": b.get("rho") or ibench.get("rho"),
        "omega_tier": b.get("omega_tier") or ibench.get("omega_tier"),
        "epsilon": b.get("epsilon") or ibench.get("epsilon"),
        "domain": (spec.get("domain") if spec else None),
    }


def summarize_spec(s: dict) -> dict:
    return {
        "artifact_id": s.get("artifact_id"),
        "parent_l1": s.get("parent_l1"),
        "title": s.get("title"),
        "spec_type": s.get("spec_type"),
        "d_spec": s.get("d_spec"),
        "ibenchmark_center": (s.get("ibenchmark_range") or {}).get("center_ibenchmark"),
    }


def principle_domains() -> Iterable[str]:
    seen = set()
    for p in principles():
        d = p.get("domain")
        if d and d not in seen:
            seen.add(d)
            yield d
