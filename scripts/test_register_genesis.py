"""Hash-invariance tests for `register_genesis.py`.

The protocol-critical invariant: adding a UI-only field (display_slug,
display_color, ui_metadata) to a manifest must NOT change the
keccak256(canonical_json) hash. Otherwise existing on-chain artifacts
would orphan when their manifests are re-saved with new display
fields, and `pwm-node mine` would fail with "benchmark not registered".

Run:
    python3 -m pytest scripts/test_register_genesis.py -xvs
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register_genesis import (  # noqa: E402
    UI_ONLY_FIELDS,
    _canonical_for_hashing,
    _canonical_json,
)


def _example_manifest() -> dict:
    """A representative L1 manifest stripped to the fields that affect hash."""
    return {
        "artifact_id": "L1-003",
        "layer": "L1",
        "title": "Coded Aperture Snapshot Spectral Imaging",
        "domain": "compressive_imaging",
        "spec_range": {
            "allowed_omega_dimensions": ["mask_density", "noise_level"],
            "omega_bounds": {"mask_density": [0.3, 0.7]},
        },
        "G": {"dag": "source -> mask -> dispersion -> sensor", "n_c": 0},
        "gate_class": "analytical",
        "error_metric": "PSNR_dB",
    }


def test_display_slug_filter_in_set():
    """`display_slug` MUST be in UI_ONLY_FIELDS — that's the field this
    whole project added."""
    assert "display_slug" in UI_ONLY_FIELDS


def test_canonical_strips_known_ui_fields():
    """The filter strips every UI_ONLY_FIELDS entry from the canonical dict."""
    obj = _example_manifest()
    obj["display_slug"] = "cassi"
    obj["display_color"] = "#00ffff"
    obj["ui_metadata"] = {"icon": "/icons/cassi.svg"}

    filtered = _canonical_for_hashing(obj)
    assert "display_slug" not in filtered
    assert "display_color" not in filtered
    assert "ui_metadata" not in filtered

    # Non-UI fields preserved.
    assert filtered["artifact_id"] == "L1-003"
    assert filtered["title"] == "Coded Aperture Snapshot Spectral Imaging"
    assert filtered["G"] == obj["G"]


def test_hash_invariant_under_display_slug_addition():
    """Core protocol invariant: adding `display_slug` must NOT change the
    canonical_json bytes (and therefore must NOT change the keccak256 hash).

    This is what makes it safe to retrofit `display_slug` into 531
    already-registered manifests without breaking on-chain lookups.
    """
    manifest_v1 = _example_manifest()  # without display_slug
    manifest_v2 = {**manifest_v1, "display_slug": "cassi"}  # with display_slug

    bytes_v1 = _canonical_json(manifest_v1)
    bytes_v2 = _canonical_json(manifest_v2)

    assert bytes_v1 == bytes_v2, (
        "Adding display_slug changed the canonical-JSON bytes; the "
        "UI_ONLY_FIELDS filter is broken. This would orphan every "
        "on-chain artifact whose manifest gets a slug retrofit."
    )


def test_hash_invariant_under_multiple_ui_field_additions():
    """Same invariant, but with all three known UI fields added at once."""
    manifest_v1 = _example_manifest()
    manifest_v2 = {
        **manifest_v1,
        "display_slug": "cassi",
        "display_color": "#00ffff",
        "ui_metadata": {"icon": "/icons/cassi.svg", "tier": "anchor"},
    }

    assert _canonical_json(manifest_v1) == _canonical_json(manifest_v2)


def test_non_ui_fields_DO_change_the_hash():
    """Sanity-check the test setup: non-UI field changes MUST still change
    the hash. Otherwise the filter could be a no-op and we'd never notice.
    """
    manifest_v1 = _example_manifest()
    manifest_v2 = {**manifest_v1, "title": "Different Title"}

    assert _canonical_json(manifest_v1) != _canonical_json(manifest_v2), (
        "Changing the title did NOT change the canonical bytes — "
        "the filter is over-aggressive (or _canonical_json is broken)."
    )


def test_hash_invariant_when_slug_added_then_removed():
    """Adding then removing the slug yields bytes-identical canonical JSON
    to the original. Round-trip safety."""
    manifest_v1 = _example_manifest()
    manifest_with_slug = {**manifest_v1, "display_slug": "cassi"}
    manifest_v3 = {k: v for k, v in manifest_with_slug.items() if k != "display_slug"}

    assert _canonical_json(manifest_v1) == _canonical_json(manifest_with_slug)
    assert _canonical_json(manifest_v1) == _canonical_json(manifest_v3)


def test_registration_tier_is_ui_only_field():
    """`registration_tier` must be in UI_ONLY_FIELDS — added 2026-05-06 to
    let the catalog self-document tier (founder_vetted / community_proposed
    / stub) without changing on-chain hashes for already-registered artifacts.
    """
    assert "registration_tier" in UI_ONLY_FIELDS


def test_hash_invariant_under_registration_tier_addition():
    """Adding `registration_tier` must NOT change the canonical-JSON bytes.
    Otherwise backfilling tier=stub on the 529 cataloged manifests would
    orphan any future registrations, and the L1-003/L1-004 hashes already
    on Sepolia would diverge from local canonical_json output.
    """
    manifest_v1 = _example_manifest()
    manifest_v2 = {**manifest_v1, "registration_tier": "founder_vetted"}
    manifest_v3 = {**manifest_v1, "registration_tier": "stub"}

    assert _canonical_json(manifest_v1) == _canonical_json(manifest_v2)
    assert _canonical_json(manifest_v1) == _canonical_json(manifest_v3)
    assert _canonical_json(manifest_v2) == _canonical_json(manifest_v3), (
        "Different registration_tier values changed the canonical bytes; "
        "the field would need to be in UI_ONLY_FIELDS to stay hash-invariant."
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-xvs"]))
