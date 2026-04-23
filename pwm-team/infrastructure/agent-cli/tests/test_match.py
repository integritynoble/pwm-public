"""Tests for pwm-node match — the faceted (LLM-free) reference matcher."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pwm_node.commands.match import (
    CONFIDENCE_FLOOR, _apply_structured_filters, _clarifying_question,
    _pick_tier, _score_card, _tokenize,
)


# Shared in-memory test cards mirroring the real CASSI + CACTI shape.
CASSI_CARD = {
    "auto": {
        "benchmark_id": "L3-003",
        "principle_title": "Coded Aperture Snapshot Spectral Imaging (CASSI)",
        "title": "CASSI Mismatch-Only Benchmark Suite",
        "domain": "Compressive Imaging",
        "sub_domain": "Hyperspectral snapshot",
        "benchmark_type": "combined_P_and_I",
        "tiers": [
            {"tier": "T1_nominal", "H": 256, "W": 256, "noise_max": 0.01},
            {"tier": "T2_low",     "H": 256, "W": 256, "noise_max": 0.02},
            {"tier": "T3_moderate","H": 512, "W": 512, "noise_max": 0.05},
            {"tier": "T4_blind",   "H": 1024,"W": 1024,"noise_max": 0.08},
        ],
    },
    "handwritten": {
        "one_line": "Reconstruct a 28-band hyperspectral image cube from a "
                    "single 2D coded-aperture snapshot.",
        "forward_model_summary": "y = sum_lambda (shift_lambda(mask * x)) + n",
        "bad_prompt_keywords": ["RGB demosaicing", "MRI reconstruction", "point cloud"],
    },
}

CACTI_CARD = {
    "auto": {
        "benchmark_id": "L3-004",
        "principle_title": "CACTI",
        "title": "CACTI Temporal Benchmark Suite",
        "domain": "Compressive Imaging",
        "sub_domain": "Temporal snapshot",
        "benchmark_type": "combined_P_and_I",
        "tiers": [
            {"tier": "T1_nominal", "H": 256, "W": 256, "noise_max": 0.01},
        ],
    },
    "handwritten": {
        "one_line": "Reconstruct a short video sequence from a single 2D "
                    "compressive temporal snapshot.",
        "forward_model_summary": "y = sum_t (mask_t * x_t) + n",
        "bad_prompt_keywords": ["hyperspectral", "spectral", "1D time series"],
    },
}


# ───── tokenizer ─────


def test_tokenize_basic():
    tokens = _tokenize("I have a CASSI snapshot with coded-aperture mask.")
    # "i", "a", "with" are stopwords; others should survive.
    assert "cassi" in tokens
    assert "snapshot" in tokens
    assert "coded-aperture" in tokens
    assert "mask" in tokens
    assert "i" not in tokens  # stopword
    assert "have" not in tokens


def test_tokenize_empty():
    assert _tokenize("") == set()
    assert _tokenize(None) == set()  # type: ignore[arg-type]


# ───── scoring ─────


def test_cassi_prompt_favors_cassi():
    prompt = _tokenize("hyperspectral cube reconstruction from coded-aperture snapshot")
    cassi_score, _ = _score_card(CASSI_CARD, prompt)
    cacti_score, _ = _score_card(CACTI_CARD, prompt)
    assert cassi_score > cacti_score


def test_cacti_prompt_favors_cacti():
    prompt = _tokenize("short video reconstruction from compressive temporal snapshot with per-frame mask")
    cassi_score, _ = _score_card(CASSI_CARD, prompt)
    cacti_score, _ = _score_card(CACTI_CARD, prompt)
    assert cacti_score > cassi_score


def test_bad_keywords_penalize():
    """A prompt containing CASSI's bad_prompt_keyword 'MRI' should lose points for CASSI."""
    prompt_clean = _tokenize("coded aperture snapshot")
    clean_score, _ = _score_card(CASSI_CARD, prompt_clean)

    prompt_bad = _tokenize("coded aperture snapshot for MRI reconstruction")
    bad_score, hits = _score_card(CASSI_CARD, prompt_bad)
    assert bad_score < clean_score
    assert any("bad:" in h for h in hits)


