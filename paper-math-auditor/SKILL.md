---
name: paper-math-auditor
description: Audit mathematical correctness in scientific and ML manuscripts. Use when asked to verify equations, derivations, proofs, theorems, assumptions, notation, dimensions, probability or optimization claims, spectral or topological arguments, implementation-to-objective consistency, counterexamples, or the mathematical strength of paper claims. Produce evidence-bound review findings rather than a proof certificate.
---

# Paper Math Auditor

Conduct a read-only, adversarial mathematical audit. Treat each mathematical
statement as an auditable object; do not accept a claim because it is standard,
plausible, or supported by an empirical result.

## Establish the audit boundary

1. Identify the exact source artifacts and their revision: manuscript, appendix,
   code, algorithms, figures, and cited definitions. Preserve source locations
   such as `Eq. (7)`, `Lemma 2`, or `Algorithm 1, line 4`.
2. State the requested scope and exclusions. Separate an equation/proof audit
   from an empirical, reproducibility, or literature audit.
3. Treat the paper's explicit assumptions as binding. Record an implicit
   assumption only when a later inference needs it; never silently add one and
   call the original claim verified.
4. Keep the audit read-only unless the user specifically asks for corrections.

## Build auditable ledgers before judging claims

Make the following ledgers as you read. Use `references/audit-protocol.md` for
the report schema and the executable helper's request format.

- **Claim inventory:** ID, source location, formalized statement, relation type,
  and downstream claims that depend on it.
- **Symbol and dimension table:** definition-before-use, scalar/vector/matrix/
  tensor type, shape, index set, domain, randomness role, and any overloaded
  meaning. Verify every contraction and broadcast explicitly.
- **Assumption ledger:** assumption, whether it is explicit, every claim using
  it, whether it is necessary, and whether it is checkable.
- **Dependency graph:** definitions -> assumptions -> lemmas -> theorems ->
  algorithms -> empirical conclusions. Flag forward references, unused lemmas,
  special-case proofs, and conclusions stronger than their parents.

Classify every relation exactly as written: `=`, `approx`, `propto`, an
inequality, distributional equality, asymptotic relation, heuristic, or
empirical observation. Do not exchange these categories. In particular, do not
promote a ranking statistic into a calibrated probability or an experiment into
a theorem.

## Audit each mathematical claim

For every nontrivial equation, lemma, theorem, proposition, or algorithmic
claim:

1. Reconstruct the intended statement with quantifiers, domains, and a source
   location. Quote only the minimum needed to identify it.
2. Check algebra, calculus, probability, dimensions, normalization, signs,
   conditioning, and equality conditions. Track original expression domains;
   algebraic cancellation must not erase excluded points.
3. List every explicit and needed implicit assumption. Check whether its
   placement is early enough for the inference that uses it.
4. For a proof, list its strategy and verify every inference. Distinguish a
   missing proof obligation from a false step.
5. Search boundary cases and minimal counterexamples. Favor exact, admissible
   substitutions over floating-point evidence. Explain why a proposed
   counterexample is in-domain.
6. State the weakest correction that makes the claim true: add an assumption,
   restrict the domain, change an equality to an approximation/bound, or weaken
   the conclusion.
7. Trace the effect of a correction to all downstream claims, algorithms, and
   experimental interpretations.

## Check high-risk ML-paper reasoning

Apply the following checks when relevant.

- **Optimization:** Match the update rule to the stated objective; distinguish
  detached values from differentiable ones; check stochastic-gradient sampling,
  bias, and interchange of gradient, sum, limit, and expectation.
- **Probability and statistics:** Name the randomness in every expectation;
  check independence, conditioning, calibration data, selection bias, multiple
  comparisons, and whether a statistic has the claimed interpretation.
- **Federated learning:** Distinguish sample, client, and participation-adjusted
  weights. Do not call a partial-participation aggregate unbiased without the
  client-sampling and reweighting argument.
- **Spectral methods:** Distinguish eigenvalues from singular values, centered
  covariance from uncentered second moments, left from right singular vectors,
  spectral energy from explained variance, and anomalous directions from causal
  backdoor attribution.
- **Topological methods:** Check metric/dissimilarity requirements, symmetry,
  nonnegativity, diagonal convention, filtration direction, infinite bars,
  stability assumptions, and claimed invariances or causal conclusions.
- **Implementation consistency:** Compare the stated loss, constraints,
  parameterization, and stopping rule against the code. Report code/paper
  disagreement as a separate finding from a mathematical error.

## Use the deterministic SymPy helper narrowly

Run `scripts/sympy_audit.py` only for local, exact scalar identities,
derivatives, and two-dimensional matrix-product shape contracts. It accepts a
restricted JSON expression language; it does **not** execute arbitrary Python,
parse LaTeX, prove inequalities, or validate theorem-level logic.

Before running it:

1. Transcribe the source equation into the helper's restricted ASCII grammar.
2. Put every symbol and its assumptions in the request.
3. Retain the source location and show the normalized parsed expressions in the
   report.
4. Supply only exact samples, or request the helper's bounded fixed-grid search.
5. Treat `unresolved`, a parser rejection, or a timeout as no mathematical
   conclusion—not as a refutation.

Example:

```bash
python3 scripts/sympy_audit.py --input audit-request.json --output audit-result.json --timeout-ms 1000
```

Do not install packages during an audit. If SymPy is unavailable or reports a
different version from prior evidence, report that backend boundary. Do not use
experimental LaTeX parsing silently: it can misread malformed or ambiguous
source. If a separate parser is necessary, display and confirm its normalized
result before any symbolic check.

## Assign verdicts and severity independently

Use exactly one mathematical verdict per completed claim:

- **Verified:** supported under the stated assumptions and stated domain.
- **Refuted:** an inference fails or an exact admissible counterexample exists.
- **Unresolved:** neither verification nor refutation was established.

Use a separate execution status for rejected syntax, unsupported operations,
resource limits, or backend failures. Describe a claim as *conditionally
verified* only in prose when a named, newly proposed assumption profile was
checked separately; do not relabel the original claim as verified.

Assign severity by downstream effect:

- **Critical:** invalidates a theorem, method, or principal conclusion.
- **Major:** needs an additional assumption or substantive correction.
- **Minor:** notation, exposition, or a locally repairable derivation issue.
- **Verified:** a checked item with no corrective action under its recorded
  assumptions.

## Deliver an evidence-bound report

Report findings in descending severity. For each issue include location,
original/formalized claim, verdict, severity, evidence or failed inference,
required assumption, proposed correction, and downstream effect.

End with:

1. the assumption ledger;
2. the symbol and dimension table;
3. the claim-dependency graph;
4. unresolved proof obligations and untested implementation links; and
5. an overall mathematical confidence statement that names the audit scope and
   limitations.

State plainly that this is adversarial review plus executable local checks, not
a machine-checked proof. Recommend human domain review or formal verification
when a claim's stakes warrant it.
