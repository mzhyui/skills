#!/usr/bin/env python3
"""Safely audit small exact mathematical claims with SymPy.

This is intentionally a narrow backend for the Paper Math Auditor skill.  It
accepts JSON only, uses a restricted AST rather than eval-like SymPy parsers,
and returns tri-state mathematical verdicts.  It is not a theorem prover.
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
import multiprocessing as mp
import queue
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

try:
    import sympy as sp
except ImportError:  # pragma: no cover - exercised by the CLI boundary
    sp = None  # type: ignore[assignment]


REQUEST_SCHEMA = "paper-math-audit/request/v1"
RESULT_SCHEMA = "paper-math-audit/result/v1"
PROFILE = "safe-v1"
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
DIMENSION = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
ALLOWED_ASSUMPTIONS = {
    "real",
    "integer",
    "positive",
    "nonnegative",
    "negative",
    "nonpositive",
    "nonzero",
}


@dataclass(frozen=True)
class Limits:
    max_input_bytes: int = 1_000_000
    max_claims: int = 50
    max_symbols: int = 8
    max_samples: int = 128
    max_expression_chars: int = 512
    max_ast_nodes: int = 128
    max_ast_depth: int = 32
    max_integer_abs: int = 1_000_000
    max_power_abs: int = 16
    max_grid_combinations: int = 256
    max_transform_nodes: int = 2_000
    max_output_bytes: int = 2_000_000


SAFE_DEFAULTS = Limits()


class AuditInputError(ValueError):
    """A controlled rejection of a request or restricted expression."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DomainCondition:
    kind: str
    expression: Any

    def text(self) -> str:
        relation = {"nonzero": "!= 0", "positive": "> 0", "nonnegative": ">= 0"}[self.kind]
        return f"{sp.sstr(self.expression)} {relation}"


