"""Read-only access to canonical demo datasets.

Each subdirectory under pwm-team/pwm_product/demos/ contains an anchor's
demo input, ground truth, pre-computed reference solution, and a
meta.json describing them. This module exposes the metadata + a file
fetch endpoint so the web explorer can surface "Try the demo" links
users can click.

Files served are small (< 50 KB per demo) and committed to the repo;
there is no write path and no auth.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


try:
    PWM_TEAM_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    PWM_TEAM_ROOT = Path("/repo/pwm-team")
DEFAULT_DEMOS_DIR = PWM_TEAM_ROOT / "pwm_product" / "demos"


def demos_dir() -> Path:
    return Path(os.environ.get("PWM_DEMOS_DIR", str(DEFAULT_DEMOS_DIR)))


# Only these filenames are servable. Prevents directory-traversal.
ALLOWED_FILES = frozenset({
    "snapshot.npz", "ground_truth.npz", "solution.npz", "meta.json", "README.md",
})


@lru_cache(maxsize=1)
def list_demos() -> list[dict]:
    """Enumerate every demo directory + expose its meta.json + file inventory."""
    root = demos_dir()
    if not root.is_dir():
        return []
    demos = []
    for sub in sorted(root.iterdir()):
        if not sub.is_dir():
            continue
        meta_path = sub / "meta.json"
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            continue
        files = {name: (sub / name).stat().st_size
                 for name in ALLOWED_FILES
                 if (sub / name).is_file()}
        demos.append({
            "name": sub.name,
            "meta": meta,
            "files": files,
        })
    return demos


def resolve_file(demo_name: str, filename: str) -> Path | None:
    """Return an absolute path to a demo file, or None if out-of-scope."""
    if filename not in ALLOWED_FILES:
        return None
    # demo_name sanity: no slashes, no ..
    if "/" in demo_name or ".." in demo_name or not demo_name:
        return None
    path = demos_dir() / demo_name / filename
    if not path.is_file():
        return None
    # Containment check: path must live under demos_dir
    try:
        path.resolve().relative_to(demos_dir().resolve())
    except ValueError:
        return None
    return path
