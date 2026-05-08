#!/usr/bin/env python3
"""Map non-canonical L1 G.vertices to the 12 canonical primitives from
papers/Proof-of-Solution/mine_example/primitives.md.

Audit (2026-05-08) found 156 uses of `M.*` (a method-class namespace
authored ad-hoc by content agents) and 1 typo `integrate.verlet`. The
12-canonical-primitive basis covers every one of these via a heuristic
mapping based on the suffix:

  M.*eigensolve, M.*Lanczos, M.transfer_matrix, M.*matrices*, M.dh.transformation_matrix → E
  M.*integrate, M.time_*, M.MD_*, M.IV_*, M.gyro.integration, M.ode.* (explicit/implicit/symplectic by context) → D.time.*
  M.verlet*, integrate.verlet → D.time.symplectic
  M.coupled_ODE, M.stiff_ODE → D.time.implicit
  M.pde.*, M.ns.*, M.swe.*, M.darcy.*, M.primitive.*, M.nwp.*, M.ade.*, M.fractional_flow.*,
    M.gassmann.*, M.dirac.*, M.reynolds.*, M.sea_ice.* → D.space.*
  M.scf*, M.self_consistent_*, M.coupled*, M.gummel_*, M.multiphysics, M.adjoint.*,
    M.fem.adjoint, M.transport.adjoint_*, M.bundle.adjustment, M.collocation.*,
    M.mpc.* → O.iter
  M.dls.*, M.sweep_optimize, M.minimize_*, M.free_energy_minimize, M.lyapunov.*,
    M.fisher.*, M.localization.covariance, M.covariance.*, M.sparse.*,
    M.variance.reduction, M.pf.systematic_resampling, M.combine_estimator,
    M.statistical.* → O
  M.metropolis*, M.MC_transport, M.gillespie_sample → int.stochastic
  M.wiener.filter, M.smooth_interp, M.kinetic_factor → K.filter
  M.shower.*, M.ps.*, M.sed.*, M.spectrum.synthesis, M.spherical_harmonics.synthesis,
    M.waveform.*, M.toa.reflectance_model, M.partition_functions → G.structured
  M.fem.stiffness, M.superpose, M.lens.deflection, M.microlens_array, M.mixing.linear_model,
    M.pmns.mixing_matrix, M.mol.absorption_xsection → L
  M.eos.*, M.energy.force_field, M.hill.*, M.recoil.*, M.heston.*, M.bs.formula,
    M.merton.*, M.hw.*, M.garch.*, M.arx.*, M.arps.*, M.arbitrage.*, M.dglap.*,
    M.hmm.*, M.felsenstein.*, M.wf.*, M.pkn.*, M.tof.range_equation, M.transit.*,
    M.pid.* → N
  M.support_mask, M.topology_update → B
  M.pseudorange.* → Pi (projection-based geometry)
  M.sensor_crop, M.sample_per_lambda → S
  M.* (anything else not matched) → O.composite_method (conservative fallback)

This is a deliberately heuristic mapping — perfect 1:1 typing of every
domain-specific composite is a multi-month content-authoring exercise. The
heuristic gets ~90% right; the rest fall back to O.composite_method (which
is canonical and not wrong, just less specific). Tier 1/2 promotion will
hand-curate stubs as authors take ownership.

Hash impact: only Tier 3 stubs are affected. L1-003 / L1-004 (the only
on-chain Tier 1 manifests) already use canonical primitives — verified
2026-05-08.

Usage:
    python3 scripts/canonicalize_l1_primitives.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 12 canonical primitives + ASCII fallbacks
CANONICAL_PREFIXES = {
    "D", "∂", "int", "∫", "L", "N", "E", "F", "Pi", "Π", "S", "K", "B", "G", "O"
}


def map_primitive(v: str) -> str:
    """Heuristic map of a non-canonical primitive name to a canonical one.

    Returns the canonical replacement, or v unchanged if already canonical.
    """
    prefix = v.split(".", 1)[0]
    if prefix in CANONICAL_PREFIXES:
        return v

    # Strip the M. prefix (or "integrate." typo) for suffix-based matching
    if v.startswith("M."):
        suffix = v[2:]
    elif v == "integrate.verlet":
        return "D.time.symplectic"
    elif v.startswith("integrate."):
        return "int." + v[10:]
    else:
        suffix = v

    s = suffix.lower()

    # ---- E: Eigensolve / linear algebra ----
    if any(t in s for t in ("eigensolve", "lanczos", "casida", "bse_eigensolve",
                            "bloch_eigensolve", "scf_eigensolve", "dyson_solve",
                            "amplitude_solve", "dh.transformation_matrix",
                            "ss.matrices", "transfer_matrix", "riccati",
                            "partition_functions", "partial_wave", "binodal_compute")):
        return "E.eigensolve"

    # ---- ∂.time variants (most-specific first) ----
    if "verlet" in s or "md_integrate" in s:
        return "D.time.symplectic"
    if "stiff_ode" in s or "coupled_ode" in s:
        return "D.time.implicit"
    if "runge_kutta" in s or "rk4" in s:
        return "D.time.explicit"
    if any(t in s for t in ("time_integrate", "time_evolve", "iv_integrate",
                            "integrate_reactive", "gyro.integration",
                            "node_integrate", "ode.equations_of_motion",
                            "euler.rigid_body", "newton_euler", "rnea.",
                            "lagrange.multiplier_dynamics", "bicycle.lateral",
                            "helix.propagation", "transit.mandel",
                            "lambert.problem", "ode.windkessel", "ode.")):
        return "D.time"
    if s == "integrate":
        return "D.time"

    # ---- ∂.space (PDEs, fluid dynamics, transport) ----
    if any(t in s for t in ("pde.", "ns.incompressible", "swe.", "darcy.",
                            "fractional_flow", "ade.advection_dispersion",
                            "gassmann.fluid", "dirac.wilson", "reynolds.thin_film",
                            "primitive.", "nwp.", "agcm.", "gaussian.plume",
                            "sea_ice.")):
        return "D.space"

    # ---- int.stochastic (Monte Carlo) ----
    if any(t in s for t in ("metropolis", "mc_transport", "gillespie_sample",
                            "stoch")):
        return "int.stochastic"

    # ---- O.iter (self-consistent / coupled / multiphysics) ----
    if any(t in s for t in ("scf", "self_consistent", "coupled", "gummel_coupled",
                            "p2d_couple", "multiphysics", "collocation.",
                            "mpc.prediction", "fem.adjoint", "adjoint.gradient",
                            "transport.adjoint", "bundle.adjustment")):
        return "O.iter"

    # ---- O (general optimize / regularize / estimate) ----
    if any(t in s for t in ("dls.", "sweep_optimize", "minimize_euler",
                            "free_energy_minimize", "lyapunov.", "fisher.",
                            "localization.covariance", "covariance.sample",
                            "sparse.regularization", "variance.reduction",
                            "pf.systematic_resampling", "combine_estimator",
                            "statistical.moment", "topology_update")):
        return "O.regularize"

    # ---- K.filter (shift-invariant filtering) ----
    if any(t in s for t in ("wiener.filter", "smooth_interp", "kinetic_factor")):
        return "K.filter"

    # ---- G.structured (generation / synthesis / templates) ----
    if any(t in s for t in ("shower.em_hadronic", "ps.parton_shower",
                            "sed.salt2", "sed.stellar", "sed.supernova",
                            "spectrum.synthesis", "spherical_harmonics.synthesis",
                            "waveform.ocean_reflection", "toa.reflectance_model",
                            "loss.ionization_synchrotron")):
        return "G.structured"

    # ---- L (other linear operators) ----
    if any(t in s for t in ("fem.stiffness", "superpose", "lens.deflection",
                            "microlens_array", "mixing.linear_model",
                            "pmns.mixing_matrix", "mol.absorption_xsection",
                            "fisher.fisher_matrix", "spc.matrices")):
        return "L.linear_op"

    # ---- N (nonlinear physics / financial / population dynamics) ----
    if any(t in s for t in ("eos.", "energy.force_field", "hill.emax",
                            "recoil.wimp", "heston.characteristic", "bs.formula",
                            "merton.structural", "hw.short_rate", "garch.",
                            "arx.regression", "arps.hyperbolic", "arbitrage.",
                            "dglap.splitting", "hmm.profile", "felsenstein.",
                            "wf.wright_fisher", "pkn.fracture", "tof.range",
                            "pid.transfer_function", "ode.fitzhugh_nagumo",
                            "ode.lotka_volterra", "ode.gompertz", "ode.hodgkin",
                            "ode.seir", "ode.sir", "ode.pbpk", "ode.pk_compartments",
                            "ode.stellar_structure", "rate_theory",
                            "nucleation_coalescence", "free_energy_minimize",
                            "self_energy", "mpm.bedload", "mol.absorption")):
        return "N.pointwise"

    # ---- B (boundary / support / mask) ----
    if any(t in s for t in ("support_mask", "topology_update")):
        return "B.support"

    # ---- Pi / projection (geometry) ----
    if any(t in s for t in ("pseudorange.geometry",)):
        return "Pi.geometry"

    # ---- S (sampling / selection) ----
    if any(t in s for t in ("sensor_crop", "sample_per_lambda",
                            "pileup.area_subtraction")):
        return "S.select"

    # ---- F (special transforms) ----
    if "fft" in s:
        return "F.fft"

    # Conservative fallback: anything genuinely composite that doesn't fit
    # the above gets routed to O.composite_method. This is canonical (O is
    # one of the 12) and not technically wrong — it just declares "this
    # principle uses an iterative composite method that combines several
    # canonical primitives". Hand-curation can refine later.
    return "O.composite_method"


def patch_dag(dag: str, mapping: dict[str, str]) -> str:
    """Substitute primitive names in a `G.dag` string ('A -> B -> C')."""
    if not isinstance(dag, str):
        return dag
    out = dag
    for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        # Match whole-token only — don't substring-match within larger names.
        out = re.sub(r"(?<![\w.])" + re.escape(old) + r"(?![\w.])", new, out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    content_root = repo_root / "pwm-team" / "content"
    genesis_root = repo_root / "pwm-team" / "pwm_product" / "genesis" / "l1"
    files = list(content_root.rglob("L1-*.json")) + list(genesis_root.glob("L1-*.json"))

    files_changed = 0
    vertices_remapped = 0
    distinct_remappings: dict[str, str] = {}

    for path in files:
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        g = m.get("G")
        if not isinstance(g, dict):
            continue

        verts = g.get("vertices") or []
        if not isinstance(verts, list):
            continue

        per_file_mapping: dict[str, str] = {}
        new_verts = []
        any_changed = False
        for v in verts:
            if not isinstance(v, str):
                new_verts.append(v)
                continue
            new_v = map_primitive(v)
            if new_v != v:
                per_file_mapping[v] = new_v
                distinct_remappings[v] = new_v
                vertices_remapped += 1
                any_changed = True
            new_verts.append(new_v)

        if not any_changed:
            continue

        # Patch the DAG string too
        new_dag = patch_dag(g.get("dag", ""), per_file_mapping)
        # Patch arcs (list of "A -> B" strings)
        new_arcs = [patch_dag(a, per_file_mapping) for a in (g.get("arcs") or [])]
        # Patch physics_fingerprint.primitives mirror if present
        pf = m.get("physics_fingerprint") or {}
        new_pf_prims = pf.get("primitives")
        if isinstance(new_pf_prims, list):
            new_pf_prims = [per_file_mapping.get(p, p) for p in new_pf_prims]

        g["vertices"] = new_verts
        g["dag"] = new_dag
        if "arcs" in g:
            g["arcs"] = new_arcs
        if isinstance(new_pf_prims, list):
            pf["primitives"] = new_pf_prims
            m["physics_fingerprint"] = pf

        files_changed += 1
        if not args.dry_run:
            path.write_text(json.dumps(m, indent=2) + "\n")

    print(f"L1 manifests scanned:        {len(files)}")
    print(f"Files modified:              {files_changed}{' (dry-run)' if args.dry_run else ''}")
    print(f"Distinct vertex remappings:  {len(distinct_remappings)}")
    print(f"Total vertex remappings:     {vertices_remapped}")
    print()
    print("=== Remapping summary ===")
    target_counts: dict[str, int] = {}
    for old, new in distinct_remappings.items():
        target_counts[new] = target_counts.get(new, 0) + 1
    for tgt, n in sorted(target_counts.items(), key=lambda kv: -kv[1]):
        print(f"  → {tgt:<30}  ({n} distinct sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
