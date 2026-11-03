# Example icons

Editable SVG examples with descriptive English, lowercase kebab-case filenames.
The filename cleanup on 2026-11-02 preserved all eight SVG files byte for byte.

| File | Subject |
| --- | --- |
| [azure.svg](azure.svg) | Azure logo |
| [huggingface-outline.svg](huggingface-outline.svg) | Hugging Face outline logo |
| [neural-network-sketch.svg](neural-network-sketch.svg) | Sketch-style neural network |
| [cloud-server-sketch.svg](cloud-server-sketch.svg) | Sketch-style cloud and server |
| [hacker-avatar-sketch.svg](hacker-avatar-sketch.svg) | Sketch-style hacker/spy with a hat and sunglasses |
| [elastic-cloud-server.svg](elastic-cloud-server.svg) | Outline cloud server |
| [neural-network-weights-hand-drawn.svg](neural-network-weights-hand-drawn.svg) | Hand-drawn 2–3–2 network with weight labels |
| [curved-arrow.svg](curved-arrow.svg) | Looping curved arrow |

## Sources for similar icons in batches

These are acquisition options, not verified origins of the existing files.

| Source | Best match | Batch acquisition |
| --- | --- | --- |
| [Iconify](https://iconify.design/docs/icons/icon-data.html) | Search across outline, filled, sketch, and brand collections | Download a collection as `@iconify-json/{prefix}` or use its API; [export collection data to SVG](https://iconify.design/docs/libraries/tools/examples/export-svg.html). |
| [Tabler Icons](https://github.com/tabler/tabler-icons) | Consistent outline servers, clouds, networks, security symbols, and arrows | Download a GitHub release or the `@tabler/icons` npm package, which contains raw SVGs. |
| [Lobe Icons](https://github.com/lobehub/lobe-icons) | AI model and provider logos | Download the `@lobehub/icons-static-svg` npm package for static SVG assets. |
| [Iconfont](https://www.iconfont.cn/) | Illustrated and hand-drawn icon collections | Select icons through the site's cart/project export workflow; batch-export availability and limits depend on the current site/account. |

Start with Tabler for a consistent technical-diagram set and Lobe Icons for AI
logos. Use Iconify to compare styles. For the rough sketch appearance, search
for terms such as `hand-drawn`, `neural network`, `cloud server`, `hacker`, and
`curved arrow`, then choose icons from the same collection where possible.

Prefer published packages, releases, or documented APIs for automated batches.
For example, run these in a separate download directory to fetch package archives
without adding dependencies to this repository:

```bash
npm pack @tabler/icons
npm pack @lobehub/icons-static-svg
npm pack @iconify-json/tabler
```

The first two packages contain SVG assets; the third contains Iconify JSON that
needs SVG export. Retain the resolved package version, upstream URL, and license
with any imported collection. Tabler uses MIT; Iconify collections have their own
licenses, and brand assets may have separate usage conditions.

The existing SVGs do not establish complete source or license provenance. Some
contain Iconfont-style export attributes (`p-id`, `t`, `class="icon"`), which are
a source clue rather than proof of an original collection or permission grant.
