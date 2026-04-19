"""AST-sandboxed epsilon_fn evaluator."""
from __future__ import annotations
import ast
import math


ALLOWED_NAMES = {"log2": math.log2, "log10": math.log10, "sqrt": math.sqrt,
                 "log": math.log, "exp": math.exp, "abs": abs, "min": min, "max": max}
ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Constant,
    ast.Name, ast.Add, ast.Sub, ast.Mul, ast.Div, ast.Pow, ast.USub,
    ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.IfExp,
)


class EpsilonEvalError(ValueError):
    pass


def eval_epsilon(epsilon_fn_str: str, omega: dict) -> float:
    """
    Evaluate epsilon_fn string with omega dict as variable bindings.
    AST-sandboxed: only math ops + log2/log10/sqrt/exp/abs/min/max allowed.
    No imports, no exec, no attribute access.

    Example:
        eval_epsilon("25.0 + 2.0 * log2(H / 64)", {"H": 256}) → 27.0
    """
    try:
        tree = ast.parse(epsilon_fn_str, mode='eval')
    except SyntaxError as e:
        raise EpsilonEvalError(f"Syntax error in epsilon_fn: {e}") from e

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise EpsilonEvalError(
                f"Disallowed AST node {type(node).__name__} in epsilon_fn"
            )
        if isinstance(node, ast.Name) and node.id not in {**ALLOWED_NAMES, **omega}:
            raise EpsilonEvalError(f"Unknown variable '{node.id}' in epsilon_fn")

    env = {**ALLOWED_NAMES, **{k: float(v) for k, v in omega.items()}}
    try:
        result = eval(compile(tree, "<epsilon_fn>", "eval"), {"__builtins__": {}}, env)
    except Exception as e:
        raise EpsilonEvalError(f"Runtime error in epsilon_fn: {e}") from e

    return float(result)
