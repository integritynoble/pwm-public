"""Add `display_slug` field to PWM L1/L2/L3 manifests.

Per `pwm-team/customer_guide/plan.md` Phase 2 task 2.1: customers see
"L1-003" in URLs and don't know it means CASSI. This script adds an
optional `display_slug` to each manifest so URLs become
`/benchmarks/cassi` and grant docs can write
`Coded Aperture Snapshot Spectral Imaging (L1-003)` cleanly.

The slug is computed deterministically:
  1. If the L1 manifest filename has a stem like "L1-003_qsm.json", use
     "qsm" as the slug.
  2. Else, derive from `title`: lowercase, strip parens, replace
     non-alphanumeric runs with hyphens, trim hyphens.

For child L2/L3 manifests, inherit the slug from the parent L1 (so
L1-003 gets "cassi" and L3-003 inherits the same slug).

CRITICAL INVARIANT: `display_slug` is in `register_genesis.py`'s
`UI_ONLY_FIELDS` filter. Adding it to a manifest MUST NOT change the
keccak256(canonical_json) hash. This is verified by
`scripts/test_register_genesis.py::test_hash_invariant_under_display_slug_addition`.

Usage:
    # Preview what slugs would be added (no writes):
    python3 scripts/add_display_slugs.py --dry-run

    # Actually write display_slug into every manifest:
    python3 scripts/add_display_slugs.py

    # Override an existing slug (default: skip files that already have one):
    python3 scripts/add_display_slugs.py --force

Search paths:
  - pwm-team/pwm_product/genesis/{l1,l2,l3}/  (canonical genesis batch)
  - pwm-team/content/agent-*/principles/...   (domain-organized full catalog)

Hand-curated slug overrides (e.g., for the 28 newest v2/v3 anchors)
live in `_HANDCURATED_SLUGS` below — preferred over the auto-derived
slug when there's a recognized ID prefix.

Exit codes:
  0  success (or dry-run completion)
  1  unrecoverable error (manifest unparseable, etc.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


# Per `PWM_HUMAN_READABLE_IDS_AND_CONTRIBUTION_FLOW_2026-05-03.md`:
# pre-curated slugs for the 28 newest v2/v3 anchors. Auto-derivation
# would produce close approximations, but these match what the human
# expert would write.
_HANDCURATED_SLUGS: dict[str, str] = {
    "L1-003": "cassi",
    "L1-004": "cacti",
    "L1-503": "qsm",
    "L1-504": "qpat",
    "L1-505": "pkpet",
    "L1-506": "hp13c-mri",
    "L1-507": "meg-eeg-joint",
    "L1-508": "oce",
    "L1-509": "paus",
    "L1-510": "cardiac-4dflow",
    "L1-511": "pillcam-optical",
    "L1-512": "pillcam-bleeding",
    "L1-513": "dr-etdrs",
    "L1-514": "chest-ct-severity",
    "L1-515": "mammographic-density",
    "L1-516": "mrs-tumor-grading",
    "L1-517": "dermoscopy-malignancy",
    "L1-518": "xrd",
    "L1-519": "xrd-space-group",
    "L1-520": "rnaseq-celltype",
    "L1-521": "drug-target-binding",
    "L1-522": "earthquake-magnitude",
    "L1-523": "pneumothorax-cxr",
    "L1-524": "stroke-ctp",
    "L1-525": "pe-ctpa",
    "L1-526": "bone-fracture-xray",
    "L1-527": "oa-kellgren-lawrence",
    "L1-528": "ecg-arrhythmia",
    "L1-529": "glaucoma-optic-disc",
    "L1-530": "amd-oct",
    "L1-531": "eeg-seizure",
}


def _slugify(s: str) -> str:
    """Lowercase, ASCII-only, hyphen-separated."""
    s = s.lower()
    # Strip parenthetical asides like " (PWDR)".
    s = re.sub(r"\([^)]*\)", "", s)
    # Replace any run of non-alphanumeric characters with single hyphen.
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def _slug_for(artifact_id: str, title: Optional[str], filename_stem: str) -> str:
    """Derive a slug for a single manifest.

    Priority:
      1. Hand-curated override from `_HANDCURATED_SLUGS`
      2. Filename stem suffix (e.g., "L1-512_pillcam_spectra_pwdr" → "pillcam-spectra-pwdr")
      3. Slugified title
      4. Lowercased artifact_id (last-resort fallback so every manifest gets one)
    """
    if artifact_id in _HANDCURATED_SLUGS:
        return _HANDCURATED_SLUGS[artifact_id]

    # If we're processing an L2-512 / L3-512 file, inherit from L1-512's hand-curated slug.
    if artifact_id.startswith("L2-") or artifact_id.startswith("L3-"):
        l1_id = "L1-" + artifact_id.split("-", 1)[1]
        if l1_id in _HANDCURATED_SLUGS:
            return _HANDCURATED_SLUGS[l1_id]

    # Try the filename stem (e.g., "L1-512_pillcam_spectra_pwdr.json" → "pillcam-spectra-pwdr")
    parts = filename_stem.split("_", 1)
    if len(parts) == 2 and parts[0] == artifact_id:
        suffix_slug = _slugify(parts[1])
        if suffix_slug:
            return suffix_slug

    # Fall back to title.
    if title:
        title_slug = _slugify(title)
        if title_slug:
            return title_slug

    # Last resort: just the artifact_id lowercased.
    return artifact_id.lower()


def _find_manifests(repo: Path) -> list[Path]:
    out: list[Path] = []
    # Canonical genesis batch.
    for layer_dir in ("l1", "l2", "l3"):
        d = repo / "pwm-team" / "pwm_product" / "genesis" / layer_dir
        if d.is_dir():
            out.extend(sorted(d.glob("*.json")))
    # Domain-organized catalog under content/.
    content = repo / "pwm-team" / "content"
    if content.is_dir():
        # All L1/L2/L3 manifests anywhere under content/
        for p in content.rglob("L[123]-*.json"):
            out.append(p)
    return sorted(set(out))


def _process(path: Path, *, dry_run: bool, force: bool) -> tuple[str, str | None]:
    """Returns (action, slug):
      action ∈ {"added", "skipped", "overwrote", "no_artifact_id"}
      slug is the slug emitted (or would be emitted on dry-run).
    """
    try:
        obj = json.loads(path.read_text())
    except json.JSONDecodeError:
        return ("parse_error", None)

    artifact_id = obj.get("artifact_id")
    if not isinstance(artifact_id, str):
        return ("no_artifact_id", None)

    existing = obj.get("display_slug")
    if existing and not force:
        return ("skipped", existing)

    title = obj.get("title")
    slug = _slug_for(artifact_id, title, path.stem)

    if dry_run:
        return ("would_add" if not existing else "would_overwrite", slug)

    obj["display_slug"] = slug
    # Preserve trailing newline if the original had one; json.dumps doesn't add one.
    serialized = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    path.write_text(serialized)
    return ("added" if not existing else "overwrote", slug)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; do not write files")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing display_slug values")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    manifests = _find_manifests(repo)
    print(f"Found {len(manifests)} manifest files.")
    print()

    counts = {"added": 0, "would_add": 0, "skipped": 0,
              "overwrote": 0, "would_overwrite": 0,
              "no_artifact_id": 0, "parse_error": 0}
    examples: dict[str, list[tuple[str, str]]] = {}

    for path in manifests:
        action, slug = _process(path, dry_run=args.dry_run, force=args.force)
        counts[action] = counts.get(action, 0) + 1
        if slug:
            examples.setdefault(action, []).append(
                (path.relative_to(repo).as_posix(), slug)
            )

    print("Summary:")
    for k in ["added", "would_add", "overwrote", "would_overwrite",
              "skipped", "no_artifact_id", "parse_error"]:
        if counts.get(k):
            print(f"  {k:>18}: {counts[k]}")

    print()
    print("Sample slugs (first 8 per action):")
    for action in ("added", "would_add", "overwrote", "would_overwrite", "skipped"):
        if action in examples:
            print(f"  [{action}]")
            for path_str, slug in examples[action][:8]:
                print(f"    {path_str:80s}  →  {slug}")

    if args.dry_run:
        print()
        print("Dry-run only — no files modified. Re-run without --dry-run to write.")
    else:
        print()
        print("Done. Run `python3 -m pytest scripts/test_register_genesis.py` to confirm")
        print("the hash-invariance test still passes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