def test_unrelated_prompt_below_floor():
    """A LiDAR/point-cloud prompt should fail to clear the confidence floor on CASSI."""
    prompt = _tokenize("LiDAR point cloud from street corner scan")
    score, _ = _score_card(CASSI_CARD, prompt)
    assert score < CONFIDENCE_FLOOR


# ───── structured filter interaction ─────


class _Args:
    """Minimal argparse Namespace substitute."""
    def __init__(self, **kw):
        self.domain = kw.get("domain")
        self.modality = kw.get("modality")
        self.h = kw.get("h")
        self.w = kw.get("w")
        self.noise = kw.get("noise")


def test_structured_domain_filter_boosts_matching_card():
    base = 5.0
    args = _Args(domain="Compressive Imaging")
    new_score, notes = _apply_structured_filters(CASSI_CARD, args, base)
    assert new_score > base
    assert any("domain" in n and "✓" in n for n in notes)


def test_structured_domain_filter_penalizes_nonmatch():
    base = 5.0
    args = _Args(domain="Spectroscopy")
    new_score, _ = _apply_structured_filters(CASSI_CARD, args, base)
    assert new_score < base


def test_pick_tier_honors_h_filter():
    args = _Args(h=512)
    tier = _pick_tier(CASSI_CARD, args)
    assert tier == "T3_moderate"


def test_pick_tier_honors_noise_filter():
    # noise=0.03 → the tightest tier that tolerates ≥ 0.03 is T3 (noise_max 0.05)
    args = _Args(noise=0.03)
    tier = _pick_tier(CASSI_CARD, args)
    # T3_moderate or T4_blind both tolerate; prefer tighter (less permissive).
    assert tier in ("T3_moderate", "T4_blind")


# ───── clarifying question ─────


def test_clarifying_question_fires_when_top_candidates_are_close():
    cands = [
        {"benchmark_id": "L3-003", "score": 10.0},
        {"benchmark_id": "L3-004", "score": 9.5},
    ]
    q = _clarifying_question(cands)
    assert q is not None
    assert "L3-003" in q and "L3-004" in q


def test_clarifying_question_quiet_when_top_candidate_dominates():
    cands = [
        {"benchmark_id": "L3-003", "score": 15.0},
        {"benchmark_id": "L3-004", "score": 3.0},
    ]
    assert _clarifying_question(cands) is None


# ───── end-to-end CLI invocation ─────


REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.skipif(
    not (REPO_ROOT / "pwm-team/pwm_product/benchmark_cards/L3-003.yaml").is_file(),
    reason="requires generated benchmark cards in the repo"
)
def test_cli_resolves_cassi_prompt_end_to_end():
    """End-to-end: CLI invocation against the real cards on disk."""
    res = subprocess.run(
        [sys.executable, "-m", "pwm_node", "match",
         "--prompt", "hyperspectral snapshot reconstruction from coded aperture",
         "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert not out.get("confidence_floor_hit")
    top_id = out["candidates"][0]["benchmark_id"]
    assert top_id == "L3-003"


@pytest.mark.skipif(
    not (REPO_ROOT / "pwm-team/pwm_product/benchmark_cards/L3-003.yaml").is_file(),
    reason="requires generated benchmark cards in the repo"
)
def test_cli_returns_floor_hit_for_out_of_scope():
    """No-match prompt should produce confidence_floor_hit=true and no candidates."""
    res = subprocess.run(
        [sys.executable, "-m", "pwm_node", "match",
         "--prompt", "LiDAR point cloud denoising for autonomous driving",
         "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out.get("confidence_floor_hit") is True
    assert out.get("candidates") == []
