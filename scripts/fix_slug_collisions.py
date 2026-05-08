#!/usr/bin/env python3
"""Resolve display_slug collisions across the L1/L2/L3 catalog.

Audit (2026-05-08) found 6 collision groups (cassi + cacti each in
L1/L2/L3, used by 3 distinct artifacts each):

  cassi:
    L1-532/L2-532/L3-532  Confocal Fluorescence (livecell)  — TYPO
    L1-025/L2-025/L3-025  CASSI Mismatch-Only (v1, content tree) — DUPLICATE
    L1-003/L2-003/L3-003  CASSI (canonical, founder-vetted)  — KEEP

  cacti:
    L1-533/L2-533/L3-533  Confocal Z-Stack            — TYPO
    L1-027/L2-027/L3-027  CACTI Mismatch-Only (v1)     — DUPLICATE
    L1-004/L2-004/L3-004  CACTI (canonical, founder-vetted) — KEEP

The 3 founder-vetted (L*-003 + L*-004) are registered on Sepolia and
must keep their slugs. The other 12 manifests get renamed:

  L*-532   cassi → confocal-livecell    (corrects copy-paste typo)
  L*-533   cacti → confocal-zstack       (corrects copy-paste typo)
  L*-025   cassi → cassi-v1              (disambiguates duplicate variant)
  L*-027   cacti → cacti-v1              (disambiguates duplicate variant)

Hash-invariant: display_slug is in UI_ONLY_FIELDS, stripped before
canonical hashing in scripts/register_genesis.py. Verified by
test_register_genesis.py — running this script does NOT change any
on-chain hash.

Usage:
    python3 scripts/fix_slug_collisions.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Mapping: artifact_id → new slug. Apply consistently across L1/L2/L3 children.
SLUG_FIXES: dict[str, str] = {
    # confocal_livecell typo (was claiming "cassi")
    "L1-532": "confocal-livecell",
    "L2-532": "confocal-livecell",
    "L3-532": "confocal-livecell",
    # confocal_zstack typo (was claiming "cacti")
    "L1-533": "confocal-zstack",
    "L2-533": "confocal-zstack",
    "L3-533": "confocal-zstack",
    # CASSI v1 duplicate in content tree
    "L1-025": "cassi-v1",
    "L2-025": "cassi-v1",
    "L3-025": "cassi-v1",
    # CACTI v1 duplicate in content tree
    "L1-027": "cacti-v1",
    "L2-027": "cacti-v1",
    "L3-027": "cacti-v1",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Show planned changes without writing files.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    files = list((repo_root / "pwm-team" / "content").rglob("L*-*.json")) + \
            list((repo_root / "pwm-team" / "pwm_product" / "genesis").rglob("L*-*.json"))

    fixed = 0
    skipped = 0
    not_found_ids = set(SLUG_FIXES.keys())

    for path in sorted(files):
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        aid = m.get("artifact_id")
        if aid not in SLUG_FIXES:
            continue
        not_found_ids.discard(aid)
        new_slug = SLUG_FIXES[aid]
        old_slug = m.get("display_slug")
        if old_slug == new_slug:
            skipped += 1
            continue
        rel = path.relative_to(repo_root)
        if args.dry_run:
            print(f"  [dry-run] {aid:<10} {rel}: '{old_slug}' → '{new_slug}'")
        else:
            m["display_slug"] = new_slug
            path.write_text(json.dumps(m, indent=2) + "\n")
            print(f"  ✓ {aid:<10} {rel}: '{old_slug}' → '{new_slug}'")
        fixed += 1

    print()
    print(f"Files {'would be' if args.dry_run else ''} updated: {fixed}")
    print(f"Already-correct files skipped: {skipped}")
    if not_found_ids:
        print(f"⚠ Manifests not found for: {sorted(not_found_ids)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
