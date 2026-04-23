"""pwm-node match — faceted (LLM-free) benchmark matcher.

Reference implementation of the PWM "faceted floor" matcher described
in `papers/Proof-of-Solution/pwm_overview1.md §8.3`. Reads benchmark
cards at `pwm-team/pwm_product/benchmark_cards/L3-*.yaml`, scores each
card against the user's input (prompt keywords + optional structured
filters), and returns the top-3 candidates with per-candidate rationales.

LLM-routed / natural-language matching is a third-party bounty
(`agent-coord/interfaces/bounties/08-llm-matcher.md`); this file is NOT
that. Scoring here is deterministic, explainable, and requires no
external API.

Inputs:
    --prompt "free-text description of my data"
    --domain {imaging,medical_imaging,spectroscopy,microscopy,...}
    --modality {snapshot,tomography,localization,beamformer,...}
    --h N          image height
    --w N          image width
    --noise F      max tolerable noise level
    --json         emit JSON instead of human-readable output

Output schema (when --json):
    {"candidates": [{"benchmark_id": "L3-003", "rank": 1,
                     "score": 0.87, "rationale": "..."}],
     "clarifying_question": "...",
     "confidence_floor_hit": false}

Matches the wire format from `08-llm-matcher.md`, so downstream tooling
(harness runner, web UI API) can swap this for any Bounty #8 qualifier
without code changes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Fields in each card that contribute to keyword scoring, and their weights.
# Handwritten text carries more signal per token than auto-generated text.
SCORED_FIELDS: list[tuple[str, str, float]] = [
    # (dotted-path, human-label, weight)
    ("handwritten.one_line",              "one_line",   3.0),
    ("handwritten.forward_model_summary", "forward",    2.0),
    ("auto.title",                        "title",      2.0),
    ("auto.principle_title",              "principle",  2.0),
    ("auto.domain",                       "domain",     1.5),
    ("auto.sub_domain",                   "sub_domain", 1.5),
]

# Very short stopword list — just the obvious filler. We keep "need", "how",
# "what" etc. because they don't appear in cards anyway (no false hits).
STOPWORDS = frozenset("""
    a an and are as at be by for from has have i if in is it its
    my of on or our that the their them this to was we were what will
    with you your can do does need want help me my our are have has
    """.split())

# Confidence floor: top candidate's score must exceed this to be returned.
# Tuned so the 3 no-match prompts in the harness land below it.
CONFIDENCE_FLOOR = 2.0


def _dotted_get(d: dict, path: str) -> Any:
    cur: Any = d
    for seg in path.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip non-alphanumeric, drop stopwords."""
    if not text:
        return set()
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", str(text).lower())
    return {w for w in words if w not in STOPWORDS}


def _load_cards(cards_dir: Path) -> list[dict]:
    """Load every L3-*.yaml card. Returns list of dicts with {auto, handwritten}."""
    try:
        import yaml  # PyYAML — already a transitive dep
    except ImportError:
        # Fallback: use our own minimal parser. Only needed if PyYAML absent.
        return _load_cards_fallback(cards_dir)
    out = []
    for p in sorted(cards_dir.glob("L3-*.yaml")):
        try:
            data = yaml.safe_load(p.read_text()) or {}
        except Exception:
            continue
        if isinstance(data, dict) and "auto" in data:
            out.append(data)
    return out


def _load_cards_fallback(cards_dir: Path) -> list[dict]:
    """PyYAML-less loader — relies on the card generator's deterministic format."""
    out = []
    for p in sorted(cards_dir.glob("L3-*.yaml")):
        card = _parse_card_minimal(p.read_text())
        if card:
            out.append(card)
    return out


