# Record formats (format 4)

A record is one Markdown file: a body a reader can act on, then a folded appendix with metadata, commands, Git facts, and sources. Body section names are required in the order shown; sections marked optional may be left out. Add `###` subheadings freely.

## Writing rules

1. **Lead with the answer.** The first section must stand alone: a reader who stops there knows what happened and what it means.
2. **Give every number a reference point**: a baseline, chance level, threshold, earlier run, or a clause on what it means. Explain values whose meaning isn't obvious (AUROC 0.5 is chance; AUROC 0 is a fully inverted ranking).
3. **Define before use.** Give every symbol, acronym, metric, and project codename a plain definition at first use or in a glossary. Assume the reader knows the field but missed this session.
4. **Organize by topic**, not by the order commands ran.
5. **Say each fact once.** The body interprets; the appendix keeps exact commands and Git facts.
6. **Keep bad news in the body.** Failures, partial results, skipped runs, and blockers stay visible, with their consequence.
7. **Tag only what wasn't observed.** Measured or computed values and inspected files need no tag. Mark `(inferred)` for reasoning from evidence, `(proposed)` for undecided or undone items, and `(user-stated)` for unchecked claims from the user.
8. **State each limit once**, where a reader could over-read the result.
9. **Tables for comparisons, prose for reasoning.** Keep paragraphs short.
10. **Stay honest and safe.** Never claim a run, inspection, or code change that didn't happen, and never turn a failed, partial, or skipped check into a pass. Never record secrets, credentials, environment-variable values, or hidden reasoning.

## Evaluation

~~~markdown
# <What was evaluated, on what>

## Readout

**Question.** <What the evaluation set out to learn.>

**Answer.** <The finding in one plain sentence.>

| Measure | Result | Compared with | Meaning |
| --- | --- | --- | --- |
| <metric, defined in plain words> | <value and n> | <baseline, chance, prior run, or other method> | <what it tells us> |

**What we now believe.** <One to three sentences.> **What this does not show.** <Limits a reader could over-read.>

**Decision.** <What to do with the result, or a (proposed) action.>

## Setup

<What was evaluated, data and models, protocol, metric definitions, and code built to run it.>

## Detailed results

<Optional: per-condition tables, surprises, failure modes.>

## Correctness checks

<What tests and verifiers establish about the code and pipeline. Keep these apart from the findings: a correct run of a method that fails is a finding, not a failed check.>

## Open items

<Remaining limits, blockers, and next steps with acceptance gates, or None.>
~~~

Example Readout, adapted from a real record (numbers as reported there):

> **Question.** Does BARBIE separate backdoored from clean VGG9 checkpoints on our development roster?
>
> **Answer.** Not usefully: at its calibrated boundary it flags almost every model, clean or attacked.
>
> | Measure | Result | Compared with | Meaning |
> | --- | --- | --- | --- |
> | Attacks flagged, CIFAR-100 | 4/4 | — | Sensitive, but see the next row |
> | Clean models flagged | 4/5 CIFAR-100, 4/5 Tiny-ImageNet | 0/5 ideal | A flag carries little information |
> | AUROC (0.5 = chance) | 0.625 on 9 test models | SPD 1.00, FreeEagle 0.71, MM-BD 0.18 (11 models, same roster) | Slightly better than chance; behind SPD and FreeEagle |
>
> **What this does not show.** The AUROC uses a locally defined score, not a published BARBIE number; one model lineage, transferred thresholds, ViT not run.
>
> **Decision.** (proposed) Report BARBIE as low-specificity here; make no general claim before calibrating on independent clean lineages.

## Session

~~~markdown
# <Topic>

## Takeaways

- <A conclusion a reader can act on; three to five bullets in total.>

## Method

<What is being discussed: its purpose, inputs, what it computes or does, and its output, in plain words.>

| Term | Meaning |
| --- | --- |
| <symbol, acronym, or codename used below> | <plain definition> |

## Discussion

<Findings by topic, each with its basis: what was inspected or computed, or a tag.>

## Decisions

| Item | Status | Reason |
| --- | --- | --- |
| <choice or question> | <decided, rejected, or open> | <why, or what would settle it> |

## Design or plan

<Optional: equations, interfaces, protocol, milestones, acceptance gates.>

## Open items

<What remains unestablished, and next steps, or None.>
~~~

Example excerpt, adapted from a real record:

> **Takeaways**
>
> - The paper's stated mechanism (new structure an update adds outside the clean subspace) is only 0.14–1.3% of the attacks' residual energy, so it does not drive the score.
> - C instead measures how unevenly a checkpoint's per-layer residual departs from its parent's near-uniform profile, so attacks that stay close to their parent score low (inferred).
>
> | Term | Meaning |
> | --- | --- |
> | e_ℓ | Fraction of layer ℓ's weight energy outside the reference's retained subspace |
> | C | Concentration score: KL divergence of the layer profile from uniform, normalized; higher is more suspicious |
> | AUROC | Chance a random attack outscores a random clean model; 0.5 is chance, 0 a fully inverted ranking |
>
> | Item | Status | Reason |
> | --- | --- | --- |
> | Rewrite the mechanism prose now | rejected | It must describe whichever statistic (C or R) is kept |
> | Keep the "outside the clean subspace" claim | open | Holds only if attacks beat recipe-matched clean runs at equal update size |

## Implementation

~~~markdown
# <What changed>

## Outcome

<What works now, in one to three sentences, and the limit that matters most.>

## Change

<The starting point and why it needed changing. For a fix: the contract that stays the same and the defect boundary. For new work: the plan source and what was built. Group by topic; name core files and functions.>

## Interface changes

<Optional, only when a CLI, API, schema, file format, default, or output changed: before, after, compatibility.>

## Checks

<What the checks establish. Group routine checks; keep failures and skips visible.>

## Open items

<Remaining limits, blockers, and next steps, or None.>
~~~

## Appendix (every kind)

~~~markdown
<details>
<summary>Record details</summary>

## Record details

- Record format: `4`
- Kind: `<implementation, evaluation, or session>`
- Change type: `<fix or new; implementation only>`
- Date: `<YYYY-MM-DD>`
- Status: `<done, partial, or blocked>`
- Project: <repository or project>
- Follows: <earlier note path; optional>

## Commands

- <Check name> — `<pass, fail, partial, or not-run>` — `<exact command>` — <observed outcome, or why it was not run>

## Git

<Output of record_tool.py custody, or: Git: not applicable>

## Sources

- <File, document, URL, or conversation relied on> — <what it supports>

</details>
~~~

`Commands` and `Git` are required for implementation and evaluation; session records may include `Commands` for analysis they ran. `Sources` is required for session records and optional otherwise. `partial` means the scope closed or paused incomplete; `blocked` needs the blocker named under Open items.
