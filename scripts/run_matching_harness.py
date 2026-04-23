"""Run the PWM matching acceptance harness against a matcher.

Scores a matcher implementation against the canonical JSONL harness at
`pwm-team/coordination/agent-coord/interfaces/matching/acceptance_harness.jsonl`.

Default target is the reference faceted matcher (`pwm-node match`).
Third-party LLM-routed matchers (Bounty #8 qualifiers) can be scored
by supplying their own command via `--matcher-cmd` — any command that
takes `--prompt <text> --json` and prints JSON matching the
08-llm-matcher.md wire schema works.

Scoring rules (matches the bounty spec exactly):

  • "accuracy" = (# prompts where expected_benchmark_ids[0] is in the
     top-3 candidates returned) / (# prompts with non-empty expected
     list)
  • "honesty" = (# no-match prompts where confidence_floor_hit==true
     and candidates list is empty) / (# no-match prompts)
  • "hallucination rate" = (# prompts where any returned benchmark_id
     is NOT a known artifact_id) / (# total prompts)

Qualifying thresholds (per 08-llm-matcher.md / MVP_FIRST_STRATEGY.md §10.2.1):
  reference floor target: ~65% accuracy
  Bounty #8 qualifier:    ≥ 80% accuracy, 0 hallucinations
  G3 gate:                ≥ 80% on each of the CASSI and CACTI sub-scores
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _run_matcher(cmd_template: list[str], prompt: str) -> dict:
    """Invoke the matcher command for one prompt; return parsed JSON output."""
    cmd = cmd_template + ["--prompt", prompt, "--json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"_error": "timeout"}
    if res.returncode != 0:
        return {"_error": f"exit {res.returncode}: {res.stderr[:200]}"}
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        return {"_error": f"bad json: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path,
                    help="JSONL harness file (default: "
                         "interfaces/matching/acceptance_harness.jsonl)")
    ap.add_argument("--matcher-cmd", default="python3 -m pwm_node match",
                    help="Matcher CLI (prefix). Default: python3 -m pwm_node match")
    ap.add_argument("--verbose", action="store_true",
                    help="Print per-prompt result")
    args = ap.parse_args()

    repo = _repo_root()
    harness = args.harness or (
        repo / "pwm-team/coordination/agent-coord/interfaces"
             / "matching/acceptance_harness.jsonl"
    )
    if not harness.is_file():
        print(f"harness not found: {harness}", file=sys.stderr)
        return 1

    # Load all known benchmark_ids so we can detect hallucinations.
    cards_dir = repo / "pwm-team/pwm_product/benchmark_cards"
    known_bids = set()
    for p in cards_dir.glob("L3-*.yaml"):
        known_bids.add(p.stem)

    cmd_template = args.matcher_cmd.split()

    prompts = []
    for line in harness.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            prompts.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    print(f"Running {len(prompts)} prompts against: {' '.join(cmd_template)}")
    print(f"Known benchmark_ids: {sorted(known_bids)}")
    print()

    results = {"correct": 0, "wrong": 0, "no_match_correct": 0,
               "no_match_wrong": 0, "hallucination": 0, "error": 0}
    cassi_hits = cassi_total = 0
    cacti_hits = cacti_total = 0
    per_prompt: list[dict] = []

    for p in prompts:
        out = _run_matcher(cmd_template, p["prompt"])
        if "_error" in out:
            results["error"] += 1
            per_prompt.append({"id": p["id"], "result": "error",
                               "detail": out["_error"]})
            continue

        candidates = out.get("candidates") or []
        returned_bids = [c.get("benchmark_id") for c in candidates][:3]
        top3 = [b for b in returned_bids if b]
        expected = p.get("expected_benchmark_ids") or []
        floor_hit = bool(out.get("confidence_floor_hit"))

        # Hallucination: any returned id not in known set
        halluc = [b for b in top3 if b not in known_bids]
        if halluc:
            results["hallucination"] += 1

        if not expected:
            # no-match prompt: success = floor_hit true AND no candidates
            if floor_hit and not top3:
                results["no_match_correct"] += 1
                outcome = "no_match_correct"
            else:
                results["no_match_wrong"] += 1
                outcome = f"no_match_wrong (returned {top3}, floor_hit={floor_hit})"
        else:
            # match-expected prompt: success = expected[0] in top-3
            if expected[0] in top3:
                results["correct"] += 1
                outcome = f"correct (rank {top3.index(expected[0]) + 1})"
            else:
                results["wrong"] += 1
                outcome = f"wrong (expected {expected[0]}, got {top3})"

        # Per-anchor sub-score
        if "L3-003" in expected:
            cassi_total += 1
            if expected[0] in top3: cassi_hits += 1
        if "L3-004" in expected:
            cacti_total += 1
            if expected[0] in top3: cacti_hits += 1

        per_prompt.append({"id": p["id"], "result": outcome})
        if args.verbose:
            print(f"  [{outcome:30}] {p['id']}: {p['prompt'][:80]}...")

    # Summary
    total_expected = results["correct"] + results["wrong"]
    total_no_match = results["no_match_correct"] + results["no_match_wrong"]

    print()
    print("=" * 60)
    print(f"Harness: {harness.relative_to(repo)}")
    print(f"Prompts: {len(prompts)}")
    print("-" * 60)
    if total_expected:
        pct = 100 * results["correct"] / total_expected
        print(f"  Accuracy:         {results['correct']}/{total_expected} "
              f"({pct:.1f}%) top-3 match")
    if cassi_total:
        print(f"    CASSI (L3-003): {cassi_hits}/{cassi_total} "
              f"({100 * cassi_hits / cassi_total:.1f}%)")
    if cacti_total:
        print(f"    CACTI (L3-004): {cacti_hits}/{cacti_total} "
              f"({100 * cacti_hits / cacti_total:.1f}%)")
    if total_no_match:
        honesty_pct = 100 * results["no_match_correct"] / total_no_match
        print(f"  No-match honesty: {results['no_match_correct']}/{total_no_match} "
              f"({honesty_pct:.1f}%) correctly returned confidence_floor_hit")
    print(f"  Hallucinations:   {results['hallucination']}")
    print(f"  Errors:           {results['error']}")
    print("=" * 60)

    # G3 gate: both CASSI and CACTI must be ≥ 80%
    cassi_pct = 100 * cassi_hits / max(cassi_total, 1)
    cacti_pct = 100 * cacti_hits / max(cacti_total, 1)
    if cassi_pct >= 80 and cacti_pct >= 80 and results["hallucination"] == 0:
        print("G3 GATE: ✓ PASS (both anchors ≥ 80%, 0 hallucinations)")
    else:
        missing = []
        if cassi_pct < 80: missing.append(f"CASSI {cassi_pct:.1f}% < 80%")
        if cacti_pct < 80: missing.append(f"CACTI {cacti_pct:.1f}% < 80%")
        if results["hallucination"] > 0:
            missing.append(f"{results['hallucination']} hallucinations > 0")
        print(f"G3 GATE: ✗ missing: {'; '.join(missing)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
