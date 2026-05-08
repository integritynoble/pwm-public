"""Regression guard: every L1 G.vertices entry must use one of the 12
canonical primitives from primitives.md.

The 12 canonical first-tokens (with ASCII fallbacks accepted):
  ∂ / D    Differentiate
  ∫ / int  Integrate
  L        Linear
  N        Nonlinear
  E        Eigensolve
  F        Fourier
  Π / Pi   Project
  S        Sample
  K        Kernel
  B        Boundary
  G        Generate
  O        Optimize

This prevents the regression that was caught and fixed on 2026-05-08:
content agents had introduced an ad-hoc `M.*` namespace (M.eigensolve,
M.time_integrate, M.scf_iterate, …) — 156 occurrences across 163 stub
manifests. `scripts/canonicalize_l1_primitives.py` mapped them all to
canonical primitives; this test fails CI if any new L1 reintroduces a
non-canonical prefix.

Run:
    python3 -m pytest scripts/test_canonical_primitives.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

CANONICAL_PREFIXES = frozenset({
    "D", "∂", "int", "∫", "L", "N", "E", "F", "Pi", "Π", "S", "K", "B", "G", "O",
})

REPO_ROOT = Path(__file__).resolve().parent.parent


def _all_l1_manifests() -> list[Path]:
    out = []
    out.extend((REPO_ROOT / "pwm-team" / "content").rglob("L1-*.json"))
    out.extend((REPO_ROOT / "pwm-team" / "pwm_product" / "genesis" / "l1").glob("L1-*.json"))
    return sorted(out)


def _first_token(vertex: str) -> str:
    return vertex.split(".", 1)[0]


@pytest.mark.parametrize("path", _all_l1_manifests(), ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_l1_uses_only_canonical_primitives(path: Path) -> None:
    m = json.loads(path.read_text())
    g = m.get("G") or {}
    vertices = g.get("vertices") or []
    bad = [v for v in vertices if isinstance(v, str)
           and _first_token(v) not in CANONICAL_PREFIXES]
    assert not bad, (
        f"{path.relative_to(REPO_ROOT)} has non-canonical primitives: {bad}\n"
        f"Allowed first-tokens: {sorted(CANONICAL_PREFIXES)}\n"
        f"See papers/Proof-of-Solution/mine_example/primitives.md for the\n"
        f"12 canonical primitives. If you've added a new physics-specific\n"
        f"composite, map it to its closest canonical primitive (often E,\n"
        f"O, D.time, or D.space) and add a sub-leaf if needed."
    )


def test_canonicalizer_is_a_no_op() -> None:
    """If the canonicalizer's heuristic still finds anything to remap,
    someone has reintroduced a non-canonical primitive somewhere."""
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from canonicalize_l1_primitives import map_primitive

    files = _all_l1_manifests()
    remappings: list[tuple[str, str, str]] = []
    for p in files:
        m = json.loads(p.read_text())
        for v in (m.get("G") or {}).get("vertices") or []:
            if isinstance(v, str):
                new = map_primitive(v)
                if new != v:
                    remappings.append((p.name, v, new))

    assert not remappings, (
        f"canonicalizer would remap {len(remappings)} vertices — "
        f"someone reintroduced non-canonical primitives:\n" +
        "\n".join(f"  {f}: {old} → {new}" for f, old, new in remappings[:10])
    )
