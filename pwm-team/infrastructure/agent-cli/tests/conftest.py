"""Shared pytest fixtures for pwm-node tests.

Creates a tmpdir-based fake genesis directory populated with realistic L1/L2/L3
JSONs modeled after CASSI (#003) and a second decoy (#004 CACTI) so tests can
exercise filtering / lookup without requiring the real repo tree.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


_L1_CASSI = {
    "artifact_id": "L1-003",
    "layer": "L1",
    "principle_number": "003",
    "title": "Coded Aperture Snapshot Spectral Imaging (CASSI)",
    "domain": "Compressive Imaging",
    "sub_domain": "Hyperspectral snapshot",
    "difficulty_tier": "standard",
    "difficulty_delta": 3,
    "E": {
        "description": "Single-shot compressive spectral.",
        "forward_model": "y = sum_lambda C * f",
    },
    "G": {
        "dag": "L.broadcast.spectral -> L.diag.binary -> L.shear.spectral -> int.spectral",
        "L_DAG": 3.7,
        "n_c": 0,
    },
    "W": {
        "condition_number_kappa": 5000,
        "condition_number_effective": 50,
    },
    "physics_fingerprint": {
        "primitives": ["L.broadcast.spectral", "L.diag.binary", "L.shear.spectral", "int.spectral"],
    },
    "verification_status": "triple-verified",
    "verified_by": ["agent-physics-verifier", "agent-numerics-verifier", "agent-cross-domain-verifier"],
    "verification_date": "2026-04-21",
}

_L1_CACTI = {
    "artifact_id": "L1-004",
    "layer": "L1",
    "principle_number": "004",
    "title": "Coded Aperture Compressive Temporal Imaging (CACTI)",
    "domain": "Compressive Imaging",
    "sub_domain": "Video snapshot compressive sensing",
    "difficulty_tier": "standard",
    "difficulty_delta": 3,
    "E": {"forward_model": "y = sum_b C_b * x_b"},
    "G": {"dag": "S.temporal.coded -> int.temporal", "L_DAG": 1.4, "n_c": 0},
    "W": {"condition_number_kappa": 2500, "condition_number_effective": 30},
    "physics_fingerprint": {"primitives": ["S.temporal.coded", "int.temporal"]},
    "verification_status": "triple-verified",
}

_L1_DRAFT = {
    "artifact_id": "L1-001",
    "layer": "L1",
    "principle_number": "001",
    "title": "Widefield Fluorescence Microscopy",
    "domain": "Microscopy",
    "sub_domain": "Fluorescence",
    "difficulty_tier": "textbook",
    "difficulty_delta": 1,
    "E": {"forward_model": "y = PSF * f"},
    "G": {"dag": "K.psf.airy -> int.temporal", "L_DAG": 1.0, "n_c": 0},
    "W": {"condition_number_kappa": 15, "condition_number_effective": 5},
    "physics_fingerprint": {"primitives": ["K.psf.airy", "int.temporal"]},
    "verification_status": "single-reviewer",
}


@pytest.fixture()
def fake_genesis(tmp_path) -> Path:
    """Build a tmp genesis/ directory with three L1 artifacts."""
    root = tmp_path / "genesis"
    (root / "l1").mkdir(parents=True)
    (root / "l2").mkdir()
    (root / "l3").mkdir()
    (root / "l1" / "L1-001.json").write_text(json.dumps(_L1_DRAFT))
    (root / "l1" / "L1-003.json").write_text(json.dumps(_L1_CASSI))
    (root / "l1" / "L1-004.json").write_text(json.dumps(_L1_CACTI))
    return root
