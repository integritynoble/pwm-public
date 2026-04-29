"""Migrate v1 genesis L1 manifests to the v2/v3-aware schema.

Per `pwm-team/pwm_product/genesis/PWM_V2_GENESIS_INCLUSION.md` and
`PWM_V3_STANDALONE_VS_COMPOSITE.md` and the schema update in
`pwm-team/content/agent-imaging/CLAUDE.md`.

For every L1-NNN.json under `pwm-team/content/agent-*/principles/`:
- Add `gate_class: "analytical"` if absent.
- Add `gate_substitutions: null` if absent.
- Add `related_principles: []` if absent.
- Add `v3_metadata` block (with is_standalone_multiphysics inferred from G.n_c) if absent.

This is purely additive. v1 contracts ignore these fields (PWMRegistry stores
only the manifest hash). Manifest hashes WILL change — but no v1 mainnet deploy
has happened yet (Step 7 still blocked on deployer ETH funding), so this is
the right window to migrate before genesis hashes get anchored on-chain.

Usage:
    python scripts/migrate_v1_principles_to_v2_schema.py
    python scripts/migrate_v1_principles_to_v2_schema.py --dry-run
    python scripts/migrate_v1_principles_to_v2_schema.py --root pwm-team/content/agent-imaging
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _migrate_manifest(path: Path, dry_run: bool) -> tuple[bool, str]:
    """Add v2/v3 forward-compat fields to a single L1 manifest.

    Returns (changed, reason). `changed=False` means no edits needed.
    """
    try:
        m = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"

    if m.get("layer") != "L1":
        return False, "not an L1 manifest"

    changed = False
    notes: list[str] = []

    if "gate_class" not in m:
        m["gate_class"] = "analytical"
        changed = True
        notes.append("+gate_class")

    if "gate_substitutions" not in m:
        m["gate_substitutions"] = None
        changed = True
        notes.append("+gate_substitutions")

    if "related_principles" not in m:
        m["related_principles"] = []
        changed = True
        notes.append("+related_principles")

    if "v3_metadata" not in m:
        n_c = m.get("G", {}).get("n_c", 0)
        m["v3_metadata"] = {
            "is_standalone_multiphysics": n_c > 0,
            "coupling_count_n_c": n_c,
            "joint_well_posedness_references": [],
            "distinctness_audit": None,
            "clinical_context": None,
        }
        changed = True
        notes.append(f"+v3_metadata (n_c={n_c})")

    if changed and not dry_run:
        # Preserve key ordering: read original, build new dict with
        # forward-compat fields right after source_file (matches QSM/CLAUDE.md template)
        original = json.loads(path.read_text())
        rebuilt: dict = {}
        v23_fields = ("gate_class", "gate_substitutions", "related_principles")
        v23_inserted = False
        for k, v in original.items():
            rebuilt[k] = v
            if k == "source_file" and not v23_inserted:
                for fk in v23_fields:
                    if fk not in original:
                        rebuilt[fk] = m[fk]
                v23_inserted = True
        # Append v3_metadata at the end (after ipfs_cid) to match QSM ordering.
        if "v3_metadata" not in rebuilt:
            rebuilt["v3_metadata"] = m["v3_metadata"]
        # If v23 fields were never inserted (no source_file key), add them up front.
        if not v23_inserted:
            for fk in v23_fields:
                if fk not in rebuilt:
                    rebuilt[fk] = m[fk]

        path.write_text(json.dumps(rebuilt, indent=2) + "\n")

    return changed, ", ".join(notes) if notes else "no changes needed"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--root", type=Path, default=Path("pwm-team/content"),
                    help="root dir to walk (default: pwm-team/content)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    if not args.root.is_dir():
        print(f"root not found: {args.root}", file=sys.stderr)
        return 1

    l1_files = sorted(args.root.rglob("L1-*.json"))
    if not l1_files:
        print(f"no L1-*.json files under {args.root}", file=sys.stderr)
        return 1

    n_changed = 0
    n_unchanged = 0
    n_errors = 0
    multiphys_count = 0

    for p in l1_files:
        changed, reason = _migrate_manifest(p, args.dry_run)
        if reason.startswith("JSON parse error"):
            print(f"  ERROR  {p}: {reason}")
            n_errors += 1
            continue
        if reason == "not an L1 manifest":
            continue
        if changed:
            n_changed += 1
            if "n_c=" in reason:
                # extract n_c value
                try:
                    n_c_val = int(reason.split("n_c=")[1].split(")")[0])
                    if n_c_val > 0:
                        multiphys_count += 1
                except (IndexError, ValueError):
                    pass
        else:
            n_unchanged += 1

    print()
    print(f"Scanned: {len(l1_files)} L1 manifest files under {args.root}")
    print(f"  Migrated:    {n_changed}")
    print(f"  Unchanged:   {n_unchanged}")
    print(f"  Errors:      {n_errors}")
    print(f"  (Of migrated: {multiphys_count} have G.n_c > 0 -> tagged as standalone multi-physics)")
    if args.dry_run:
        print("\n(dry-run — no files modified)")
    elif n_changed > 0:
        print(f"\nNext: git add pwm-team/content/ && git commit")

    return 0 if n_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
