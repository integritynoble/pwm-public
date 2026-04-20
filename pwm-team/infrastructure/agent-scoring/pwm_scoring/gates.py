"""S1-S4 gate checks — see CLAUDE.md §S1-S4 gates."""
from __future__ import annotations
import numpy as np


# --- S1: dimensional consistency -------------------------------------------

def check_s1(solver_output: np.ndarray, manifest: dict) -> tuple[bool, str]:
    """S1 — output shape / dtype / finiteness match the benchmark manifest.

    The manifest may declare an expected shape in any of:
      - manifest['output_format']['shape'] (list[int] | tuple[int])
      - manifest['expected_shape']
      - manifest['omega_tier'] (fallback: (H, W, N_bands) or (H, W))
    NaN/Inf in the output is always a fail.
    """
    if not isinstance(solver_output, np.ndarray):
        return False, f"solver_output must be np.ndarray, got {type(solver_output).__name__}"
    if not np.all(np.isfinite(solver_output)):
        return False, "solver_output contains NaN/Inf"

    expected = _expected_shape(manifest)
    if expected is None:
        return True, f"shape {solver_output.shape} accepted (no expected shape in manifest)"
    if tuple(solver_output.shape) != tuple(expected):
        return False, f"shape mismatch: expected {tuple(expected)}, got {tuple(solver_output.shape)}"
    return True, f"shape {tuple(solver_output.shape)} matches manifest"


def _expected_shape(manifest: dict):
    fmt = manifest.get("output_format") or {}
    if isinstance(fmt, dict) and "shape" in fmt:
        return tuple(fmt["shape"])
    if "expected_shape" in manifest:
        return tuple(manifest["expected_shape"])
    omega = manifest.get("omega_tier") or manifest.get("omega") or {}
    H, W = omega.get("H"), omega.get("W")
    N = omega.get("N_bands") or omega.get("N")
    if H and W and N:
        return (int(H), int(W), int(N))
    if H and W:
        return (int(H), int(W))
    return None


# --- S2: well-posedness (Hadamard, w.r.t. the parent Principle) ------------

# Method signatures used across the codebase (see cassi.md §2.1):
#   L = linear inverse, T = transformer, O = optimization (TV/ADMM), N = neural/PnP.
# A solver method_sig is a "+"-separated set (order-insensitive) of these letters.
_VALID_METHOD_LETTERS = {"L", "T", "O", "N"}


def check_s2(method_sig: str, principle: dict) -> tuple[bool, str]:
    """S2 — the solver's method signature is admissible under the Principle.

    Principle schema (from cassi.md): principle['well_posedness'] may declare:
      - 'existence':   bool          (solution exists at all)
      - 'uniqueness':  bool          (solution unique without regularization)
      - 'stability':   bool          (continuous in the data)
      - 'allowed_method_sigs': list[str]  (whitelist override)

    If uniqueness is False, direct-inversion-only solvers (method_sig == "L")
    are rejected: an iterative / MAP / regularized method is required.
    """
    if not isinstance(method_sig, str) or not method_sig.strip():
        return False, "method_sig missing or empty"

    letters = {p.strip().upper() for p in method_sig.split("+") if p.strip()}
    unknown = letters - _VALID_METHOD_LETTERS
    if unknown:
        return False, f"unknown method letter(s) {sorted(unknown)}; allowed: {sorted(_VALID_METHOD_LETTERS)}"

    wp = (principle or {}).get("well_posedness", {}) or {}
    allowed = wp.get("allowed_method_sigs")
    if allowed:
        normalized = {"+".join(sorted(s.upper() for s in sig.split("+"))) for sig in allowed}
        provided_norm = "+".join(sorted(letters))
        if provided_norm not in normalized:
            return False, f"method_sig '{method_sig}' not in allowed list {sorted(allowed)}"
        return True, f"method_sig '{method_sig}' in principle whitelist"

    uniqueness = wp.get("uniqueness", True)
    if uniqueness is False and letters == {"L"}:
        return False, "principle.uniqueness=False requires regularization (O/N), not pure L"

    return True, f"method_sig '{method_sig}' admissible under principle"


# --- S3: convergent solver (residual rate across resolutions) --------------

def check_s3(
    residuals: list[float],
    resolutions: list[int],
    min_slope: float = 1.8,
) -> tuple[bool, str]:
    """S3 — solver exhibits O(h^alpha) convergence across resolutions.

    Given residuals r_i at grid spacings h_i = 1 / resolution_i,
    a log-log least-squares fit of log(r) vs log(h) should yield slope ≥ min_slope
    (≈ O(h^2) by default). Residuals must also be strictly positive.
    """
    r = np.asarray(residuals, dtype=np.float64)
    N = np.asarray(resolutions, dtype=np.float64)
    if r.size < 3 or r.size != N.size:
        return False, f"need ≥3 matched (residual, resolution) pairs, got {r.size} and {N.size}"
    if np.any(r <= 0) or np.any(N <= 0):
        return False, "residuals and resolutions must be positive"

    h = 1.0 / N
    log_h = np.log(h)
    log_r = np.log(r)
    slope, _intercept = np.polyfit(log_h, log_r, 1)
    pass_ = bool(slope >= min_slope)
    return pass_, (
        f"log-log slope {slope:.3f} "
        f"{'≥' if pass_ else '<'} threshold {min_slope:.2f}"
    )


# --- S4: bounded error (per-instance PSNR ≥ ε) -----------------------------

def check_s4(psnr_worst: float, epsilon: float) -> tuple[bool, str]:
    """S4 — worst-case PSNR across instances meets the ε threshold."""
    pass_ = psnr_worst >= epsilon
    msg = f"worst PSNR {psnr_worst:.2f} dB {'≥' if pass_ else '<'} ε {epsilon:.2f} dB"
    return pass_, msg
