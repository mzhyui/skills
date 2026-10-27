# Arrow geometry without protruding shafts

Use one continuous shaft path for each routed edge. Keep the full-width shaft
out of the arrowhead's narrowing taper. A triangle placed over a line ending at
its tip leaves a blunt bump or shoulders: `stroke-linecap="round"` extends past
the tip, and a butt cap still exposes shaft corners beside the taper. Merely
switching to an SVG marker does not solve this geometry.

For straight or polyline routes, prefer the bundled
[`add_arrow`](../scripts/arrow_geometry.py) helper. Pass route points through the
**intended tip**, not the shortened shaft endpoint. It preserves the tip and
all bends, shortens only the last shaft segment, and supplies an unstroked solid
marker with an explicit color and a butt-capped shaft. Dash patterns apply only
to the shaft. The scene graph should retain the intended route/tip; record any
derived shaft geometry separately.

```python
# Import from the actual skill directory; retain that dependency in reproduce
# instructions, or copy arrow_geometry.py beside a standalone figure generator.
from arrow_geometry import add_arrow

add_arrow(root, defs, "encoder-to-head", [(30, 40), (120, 40), (120, 100)],
          color="#26364A", stroke_width=4, head_length=12, head_width=12)
```

For another authoring tool, use equivalent geometry:

- Let head length be $L$, full head width $W$, shaft width $w$, and overlap $o$.
  Choose $W > w$ and $0 < o < L(1-w/W)$ so the shaft's end corners lie strictly
  inside the broad part of the triangle. The helper uses
  $o=\min(w/2, L(1-w/W)/2)$.
- In head-local coordinates the triangle is `(0,0) → (L,W/2) → (0,W)`.
  Set `refX=o`, `refY=W/2`, `markerUnits="userSpaceOnUse"`, and explicit marker
  dimensions/viewBox. Stop the butt-capped shaft $L-o$ before the intended tip
  along the terminal direction. Set the head's `stroke="none"` explicitly to
  prevent it inheriting an outline. Avoid gaps by retaining the small overlap.
- Keep the head entirely within the final segment; if that segment is too
  short, reduce the head or reroute it. Do not trim across a bend or silently
  move the attachment point. Check thick, thin, diagonal, and reverse arrows,
  short connectors, feedback loops, and legend samples.
- For curves, shorten along the actual curve and align the head with its final
  tangent, or author a single filled outline for the complete arrow. Preserve
  the intended tip. Do not approximate a curve with this polyline helper.
- A single filled arrow outline is also valid, especially for thick solid
  arrows. Its shaft must terminate at the head's broad portion before union;
  uniting a triangle with a shaft that still reaches the tip preserves the bump.
  Avoid background-colored covers: they fail on transparent/colored panels.

Enlarge the rendered PNG **and a PDF-rendered preview** to inspect the head's
taper, shoulders, tip, and connection. Check them again at final figure width.
The export helper does not certify arrowhead geometry. Keep archived figure
bundles byte-preserved; use corrected copies when demonstrating this repair.
