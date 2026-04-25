"""Read-only access to canonical demo datasets.

Layout (as produced by scripts/generate_demos.py)::

    pwm_product/demos/<demo_name>/
        README.md                   # benchmark-level intro
        sample_01/
            snapshot.npz
            ground_truth.npz
            solution.npz
            snapshot.png
            ground_truth.png
            meta.json
        sample_02/
            ... same structure

Each benchmark ships N independent samples (N_SAMPLES in the generator),
so external users can see the reference solver is deterministic, not
cherry-picked.
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


SAMPLE_FILES = frozenset({
    "snapshot.npz", "ground_truth.npz", "solution.npz",
    "snapshot.png", "ground_truth.png", "solution.png",
    "meta.json",
})

BENCHMARK_FILES = frozenset({"README.md"})


def _safe_name(s: str) -> bool:
    return bool(s) and "/" not in s and ".." not in s


@lru_cache(maxsize=1)
def list_demos() -> list[dict]:
    """Enumerate every demo directory with its samples + metadata."""
    root = demos_dir()
    if not root.is_dir():
        return []
    demos_out = []
    for demo_dir in sorted(root.iterdir()):
        if not demo_dir.is_dir():
            continue
        samples = []
        for sample_dir in sorted(demo_dir.iterdir()):
            if not sample_dir.is_dir() or not sample_dir.name.startswith("sample_"):
                continue
            meta_path = sample_dir / "meta.json"
            if not meta_path.is_file():
                continue
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                continue
            files = {name: (sample_dir / name).stat().st_size
                     for name in SAMPLE_FILES
                     if (sample_dir / name).is_file()}
            samples.append({
                "name": sample_dir.name,
                "meta": meta,
                "files": files,
            })
        if not samples:
            continue
        benchmark_id = samples[0]["meta"].get("benchmark", "").split()[0] or None
        demos_out.append({
            "name": demo_dir.name,
            "benchmark_id": benchmark_id,
            "readme_available": (demo_dir / "README.md").is_file(),
            "samples": samples,
        })
    return demos_out


def find_demo(demo_name: str) -> dict | None:
    if not _safe_name(demo_name):
        return None
    for d in list_demos():
        if d["name"] == demo_name:
            return d
    return None


def resolve_sample_file(demo_name: str, sample_name: str, filename: str) -> Path | None:
    if filename not in SAMPLE_FILES:
        return None
    if not (_safe_name(demo_name) and _safe_name(sample_name)):
        return None
    if not sample_name.startswith("sample_"):
        return None
    path = demos_dir() / demo_name / sample_name / filename
    if not path.is_file():
        return None
    try:
        path.resolve().relative_to(demos_dir().resolve())
    except ValueError:
        return None
    return path


def resolve_benchmark_file(demo_name: str, filename: str) -> Path | None:
    if filename not in BENCHMARK_FILES:
        return None
    if not _safe_name(demo_name):
        return None
    path = demos_dir() / demo_name / filename
    if not path.is_file():
        return None
    try:
        path.resolve().relative_to(demos_dir().resolve())
    except ValueError:
        return None
    return path
