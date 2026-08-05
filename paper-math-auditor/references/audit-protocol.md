# Audit protocol and SymPy helper schema

Use this reference for a complete mathematical-audit report or for the
deterministic `scripts/sympy_audit.py` helper. The helper checks only local
claims; it does not replace semantic proof review.

## Report structure

Begin with scope, source revision, and what was not audited. Then include:

| ID | Location | Claim | Verdict | Severity | Required correction | Downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Eq. (7) | `A^T A = I` | Unresolved | Major | State orthonormal-column assumption | Lemma 2 and Alg. 1 |

Use a separate table for assumptions:

| Assumption | Explicit? | Used by | Necessity | Evidence or gap |
| --- | --- | --- | --- | --- |
| L-smoothness | Yes | Theorem 1 | Required for descent lemma | Stated before theorem |

Use a symbol/dimension table for every nontrivial notation family:

| Symbol | Type and shape | Domain/indexing | Meaning | Defined at |
| --- | --- | --- | --- | --- |
| `X` | matrix `n x d` | samples x features | input matrix | Sec. 3 |

For theorem findings, record formal claim, assumptions, proof strategy,
line-by-line evidence, boundary cases, counterexample search, correction, and
downstream effect. Mark an unproved step as an obligation rather than guessing
that the conclusion is false.

## Helper request format

The helper accepts a single JSON object using schema
`paper-math-audit/request/v1`.

```json
{
  "schema": "paper-math-audit/request/v1",
  "claims": [
    {
      "id": "eq-trig",
      "location": "Eq. (4)",
      "operation": "identity",
      "relation": "=",
      "symbols": {"x": ["real"]},
      "lhs": "sin(2*x)",
      "rhs": "2*sin(x)*cos(x)",
      "domain_policy": "common_defined_domain",
      "samples": [{"x": "1/3"}],
      "search": {"mode": "provided_only"}
    }
  ]
}
```

Supported operations are:

- `identity`: `lhs = rhs` for scalar expressions.
- `derivative`: `d(expression)/d(variable) = claimed`.
- `matrix_product`: verify the dimension contract for `left @ right`.

For a derivative, replace `lhs` and `rhs` with `expression`, `variable`, and
`claimed`:

```json
{
  "id": "grad-1",
  "operation": "derivative",
  "symbols": {"theta": ["real"]},
  "expression": "log(1 + exp(-theta))",
  "variable": "theta",
  "claimed": "-1 / (1 + exp(theta))",
  "samples": [{"theta": "0"}]
}
```

For a matrix product, use two rank-two declared shapes. `equal_dimensions` and
`unequal_dimensions` are lists of two-element arrays.

```json
{
  "id": "shape-1",
  "operation": "matrix_product",
  "left": "X",
  "right": "W",
  "matrices": {"X": ["n", "d"], "W": ["d", "k"]},
  "equal_dimensions": [],
  "unequal_dimensions": []
}
```

If contracted labels are distinct and no equality is supplied, the matrix
result is `unresolved`, not refuted. An explicitly unequal pair is refuted.

## Exact-expression grammar

Use declared ASCII identifiers, exact integers and rational expressions, `+`,
`-`, `*`, `/`, bounded integer powers, `pi`, `E`, and the functions `sin`,
`cos`, `tan`, `exp`, `log`, `sqrt`, and `Abs`. Expressions are parsed through a
restricted Python AST, not `eval`, `sympify`, `parse_expr`, or LaTeX parsing.

Reject float literals, strings, attributes, subscripts, imports, unknown names,
symbolic exponents, and all unsupported syntax. This is intentional: symbolic
verification is only trustworthy when the executed expression is visible and
controlled.

Declare only these positive assumptions per symbol: `real`, `integer`,
`positive`, `nonnegative`, `negative`, `nonpositive`, and `nonzero`. The helper
records all supplied assumptions and does not invent them.

## Domain policies and results

`common_defined_domain` (the default) verifies an equality only over points
where both original expressions are defined. The report retains structural
conditions such as `x != 0`; cancellation does not erase them.

`declared_domain` requires those conditions to follow from the supplied symbol
assumptions. If they do not, the claim stays unresolved unless an exact supplied
sample shows one side defined and the other undefined, which refutes a global
claim over the declared domain.

Every completed claim receives exactly one verdict: `verified`, `refuted`, or
`unresolved`. Rejected syntax, unsupported features, resource limits, and
backend failures use `verdict: null` with a separate status. A residual that
SymPy cannot simplify is unresolved, never automatically false.

The helper's output includes parsed expressions, original-domain conditions,
normalization evidence, skipped samples, and exact counterexamples. Preserve
that output with the audit record; it is local evidence, not a theorem proof.
