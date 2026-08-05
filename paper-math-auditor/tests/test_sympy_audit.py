from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sympy_audit.py"
SPEC = importlib.util.spec_from_file_location("paper_math_sympy_audit", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def document(claim: dict) -> dict:
    return {"schema": AUDIT.REQUEST_SCHEMA, "claims": [claim]}


class SympyAuditTests(unittest.TestCase):
    def audit(self, claim: dict) -> dict:
        return AUDIT.audit_document(document(claim))["results"][0]

    def test_trigonometric_identity_is_verified(self) -> None:
        result = self.audit(
            {
                "id": "trig",
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "sin(2*x)",
                "rhs": "2*sin(x)*cos(x)",
            }
        )
        self.assertEqual((result["status"], result["verdict"]), ("completed", "verified"))

    def test_exact_sample_refutes_false_identity(self) -> None:
        result = self.audit(
            {
                "id": "false-polynomial",
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "(x+1)**2",
                "rhs": "x**2+1",
                "samples": [{"x": "0"}, {"x": "1"}],
            }
        )
        self.assertEqual(result["verdict"], "refuted")
        self.assertEqual(result["counterexample"]["assignment"], {"x": "1"})
        self.assertEqual(result["counterexample"]["residual"], "2")

    def test_assumptions_change_square_root_result(self) -> None:
        unresolved = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "sqrt(x**2)",
                "rhs": "x",
                "samples": [{"x": "0"}, {"x": "1"}],
            }
        )
        verified = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real", "nonnegative"]},
                "lhs": "sqrt(x**2)",
                "rhs": "x",
            }
        )
        self.assertEqual(unresolved["verdict"], "unresolved")
        self.assertEqual(verified["verdict"], "verified")

    def test_fixed_exact_grid_can_find_a_counterexample(self) -> None:
        result = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "sqrt(x**2)",
                "rhs": "x",
                "search": {"mode": "fixed_grid", "values": ["-1", "0", "1"]},
            }
        )
        self.assertEqual(result["verdict"], "refuted")
        self.assertEqual(result["counterexample"]["assignment"], {"x": "-1"})

    def test_common_domain_is_preserved_after_cancellation(self) -> None:
        result = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "x/x",
                "rhs": "1",
                "samples": [{"x": "0"}, {"x": "1"}],
            }
        )
        self.assertEqual(result["verdict"], "verified")
        self.assertIn("x != 0", result["scope"]["domain_conditions"])
        sample_evidence = next(item for item in result["evidence"] if item["kind"] == "exact_samples")
        self.assertEqual(sample_evidence["samples"][0]["reason"], "OUTSIDE_COMMON_DOMAIN")

    def test_declared_domain_detects_one_sided_undefined_sample(self) -> None:
        result = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "x/x",
                "rhs": "1",
                "domain_policy": "declared_domain",
                "samples": [{"x": "0"}],
            }
        )
        self.assertEqual(result["verdict"], "refuted")
        self.assertFalse(result["counterexample"]["both_sides_defined"])

    def test_derivative_is_checked_independently(self) -> None:
        result = self.audit(
            {
                "operation": "derivative",
                "symbols": {"theta": ["real"]},
                "expression": "log(1 + exp(-theta))",
                "variable": "theta",
                "claimed": "-1 / (1 + exp(theta))",
            }
        )
        self.assertEqual(result["verdict"], "verified")
        self.assertIn("derived", result["parsed"])

    def test_matrix_dimension_states_are_distinguished(self) -> None:
        verified = self.audit(
            {
                "operation": "matrix_product",
                "left": "X",
                "right": "W",
                "matrices": {"X": ["n", "d"], "W": ["d", "k"]},
            }
        )
        unresolved = self.audit(
            {
                "operation": "matrix_product",
                "left": "X",
                "right": "W",
                "matrices": {"X": ["n", "d"], "W": ["q", "k"]},
            }
        )
        refuted = self.audit(
            {
                "operation": "matrix_product",
                "left": "X",
                "right": "W",
                "matrices": {"X": ["n", "d"], "W": ["q", "k"]},
                "unequal_dimensions": [["d", "q"]],
            }
        )
        self.assertEqual(verified["verdict"], "verified")
        self.assertEqual(unresolved["verdict"], "unresolved")
        self.assertEqual(refuted["verdict"], "refuted")

    def test_unsafe_or_inexact_syntax_is_rejected_without_verdict(self) -> None:
        unsafe = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "__import__('os')",
                "rhs": "x",
            }
        )
        float_literal = self.audit(
            {
                "operation": "identity",
                "symbols": {"x": ["real"]},
                "lhs": "x + 0.1",
                "rhs": "x",
            }
        )
        self.assertEqual((unsafe["status"], unsafe["verdict"]), ("rejected", None))
        self.assertEqual(unsafe["diagnostics"][0]["code"], "UNSUPPORTED_SYNTAX")
        self.assertEqual(float_literal["diagnostics"][0]["code"], "NONEXACT_LITERAL")


if __name__ == "__main__":
    unittest.main()