def _parse_card_minimal(text: str) -> dict:
    """Minimal parse: extract the 6 fields our scorer actually reads."""
    auto: dict[str, Any] = {}
    hw: dict[str, Any] = {}
    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if line.startswith("auto:"):
            section = "auto"; continue
        if line.startswith("handwritten:"):
            section = "hw"; continue
        m = re.match(r"  (\w+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            if section == "auto" and key in ("title", "principle_title", "domain", "sub_domain", "benchmark_id"):
                auto[key] = val
            elif section == "hw" and key in ("one_line", "forward_model_summary"):
                hw[key] = val
    return {"auto": auto, "handwritten": hw} if auto else {}


def _score_card(card: dict, prompt_tokens: set[str]) -> tuple[float, list[str]]:
    """Return (score, contributing field labels) for one card."""
    score = 0.0
    hits: list[str] = []
    # Positive: keyword overlap per scored field (weighted)
    for path, label, weight in SCORED_FIELDS:
        card_tokens = _tokenize(_dotted_get(card, path) or "")
        overlap = prompt_tokens & card_tokens
        if overlap:
            score += weight * len(overlap)
            hits.append(f"{label}:{len(overlap)}")
    # Negative: penalty if any bad_prompt_keyword appears in the prompt
    bad = _dotted_get(card, "handwritten.bad_prompt_keywords") or []
    bad_tokens: set[str] = set()
    for kw in bad:
        bad_tokens |= _tokenize(kw)
    bad_overlap = prompt_tokens & bad_tokens
    if bad_overlap:
        score -= 3.0 * len(bad_overlap)
        hits.append(f"bad:-{len(bad_overlap)}")
    return score, hits


def _apply_structured_filters(card: dict, args: argparse.Namespace,
                              base_score: float) -> tuple[float, list[str]]:
    """Apply explicit --domain/--h/--noise filter boosts or penalties."""
    score = base_score
    notes: list[str] = []
    auto = card.get("auto") or {}

    if args.domain:
        card_domain = (auto.get("domain") or "").lower()
        if args.domain.lower() in card_domain:
            score += 3.0
            notes.append(f"domain:{args.domain}=✓")
        elif card_domain:
            score -= 2.0
            notes.append(f"domain:{args.domain}≠{card_domain}")

    if args.modality or args.h or args.w or args.noise is not None:
        tiers = auto.get("tiers") or []
        best_tier_fit = -1.0
        for t in tiers:
            fit = 0.0
            if args.modality and (auto.get("benchmark_type") or "").lower().find(
                    args.modality.lower()) >= 0:
                fit += 0.5
            if args.h and t.get("H") == args.h:
                fit += 1.0
            if args.w and t.get("W") == args.w:
                fit += 0.5
            if args.noise is not None and t.get("noise_max") is not None:
                if t["noise_max"] >= args.noise - 1e-9:
                    fit += 1.0
            best_tier_fit = max(best_tier_fit, fit)
        if best_tier_fit > 0:
            score += best_tier_fit
            notes.append(f"tier_fit:+{best_tier_fit:.1f}")

    return score, notes


def _pick_tier(card: dict, args: argparse.Namespace) -> str | None:
    """Return the best-fitting tier name given structured filters."""
    tiers = (card.get("auto") or {}).get("tiers") or []
    if not tiers:
        return None
    best_name = None
    best_fit = -1.0
    for t in tiers:
        fit = 0.0
        if args.h and t.get("H") == args.h:
            fit += 2.0
        if args.w and t.get("W") == args.w:
            fit += 1.0
        if args.noise is not None and t.get("noise_max") is not None:
            # prefer the tightest tier whose noise_max tolerates the user's noise
            if t["noise_max"] >= args.noise - 1e-9:
                fit += 1.5
                # bias toward less permissive (tighter mismatch) tier for same noise
                fit -= 0.1 * t["noise_max"]
        if fit > best_fit:
            best_fit = fit
            best_name = t.get("tier")
    return best_name if best_fit > 0 else tiers[0].get("tier")


def _rationale(card: dict, score: float, hits: list[str],
               picked_tier: str | None) -> str:
    """Human-readable per-candidate explanation."""
    auto = card.get("auto") or {}
    hw = card.get("handwritten") or {}
    one_line = hw.get("one_line") or auto.get("title") or "(no summary)"
    bid = auto.get("benchmark_id") or "?"
    tier_s = f" (tier: {picked_tier})" if picked_tier else ""
    # Truncate one_line for display
    oneline_short = one_line[:140] + ("…" if len(one_line) > 140 else "")
    hits_s = ", ".join(hits) if hits else "no direct keyword overlap"
    return (f"{bid}{tier_s}: {oneline_short}\n"
            f"    match signals: {hits_s}  (score {score:.2f})")


def _clarifying_question(candidates: list[dict]) -> str | None:
    """If top-2 candidates are close, ask the user to disambiguate."""
    if len(candidates) < 2:
        return None
    top, second = candidates[0], candidates[1]
    if top["score"] - second["score"] < 1.5:
        return (f"Your prompt is close to both {top['benchmark_id']} and "
                f"{second['benchmark_id']}. Which axis is primary: "
                f"spectral (wavelength/λ) or temporal (time/frames)?")
    return None


def run(args: argparse.Namespace) -> int:
    """Load cards, score, print top-3. Returns 0 on success."""
    cards_dir = Path(args.cards_dir)
    if not cards_dir.is_dir():
        print(f"[pwm-node match] cards dir not found: {cards_dir}", file=sys.stderr)
        return 1

    cards = _load_cards(cards_dir)
    if not cards:
        print(f"[pwm-node match] no L3-*.yaml cards in {cards_dir}. "
              "Run scripts/generate_benchmark_cards.py first.", file=sys.stderr)
        return 1

    prompt_tokens = _tokenize(args.prompt or "")
    if not prompt_tokens and not any([args.domain, args.modality, args.h, args.w,
                                       args.noise is not None]):
        print("[pwm-node match] need --prompt or at least one structured filter "
              "(--domain / --modality / --h / --w / --noise).", file=sys.stderr)
        return 1

    scored: list[tuple[float, dict, list[str], str | None]] = []
    for card in cards:
        base, hits = _score_card(card, prompt_tokens)
        total, extra = _apply_structured_filters(card, args, base)
        hits = hits + extra
        tier = _pick_tier(card, args)
        scored.append((total, card, hits, tier))

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
            "tier": tier,
            "rationale": _rationale(card, score, hits, tier),
        })

    clarifying = _clarifying_question(candidates) if not floor_hit else (
        "I couldn't match this prompt to any existing PWM benchmark with "
        "confidence. Could you specify the physical axis (spectral / "
        "temporal / spatial / depth / none) and the primary measurement "
        "modality (snapshot / scan / tomography / etc.)?"
    )

    if args.json:
        print(json.dumps({
            "candidates": candidates if not floor_hit else [],
            "clarifying_question": clarifying,
            "confidence_floor_hit": floor_hit,
        }, indent=2))
        return 0

    # Human output
    if floor_hit:
        print("[pwm-node match] no confident match. Candidate list suppressed.")
        print(f"[pwm-node match] top raw score was {top_score:.2f} "
              f"(confidence floor {CONFIDENCE_FLOOR}).")
        print()
        print(clarifying)
        return 0

    print(f"[pwm-node match] top {len(candidates)} candidate(s):")
    print()
    for c in candidates:
        print(f"  #{c['rank']} {c['rationale']}")
        print()
    if clarifying:
        print(f"[clarifying question] {clarifying}")
    return 0
