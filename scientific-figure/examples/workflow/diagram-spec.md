# Diagram specification: scientific figure generation

Illustrative process diagram based on the supplied workflow, not experimental evidence.

## Brief and source
Landscape, 7 inches wide, 1440 × 620 user units, white background; editable text and native vectors. Minimum body font 24 units = 8.4 pt. Rounded panels and restrained illustrated icons use orange, blue, and purple as stage identifiers, reinforced by titles and numbers. These colors do not denote modalities in this example.

Source S1: `method-source.md`, SHA-256 `2943069995ca35cdffa53ee7786103fa484efbbc440b724353d147ee93175938`. Section headings are stable anchors for the excerpt. PNG preview and editable SVG are source-requested; PDF is an additional publication export chosen in this implementation.

## Stages and nodes
| ID | Operation | Input | Output | Anchor |
| --- | --- | --- | --- | --- |
| abstraction | Identify entities and relations | Methods and exact notation | Diagram specification | S1 §1 |
| composition | Position panels, icons, labels, and arrows | Diagram specification | Scene graph and vector geometry | S1 §2 |
| validation | Render, inspect, and correct | Vector source | Editable figure and inspected previews | S1 §3; requested output |

## Edges
| ID | From → to | Meaning | Anchor |
| --- | --- | --- | --- |
| specify-to-compose | abstraction → composition | Specification informs composition | S1 §1–2 |
| compose-to-validate | composition → validation | Vector geometry goes to rendering/review | S1 §2–3 |
| revise-layout | validation → composition | If visual issues remain, revise layout and render again | S1 §3 |

The feedback arrow denotes visual revision, with stopping condition: the figure works at final manuscript size (S1 §3). It does not represent a learning algorithm. Scientific source problems would require revisiting abstraction; this compact example shows the explicitly described layout-revision loop only.

## Notation, icons, and abstraction choices
No mathematical equations, tensor dimensions, empirical scores, or scientific decision blocks occur in this source. None are added. Document, scene, and preview icons are schematic visual summaries of the three operations. Text lines inside icons are decorative strokes, not illegible scientific labels. Exact node wording is shortened for figure readability; the source excerpt preserves the full text.

## Open questions
None for this illustrative workflow. No inaccessible linked reference image was inspected; styling follows the user's written description.
