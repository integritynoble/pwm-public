"""Tests for pwm_scoring.epsilon — AST-sandboxed threshold evaluator."""
from __future__ import annotations
import math
import pytest

from pwm_scoring.epsilon import eval_epsilon, EpsilonEvalError


class TestEvalEpsilonHappyPath:
    def test_plain_constant(self):
        assert eval_epsilon("28.0", {}) == 28.0

    def test_cassi_log_form(self):
        # from cassi.md: ε(Ω) = 20 + 5 * log2(N/64)
        assert abs(eval_epsilon("20 + 5 * log2(N/64)", {"N": 128}) - 25.0) < 1e-9

    def test_cassi_spatial_form(self):
        assert abs(eval_epsilon("22 + 3 * log2(H*W / 4096)", {"H": 64, "W": 64}) - 22.0) < 1e-9

    def test_log10(self):
        assert abs(eval_epsilon("log10(100)", {}) - 2.0) < 1e-9

    def test_sqrt(self):
        assert abs(eval_epsilon("sqrt(x)", {"x": 9}) - 3.0) < 1e-9

    def test_abs_unary_and_builtin(self):
        assert eval_epsilon("abs(-5)", {}) == 5.0
        assert eval_epsilon("-x", {"x": 3}) == -3.0

    def test_min_max(self):
        assert eval_epsilon("min(a, b)", {"a": 2, "b": 5}) == 2.0
        assert eval_epsilon("max(a, b)", {"a": 2, "b": 5}) == 5.0

    def test_ifexp_conditional(self):
        # eps depends on regime
        assert eval_epsilon("25 if H < 256 else 22", {"H": 128}) == 25.0
        assert eval_epsilon("25 if H < 256 else 22", {"H": 512}) == 22.0

    def test_power_operator(self):
        assert eval_epsilon("2 ** n", {"n": 10}) == 1024.0

    def test_exp(self):
        assert abs(eval_epsilon("exp(0)", {}) - 1.0) < 1e-9

    def test_nested_expression(self):
        # ε = max(20, 25 + 5*log2(H/256))
        v = eval_epsilon("max(20, 25 + 5 * log2(H/256))", {"H": 512})
        assert abs(v - 30.0) < 1e-9


class TestEvalEpsilonSandbox:
    @pytest.mark.parametrize("expr", [
        "__import__('os').system('ls')",
        "open('/etc/passwd').read()",
        "globals()",
        "().__class__.__bases__",
        "x.real",                 # Attribute access forbidden
        "list[0]",                # Subscript forbidden
        "lambda x: x",
        "[1, 2, 3]",
        "{'a': 1}",
        "yield 1",
    ])
    def test_forbidden_ast_nodes(self, expr):
        with pytest.raises(EpsilonEvalError):
            eval_epsilon(expr, {})

    def test_unknown_variable_rejected(self):
        with pytest.raises(EpsilonEvalError):
            eval_epsilon("undefined_var + 1", {})

    def test_syntax_error(self):
        with pytest.raises(EpsilonEvalError):
            eval_epsilon("20 +", {})

    def test_division_by_zero_wrapped(self):
        with pytest.raises(EpsilonEvalError):
            eval_epsilon("1 / x", {"x": 0})

    def test_no_hidden_builtins(self):
        with pytest.raises(EpsilonEvalError):
            eval_epsilon("len(x)", {"x": 10})

    def test_only_declared_omega_accessible(self):
        # only bound omega keys + whitelisted math names
        with pytest.raises(EpsilonEvalError):
            eval_epsilon("math", {})


class TestEvalEpsilonReturnType:
    def test_returns_float(self):
        result = eval_epsilon("20 + 5", {})
        assert isinstance(result, float)

    def test_omega_ints_cast_to_float(self):
        # omega values are forcibly cast to float; integer inputs must still work
        assert eval_epsilon("N / 2", {"N": 5}) == 2.5
