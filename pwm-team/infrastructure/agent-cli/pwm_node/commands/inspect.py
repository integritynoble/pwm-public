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


def run(args: argparse.Namespace) -> int:
    """Resolve and print an artifact. Returns 0 on hit, 3 on miss."""
    target = args.target
    hit = _find_by_id(args.genesis_dir, target)
    if hit is None:
        print(
            f"[pwm-node inspect] no offline match for '{target}'. "
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
        # Spec-layer detail: parent links + six-tuple + d_spec + ibenchmark range.
        if artifact.get("parent_l1"):
            print(f"Parent L1:    {artifact['parent_l1']}")
        if artifact.get("spec_type"):
            print(f"Spec type:    {artifact['spec_type']}")
        if artifact.get("d_spec") is not None:
            print(f"d_spec:       {artifact['d_spec']}")
        st = artifact.get("six_tuple", {})
        if st.get("epsilon_fn"):
            eps = st["epsilon_fn"]
            print(f"epsilon_fn:   {eps if isinstance(eps, str) else '<...>'}")
        ibr = artifact.get("ibenchmark_range", {})
        center = ibr.get("center_ibenchmark", {})
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
