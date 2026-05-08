"""Regression guard: every (layer, display_slug) pair must be unique
across the L1/L2/L3 catalog.

Resolves the slug-collision findings from 2026-05-08. Without this gate,
a future PR can re-introduce duplicate slugs (a simple copy-paste of an
existing manifest with the original slug retained), and `pwm-node inspect <slug>`
+ web `/principles/<slug>` lookups would silently route to whichever
artifact happened to be loaded first.

Run:
    python3 -m pytest scripts/test_unique_slugs.py -v
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _all_manifests() -> list[Path]:
    out = list((REPO_ROOT / "pwm-team" / "content").rglob("L*-*.json"))
    out.extend((REPO_ROOT / "pwm-team" / "pwm_product" / "genesis").rglob("L*-*.json"))
    return sorted(out)


def _slug_groups() -> dict[tuple[str, str], list[str]]:
    """Build (layer, slug) → [artifact_ids]."""
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in _all_manifests():
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        aid = m.get("artifact_id") or ""
        layer = aid.split("-", 1)[0]
        slug = (m.get("display_slug") or "").lower()
        if layer in ("L1", "L2", "L3") and slug:
            groups[(layer, slug)].append(aid)
    return groups


def test_no_slug_collisions() -> None:
    """No (layer, slug) pair may be claimed by 2+ distinct artifacts."""
    groups = _slug_groups()
    collisions = {k: v for k, v in groups.items() if len(v) > 1}
    if collisions:
        details = "\n".join(
            f"  {layer} slug='{slug}' is claimed by: {aids}"
            for (layer, slug), aids in sorted(collisions.items())
        )
        pytest.fail(
            f"Found {len(collisions)} slug collision group(s):\n{details}\n\n"
            f"Fix: edit the offending manifests to use unique display_slug "
            f"values, then re-run scripts/fix_slug_collisions.py if you want "
            f"the canonical naming convention applied. Slugs must be unique "
            f"WITHIN each layer (the same slug across L1/L2/L3 of the same "
            f"modality is fine)."
        )
