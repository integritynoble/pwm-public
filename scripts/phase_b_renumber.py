#!/usr/bin/env python3
"""Phase B: renumber the Tier-3 stub catalog into the hierarchical naming.

Per PWM_HIERARCHICAL_ARTIFACT_NAMING_2026-05-08.md:

1. The 6 founder-vetted artifacts (L1-003, L2-003, L3-003, L1-004, L2-004,
   L3-004) STAY in flat legacy form forever — registered on Sepolia,
   immutable.

2. The 527 plain (non-suffix-letter) Tier-3 stubs get hierarchical
   children:
     L1-NNN          stays as L1-NNN
       └── L2-NNN    →  L2-NNN-001    (the only spec under it)
             └── L3-NNN  →  L3-NNN-001-001  (the only benchmark)
   Their parent_l1 / parent_l2 fields update accordingly.

3. The 2 suffix-variant L1 families (L1-026/L1-026b, L1-208/L1-208b)
   merge: the variant becomes a sibling sub-spec under the base L1's
   tree.
     L1-026  +  L1-026b   →   L1-026 only (L1-026b file retired)
     L2-026                →   L2-026-001    (random-basis spec)
     L2-026b               →   L2-026-002    (Hadamard spec, was suffix-variant)
     L3-026                →   L3-026-001-001
     L3-026b               →   L3-026-002-001
     parent_l1 / parent_l2 fields rewritten throughout.

In-place edits use json.dumps(indent=2). display_slug stays unchanged
(already in UI_ONLY_FIELDS, plus we deliberately want slugs like
'cassi-v1' / 'cacti-v1' to keep their human-readable names).

Hash impact: ZERO on-chain. All affected files are Tier-3 stubs not
registered. The 6 founder-vetted hashes verified unchanged after run.

Usage:
    python3 scripts/phase_b_renumber.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Frozen set: NEVER renumber these
FROZEN = {"L1-003", "L1-004", "L2-003", "L2-004", "L3-003", "L3-004"}

# Suffix-variant families to merge (variant → new sub-spec ID under base)
SUFFIX_MERGE: dict[str, str | None] = {
    # L1-NNNb: the L1 file is content-duplicate of L1-NNN; the variant's
    # uniqueness lives at L2/L3 layer. The L1 file is retired (deleted).
    # The L2-NNNb / L3-NNNb files become L2-NNN-002 / L3-NNN-002-001.
    "L1-026b": None,        # delete; L1-026 already exists
    "L2-026b": "L2-026-002",
    "L3-026b": "L3-026-002-001",
    "L1-208b": None,        # delete
    "L2-208b": "L2-208-002",
    "L3-208b": "L3-208-002-001",
}

# Re-parent map: when a parent is being deleted, what's the surviving
# parent it should be redirected to?
SUFFIX_REPARENT: dict[str, str] = {
    "L1-026b": "L1-026",
    "L1-208b": "L1-208",
    "L2-026b": "L2-026-001",  # legacy L2-026 will become L2-026-001 in this run
    "L2-208b": "L2-208-001",
}


def _new_id(aid: str) -> str | None:
    """Compute the hierarchical replacement for a flat ID. Returns None
    if the artifact is frozen, has no children to disambiguate, or is a
    suffix-variant handled separately."""
    if aid in FROZEN:
        return None
    if aid in SUFFIX_MERGE:
        return SUFFIX_MERGE[aid]
    parts = aid.split("-")
    if len(parts) != 2:
        return None  # already hierarchical or malformed
    layer, num = parts
    if layer == "L1":
        return None  # L1 stays as is in Phase B (no parent path)
    if layer == "L2":
        return f"L2-{num}-001"
    if layer == "L3":
        return f"L3-{num}-001-001"
    return None


def _new_parent(parent_aid: str | None, layer_being_set: str) -> str | None:
    """When we rewrite L2/L3 IDs, also rewrite their parent_l1 / parent_l2
    fields to use the same scheme. Frozen parents stay flat; renumbered
    parents get the new hierarchical form. Suffix-variant parents
    (L1-026b, L1-208b) get redirected to the surviving sibling per
    SUFFIX_REPARENT (since the variant L1 is being deleted)."""
    if not parent_aid:
        return parent_aid
    if parent_aid in FROZEN:
        return parent_aid
    if parent_aid in SUFFIX_REPARENT:
        return SUFFIX_REPARENT[parent_aid]
    if parent_aid in SUFFIX_MERGE and SUFFIX_MERGE[parent_aid] is not None:
        return SUFFIX_MERGE[parent_aid]
    parts = parent_aid.split("-")
    if len(parts) != 2:
        return parent_aid  # already hierarchical
    layer, num = parts
    if layer == "L1":
        return parent_aid  # L1 stays flat
    if layer == "L2":
        return f"L2-{num}-001"
    return parent_aid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview changes without writing or deleting files.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    files = sorted(list((repo_root / "pwm-team" / "content").rglob("L*-*.json")) +
                   list((repo_root / "pwm-team" / "pwm_product" / "genesis").rglob("L*-*.json")))

    renamed = 0
    deleted = 0
    parent_rewrites = 0
    skipped_frozen = 0

    for path in files:
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        aid = m.get("artifact_id")
        if not isinstance(aid, str):
            continue

        # ---- Decide what to do with this manifest ----
        new_aid = _new_id(aid)

        if aid in FROZEN:
            skipped_frozen += 1
            continue

        if aid in SUFFIX_MERGE and SUFFIX_MERGE[aid] is None:
            # Delete (L1-NNNb files)
            if args.dry_run:
                print(f"  [delete] {aid:<14} {path.relative_to(repo_root)}")
            else:
                path.unlink()
                print(f"  ✓ deleted {aid:<14} {path.relative_to(repo_root)}")
            deleted += 1
            continue

        if new_aid and new_aid != aid:
            m["artifact_id"] = new_aid
            renamed += 1

        # ---- Rewrite parent links (always, not gated on this aid changing) ----
        for parent_field in ("parent_l1", "parent_l2"):
            old_parent = m.get(parent_field)
            new_parent = _new_parent(old_parent, parent_field)
            if new_parent != old_parent:
                m[parent_field] = new_parent
                parent_rewrites += 1

        if new_aid != aid or any(m.get(f) != json.loads(path.read_text()).get(f)
                                  for f in ("parent_l1", "parent_l2") if m.get(f)):
            if args.dry_run:
                print(f"  [rename] {aid:<14} → {new_aid or aid:<18} {path.relative_to(repo_root)}")
            else:
                path.write_text(json.dumps(m, indent=2) + "\n")

    print()
    print(f"Renamed:           {renamed}")
    print(f"Deleted:           {deleted}")
    print(f"Parent rewrites:   {parent_rewrites}")
    print(f"Skipped (frozen):  {skipped_frozen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
