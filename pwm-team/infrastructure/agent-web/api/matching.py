"""API-layer facet matcher — mirrors pwm-node match's logic.

This module implements the same scoring algorithm as
`pwm-team/infrastructure/agent-cli/pwm_node/commands/match.py` so the
web `/api/match` endpoint returns the same answers as the CLI.

The logic is duplicated here (not imported from pwm_node) because the
web container doesn't install the CLI package — keeping the two as
separate deployable units. Both read the same benchmark cards from
`pwm-team/pwm_product/benchmark_cards/`, so the canonical source of
truth is the card data, not either code path.

If Bounty #8 qualifies a third-party LLM-routed matcher, that matcher
replaces this module's `match_prompt()` by wiring a different
implementation behind the same function signature.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


CONFIDENCE_FLOOR = 2.0

# Banding for "strong/weak/no" match UI label (frontend also computes this
# for resilience; keep thresholds in one place).
SCORE_BAND_STRONG = 3.0
SCORE_BAND_WEAK = CONFIDENCE_FLOOR  # i.e., 2.0

# benchmark_id -> demo directory name (for preview thumbnails)
_BENCHMARK_TO_DEMO = {
    "L3-003": "cassi",
    "L3-004": "cacti",
}


def _preview_urls(benchmark_id: str) -> dict | None:
    """Return snapshot + ground-truth preview URLs for a matched benchmark,
    or None if no demo exists yet for this id."""
    demo = _BENCHMARK_TO_DEMO.get(benchmark_id)
    if demo is None:
        return None
    base = f"/api/demos/{demo}/sample_01"
    return {
        "snapshot": f"{base}/snapshot.png",
        "ground_truth": f"{base}/ground_truth.png",
        "solution": f"{base}/solution.png",
    }


def _confidence_band(score: float) -> str:
    """Return one of 'strong', 'weak', 'none' based on the score."""
    if score >= SCORE_BAND_STRONG:
        return "strong"
    if score >= SCORE_BAND_WEAK:
        return "weak"
    return "none"

SCORED_FIELDS: list[tuple[str, str, float]] = [
    ("handwritten.one_line",              "one_line",   3.0),
    ("handwritten.forward_model_summary", "forward",    2.0),
    ("auto.title",                        "title",      2.0),
    ("auto.principle_title",              "principle",  2.0),
    ("auto.domain",                       "domain",     1.5),
    ("auto.sub_domain",                   "sub_domain", 1.5),
]

STOPWORDS = frozenset("""
    a an and are as at be by for from has have i if in is it its
    my of on or our that the their them this to was we were what will
    with you your can do does need want help me my our are have has
    """.split())


def _dotted_get(d: dict, path: str) -> Any:
    cur: Any = d
    for seg in path.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", str(text).lower())
    return {w for w in words if w not in STOPWORDS}


def _cards_dir() -> Path:
    # Production container mounts at /app/cards; local dev uses the repo path.
    env = os.environ.get("PWM_CARDS_DIR")
    if env:
        return Path(env)
    # Repo-layout default: this file is .../agent-web/api/matching.py
    # parents[3] = .../pwm-team/ → then pwm_product/benchmark_cards
    try:
        return Path(__file__).resolve().parents[3] / "pwm_product" / "benchmark_cards"
    except IndexError:
        return Path("/app/cards")


@lru_cache(maxsize=1)
def _load_cards() -> list[dict]:
    cards_dir = _cards_dir()
    if not cards_dir.is_dir():
        return []
    try:
        import yaml
    except ImportError:
        return []
    out: list[dict] = []
    for p in sorted(cards_dir.glob("L3-*.yaml")):
        try:
            data = yaml.safe_load(p.read_text()) or {}
        except Exception:
            continue
        if isinstance(data, dict) and "auto" in data:
            out.append(data)
    return out


def _score_card(card: dict, tokens: set[str]) -> tuple[float, list[str]]:
    score = 0.0
    hits: list[str] = []
    for path, label, weight in SCORED_FIELDS:
        card_tokens = _tokenize(_dotted_get(card, path))
        overlap = tokens & card_tokens
        if overlap:
            score += weight * len(overlap)
            hits.append(f"{label}:{len(overlap)}")
    bad = _dotted_get(card, "handwritten.bad_prompt_keywords") or []
    bad_tokens: set[str] = set()
    for kw in bad:
        bad_tokens |= _tokenize(kw)
    bad_overlap = tokens & bad_tokens
    if bad_overlap:
        score -= 3.0 * len(bad_overlap)
        hits.append(f"bad:-{len(bad_overlap)}")
    return score, hits


def _apply_filters(card: dict, filters: dict, base: float) -> tuple[float, list[str]]:
    score = base
    notes: list[str] = []
    auto = card.get("auto") or {}

    domain = filters.get("domain")
    if domain:
        card_domain = (auto.get("domain") or "").lower()
        if domain.lower() in card_domain:
            score += 3.0
            notes.append(f"domain:{domain}=ok")
        elif card_domain:
            score -= 2.0
            notes.append(f"domain:{domain} != {card_domain}")

    h = filters.get("h")
    w = filters.get("w")
    noise = filters.get("noise")
    if any(v is not None for v in (h, w, noise)):
        tiers = auto.get("tiers") or []
        best_fit = -1.0
        for t in tiers:
            fit = 0.0
            if h and t.get("H") == h: fit += 1.0
            if w and t.get("W") == w: fit += 0.5
            if noise is not None and t.get("noise_max") is not None:
                if t["noise_max"] >= noise - 1e-9:
                    fit += 1.0
            best_fit = max(best_fit, fit)
        if best_fit > 0:
            score += best_fit
            notes.append(f"tier_fit:+{best_fit:.1f}")

    return score, notes


def _pick_tier(card: dict, filters: dict) -> str | None:
    tiers = (card.get("auto") or {}).get("tiers") or []
    if not tiers:
        return None
    best_name = None
    best_fit = -1.0
    h = filters.get("h")
    w = filters.get("w")
    noise = filters.get("noise")
    for t in tiers:
        fit = 0.0
        if h and t.get("H") == h: fit += 2.0
        if w and t.get("W") == w: fit += 1.0
        if noise is not None and t.get("noise_max") is not None:
            if t["noise_max"] >= noise - 1e-9:
                fit += 1.5
                fit -= 0.1 * t["noise_max"]
        if fit > best_fit:
            best_fit = fit
            best_name = t.get("tier")
    return best_name if best_fit > 0 else tiers[0].get("tier")


def _rationale(card: dict, score: float, hits: list[str], tier: str | None) -> str:
    auto = card.get("auto") or {}
    hw = card.get("handwritten") or {}
    one_line = hw.get("one_line") or auto.get("title") or "(no summary)"
    oneline_short = (one_line[:140] + "…") if len(one_line) > 140 else one_line
    tier_s = f" (tier: {tier})" if tier else ""
    hits_s = ", ".join(hits) if hits else "no direct keyword overlap"
    return (f"{auto.get('benchmark_id')}{tier_s}: {oneline_short}  "
            f"[signals: {hits_s}; score {score:.2f}]")


def _clarifying(candidates: list[dict]) -> str | None:
    if len(candidates) < 2:
        return None
    top, second = candidates[0], candidates[1]
    if top["score"] - second["score"] < 1.5:
        return (f"Your prompt is close to both {top['benchmark_id']} and "
                f"{second['benchmark_id']}. Which axis is primary: "
                f"spectral (wavelength/λ) or temporal (time/frames)?")
    return None


def match_prompt(prompt: str | None = None, **filters) -> dict:
    """Public API: take a prompt + optional filters, return the 08-llm-matcher.md
    wire-format response dict."""
    tokens = _tokenize(prompt or "")
    has_filters = any(
        filters.get(k) is not None
        for k in ("domain", "modality", "h", "w", "noise")
    )
    if not tokens and not has_filters:
        return {
            "candidates": [],
            "clarifying_question":
                "Please describe your data (e.g. 'I have a CASSI snapshot, "
                "256x256, mild mismatch') or set at least one structured "
                "filter (domain, modality, H/W, noise).",
            "confidence_floor_hit": True,
        }

    cards = _load_cards()
    scored = []
    for card in cards:
        base, hits = _score_card(card, tokens)
        total, extra = _apply_filters(card, filters, base)
        tier = _pick_tier(card, filters)
        scored.append((total, card, hits + extra, tier))
    scored.sort(key=lambda r: r[0], reverse=True)
    top3 = scored[:3]
    top_score = top3[0][0] if top3 else 0.0
    floor_hit = top_score < CONFIDENCE_FLOOR

    candidates = []
    for rank, (score, card, hits, tier) in enumerate(top3, start=1):
        bid = (card.get("auto") or {}).get("benchmark_id")
        if bid is None:
            continue
        candidates.append({
            "benchmark_id": bid,
            "rank": rank,
            "score": round(score, 3),
            "score_band": _confidence_band(score),
            "tier": tier,
            "rationale": _rationale(card, score, hits, tier),
            "preview_urls": _preview_urls(bid),
        })

    if floor_hit:
        q = ("I couldn't match this prompt to any existing PWM benchmark "
             "with confidence. Could you specify the physical axis "
             "(spectral/temporal/spatial/depth/none) and the primary "
             "measurement modality (snapshot/scan/tomography/etc.)?")
        return {"candidates": [], "clarifying_question": q,
                "confidence_floor_hit": True}

    return {
        "candidates": candidates,
        "clarifying_question": _clarifying(candidates),
        "confidence_floor_hit": False,
    }
