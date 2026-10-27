# Readable progress records

The body answers: what happened, why it matters, what changed, what was checked, and what remains. The appendix lets a later reader reproduce and audit it. Keep both in the same Markdown file so the record remains useful after its temporary manifest disappears.

## Body

Use this order for coding records. Keep the level-two headings for tooling; choose natural subheadings only when they help. `### Test Result` and the old implementation subheadings are no longer required.

1. **Outcome:** one or two short paragraphs with the achieved result and any qualification that changes the verdict. A completed experiment with rejected candidates must say so here.
2. **Task and Scope:** the requested change, relevant starting point, and material constraints. Avoid reciting every instruction.
3. **Implementation:** explain the meaningful changes and why they were needed, grouped by capability or problem. For a function fix, identify the evidence-backed preserved contract and corrective change. For a fresh implementation, identify the plan source, starting status, core functions, and resulting behavior. Use a short path table only if it helps locate the implementation.
4. **Interface and Behavior Changes:** include only when a contract or behavior changed.
5. **Validation:** explain what the checks establish. A short table can compare different validation areas; use named rows and plain-language outcomes. Group routine compilation, formatting, and smoke checks in one sentence. Highlight failures, partial checks, skips, and not-run checks with their consequences. Do not paste commands here or make one subsection per tool call. The aggregate manifest state belongs in metadata; it is not a substitute for explaining the results.
6. **Evidence Boundary:** state substantive limits that have not already been explained. Do not repeat a defensive conclusion in several sections.
7. **Next Steps:** unresolved work and concrete acceptance gates, or `None`. Do not repeat the completed work.

Keep the date and a brief status near the title if useful. Put full metadata in the appendix; each machine-readable metadata field must occur only once. A current blocker or negative qualification must remain visible in the body even though its event history is folded away.

For session documentation, use Outcome → Context and Scope → Findings and Decisions → optional Technical Design or Experimental Plan → Evidence Boundary → Next Steps. Preserve meaningful design detail, equations, rationale, and alternatives. Put metadata, sources, and v3 lifecycle history in the appendix; omit checks and Git custody.

## Appendix

Use native Markdown details with blank lines after the summary and before the closing tag. Keep the internal headings at level two so validation and discovery can read them. When the renderer does not support folding, use an ordinary final appendix with the same headings and content.

~~~~markdown
<details>
<summary>Record details — checks, sources, and history</summary>

## Record Metadata

Copy the selected format's metadata here, except fields already shown near the title.

## Check Details

### CUDA contract tests

- Check: `V1`
- Result: `pass`
- Evidence: `verified`

```text
python run_tests.py --unit-only
```

270 tests passed with local CUDA access; no skips.

### Target qualification

- Check: `V2`
- Result: `partial`
- Evidence: `verified`

```text
python analyze_models.py
```

Analysis completed; both target candidates rejected.

## Evidence Ledger

- E1 (user-stated): Current conversation requesting the bounded migration case study.
- E2 (verified): docs/case-study.md; SHA-256: copy the captured source hash.

## Git Custody

Copy the captured branch, baseline/final HEAD, history relation, commits,
scope/ownership distinctions, record path, and exact scoped-diff token.

## Lifecycle

For v3 only: copy the current blocker, events, and local relationships.

</details>
~~~~

The commands and outcomes above illustrate layout, not checks run by this skill. Use the actual manifest values in real records.

Each named check entry must contain its tool-assigned ID, exact result, `Evidence: verified`, exact command, observed summary, and artifact hash when captured. Use each check ID once in Check Details. “Verified” classifies the recorded observation, including a failure or a recorded non-execution; it does not claim the tested system passed. Do not duplicate these entries in Evidence Ledger. Keep `E*` source IDs, classification, locators, hashes, and claim support there. Link from the body using names such as `[target qualification](#target-qualification)`, rather than `(V7)`.

Existing `### V1 - pass` layouts with check classifications in Evidence Ledger remain valid. Preserve original evidence and format when updating an existing record; do not invent a missing manifest or rewrite unrelated historical notes.

## Example of the visible body

Adapted from the RTX 3080 → A6000 case study supplied for this redesign. These are historical reported results, not measurements rerun during the redesign. This excerpt demonstrates the body only; a complete record also retains all original receipts in its appendix.

> **Outcome**
>
> The paired-device case study is complete. It demonstrates useful kernel-level transfer prediction, but neither A6000 model candidate passed qualification, so no configuration was promoted.
>
> **Validation**
>
> | Area | Finding | Meaning |
> | --- | --- | --- |
> | Contract tests | All 270 tests passed with CUDA enabled and no skips. | The tested implementation contracts hold. |
> | Region measurements | Both devices produced 216 numerically valid, stable rows. | The paired region analysis has usable measurements. |
> | Transfer prediction and search | Held-out target MAPE was 8.68%; one-probe mean regret was 1.10%. | Prediction and offline search replay were useful within this bounded workload. |
> | End-to-end qualification | CUDA graphs improved throughput by 13.02% but worsened time to first token by 10.86%; stability and complete-token gates also failed. | Both target candidates were rejected. Request-level prediction remains diagnostic. |
>
> Compilation, the dummy public-validation smoke test, and whitespace checks passed. The historical Nsight Systems report was recovered, and the summary figures were generated and visually inspected. Nsight Compute counters remain permission-blocked.
>
> **Next Steps**
>
> Establish stable paired model controls and resolve token differences before attempting promotion. Demonstrating the broader migration objective also requires dependency- and fusion-aware request modeling, genuine online tuning with measurement overhead included, and a target candidate that passes all qualification gates.