class RestrictedParser:
    """Parse a deliberately small, exact scalar-expression language."""

    FUNCTIONS: Mapping[str, Callable[[Any], Any]] = {
        "sin": lambda value: sp.sin(value),
        "cos": lambda value: sp.cos(value),
        "tan": lambda value: sp.tan(value),
        "exp": lambda value: sp.exp(value),
        "log": lambda value: sp.log(value),
        "sqrt": lambda value: sp.sqrt(value),
        "Abs": lambda value: sp.Abs(value),
    }
    CONSTANTS: Mapping[str, Any] = {"pi": sp.pi if sp else None, "E": sp.E if sp else None}

    def __init__(self, symbols: Mapping[str, Any], limits: Limits) -> None:
        self.symbols = symbols
        self.limits = limits
        self.conditions: list[DomainCondition] = []

    def parse(self, text: Any) -> Any:
        if not isinstance(text, str):
            raise AuditInputError("EXPRESSION_NOT_STRING", "An expression must be a string.")
        if not text.strip():
            raise AuditInputError("EMPTY_EXPRESSION", "An expression cannot be empty.")
        if len(text) > self.limits.max_expression_chars:
            raise AuditInputError("INPUT_LIMIT", "An expression exceeds the character limit.")
        try:
            tree = ast.parse(text, mode="eval")
        except SyntaxError as error:
            raise AuditInputError("UNSUPPORTED_SYNTAX", "The expression is not valid restricted syntax.") from error

        nodes = list(ast.walk(tree))
        if len(nodes) > self.limits.max_ast_nodes or self._depth(tree) > self.limits.max_ast_depth:
            raise AuditInputError("INPUT_LIMIT", "The expression exceeds the AST complexity limit.")
        return self._visit(tree.body)

    def _depth(self, node: ast.AST) -> int:
        children = list(ast.iter_child_nodes(node))
        return 1 + max((self._depth(child) for child in children), default=0)

    def _visit(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                raise AuditInputError("UNSUPPORTED_LITERAL", "Boolean literals are not allowed.")
            if isinstance(node.value, int):
                if abs(node.value) > self.limits.max_integer_abs:
                    raise AuditInputError("INPUT_LIMIT", "An integer literal exceeds the configured limit.")
                return sp.Integer(node.value)
            if isinstance(node.value, float):
                raise AuditInputError("NONEXACT_LITERAL", "Float literals are not allowed; use an exact rational expression.")
            raise AuditInputError("UNSUPPORTED_LITERAL", "Only exact integer literals are allowed.")

        if isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise AuditInputError("UNSUPPORTED_SYNTAX", "Dunder names are not allowed.")
            if node.id in self.symbols:
                return self.symbols[node.id]
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[node.id]
            raise AuditInputError("UNDECLARED_SYMBOL", f"'{node.id}' is not a declared symbol or allowed constant.")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else sp.Mul(-1, value, evaluate=False)

        if isinstance(node, ast.BinOp):
            left = self._visit(node.left)
            right = self._visit(node.right)
            if isinstance(node.op, ast.Add):
                return sp.Add(left, right, evaluate=False)
            if isinstance(node.op, ast.Sub):
                return sp.Add(left, sp.Mul(-1, right, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Mult):
                return sp.Mul(left, right, evaluate=False)
            if isinstance(node.op, ast.Div):
                self.conditions.append(DomainCondition("nonzero", right))
                return sp.Mul(left, sp.Pow(right, -1, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Pow):
                if not getattr(right, "is_Integer", False):
                    raise AuditInputError("UNSUPPORTED_POWER", "Only exact integer exponents are allowed.")
                exponent = int(right)
                if abs(exponent) > self.limits.max_power_abs:
                    raise AuditInputError("INPUT_LIMIT", "The exponent exceeds the configured limit.")
                if exponent < 0:
                    self.conditions.append(DomainCondition("nonzero", left))
                return sp.Pow(left, right, evaluate=False)
            raise AuditInputError("UNSUPPORTED_SYNTAX", "Only +, -, *, /, and ** are allowed operators.")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.keywords or len(node.args) != 1:
                raise AuditInputError("UNSUPPORTED_SYNTAX", "Only one-argument calls to allowed functions are permitted.")
            if node.func.id.startswith("__"):
                raise AuditInputError("UNSUPPORTED_SYNTAX", "Dunder calls are not allowed.")
            if node.func.id not in self.FUNCTIONS:
                raise AuditInputError("UNSUPPORTED_FUNCTION", f"'{node.func.id}' is not an allowed function.")
            argument = self._visit(node.args[0])
            if node.func.id == "log":
                self.conditions.append(DomainCondition("positive", argument))
            elif node.func.id == "sqrt":
                self.conditions.append(DomainCondition("nonnegative", argument))
            elif node.func.id == "tan":
                self.conditions.append(DomainCondition("nonzero", sp.cos(argument)))
            return self.FUNCTIONS[node.func.id](argument)

        raise AuditInputError("UNSUPPORTED_SYNTAX", "The expression contains unsupported syntax.")


def _claim_identifier(claim: Any, index: int | None = None) -> str:
    if isinstance(claim, Mapping) and isinstance(claim.get("id"), str) and claim["id"]:
        return claim["id"]
    return f"claim-{index + 1}" if index is not None else "claim"


def _deduplicate_conditions(conditions: Iterable[DomainCondition]) -> list[DomainCondition]:
    result: list[DomainCondition] = []
    seen: set[tuple[str, str]] = set()
    for condition in conditions:
        key = (condition.kind, sp.srepr(condition.expression))
        if key not in seen:
            seen.add(key)
            result.append(condition)
    return result


def _build_symbols(raw_symbols: Any, limits: Limits) -> tuple[dict[str, Any], dict[str, list[str]]]:
    if raw_symbols is None:
        raw_symbols = {}
    if not isinstance(raw_symbols, Mapping):
        raise AuditInputError("INVALID_SYMBOLS", "'symbols' must be an object mapping names to assumption lists.")
    if len(raw_symbols) > limits.max_symbols:
        raise AuditInputError("INPUT_LIMIT", "The request has too many declared symbols.")

    symbols: dict[str, Any] = {}
    ledger: dict[str, list[str]] = {}
    reserved = set(RestrictedParser.FUNCTIONS) | set(RestrictedParser.CONSTANTS)
    for name, assumptions in raw_symbols.items():
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name in reserved or name.startswith("__"):
            raise AuditInputError("INVALID_SYMBOL", "Each symbol must be a non-reserved ASCII identifier.")
        if not isinstance(assumptions, list) or not all(isinstance(item, str) for item in assumptions):
            raise AuditInputError("INVALID_ASSUMPTIONS", f"Assumptions for '{name}' must be a list of strings.")
        if len(set(assumptions)) != len(assumptions) or any(item not in ALLOWED_ASSUMPTIONS for item in assumptions):
            raise AuditInputError("INVALID_ASSUMPTIONS", f"'{name}' has an unsupported or duplicate assumption.")
        try:
            symbols[name] = sp.Symbol(name, **{item: True for item in assumptions})
        except (TypeError, ValueError) as error:
            raise AuditInputError("INCONSISTENT_ASSUMPTIONS", f"Assumptions for '{name}' are inconsistent.") from error
        ledger[name] = sorted(assumptions)
    return symbols, ledger


def _parse_exact_value(value: Any, limits: Limits) -> Any:
    parser = RestrictedParser({}, limits)
    parsed = parser.parse(value)
    parsed = sp.simplify(parsed)
    if parsed.free_symbols or parsed.has(sp.Float) or parsed.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise AuditInputError("NONEXACT_LITERAL", "Samples must be finite, exact expressions without symbols.")
    return parsed


def _normalise_samples(raw_claim: Mapping[str, Any], symbol_names: list[str], limits: Limits) -> list[tuple[str, dict[str, Any]]]:
    raw_samples = raw_claim.get("samples", [])
    if not isinstance(raw_samples, list):
        raise AuditInputError("INVALID_SAMPLES", "'samples' must be a list of assignment objects.")
    if len(raw_samples) > limits.max_samples:
        raise AuditInputError("INPUT_LIMIT", "The request has too many supplied samples.")
    samples: list[tuple[str, dict[str, Any]]] = []
    for raw_sample in raw_samples:
        if not isinstance(raw_sample, Mapping):
            raise AuditInputError("INVALID_SAMPLES", "Each sample must be an object.")
        assignment: dict[str, Any] = {}
        for name, value in raw_sample.items():
            if name not in symbol_names:
                raise AuditInputError("UNKNOWN_SAMPLE_SYMBOL", f"Sample assigns undeclared symbol '{name}'.")
            assignment[name] = _parse_exact_value(value, limits)
        samples.append(("provided", assignment))

    search = raw_claim.get("search", {"mode": "provided_only"})
    if not isinstance(search, Mapping) or not isinstance(search.get("mode", "provided_only"), str):
        raise AuditInputError("INVALID_SEARCH", "'search' must be an object with a string 'mode'.")
    mode = search.get("mode", "provided_only")
    if mode == "provided_only":
        return samples
    if mode != "fixed_grid":
        raise AuditInputError("UNSUPPORTED_SEARCH", "Only 'provided_only' and 'fixed_grid' searches are supported.")
    raw_values = search.get("values", ["-2", "-1", "0", "1", "2"])
    if not isinstance(raw_values, list) or not raw_values:
        raise AuditInputError("INVALID_SEARCH", "A fixed grid needs a non-empty 'values' list.")
    values = [_parse_exact_value(value, limits) for value in raw_values]
    combinations = len(values) ** len(symbol_names)
    if combinations > limits.max_grid_combinations:
        raise AuditInputError("INPUT_LIMIT", "The fixed grid exceeds the combination limit.")
    for values_tuple in itertools.product(values, repeat=len(symbol_names)):
        samples.append(("fixed_grid", dict(zip(sorted(symbol_names), values_tuple))))
    if len(samples) > limits.max_samples + limits.max_grid_combinations:
        raise AuditInputError("INPUT_LIMIT", "The generated sample count exceeds the limit.")
    return samples


def _predicate(kind: str, expression: Any) -> Any:
    return getattr(sp.Q, kind)(expression)


def _condition_holds(condition: DomainCondition, substitutions: Mapping[Any, Any] | None = None) -> bool:
    expression = condition.expression
    if substitutions:
        expression = sp.simplify(expression.subs(substitutions))
    return sp.ask(_predicate(condition.kind, expression)) is True


def _assumptions_hold(symbols: Mapping[str, Any], ledger: Mapping[str, list[str]], assignment: Mapping[str, Any]) -> tuple[bool, str | None]:
    for name, symbol in symbols.items():
        if name not in assignment:
            return False, f"MISSING_SYMBOL:{name}"
        value = assignment[name]
        for assumption in ledger[name]:
            if sp.ask(_predicate(assumption, value)) is not True:
                return False, f"ASSUMPTION_NOT_SATISFIED:{name}:{assumption}"
    return True, None


def _is_finite_exact(expression: Any) -> bool:
    return not expression.has(sp.Float, sp.nan, sp.zoo, sp.oo, -sp.oo) and expression.is_finite is not False


def _expression_is_defined(expression: Any, conditions: Iterable[DomainCondition], substitutions: Mapping[Any, Any]) -> bool:
    if not all(_condition_holds(condition, substitutions) for condition in conditions):
        return False
    value = sp.simplify(expression.subs(substitutions))
    return _is_finite_exact(value)


def _transform_residual(residual: Any, limits: Limits) -> tuple[Any, list[str], list[dict[str, str]]]:
    transforms: list[tuple[str, Callable[[Any], Any]]] = [
        ("together", sp.together),
        ("cancel", sp.cancel),
        ("factor", sp.factor),
        ("trigsimp", sp.trigsimp),
        ("simplify", sp.simplify),
    ]
    current = residual
    applied: list[str] = []
    diagnostics: list[dict[str, str]] = []
    for name, transform in transforms:
        try:
            candidate = transform(current)
        except (TypeError, ValueError, NotImplementedError, RuntimeError) as error:
            diagnostics.append({"code": "TRANSFORM_SKIPPED", "message": f"{name}: {type(error).__name__}"})
            continue
        if sum(1 for _ in sp.preorder_traversal(candidate)) > limits.max_transform_nodes:
            raise AuditInputError("RESOURCE_LIMIT", f"{name} exceeded the transformed-expression node limit.")
        current = candidate
        applied.append(name)
        if current == sp.S.Zero or current.is_zero is True:
            break
    return current, applied, diagnostics


def _base_result(claim: Mapping[str, Any], operation: str, status: str, verdict: str | None) -> dict[str, Any]:
    return {
        "id": _claim_identifier(claim),
        "location": claim.get("location") if isinstance(claim.get("location"), str) else None,
        "operation": operation,
        "status": status,
        "verdict": verdict,
        "scope": {},
        "parsed": {},
        "normalization": {},
        "evidence": [],
        "counterexample": None,
        "diagnostics": [],
    }


def _rejected_result(claim: Any, error: AuditInputError, index: int | None = None) -> dict[str, Any]:
    safe_claim = claim if isinstance(claim, Mapping) else {}
    result = _base_result(safe_claim, str(safe_claim.get("operation", "unknown")), "rejected", None)
    result["id"] = _claim_identifier(claim, index)
    result["diagnostics"] = [{"code": error.code, "message": error.message}]
    return result


def _evaluate_samples(
    lhs: Any,
    rhs: Any,
    lhs_conditions: list[DomainCondition],
    rhs_conditions: list[DomainCondition],
    symbols: Mapping[str, Any],
    ledger: Mapping[str, list[str]],
    raw_claim: Mapping[str, Any],
    policy: str,
    limits: Limits,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    tested: list[dict[str, Any]] = []
    samples = _normalise_samples(raw_claim, list(symbols), limits)
    for source, assignment_by_name in samples:
        admissible, reason = _assumptions_hold(symbols, ledger, assignment_by_name)
        printable_assignment = {name: sp.sstr(value) for name, value in sorted(assignment_by_name.items())}
        if not admissible:
            tested.append({"source": source, "assignment": printable_assignment, "status": "skipped", "reason": reason})
            continue
        substitutions = {symbols[name]: value for name, value in assignment_by_name.items()}
        lhs_defined = _expression_is_defined(lhs, lhs_conditions, substitutions)
        rhs_defined = _expression_is_defined(rhs, rhs_conditions, substitutions)
        if policy == "declared_domain" and lhs_defined != rhs_defined:
            return (
                {
                    "assignment": printable_assignment,
                    "residual": None,
                    "assumptions_satisfied": True,
                    "both_sides_defined": False,
                    "reason": "The two original expressions have different domains at this declared-domain sample.",
                },
                tested,
            )
        if not (lhs_defined and rhs_defined):
            tested.append(
                {
                    "source": source,
                    "assignment": printable_assignment,
                    "status": "skipped",
                    "reason": "OUTSIDE_COMMON_DOMAIN",
                }
            )
            continue
        value = sp.simplify(lhs.subs(substitutions) - rhs.subs(substitutions))
        if not _is_finite_exact(value):
            tested.append({"source": source, "assignment": printable_assignment, "status": "skipped", "reason": "NONFINITE_RESULT"})
            continue
        if value.is_zero is False:
            return (
                {
                    "assignment": printable_assignment,
                    "residual": sp.sstr(value),
                    "assumptions_satisfied": True,
                    "both_sides_defined": True,
                    "reason": "An exact in-domain substitution has nonzero residual.",
                },
                tested,
            )
        tested.append(
            {
                "source": source,
                "assignment": printable_assignment,
                "status": "used",
                "residual": sp.sstr(value),
            }
        )
    return None, tested


def _audit_equality(
    claim: Mapping[str, Any],
    operation: str,
    lhs: Any,
    rhs: Any,
    lhs_conditions: list[DomainCondition],
    rhs_conditions: list[DomainCondition],
    symbols: Mapping[str, Any],
    ledger: Mapping[str, list[str]],
    parsed: Mapping[str, str],
    limits: Limits,
    extra_diagnostics: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    policy = claim.get("domain_policy", "common_defined_domain")
    if policy not in {"common_defined_domain", "declared_domain"}:
        raise AuditInputError("INVALID_DOMAIN_POLICY", "domain_policy must be common_defined_domain or declared_domain.")

    result = _base_result(claim, operation, "completed", "unresolved")
    all_conditions = _deduplicate_conditions([*lhs_conditions, *rhs_conditions])
    result["scope"] = {
        "assumptions": ledger,
        "domain_policy": policy,
        "domain_conditions": [condition.text() for condition in all_conditions],
    }
    result["parsed"] = dict(parsed)
    if extra_diagnostics:
        result["diagnostics"].extend(extra_diagnostics)

    residual = sp.Add(lhs, sp.Mul(-1, rhs, evaluate=False), evaluate=False)
    final_residual, transforms, transform_diagnostics = _transform_residual(residual, limits)
    result["normalization"] = {
        "initial_residual": sp.sstr(residual),
        "final_residual": sp.sstr(final_residual),
        "transforms": transforms,
    }
    result["diagnostics"].extend(transform_diagnostics)
    symbolic_zero = final_residual == sp.S.Zero or final_residual.is_zero is True

    counterexample, tested_samples = _evaluate_samples(
        lhs, rhs, lhs_conditions, rhs_conditions, symbols, ledger, claim, policy, limits
    )
    if tested_samples:
        result["evidence"].append({"kind": "exact_samples", "samples": tested_samples})
    if counterexample is not None:
        result["verdict"] = "refuted"
        result["counterexample"] = counterexample
        result["evidence"].append({"kind": "exact_counterexample"})
        return result

    unproved_conditions = [condition for condition in all_conditions if not _condition_holds(condition)]
    if symbolic_zero and (policy == "common_defined_domain" or not unproved_conditions):
        result["verdict"] = "verified"
        result["evidence"].append({"kind": "symbolic_zero"})
    elif symbolic_zero:
        result["diagnostics"].append(
            {
                "code": "DOMAIN_NOT_ENTAILED",
                "message": "The residual is zero only after conditions not entailed by the declared assumptions.",
            }
        )
    else:
        result["diagnostics"].append(
            {
                "code": "SYMBOLIC_UNRESOLVED",
                "message": "No exact symbolic zero or exact admissible counterexample was established.",
            }
        )
    return result


def _audit_identity(claim: Mapping[str, Any], limits: Limits) -> dict[str, Any]:
    if claim.get("relation", "=") != "=":
        raise AuditInputError("UNSUPPORTED_RELATION", "The exact identity backend supports only relation '='.")
    symbols, ledger = _build_symbols(claim.get("symbols", {}), limits)
    lhs_parser = RestrictedParser(symbols, limits)
    lhs = lhs_parser.parse(claim.get("lhs"))
    rhs_parser = RestrictedParser(symbols, limits)
    rhs = rhs_parser.parse(claim.get("rhs"))
    return _audit_equality(
        claim,
        "identity",
        lhs,
        rhs,
        lhs_parser.conditions,
        rhs_parser.conditions,
        symbols,
        ledger,
        {"lhs": sp.sstr(lhs), "rhs": sp.sstr(rhs)},
        limits,
    )


def _audit_derivative(claim: Mapping[str, Any], limits: Limits) -> dict[str, Any]:
    if claim.get("relation", "=") != "=":
        raise AuditInputError("UNSUPPORTED_RELATION", "The derivative backend supports only relation '='.")
    symbols, ledger = _build_symbols(claim.get("symbols", {}), limits)
    variable_name = claim.get("variable")
    if not isinstance(variable_name, str) or variable_name not in symbols:
        raise AuditInputError("INVALID_VARIABLE", "'variable' must name a declared symbol.")
    expression_parser = RestrictedParser(symbols, limits)
    expression = expression_parser.parse(claim.get("expression"))
    claimed_parser = RestrictedParser(symbols, limits)
    claimed = claimed_parser.parse(claim.get("claimed"))
    try:
        derived = sp.diff(expression, symbols[variable_name])
    except (TypeError, ValueError, NotImplementedError) as error:
        raise AuditInputError("DERIVATIVE_UNAVAILABLE", "SymPy could not derive this restricted expression.") from error
    return _audit_equality(
        claim,
        "derivative",
        derived,
        claimed,
        expression_parser.conditions,
        claimed_parser.conditions,
        symbols,
        ledger,
        {"expression": sp.sstr(expression), "derived": sp.sstr(derived), "claimed": sp.sstr(claimed)},
        limits,
        [
            {
                "code": "FORMAL_DERIVATIVE_SCOPE",
                "message": "This checks SymPy's formal derivative, not all analytic differentiability conditions.",
            }
        ],
    )


class _UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def _dimension_label(value: Any) -> str:
    if isinstance(value, int) and value > 0:
        return str(value)
    if isinstance(value, str) and (value.isdigit() or DIMENSION.fullmatch(value)):
        if value.isdigit() and int(value) <= 0:
            raise AuditInputError("INVALID_DIMENSION", "Numeric dimensions must be positive.")
        return value
    raise AuditInputError("INVALID_DIMENSION", "A dimension must be a positive integer or an ASCII label.")


def _dimension_pairs(raw_pairs: Any, field: str) -> list[tuple[str, str]]:
    if raw_pairs is None:
        return []
    if not isinstance(raw_pairs, list):
        raise AuditInputError("INVALID_DIMENSION_FACTS", f"'{field}' must be a list of pairs.")
    pairs: list[tuple[str, str]] = []
    for pair in raw_pairs:
        if not isinstance(pair, list) or len(pair) != 2:
            raise AuditInputError("INVALID_DIMENSION_FACTS", f"Every '{field}' item must be a two-element array.")
        pairs.append((_dimension_label(pair[0]), _dimension_label(pair[1])))
    return pairs


def _pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _audit_matrix_product(claim: Mapping[str, Any], limits: Limits) -> dict[str, Any]:
    del limits  # Matrix contracts are bounded by the fixed rank-two schema.
    left_name, right_name = claim.get("left"), claim.get("right")
    matrices = claim.get("matrices")
    if not isinstance(left_name, str) or not isinstance(right_name, str) or not isinstance(matrices, Mapping):
        raise AuditInputError("INVALID_MATRIX_PRODUCT", "matrix_product needs string left/right names and a matrices object.")
    if left_name not in matrices or right_name not in matrices:
        raise AuditInputError("UNKNOWN_MATRIX", "Both product operands must appear in 'matrices'.")

    shapes: dict[str, list[str]] = {}
    for name, raw_shape in matrices.items():
        if not isinstance(name, str) or not isinstance(raw_shape, list) or len(raw_shape) != 2:
            raise AuditInputError("INVALID_MATRIX_SHAPE", "Every declared matrix must have a rank-two shape.")
        shapes[name] = [_dimension_label(value) for value in raw_shape]

    equal_pairs = _dimension_pairs(claim.get("equal_dimensions", []), "equal_dimensions")
    unequal_pairs = _dimension_pairs(claim.get("unequal_dimensions", []), "unequal_dimensions")
    all_dimensions = {dimension for shape in shapes.values() for dimension in shape}
    for left, right in [*equal_pairs, *unequal_pairs]:
        all_dimensions.update((left, right))
    equivalent = _UnionFind(all_dimensions)
    for left, right in equal_pairs:
        equivalent.union(left, right)
    unequal = {_pair_key(left, right) for left, right in unequal_pairs}
    if any(equivalent.find(left) == equivalent.find(right) for left, right in unequal_pairs):
        raise AuditInputError("CONTRADICTORY_DIMENSION_FACTS", "An unequal pair is also declared equal.")

    left_shape, right_shape = shapes[left_name], shapes[right_name]
    contracted = (left_shape[1], right_shape[0])
    computed_shape = [left_shape[0], right_shape[1]]
    result = _base_result(claim, "matrix_product", "completed", "unresolved")
    result["scope"] = {"equal_dimensions": [list(pair) for pair in equal_pairs], "unequal_dimensions": [list(pair) for pair in unequal_pairs]}
    result["parsed"] = {"left": left_name, "right": right_name, "left_shape": left_shape, "right_shape": right_shape}
    result["normalization"] = {"computed_shape": computed_shape, "contracted_dimensions": list(contracted)}

    if equivalent.find(contracted[0]) == equivalent.find(contracted[1]):
        result["verdict"] = "verified"
        result["evidence"].append({"kind": "compatible_matrix_contract"})
    elif _pair_key(*contracted) in unequal:
        result["verdict"] = "refuted"
        result["counterexample"] = {"reason": f"Contracted dimensions {contracted[0]} and {contracted[1]} are explicitly unequal."}
    else:
        result["diagnostics"].append(
            {"code": "MISSING_DIMENSION_EQUALITY", "message": f"Require {contracted[0]} = {contracted[1]} for this product."}
        )
    return result


def audit_claim(claim: Any, limits: Limits = SAFE_DEFAULTS, index: int | None = None) -> dict[str, Any]:
    if not isinstance(claim, Mapping):
        return _rejected_result(claim, AuditInputError("INVALID_CLAIM", "Each claim must be an object."), index)
    try:
        operation = claim.get("operation")
        if operation == "identity":
            return _audit_identity(claim, limits)
        if operation == "derivative":
            return _audit_derivative(claim, limits)
        if operation == "matrix_product":
            return _audit_matrix_product(claim, limits)
        raise AuditInputError("UNSUPPORTED_OPERATION", "operation must be identity, derivative, or matrix_product.")
    except AuditInputError as error:
        return _rejected_result(claim, error, index)
    except Exception as error:  # Keep a backend crash separate from a math verdict.
        result = _base_result(claim, str(claim.get("operation", "unknown")), "backend_error", None)
        result["diagnostics"] = [{"code": "BACKEND_ERROR", "message": type(error).__name__}]
        return result


def _worker(claim: Any, limits: Limits, index: int, result_queue: Any) -> None:
    result_queue.put(audit_claim(claim, limits, index))


def _audit_claim_with_timeout(claim: Any, limits: Limits, index: int, timeout_ms: int) -> dict[str, Any]:
    context = mp.get_context("spawn")
    result_queue = context.Queue(maxsize=1)
    process = context.Process(target=_worker, args=(claim, limits, index, result_queue))
    process.start()
    process.join(timeout_ms / 1000)
    if process.is_alive():
        process.terminate()
        process.join()
        safe_claim = claim if isinstance(claim, Mapping) else {}
        result = _base_result(safe_claim, str(safe_claim.get("operation", "unknown")), "resource_limited", None)
        result["id"] = _claim_identifier(claim, index)
        result["diagnostics"] = [{"code": "TIMEOUT", "message": f"Claim exceeded {timeout_ms} ms."}]
        return result
    try:
        return result_queue.get(timeout=0.25)
    except queue.Empty:
        safe_claim = claim if isinstance(claim, Mapping) else {}
        result = _base_result(safe_claim, str(safe_claim.get("operation", "unknown")), "backend_error", None)
        result["id"] = _claim_identifier(claim, index)
        result["diagnostics"] = [{"code": "WORKER_NO_RESULT", "message": "The symbolic worker exited without a result."}]
        return result
    finally:
        result_queue.close()


def _validate_document(document: Any, limits: Limits) -> list[Any]:
    if not isinstance(document, Mapping):
        raise AuditInputError("INVALID_DOCUMENT", "The request root must be an object.")
    if document.get("schema") != REQUEST_SCHEMA:
        raise AuditInputError("INVALID_SCHEMA", f"schema must be '{REQUEST_SCHEMA}'.")
    claims = document.get("claims")
    if not isinstance(claims, list) or not claims:
        raise AuditInputError("INVALID_CLAIMS", "'claims' must be a non-empty list.")
    if len(claims) > limits.max_claims:
        raise AuditInputError("INPUT_LIMIT", "The request contains too many claims.")
    return claims


def audit_document(document: Mapping[str, Any], *, limits: Limits = SAFE_DEFAULTS, timeout_ms: int | None = None) -> dict[str, Any]:
    """Return JSON-serializable audit results for a validated request object."""
    if sp is None:
        return {
            "schema": RESULT_SCHEMA,
            "engine": {"name": "sympy-audit", "profile": PROFILE, "sympy_version": None},
            "status": "backend_unavailable",
            "diagnostics": [{"code": "SYMPY_UNAVAILABLE", "message": "SymPy could not be imported."}],
            "results": [],
            "summary": {"verified": 0, "refuted": 0, "unresolved": 0, "not_completed": 0},
        }
    claims = _validate_document(document, limits)
    results = [
        _audit_claim_with_timeout(claim, limits, index, timeout_ms) if timeout_ms is not None else audit_claim(claim, limits, index)
        for index, claim in enumerate(claims)
    ]
    summary = {
        "verified": sum(result["verdict"] == "verified" for result in results),
        "refuted": sum(result["verdict"] == "refuted" for result in results),
        "unresolved": sum(result["verdict"] == "unresolved" for result in results),
        "not_completed": sum(result["status"] != "completed" for result in results),
    }
    return {
        "schema": RESULT_SCHEMA,
        "engine": {"name": "sympy-audit", "profile": PROFILE, "sympy_version": sp.__version__},
        "limits": asdict(limits),
        "results": results,
        "summary": summary,
    }


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditInputError("DUPLICATE_JSON_KEY", f"Duplicate JSON key '{key}'.")
        result[key] = value
    return result


def _load_document(path: str, limits: Limits) -> Mapping[str, Any]:
    raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    if len(raw) > limits.max_input_bytes:
        raise AuditInputError("INPUT_LIMIT", "The JSON request exceeds the byte limit.")
    try:
        document = json.loads(raw, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as error:
        raise AuditInputError("INVALID_JSON", "The input is not valid JSON.") from error
    if not isinstance(document, Mapping):
        raise AuditInputError("INVALID_DOCUMENT", "The request root must be an object.")
    return document


def _write_report(report: Mapping[str, Any], path: str, limits: Limits) -> None:
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if len(encoded.encode("utf-8")) > limits.max_output_bytes:
        raise AuditInputError("OUTPUT_LIMIT", "The generated report exceeds the byte limit.")
    if path == "-":
        sys.stdout.write(encoded)
    else:
        Path(path).write_text(encoded, encoding="utf-8")


def _self_test() -> dict[str, Any]:
    cases = [
        (
            "trigonometric identity",
            {
                "schema": REQUEST_SCHEMA,
                "claims": [
                    {
                        "id": "trig",
                        "operation": "identity",
                        "symbols": {"x": ["real"]},
                        "lhs": "sin(2*x)",
                        "rhs": "2*sin(x)*cos(x)",
                    }
                ],
            },
            "verified",
        ),
        (
            "exact counterexample",
            {
                "schema": REQUEST_SCHEMA,
                "claims": [
                    {
                        "id": "polynomial",
                        "operation": "identity",
                        "symbols": {"x": ["real"]},
                        "lhs": "(x+1)**2",
                        "rhs": "x**2+1",
                        "samples": [{"x": "0"}, {"x": "1"}],
                    }
                ],
            },
            "refuted",
        ),
        (
            "assumption-sensitive square root",
            {
                "schema": REQUEST_SCHEMA,
                "claims": [
                    {
                        "id": "sqrt",
                        "operation": "identity",
                        "symbols": {"x": ["real"]},
                        "lhs": "sqrt(x**2)",
                        "rhs": "x",
                        "samples": [{"x": "0"}, {"x": "1"}],
                    }
                ],
            },
            "unresolved",
        ),
        (
            "matrix contract",
            {
                "schema": REQUEST_SCHEMA,
                "claims": [
                    {
                        "id": "matrix",
                        "operation": "matrix_product",
                        "left": "X",
                        "right": "W",
                        "matrices": {"X": ["n", "d"], "W": ["d", "k"]},
                    }
                ],
            },
            "verified",
        ),
    ]
    results = []
    for name, document, expected in cases:
        report = audit_document(document)
        actual = report["results"][0]["verdict"]
        results.append({"name": name, "expected": expected, "actual": actual, "passed": actual == expected})
    return {"self_test": results, "passed": all(item["passed"] for item in results)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit small exact math claims using a restricted SymPy backend.")
    parser.add_argument("--input", default="-", help="Request JSON path, or - for stdin.")
    parser.add_argument("--output", default="-", help="Result JSON path, or - for stdout.")
    parser.add_argument("--timeout-ms", type=int, default=1000, help="Per-claim wall-clock limit (50-10000 ms).")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic built-in regression checks.")
    args = parser.parse_args(argv)
    if not 50 <= args.timeout_ms <= 10_000:
        parser.error("--timeout-ms must be between 50 and 10000")
    if sp is None:
        report = {
            "schema": RESULT_SCHEMA,
            "engine": {"name": "sympy-audit", "profile": PROFILE, "sympy_version": None},
            "status": "backend_unavailable",
            "diagnostics": [{"code": "SYMPY_UNAVAILABLE", "message": "SymPy could not be imported."}],
        }
        _write_report(report, args.output, SAFE_DEFAULTS)
        return 3
    try:
        if args.self_test:
            report = _self_test()
            _write_report(report, args.output, SAFE_DEFAULTS)
            return 0 if report["passed"] else 1
        document = _load_document(args.input, SAFE_DEFAULTS)
        report = audit_document(document, timeout_ms=args.timeout_ms)
        _write_report(report, args.output, SAFE_DEFAULTS)
        return 0
    except AuditInputError as error:
        report = {
            "schema": RESULT_SCHEMA,
            "status": "rejected",
            "diagnostics": [{"code": error.code, "message": error.message}],
            "results": [],
        }
        _write_report(report, args.output, SAFE_DEFAULTS)
        return 2
    except OSError as error:
        report = {
            "schema": RESULT_SCHEMA,
            "status": "backend_error",
            "diagnostics": [{"code": "IO_ERROR", "message": type(error).__name__}],
            "results": [],
        }
        _write_report(report, args.output, SAFE_DEFAULTS)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
