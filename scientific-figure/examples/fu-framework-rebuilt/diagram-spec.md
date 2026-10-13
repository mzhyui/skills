# Figure specification

Source: `source/fu_framework.svg`, the preserved input. SHA-256: `14341f8c25ded41e30da1e3c535fc5e454c19f98b30f9664013bba39c43f4664`.
Style reference: `../gbhinder-rebuilt/figure.svg`. Secondary visual reference: `../federated-unlearning-rebuilt/preview.png`.

Cosmetic reconstruction only: preserve all 67 source text objects (including exact tspan strings and indices), all directed connector IDs, the three-stage order, white background, and 1280 × 460 canvas. The original SVG has unitless dimensions: interpreted at the SVG standard 96 units/inch, this is 13.333 × 4.792 inches. No venue width was supplied.

1. `training`: participating clients C1, C2, Cj, Cn; local ε0-LDP randomization; optional shuffler; server history retaining round aggregates and randomized reports. Source anchors are the corresponding `client-*-label`, `noise-heading`, `shuffler-*`, and `history-*` text IDs. The local privacy boundary remains explicit.
2. `unlearning`: Cj withdraws, issues an unlearning request, server reconstructs round aggregates without Cj, decodes and averages retained messages and clips afterward, replays from original initialization, then performs private recovery with fresh locally randomized client gradients. Output is the unlearned model θ−j. All operation text is retained exactly from matching source IDs.
3. `verification`: withdrawn-client samples and clean test samples use separate model illustrations, producing MIA AUC / balanced accuracy against retraining and clean accuracy against a reference model. Diagnostic yes/no branches retain empirical-evidence and inconclusive-outcome qualifications. Criteria are not defined by the source; this revision does not invent them.

Every scientific node, exact label, math run, and arrow is enumerated in `scene-graph.json` with source IDs. Arrow routing follows the supplied figure: four client → randomization → shuffler flows; shuffler → history; withdrawal → request → recomputation → replay → recovery → output; each evaluation row has sample → model → result; evaluation → diagnostic with yes/no outcomes. Stage transitions are conveyed by order, as in the source, without extra directed connectors.

The model slabs are schematic icons, not specified layer counts. Database and document stacks denote stored information and samples; permutation wires are illustrative. The source uses generic i on every training-message label, including the leaving-client row; this notation is preserved. No mathematical or empirical acceptance claim is made.
