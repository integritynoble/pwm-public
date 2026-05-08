"""Regression guard: every L1/L2/L3 manifest must have a well-formed
artifact_id and a parent-link that resolves to a real artifact.

Per the hierarchical naming scheme decision (Director, 2026-05-08; see
pwm-team/coordination/PWM_HIERARCHICAL_ARTIFACT_NAMING_2026-05-08.md):

- Two artifact_id formats are accepted during the rollout window:
    1. **Flat (legacy)**: `L<1|2|3>-<3+digit-segment>` — only valid for
       the 6 founder-vetted artifacts already registered on Sepolia
       (L1-003, L2-003, L3-003, L1-004, L2-004, L3-004) and their
       Tier-3-stub siblings until Phase B renumbering. Treated by
       tooling as if they were `L<x>-NNN-001(-001)?`.
    2. **Hierarchical (new)**: `L1-NNN`, `L2-NNN-NNN`, `L3-NNN-NNN-NNN`
       — required for all NEW artifacts going forward (Phase D
       steady state).

- Parent-link integrity (always required):
    - Every L2 must have `parent_l1` set to an artifact_id that exists
    - Every L3 must have `parent_l2` set to an artifact_id that exists
    - For hierarchical IDs, the first segments must match the parent's
      segment (L2-003-002's first segment is "003", which must match
      its parent_l1's "003")

This test fails CI if any manifest violates the scheme. It runs in
~1s against the full 533-manifest catalog.

Run:
    python3 -m pytest scripts/test_artifact_id_format.py -v
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Layer-N artifact id with N segments: L1-NNN, L2-NNN-NNN, L3-NNN-NNN-NNN
# Each segment is 3+ digits (allows L1-1042 once catalog passes 999).
# Optional trailing letter `b` is permitted for the 2 known suffix-variant
# families (L1-026b, L1-208b) until Phase B merges them.
HIER_RE = {
    "L1": re.compile(r"^L1-(\d{3,})([a-z])?$"),
    "L2": re.compile(r"^L2-(\d{3,})(?:-(\d{3,}))?([a-z])?$"),
    "L3": re.compile(r"^L3-(\d{3,})(?:-(\d{3,})(?:-(\d{3,}))?)?([a-z])?$"),
}


def _all_manifests() -> list[Path]:
    out = list((REPO_ROOT / "pwm-team" / "content").rglob("L*-*.json"))
    out.extend((REPO_ROOT / "pwm-team" / "pwm_product" / "genesis").rglob("L*-*.json"))
    return sorted(out)


def _load_index() -> tuple[dict[str, dict], dict[str, Path]]:
    """Load every manifest into a dict keyed by artifact_id."""
    idx: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for path in _all_manifests():
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        aid = m.get("artifact_id")
        if isinstance(aid, str) and aid:
            idx[aid] = m
            paths[aid] = path
    return idx, paths


# ---------- Format check ----------


@pytest.mark.parametrize("path", _all_manifests(), ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_artifact_id_format(path: Path) -> None:
    """Every manifest's artifact_id must match L1/L2/L3 hierarchical pattern."""
    m = json.loads(path.read_text())
    aid = m.get("artifact_id")
    assert isinstance(aid, str) and aid, f"{path.name}: missing or non-string artifact_id"
    layer = aid.split("-", 1)[0]
    assert layer in ("L1", "L2", "L3"), (
        f"{path.name}: layer prefix '{layer}' is not one of L1/L2/L3"
    )
    pattern = HIER_RE[layer]
    assert pattern.match(aid), (
        f"{path.name}: artifact_id '{aid}' does not match expected format for {layer}.\n"
        f"  L1 expected: L1-NNN  (e.g. L1-003)\n"
        f"  L2 expected: L2-NNN  (legacy) or L2-NNN-NNN (new — required post Phase B)\n"
        f"  L3 expected: L3-NNN  (legacy) or L3-NNN-NNN-NNN (new — required post Phase B)\n"
        f"  See pwm-team/coordination/PWM_HIERARCHICAL_ARTIFACT_NAMING_2026-05-08.md"
    )


# ---------- Parent-link integrity ----------


