# GBHINDER reference reconstruction

Source S1: `../图片4.png`, SHA-256 `a0ba1213fe3d0a12fb0656b533d0165db15cf83e64bf4975e39dc5e996db4ad3`, 2065 × 855 pixels. The figure itself supplies all content. No paper or algorithm code was supplied.

Brief: faithful reconstruction with editable SVG/PDF and PNG, white background, original aspect ratio. Assumed delivery width 14 inches preserves dense labels; this is not a venue-specific print-size claim.

Stages and source anchors:
- local-data: left dashed panel, three illustrative graph instances.
- aggregation: upper dashed panel, client models combined toward global model; red download and green upload arrows; malicious-update legend and icon.
- historical-channel-attention: lower left, current weights w_k^t ← w^t, historical weights h_k^t ← w_k^{t−1}, channel attention, CE Loss and 1/0/1 labels, pre-pooling and Topological Consistency. Layer channels 1, 2, 3, …, D_l feed ℋ_CH(ℱ^l) and an ℝ^N graph representation.
- adaptive-momentum: lower right, G_i and perturbed G_i^adv, local and historical models, feature columns ℱ(G_1), ℱ(G_2), …, ℱ(G_i) and adversarial counterparts. δ = [π_1 π_2 π_i] follows the source's displayed terms; the reference shows feature-column ellipses but no explicit ellipsis in the delta row.

Node/edge/notation inventory: `scene-graph.json` records labels, math runs, model and graph groups, arrow routes and complete editable geometry. Arrow direction follows S1; colored update arrows are transcribed without adding causal or algorithmic claims. Two-way CE connectors are retained. No convergence rule or tensor dimensions can be recovered and none are invented.

Abstraction: vector devil icons approximate the raster artwork; model faces, graphs, channel planes and feature bars are schematic redraws. Fine icon contours, model shadows, and exact raster antialiasing are not recovered. Font identity is estimated from pixels. The illustration is not measured evidence or verification of the method.
