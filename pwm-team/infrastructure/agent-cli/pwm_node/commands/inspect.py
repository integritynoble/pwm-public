"""pwm-node inspect — resolve a hash/id to its artifact (offline).

Offline variant: matches against L1/L2/L3 JSONs in ``--genesis-dir`` by
``artifact_id`` (L1-NNN / L2-NNN / L3-NNN). Chain-connected variant (next
session) will also accept cert_hash and query PWMRegistry via chain.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_layer(genesis_dir: Path, layer: str) -> list[dict]:
    """Read all artifacts for a given layer."""
    d = genesis_dir / layer.lower()
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.glob(f"{layer}-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _find_by_id(genesis_dir: Path, target: str) -> tuple[dict, str] | None:
    """Return (artifact, layer) for the first artifact with artifact_id == target."""
    for layer in ("L1", "L2", "L3"):
        for a in _load_layer(genesis_dir, layer):
            if a.get("artifact_id") == target:
                return a, layer
    return None


def _find_by_slug(genesis_dir: Path, target: str, prefer_layer: str | None = None) -> tuple[dict, str] | None:
    """Return (artifact, layer) for the first artifact with display_slug == target.

    Default search order is L1 → L2 → L3 (matches web /principles/<slug>;
    L1 is "what is this principle?", the most fundamental answer).
    A user wanting the spec/benchmark instead passes prefer_layer=L2|L3.
    """
    target_lower = target.lower()
    if prefer_layer:
        layers: tuple[str, ...] = (prefer_layer.upper(),)
    else:
        layers = ("L1", "L2", "L3")
    for layer in layers:
        for a in _load_layer(genesis_dir, layer):
            if (a.get("display_slug") or "").lower() == target_lower:
                return a, layer
    return None


def _slug_siblings(genesis_dir: Path, target: str, found_layer: str) -> list[str]:
    """For a slug match, find all OTHER layers that share the same slug.

    Used to print a hint like "(slug 'cassi' also matches L2-003, L3-003 —
    use --layer L2/L3 to switch)".
    """
    target_lower = target.lower()
    siblings: list[str] = []
    for layer in ("L1", "L2", "L3"):
        if layer == found_layer.upper():
            continue
        for a in _load_layer(genesis_dir, layer):
            if (a.get("display_slug") or "").lower() == target_lower:
                aid = a.get("artifact_id")
                if aid:
                    siblings.append(aid)
                break
    return siblings


def _find_in_content_tree(target: str, prefer_layer: str | None = None) -> tuple[dict, str] | None:
    """Fallback for stubs not in the genesis tree — walk pwm-team/content/.

    Matches by artifact_id OR display_slug. When prefer_layer is set,
    only return artifacts on that layer (used to disambiguate slugs
    that span L1/L2/L3 — e.g. 'spc' matches L1-026b + L2-026b + L3-026b).
    """
    target_lower = target.lower()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pwm-team" / "content"
        if candidate.is_dir():
            content_root = candidate
            break
    else:
        return None
    prefer_upper = prefer_layer.upper() if prefer_layer else None
    # First pass: prefer_layer-only
    if prefer_upper:
        for path in content_root.rglob(f"{prefer_upper}-*.json"):
            try:
                a = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(a, dict):
                continue
            if a.get("artifact_id") == target or (a.get("display_slug") or "").lower() == target_lower:
                return a, prefer_upper
        return None
    # No layer preference: fall back to L1 → L2 → L3 priority
    for layer_pref in ("L1", "L2", "L3"):
        for path in content_root.rglob(f"{layer_pref}-*.json"):
            try:
                a = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(a, dict):
                continue
            if a.get("artifact_id") == target or (a.get("display_slug") or "").lower() == target_lower:
                aid = a.get("artifact_id") or ""
                layer = aid.split("-", 1)[0] if aid else layer_pref
                return a, layer
    return None


def _content_tree_siblings(target: str, found_layer: str) -> list[str]:
    """Find sibling-layer artifact_ids for a slug match in the content tree."""
    target_lower = target.lower()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pwm-team" / "content"
        if candidate.is_dir():
            content_root = candidate
            break
    else:
        return []
    siblings: list[str] = []
    for layer in ("L1", "L2", "L3"):
        if layer == found_layer.upper():
            continue
        for path in content_root.rglob(f"{layer}-*.json"):
            try:
                a = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(a, dict) and (a.get("display_slug") or "").lower() == target_lower:
                aid = a.get("artifact_id")
                if aid:
                    siblings.append(aid)
                    break
    return siblings


def _normalize_layer(layer_arg: str | None) -> str | None:
    """Normalize the --layer flag value to L1 / L2 / L3 (or None)."""
    if not layer_arg:
        return None
    s = str(layer_arg).strip().upper()
    if s in ("1", "L1"):
        return "L1"
    if s in ("2", "L2"):
        return "L2"
    if s in ("3", "L3"):
        return "L3"
    return None


def run(args: argparse.Namespace) -> int:
    """Resolve and print an artifact. Returns 0 on hit, 3 on miss.

    Resolution order:
      1. Genesis tree by artifact_id ("L1-003", "L3-026b") — exact match
      2. Genesis tree by slug ("cassi") — defaults to L1, --layer to override
      3. Content tree by either artifact_id or slug (same layer rules)

    For slug matches, prints sibling-layer hints if other layers share the
    same slug — e.g. `inspect cassi` shows L1-003 plus a note that L2-003
    and L3-003 also exist under that slug.
    """
    target = args.target
    prefer_layer = _normalize_layer(getattr(args, "layer", None))
    is_artifact_id = "-" in target and target.split("-", 1)[0].upper() in ("L1", "L2", "L3")

    # Exact artifact_id always wins (no ambiguity)
    hit = None
    if is_artifact_id:
        hit = _find_by_id(args.genesis_dir, target)
        if hit is None:
            hit = _find_in_content_tree(target)
    else:
        # Slug path: honor --layer; default L1
        hit = _find_by_slug(args.genesis_dir, target, prefer_layer=prefer_layer)
        if hit is None:
            hit = _find_in_content_tree(target, prefer_layer=prefer_layer)

    if hit is None:
        layer_msg = f" --layer {prefer_layer}" if prefer_layer else ""
        print(
            f"[pwm-node inspect] no offline match for '{target}'{layer_msg}. "
            f"Try `pwm-node match \"<your problem in plain English>\"` for fuzzy search, "
            f"or `pwm-node principles` to list all entries. "
            f"If this is a cert_hash, retry with --network testnet (not yet implemented in Phase C-stub).",
        )
        return 3

    artifact, layer = hit
    title = artifact.get("title", "?")
    aid = artifact.get("artifact_id", "?")
    slug = artifact.get("display_slug")
    # Title-first inline header (per customer-guide plan task 2.8); the
    # labelled lines below are kept for parser-friendliness.
    print(f"{title} ({aid})")
    if slug:
        print(f"  slug: {slug}")

    # If the user passed a slug (not an artifact_id), tell them which layer
    # got returned and what other layers are available under the same slug.
    # Prevents the "I asked for cassi and got L3, but I wanted L1" surprise.
    if not is_artifact_id and slug:
        siblings = _slug_siblings(args.genesis_dir, target, layer)
        if not siblings:
            siblings = _content_tree_siblings(target, layer)
        if siblings:
            sib_list = ", ".join(siblings)
            print(f"  layer: {layer.upper()} (slug '{slug}' also matches {sib_list} — use --layer to switch)")
        else:
            print(f"  layer: {layer.upper()}")

    print(f"=== {aid} ({layer.upper()}) ===")
    print(f"Title:        {title}")

    # Universal fields — only print when present, so L2/L3 manifests
    # (which lack domain / difficulty_tier) don't render as bare '?'.
    # Per smoke-test finding F3 (PWM_PUBLIC_REPO_SMOKE_TEST_RESULTS_2026-05-03.md).
    if artifact.get("domain"):
        print(f"Domain:       {artifact['domain']}")
    if artifact.get("sub_domain"):
        print(f"Sub-domain:   {artifact['sub_domain']}")
    if artifact.get("difficulty_tier") or artifact.get("difficulty_delta") is not None:
        delta = artifact.get("difficulty_delta", "?")
        print(f"Difficulty:   {artifact.get('difficulty_tier', '?')} (delta={delta})")
    if artifact.get("verification_status"):
        print(f"Verification: {artifact['verification_status']}")

    if artifact.get("verified_by"):
        print(f"Verified by:  {', '.join(artifact['verified_by'])}")
    if artifact.get("verification_date"):
        print(f"Verified on:  {artifact['verification_date']}")

    if layer == "L1":
        e = artifact.get("E", {})
        print(f"Forward:      {e.get('forward_model', '?')}")
        g = artifact.get("G", {})
        print(f"DAG:          {g.get('dag', '?')}")
        print(f"L_DAG:        {g.get('L_DAG', '?')}")
        w = artifact.get("W", {})
        print(f"kappa_sys:    {w.get('condition_number_kappa', '?')}")
        print(f"kappa_eff:    {w.get('condition_number_effective', '?')}")
        primitives = artifact.get("physics_fingerprint", {}).get("primitives", [])
        if primitives:
            print(f"Primitives:   {', '.join(primitives)}")

    elif layer == "L2":
        # Spec-layer detail: parent links + full six-tuple + s1-s4 gates +
        # d_spec + ibenchmark range. The customer guide explicitly documents
        # the six-tuple block (omega, E, B, I, O, epsilon_fn) and the
        # s1-s4 gate verdicts as the L2 inspect surface, so render both
        # whenever the manifest carries the fields.
        if artifact.get("parent_l1"):
            print(f"Parent L1:    {artifact['parent_l1']}")
        if artifact.get("spec_type"):
            print(f"Spec type:    {artifact['spec_type']}")
        if artifact.get("d_spec") is not None:
            print(f"d_spec:       {artifact['d_spec']}")

        st = artifact.get("six_tuple") or {}
        if st:
            print("six_tuple:")
            # omega — parameter space (dict of name -> [lo, hi] ranges or values)
            omega = st.get("omega") or {}
            if omega:
                # Pretty-print as a compact one-line summary; long manifests
                # have 10+ keys so wrap to 80 cols by chunking.
                pieces = []
                for k, v in omega.items():
                    if isinstance(v, list) and len(v) == 2:
                        pieces.append(f"{k}=[{v[0]}-{v[1]}]")
                    else:
                        pieces.append(f"{k}={v}")
                # Print on one line if short, else break onto continuations
                line = "  Omega:      " + " ".join(pieces)
                if len(line) <= 100:
                    print(line)
                else:
                    print(f"  Omega:      ({len(pieces)} dimensions)")
                    for p in pieces:
                        print(f"    {p}")
            # E — forward operator + DAG primitive chain
            e = st.get("E") or {}
            if e:
                if e.get("forward"):
                    print(f"  E:          forward: {e['forward']}")
                if e.get("primitive_chain"):
                    print(f"              chain:   {e['primitive_chain']}")
            # B — boundary constraints (dict of named flags / strings)
            b = st.get("B") or {}
            if b:
                # Only print key names when value is True/string; skip falsy
                keys = [k for k, v in b.items() if v]
                if keys:
                    print(f"  B:          {', '.join(keys)}")
            # I — initialization strategy (dict)
            i = st.get("I") or {}
            if i:
                strategy = i.get("strategy") or i
                print(f"  I:          {strategy}")
            # O — observable list
            o = st.get("O") or []
            if o:
                if isinstance(o, list):
                    print(f"  O:          {', '.join(str(x) for x in o)}")
                else:
                    print(f"  O:          {o}")
            # epsilon_fn — acceptance threshold formula
            if st.get("epsilon_fn"):
                eps = st["epsilon_fn"]
                print(f"  epsilon_fn: {eps if isinstance(eps, str) else '<...>'}")

        # S1-S4 gate verdicts — verifies the spec passes the four hardness +
        # convergence gates. Customer guide claims this row.
        gates = artifact.get("s1_s4_gates") or []
        if gates:
            print(f"S1-S4:        {gates}")

        ibr = artifact.get("ibenchmark_range") or {}
        center = ibr.get("center_ibenchmark") or {}
        if center:
            print(f"Center rho:   {center.get('rho', '?')}")
            if center.get("epsilon") is not None:
                print(f"Center eps:   {center['epsilon']}")

    elif layer == "L3":
        # Benchmark-layer detail: parent links + dataset + ibenchmark tiers.
        # Per smoke-test finding F3 — these fields ARE in the manifest;
        # the renderer just wasn't reading them.
        if artifact.get("parent_l1"):
            print(f"Parent L1:    {artifact['parent_l1']}")
        if artifact.get("parent_l2"):
            print(f"Parent L2:    {artifact['parent_l2']}")
        if artifact.get("benchmark_type"):
            print(f"Type:         {artifact['benchmark_type']}")
        if artifact.get("rho") is not None:
            print(f"rho:          {artifact['rho']}")

        ds = artifact.get("dataset_registry") or {}
        if ds:
            primary = ds.get("primary", "?")
            secondary = ds.get("secondary")
            print(f"Datasets:     {primary}" + (f" + {secondary}" if secondary else ""))
            if ds.get("construction_method"):
                print(f"  build:      {ds['construction_method']}")
            n_dev = ds.get("num_dev_instances_per_tier") or ds.get("num_dev_instances")
            n_holdout = ds.get("holdout_instances_per_tier") or ds.get("holdout_instances")
            if n_dev or n_holdout:
                print(f"  instances:  {n_dev or '?'} dev + {n_holdout or '?'} holdout")

        ibench = artifact.get("ibenchmarks") or []
        if ibench:
            tier_names = ", ".join(t.get("tier", "?") for t in ibench)
            print(f"Tiers:        {len(ibench)} ({tier_names})")
            t1 = ibench[0]
            omega = t1.get("omega_tier") or {}
            tier1 = t1.get("tier", "T1")
            print(f"  {tier1} eps:  {t1.get('epsilon', '?')}")
            if omega:
                omega_str = " ".join(f"{k}={v}" for k, v in omega.items())
                print(f"  {tier1} omega: {omega_str}")
            baselines = t1.get("baselines") or []
            if baselines:
                b = baselines[0]
                print(f"  {tier1} baseline: "
                      f"{b.get('name', '?')} = {b.get('score', '?')} {b.get('metric', '')}".rstrip())

        scoring = artifact.get("scoring") or {}
        if scoring.get("primary_metric"):
            print(f"Metric:       {scoring['primary_metric']}"
                  + (f" (+ {scoring['secondary_metric']})" if scoring.get("secondary_metric") else ""))

        if artifact.get("reference_solver"):
            print(f"Ref solver:   {artifact['reference_solver']}")

    return 0