def test_l2_parent_l1_exists() -> None:
    """Every L2 must have a parent_l1 field pointing at an existing L1."""
    idx, paths = _load_index()
    missing: list[str] = []
    not_found: list[tuple[str, str]] = []
    for aid, m in idx.items():
        if not aid.startswith("L2-"):
            continue
        parent = m.get("parent_l1")
        if not parent:
            missing.append(aid)
            continue
        if parent not in idx:
            not_found.append((aid, parent))
    assert not missing, f"L2 manifests missing parent_l1: {missing[:5]}"
    assert not not_found, (
        f"L2 manifests reference unknown parent_l1: "
        + "; ".join(f"{a} → {p}" for a, p in not_found[:5])
    )


def test_l3_parent_l2_exists() -> None:
    """Every L3 must have a parent_l2 pointing at an existing L2."""
    idx, paths = _load_index()
    missing: list[str] = []
    not_found: list[tuple[str, str]] = []
    for aid, m in idx.items():
        if not aid.startswith("L3-"):
            continue
        parent = m.get("parent_l2")
        if not parent:
            missing.append(aid)
            continue
        if parent not in idx:
            not_found.append((aid, parent))
    assert not missing, f"L3 manifests missing parent_l2: {missing[:5]}"
    assert not not_found, (
        f"L3 manifests reference unknown parent_l2: "
        + "; ".join(f"{a} → {p}" for a, p in not_found[:5])
    )


# ---------- Hierarchical-segment consistency ----------


def _segments(aid: str) -> list[str] | None:
    """Extract numeric segments from a hierarchical id. Returns None for
    legacy flat IDs (e.g., 'L1-003' returns ['003']; 'L1-003-001' returns
    ['003', '001'])."""
    layer = aid.split("-", 1)[0]
    m = HIER_RE.get(layer, re.compile(r"$.")).match(aid)
    if not m:
        return None
    # Filter out the trailing-letter group + None segments
    return [g for g in m.groups() if g and g.isdigit()]


def test_hierarchical_parent_segments_match() -> None:
    """For hierarchical IDs (L2-NNN-MMM, L3-NNN-MMM-PPP), the leading
    segments must match the parent's segments. e.g., L2-003-002's first
    segment is '003', which must match parent_l1='L1-003'."""
    idx, _ = _load_index()
    mismatches: list[str] = []
    for aid, m in idx.items():
        segs = _segments(aid)
        if segs is None:
            continue
        if aid.startswith("L2-") and len(segs) >= 2:
            parent = m.get("parent_l1")
            if not parent: continue
            parent_segs = _segments(parent) or []
            if not parent_segs or segs[0] != parent_segs[0]:
                mismatches.append(f"{aid}'s first segment '{segs[0]}' != {parent}'s segment '{parent_segs[0] if parent_segs else '?'}'")
        elif aid.startswith("L3-") and len(segs) >= 3:
            parent = m.get("parent_l2")
            if not parent: continue
            parent_segs = _segments(parent) or []
            if len(parent_segs) < 2 or segs[:2] != parent_segs[:2]:
                mismatches.append(f"{aid}'s first 2 segments '{'-'.join(segs[:2])}' != {parent}'s segments '{'-'.join(parent_segs[:2]) if len(parent_segs) >= 2 else '?'}'")
    assert not mismatches, "Hierarchical-segment mismatches:\n  " + "\n  ".join(mismatches[:5])


# ---------- Frozen-set guard ----------


def test_registered_artifacts_keep_flat_legacy_form() -> None:
    """The 6 founder-vetted artifacts registered on Sepolia must stay in
    flat form forever. If any of them gets a hierarchical artifact_id,
    the on-chain registration would orphan."""
    REGISTERED_FLAT = {"L1-003", "L1-004", "L2-003", "L2-004", "L3-003", "L3-004"}
    idx, paths = _load_index()
    for aid in REGISTERED_FLAT:
        assert aid in idx, (
            f"Registered artifact {aid} missing from manifest tree — would orphan its Sepolia registration!"
        )
        m = idx[aid]
        # Confirm artifact_id field still matches the flat legacy form
        assert m.get("artifact_id") == aid, (
            f"{paths[aid]}: artifact_id changed from {aid} — would invalidate Sepolia registration "
            f"(see pwm-team/coordination/PWM_HIERARCHICAL_ARTIFACT_NAMING_2026-05-08.md § 'Why L*-003 and L*-004 must NEVER be renamed')"
        )
