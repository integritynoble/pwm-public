"""pwm-node benchmarks / pwm-node principles — list local genesis artifacts.

Per smoke-test finding F1 (PWM_PUBLIC_REPO_SMOKE_TEST_RESULTS_2026-05-03.md):
the historical `benchmarks` command actually walked `genesis/l1/` and listed
**Principles**, not benchmarks. That's a docstring/UX mismatch with what
customers expect when they read "list benchmarks".

This module now exposes both:

  - `_run_principles(args)`  — the original behaviour (walks `l1/`); wired
                               to the new `pwm-node principles` subcommand
  - `_run_benchmarks(args)`  — new behaviour: walks `l3/` and prints
                               L3-flavored columns (parent L1/L2, ρ, ε,
                               primary metric, ref-baseline). Wired to
                               `pwm-node benchmarks`.

Back-compat: the public `run(args)` entry point continues to exist for any
external caller. New top-level callers should target `_run_principles` or
`_run_benchmarks` directly via the dispatcher in `__main__.py`.

Both functions remain offline by design — they only read the local
``--genesis-dir`` JSON files. A future chain-connected version will overlay
on-chain state (registered, promoted ρ, current rank-1 score).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# ---------- Loaders ----------


def _load_layer_artifacts(genesis_dir: Path, layer: str) -> list[dict]:
    """Read every L<layer>-*.json under genesis_dir/l<layer>/."""
    sub = genesis_dir / layer
    if not sub.is_dir():
        return []
    layer_upper = layer.upper()
    out: list[dict] = []
    for f in sorted(sub.glob(f"{layer_upper}-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue  # skip corrupt files in listing; users can inspect individually
    return out


def _load_l1_artifacts(genesis_dir: Path) -> list[dict]:
    """Read every L1-*.json under genesis_dir/l1/."""
    return _load_layer_artifacts(genesis_dir, "l1")


def _load_l3_artifacts(genesis_dir: Path) -> list[dict]:
    """Read every L3-*.json under genesis_dir/l3/."""
    return _load_layer_artifacts(genesis_dir, "l3")


# ---------- principles (the historical behaviour) ----------


def _run_principles(args: argparse.Namespace) -> int:
    """List Principles (L1 layer). Renamed from the historical `benchmarks`
    command — same behaviour, more accurate name. See F1 in smoke-test
    results."""
    arts = _load_l1_artifacts(args.genesis_dir)
    if not arts:
        print(
            f"[pwm-node principles] no L1 artifacts found under "
            f"{args.genesis_dir}/l1/. Pass --genesis-dir to point elsewhere."
        )
        return 0

    if getattr(args, "domain", None):
        needle = args.domain.lower()
        arts = [a for a in arts if needle in a.get("domain", "").lower()
                or needle in a.get("sub_domain", "").lower()]

    if getattr(args, "spec", None):
        arts = [a for a in arts if a.get("artifact_id") == args.spec
                or f"L2-{a.get('principle_number')}" == args.spec]

    if not arts:
        print("[pwm-node principles] filter matched zero artifacts.")
        return 0

    # Title-first table per customer-guide plan task 2.9.
    header = f"{'Title':<52} {'ID':<10} {'Domain':<22} {'Tier':<10} {'Verification':<20}"
    print(header)
    print("-" * len(header))
    for a in arts:
        title = (a.get("title", "?"))[:52]
        aid = a.get("artifact_id", "?")
        dom = (a.get("domain", "?"))[:22]
        tier = (a.get("difficulty_tier", "?") or "?")[:10]
        verif = (a.get("verification_status", "draft") or "draft")[:20]
        print(f"{title:<52} {aid:<10} {dom:<22} {tier:<10} {verif:<20}")

    return 0


# ---------- benchmarks (the new L3-walking behaviour) ----------


def _run_benchmarks(args: argparse.Namespace) -> int:
    """List L3 P-benchmarks. Walks `genesis/l3/` and prints L3-relevant
    columns: parent L1/L2 IDs, primary metric, ρ floor, T1 ε floor, and
    the first-tier reference-baseline solver score (e.g., GAP-TV @ 26.0 dB
    for CASSI L3-003).

    Per smoke-test finding F1 — this is what customers actually expect
    when they type "pwm-node benchmarks".
    """
    arts = _load_l3_artifacts(args.genesis_dir)
    if not arts:
        # Helpful fallback: tell the user the command they probably wanted.
        print(
            f"[pwm-node benchmarks] no L3 artifacts found under "
            f"{args.genesis_dir}/l3/. If you wanted to list Principles "
            f"(L1 layer), run `pwm-node principles` instead."
        )
        return 0

    # Optional filters: by parent L1, by parent L2 (re-using --domain / --spec).
    if getattr(args, "domain", None):
        needle = args.domain.lower()
        arts = [a for a in arts if needle in (a.get("title", "") or "").lower()
                or needle in (a.get("display_slug", "") or "").lower()]

    if getattr(args, "spec", None):
        arts = [a for a in arts if a.get("parent_l2") == args.spec]

    if not arts:
        print("[pwm-node benchmarks] filter matched zero L3 artifacts.")
        return 0

    # L3-flavoured columns: title, ID, parent L1, ρ, T1 ε, T1 baseline.
    header = (
        f"{'Title':<48} {'ID':<10} {'L1':<8} {'rho':<5} {'T1_eps':<8} {'T1 baseline':<28}"
    )
    print(header)
    print("-" * len(header))
    for a in arts:
        title = (a.get("title", "?"))[:48]
        aid = a.get("artifact_id", "?")
        parent_l1 = a.get("parent_l1", "?")
        rho = str(a.get("rho", "?"))
        ibench = a.get("ibenchmarks") or []
        t1_eps = "?"
        baseline = "?"
        if ibench:
            t1 = ibench[0]
            t1_eps = str(t1.get("epsilon", "?"))
            baselines = t1.get("baselines") or []
            if baselines:
                b = baselines[0]
                name = b.get("name", "?")
                score = b.get("score", "?")
                metric = b.get("metric", "")
                baseline = f"{name} = {score} {metric}".strip()[:28]
        print(f"{title:<48} {aid:<10} {parent_l1:<8} {rho:<5} {t1_eps:<8} {baseline:<28}")

    return 0


# ---------- specs (L2 listing — new 2026-05-08) ----------


def _resolve_l1_filter(genesis_dir: Path, raw: str) -> str | None:
    """Resolve an L1 reference (artifact_id like 'L1-003' or slug like 'cassi')
    to its canonical artifact_id. Returns None if no match.

    Walks both genesis tree and the content tree (Tier-3 stubs) so users
    can filter L2 listings by either form.
    """
    if not raw:
        return None
    raw_lc = raw.lower()
    # Direct artifact_id match first
    for a in _load_l1_artifacts(genesis_dir):
        if a.get("artifact_id") == raw:
            return raw
        if (a.get("display_slug") or "").lower() == raw_lc:
            return a.get("artifact_id")
    # Content tree fallback for stubs
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pwm-team" / "content"
        if candidate.is_dir():
            for path in candidate.rglob("L1-*.json"):
                try:
                    a = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                if not isinstance(a, dict):
                    continue
                if a.get("artifact_id") == raw or (a.get("display_slug") or "").lower() == raw_lc:
                    return a.get("artifact_id")
            break
    return None


def _load_l2_artifacts(genesis_dir: Path) -> list[dict]:
    """Read every L2-*.json under genesis_dir/l2/ AND content tree."""
    out = _load_layer_artifacts(genesis_dir, "l2")
    seen = {a.get("artifact_id") for a in out if a.get("artifact_id")}
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pwm-team" / "content"
        if candidate.is_dir():
            for path in candidate.rglob("L2-*.json"):
                try:
                    a = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                if isinstance(a, dict) and a.get("artifact_id") not in seen:
                    out.append(a)
                    seen.add(a.get("artifact_id"))
            break
    return out


def _run_specs(args: argparse.Namespace) -> int:
    """List L2 Specs (with optional --principle filter for L1→L2 traversal).

    Closes the L1→L2 enumeration gap surfaced 2026-05-08: without this,
    users couldn't list the L2 children of a given L1 from the CLI.
    """
    arts = _load_l2_artifacts(args.genesis_dir)
    if not arts:
        print(f"[pwm-node specs] no L2 artifacts found.")
        return 0

    # Optional filter: by parent L1 (accept either artifact_id or slug)
    if getattr(args, "principle", None):
        l1_id = _resolve_l1_filter(args.genesis_dir, args.principle)
        if l1_id is None:
            print(f"[pwm-node specs] no L1 found matching '{args.principle}'. "
                  f"Try `pwm-node principles` to list available L1s.")
            return 3
        arts = [a for a in arts if a.get("parent_l1") == l1_id]
        if not arts:
            print(f"[pwm-node specs] no L2 specs registered under {l1_id}.")
            return 0
        print(f"L2 Specs under {l1_id}:")
    else:
        print(f"All L2 Specs (genesis + content tree):")

    if getattr(args, "domain", None):
        needle = args.domain.lower()
        arts = [a for a in arts if needle in (a.get("title", "") or "").lower()]

    header = (
        f"{'Title':<55} {'ID':<10} {'Parent L1':<10} {'Slug':<22} {'Tier':<18}"
    )
    print(header)
    print("-" * len(header))
    for a in arts:
        title = (a.get("title", "?"))[:55]
        aid = a.get("artifact_id", "?")
        parent_l1 = a.get("parent_l1", "?")
        slug = (a.get("display_slug") or "")[:22]
        tier = (a.get("registration_tier") or "stub")[:18]
        print(f"{title:<55} {aid:<10} {parent_l1:<10} {slug:<22} {tier:<18}")
    print()
    print(f"  ({len(arts)} L2 spec{'s' if len(arts) != 1 else ''} listed)")
    return 0


# ---------- back-compat dispatch ----------


def run(args: argparse.Namespace) -> int:
    """Default dispatch — kept for backward compatibility with callers that
    imported `run` directly. New code should call `_run_benchmarks` for the
    L3 listing and `_run_principles` for the L1 listing.

    The argparse subcommand wiring in `__main__.py` chooses which of the
    two functions to call based on which subcommand the user typed; this
    `run` is the legacy entry that defaults to the L3 listing (matching the
    new `benchmarks` semantics that fix smoke-test F1).
    """
    return _run_benchmarks(args)
