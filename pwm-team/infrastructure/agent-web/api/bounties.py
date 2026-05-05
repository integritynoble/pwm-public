"""Open-bounty listing — reads the static specs published by agent-coord.

Bounty INDEX.md and per-bounty markdown files live in
`pwm-team/bounties/` (moved out of `coordination/` 2026-05-05 so they
ship in the public mirror per `PWM_CUSTOMER_GUIDE_AUDIT_2026-05-04.md`
G4). We expose a minimal JSON view so the /bounties frontend route
can render without scraping markdown.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path


try:
    PWM_TEAM_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    PWM_TEAM_ROOT = Path("/repo/pwm-team")
REPO_ROOT = PWM_TEAM_ROOT.parent  # used only for relative display paths
DEFAULT_DIR = PWM_TEAM_ROOT / "bounties"


def bounties_dir() -> Path:
    return Path(os.environ.get("PWM_BOUNTIES_DIR", str(DEFAULT_DIR)))


_HEADER_RE = re.compile(r"^#\s+(?P<title>.+?)\s*(?:\((?P<amount>[\d,]+)\s*PWM\))?$", re.MULTILINE)
_AMOUNT_RE = re.compile(r"\*\*Amount:?\*\*\s*([\d,]+)\s*PWM", re.IGNORECASE)


@lru_cache(maxsize=1)
def list_bounties() -> list[dict]:
    root = bounties_dir()
    if not root.exists():
        return []
    out = []
    for path in sorted(root.glob("*.md")):
        if path.name.upper() == "INDEX.MD":
            continue
        text = path.read_text()
        title = path.stem
        amount = None
        header = _HEADER_RE.search(text)
        if header:
            title = header.group("title").strip()
            if header.group("amount"):
                amount = int(header.group("amount").replace(",", ""))
        if amount is None:
            body_match = _AMOUNT_RE.search(text)
            if body_match:
                amount = int(body_match.group(1).replace(",", ""))
        # Grab first paragraph as summary.
        summary = ""
        for chunk in text.split("\n\n"):
            chunk = chunk.strip()
            if not chunk.startswith("#") and chunk:
                summary = chunk.replace("\n", " ")
                break
        try:
            spec_path = str(path.relative_to(REPO_ROOT))
        except ValueError:
            spec_path = str(path)
        out.append({
            "slug": path.stem,
            "title": title,
            "amount_pwm": amount,
            "summary": summary[:400],
            "spec_path": spec_path,
        })
    return out


def reload() -> None:
    list_bounties.cache_clear()
