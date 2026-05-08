"""Canonical-JSON hashing for PWM artifacts — single source of truth.

The on-chain `bytes32` artifact hash is keccak256 over a canonical-JSON
serialization of the manifest with `UI_ONLY_FIELDS` stripped. The same
recipe must be used everywhere a hash is computed:

  - ``scripts/register_genesis.py`` (when founders register an artifact
    on-chain).
  - ``pwm_node.commands.mine`` (when a miner builds a cert payload that
    will reference an existing benchmark by ``benchmarkHash``).
  - Any auditor / verifier that wants to recompute an artifact hash from
    its committed JSON to confirm on-chain registration matches the
    file in the repo.

Keeping a single module here prevents the failure mode that surfaced
during the 2026-05-07 audit, where a duplicate ``_UI_ONLY_FIELDS``
frozenset in ``mine.py`` had drifted from the one in
``register_genesis.py`` (was missing ``display_baselines`` after
2026-05-06's two-tier-reference-floor commit landed). The drift broke
``benchmarkHash`` invariance and caused real ``pwm-node mine`` calls
to revert with "benchmark not registered" until the duplicate was
brought back in sync.

Adding a new UI-only field in the future:
  1. Add the field name here in ``UI_ONLY_FIELDS``.
  2. That's it — both consumers (the registration script and the mine
     command) automatically pick up the change because they import
     this module.
"""
from __future__ import annotations

import json
from typing import Any


# UI-only fields excluded from the canonical-JSON serialization. Adding
# a slug or other pure-display field must NOT change the on-chain
# artifact hash — otherwise existing registrations orphan and
# ``pwm-node mine`` fails with "benchmark not registered" against any
# benchmark whose manifest carries the new field. Keep this set small
# and only extend it for fields that are STRICTLY presentation.
UI_ONLY_FIELDS: frozenset[str] = frozenset({
    "display_slug",
    "display_color",
    "ui_metadata",
    "registration_tier",
    "display_baselines",  # leaderboard-floor sidecar; e.g. deep-learning
                          # SOTA landmarks added off-chain via cert-meta.
                          # `baselines[]` is canonical (contributes to hash);
                          # `display_baselines` is UI-only (stripped before keccak).
})


def canonical_for_hashing(obj: Any) -> Any:
    """Strip UI-only fields before computing the canonical hash.

    The chain stores ``keccak256(canonical_json(manifest))``. Manifests
    authored after 2026-05-03 may include human-readable display fields
    that DID NOT exist when earlier artifacts were registered. To keep
    hash-invariance across schema additions, we filter those fields out
    before hashing.

    For non-dict inputs the value is returned unchanged.
    """
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in UI_ONLY_FIELDS}
    return obj


def canonical_json(obj: Any) -> bytes:
    """Stable-serialize ``obj`` to UTF-8 bytes for hashing.

    Convention: sorted keys, compact separators, UTF-8 encoding. Matches
    Python's ``json.dumps(sort_keys=True, separators=(",", ":")).encode("utf-8")``.

    The JavaScript registration script ``register_genesis.js`` cannot
    faithfully reproduce this — JS Numbers lose the int/float distinction
    at parse time, so ``26.0`` serializes as ``"26"`` in JS and
    ``"26.0"`` in Python. The hashes diverge. Always use this Python
    routine for any on-chain registration or verification.
    """
    filtered = canonical_for_hashing(obj)
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")
