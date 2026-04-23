"""Generate benchmark cards (user-facing summaries) from L3 JSON artifacts.

Per pwm_overview1.md §8.1. Each card is a flat ≤ 20-field YAML file that
sits beside the L3 JSON; the web explorer + faceted matcher read cards,
not L3 JSON directly.

Card structure:

    auto:          # generator-owned; regenerated every run
      benchmark_id, principle_number, principle_title, title, domain,
      sub_domain, benchmark_type, tiers[], best_baseline_name,
      best_baseline_q, quality_metric, quality_metric_secondary,
      difficulty_delta
    handwritten:   # author-owned; preserved across runs
      one_line, forward_model_summary, bad_prompt_keywords

On first run for a principle, ``handwritten:`` is filled with
placeholders that render as "Claim this — 2,000 PWM" CTAs in the web
explorer (per Bounty #7 / MVP_FIRST_STRATEGY.md §10.3). On subsequent
runs, handwritten fields are preserved untouched — only the ``auto:``
block is regenerated.

Usage::

    python3 scripts/generate_benchmark_cards.py              # all L3s
    python3 scripts/generate_benchmark_cards.py L3-003       # one L3
    python3 scripts/generate_benchmark_cards.py --check       # CI dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

GENERATOR_VERSION = "1.0.0"

HANDWRITTEN_PLACEHOLDER_ONE_LINE = "[not yet claimed — Bounty #7]"
HANDWRITTEN_PLACEHOLDER_FORWARD = "[not yet claimed — Bounty #7]"
HANDWRITTEN_PLACEHOLDER_BAD_KEYWORDS: list[str] = []


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team" / "pwm_product" / "genesis").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _principle_id_from_parent(parent_l1: str | None, default: int = 0) -> int:
    """Extract integer id from parent_l1 like 'L1-003' → 3."""
    if not parent_l1:
        return default
    m = re.search(r"(\d+)\s*$", str(parent_l1))
    return int(m.group(1)) if m else default


def _infer_shapes_from_l3(l3: dict) -> tuple[list | None, list | None]:
    """Best-effort input/output shape inference from ibenchmark Ω fields.

    Returns (input_shape, output_shape) as lists that may use "H"/"W"/"N"
    as dimension labels. If we can't infer confidently, returns None.
    """
    ibs = l3.get("ibenchmarks") or []
    if not ibs:
        return None, None
    omega = (ibs[0].get("omega_tier") or {})
    # Common hyperspectral / video / tomography shape families.
    H = "H" if "H" in omega else None
    W = "W" if "W" in omega else None
    N = "N_bands" if "N_bands" in omega else (
        "N_frames" if "N_frames" in omega else None
    )
    if H and W and N:
        # e.g. CASSI: snapshot (H,W,1) → HSI (H,W,N_bands)
        return [H, W, 1], [H, W, N]
    if H and W:
        return [H, W, 1], [H, W]
    return None, None


def _extract_tiers(l3: dict) -> list[dict]:
    """Flatten ibenchmark tiers to the 5 most useful fields per tier."""
    out = []
    for ib in (l3.get("ibenchmarks") or []):
        omega = ib.get("omega_tier") or {}
        mismatch_keys = [
            k for k in omega
            if k not in ("H", "W", "N_bands", "N_frames", "mask_density")
            and not str(k).startswith("_")
        ]
        mismatch_pairs = [f"{k}={omega[k]}" for k in mismatch_keys
                          if omega.get(k) not in (0, 0.0, None)]
        out.append({
            "tier": ib.get("tier"),
            "rho": ib.get("rho"),
            "H": omega.get("H"),
            "W": omega.get("W"),
            "noise_max": omega.get("noise_level") or omega.get("noise_std"),
            "mismatch_summary": ", ".join(mismatch_pairs) or "no mismatch",
            "epsilon": ib.get("epsilon"),
        })
    return out


def _extract_best_baseline(l3: dict) -> tuple[str | None, float | None]:
    """Return (name, overall_Q) of the best baseline in p_benchmark, else from ibenchmarks[0]."""
    pb = l3.get("p_benchmark") or {}
    bs = pb.get("baselines") or []
    best = max(bs, key=lambda b: b.get("overall_Q") or b.get("Q") or -1, default=None)
    if best is not None:
        return best.get("name"), best.get("overall_Q") or best.get("Q")
    # Fall back to first ibenchmark's top baseline
    for ib in (l3.get("ibenchmarks") or []):
        ib_bs = ib.get("baselines") or []
        if ib_bs:
            b = max(ib_bs, key=lambda b: b.get("Q") or -1)
            return b.get("name"), b.get("Q")
    return None, None


def _build_auto_fields(l3: dict, l1: dict | None, l2: dict | None) -> dict:
    """Assemble the auto-generated half of a card."""
    artifact_id = l3.get("artifact_id")
    parent_l1 = l3.get("parent_l1")
    principle_id = _principle_id_from_parent(parent_l1)
    in_shape, out_shape = _infer_shapes_from_l3(l3)

    baseline_name, baseline_q = _extract_best_baseline(l3)

    auto: dict[str, Any] = {
        "benchmark_id": artifact_id,
        "principle_number": principle_id,
        "principle_title": (l1 or {}).get("title"),
        "title": l3.get("title"),
        "domain": (l1 or {}).get("domain"),
        "sub_domain": (l1 or {}).get("sub_domain"),
        "benchmark_type": l3.get("benchmark_type"),
        "input_shape": in_shape,
        "output_shape": out_shape,
        "tiers": _extract_tiers(l3),
        "best_baseline_name": baseline_name,
        "best_baseline_q": baseline_q,
        "quality_metric": (l1 or {}).get("error_metric"),
        "quality_metric_secondary": (l1 or {}).get("error_metric_secondary"),
        "difficulty_delta": (l1 or {}).get("difficulty_delta"),
    }
    # Strip top-level None-valued keys for cleaner output.
    return {k: v for k, v in auto.items() if v is not None}


def _load_existing_handwritten(card_path: Path) -> dict:
    """Read the existing card's handwritten block so generator doesn't overwrite it.

    Returns empty dict if card doesn't exist, or if the handwritten block is
    missing/corrupt (in which case placeholders are emitted anew).
    """
    if not card_path.is_file():
        return {}
    try:
        import yaml  # PyYAML
    except ImportError:
        # Fall back to naive parse of just the 3 fields we care about.
        return _parse_handwritten_minimal(card_path)
    try:
        data = yaml.safe_load(card_path.read_text()) or {}
    except Exception:
        return {}
    hw = (data.get("handwritten") or {}) if isinstance(data, dict) else {}
    return hw


def _parse_handwritten_minimal(card_path: Path) -> dict:
    """Minimal yaml-less fallback parser for the handwritten block."""
    text = card_path.read_text().splitlines()
    hw: dict[str, Any] = {}
    in_hw = False
    for line in text:
        if line.startswith("handwritten:"):
            in_hw = True
            continue
        if in_hw and line and not line.startswith((" ", "\t", "#")):
            # left the handwritten block
            in_hw = False
        if in_hw:
            m = re.match(r"\s{2}(\w+):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    hw[key] = val[1:-1]
                elif val.startswith("["):
                    # crude list parsing
                    hw[key] = []
                elif val:
                    hw[key] = val
    return hw


def _default_handwritten() -> dict:
    return {
        "one_line": HANDWRITTEN_PLACEHOLDER_ONE_LINE,
        "forward_model_summary": HANDWRITTEN_PLACEHOLDER_FORWARD,
        "bad_prompt_keywords": list(HANDWRITTEN_PLACEHOLDER_BAD_KEYWORDS),
    }


def _render_card(auto: dict, handwritten: dict) -> str:
    """Render the card YAML without requiring PyYAML (deterministic string layout)."""
    lines = [
        "# Benchmark card — auto-generated + handwritten blocks.",
        "# DO NOT edit the `auto:` block by hand; it regenerates from L3 JSON.",
        "# DO handwrite the fields under `handwritten:` — the generator preserves them.",
        f"# Generator: scripts/generate_benchmark_cards.py v{GENERATOR_VERSION}",
        "",
        "auto:",
    ]
    for k, v in auto.items():
        lines.append(_yaml_line(k, v, indent=2))
    lines.append("")
    lines.append("handwritten:")
    for k, v in handwritten.items():
        lines.append(_yaml_line(k, v, indent=2))
    lines.append("")
    return "\n".join(lines)


def _yaml_line(key: str, value: Any, indent: int) -> str:
    """Crude YAML emitter — handles scalars, lists of scalars, and lists of dicts."""
    pad = " " * indent
    if value is None:
        return f"{pad}{key}: null"
    if isinstance(value, bool):
        return f"{pad}{key}: {'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"{pad}{key}: {value}"
    if isinstance(value, str):
        # Quote if contains special chars or is empty
        if not value or any(c in value for c in ":#{}[],&*!|>'%@`") or value[0] in " -?":
            esc = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'{pad}{key}: "{esc}"'
        return f"{pad}{key}: {value}"
    if isinstance(value, list):
        if not value:
            return f"{pad}{key}: []"
        if all(isinstance(x, (int, float, str)) for x in value):
            # inline scalar list
            parts = []
            for x in value:
                if isinstance(x, str):
                    parts.append(f'"{x}"' if any(c in x for c in ":#{}[],") else x)
                else:
                    parts.append(str(x))
            return f"{pad}{key}: [{', '.join(parts)}]"
        # list of dicts → block style
        result = [f"{pad}{key}:"]
        for item in value:
            if isinstance(item, dict):
                first = True
                for ik, iv in item.items():
                    if first:
                        result.append(f"{pad}  - {ik}: {_scalar_str(iv)}")
                        first = False
                    else:
                        result.append(f"{pad}    {ik}: {_scalar_str(iv)}")
            else:
                result.append(f"{pad}  - {_scalar_str(item)}")
        return "\n".join(result)
    if isinstance(value, dict):
        result = [f"{pad}{key}:"]
        for ik, iv in value.items():
            result.append(_yaml_line(ik, iv, indent + 2))
        return "\n".join(result)
    return f"{pad}{key}: {value!r}"


def _scalar_str(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        if not v or any(c in v for c in ":#{}[],"):
            esc = v.replace('"', '\\"')
            return f'"{esc}"'
        return v
    return str(v)


def process_one(l3_path: Path, out_dir: Path, genesis_dir: Path,
                check_only: bool = False) -> tuple[str, str]:
    """Generate one card. Returns (status, message)."""
    l3 = _load_json(l3_path)
    if l3 is None:
        return ("skip", f"cannot read {l3_path}")

    artifact_id = l3.get("artifact_id")
    if not artifact_id:
        return ("skip", f"{l3_path.name}: no artifact_id")

    parent_l1_id = l3.get("parent_l1")
    parent_l2_id = l3.get("parent_l2")
    l1 = _load_json(genesis_dir / "l1" / f"{parent_l1_id}.json") if parent_l1_id else None
    l2 = _load_json(genesis_dir / "l2" / f"{parent_l2_id}.json") if parent_l2_id else None

    auto = _build_auto_fields(l3, l1, l2)
    card_path = out_dir / f"{artifact_id}.yaml"

    existing_hw = _load_existing_handwritten(card_path)
    handwritten = _default_handwritten()
    # Preserve any non-placeholder handwritten fields.
    for key in ("one_line", "forward_model_summary", "bad_prompt_keywords"):
        if key in existing_hw and existing_hw[key] not in (
            HANDWRITTEN_PLACEHOLDER_ONE_LINE,
            HANDWRITTEN_PLACEHOLDER_FORWARD,
            "",
            [],
            None,
        ):
            handwritten[key] = existing_hw[key]

    rendered = _render_card(auto, handwritten)

    if check_only:
        existing = card_path.read_text() if card_path.is_file() else ""
        return (
            ("unchanged" if existing == rendered else "would-change"),
            f"{artifact_id}",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    card_path.write_text(rendered)
    return ("wrote", f"{artifact_id} → {card_path.relative_to(_repo_root())}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate PWM benchmark cards from L3 JSON")
    ap.add_argument("artifacts", nargs="*", help="Specific artifact_ids (e.g. L3-003). "
                    "If omitted, all L3-*.json under genesis/l3/ are processed.")
    ap.add_argument("--check", action="store_true",
                    help="Dry-run: report what would change, don't write files.")
    args = ap.parse_args(argv)

    repo = _repo_root()
    genesis_dir = repo / "pwm-team" / "pwm_product" / "genesis"
    l3_dir = genesis_dir / "l3"
    out_dir = repo / "pwm-team" / "pwm_product" / "benchmark_cards"

    if args.artifacts:
        paths = [l3_dir / f"{aid}.json" for aid in args.artifacts]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            print(f"ERROR: missing L3 files: {missing}", file=sys.stderr)
            return 1
    else:
        paths = sorted(l3_dir.glob("L3-*.json"))
        if not paths:
            print(f"ERROR: no L3-*.json found under {l3_dir}", file=sys.stderr)
            return 1

    counts = {"wrote": 0, "unchanged": 0, "would-change": 0, "skip": 0}
    for p in paths:
        status, msg = process_one(p, out_dir, genesis_dir, check_only=args.check)
        counts[status] = counts.get(status, 0) + 1
        if status in ("wrote", "would-change", "skip"):
            print(f"  [{status:13}] {msg}")
    print()
    print(f"Summary: {counts}")
    if args.check and counts.get("would-change", 0) > 0:
        return 2  # CI-signal: cards are stale
    return 0


if __name__ == "__main__":
    sys.exit(main())
