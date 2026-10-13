# Reconstruction specification

Source S1: `../图片.png`, SHA-256 `6010ec8bf304bac996a1da654c2a573c13bee7c2b3a510565f883805dc9bfd84`; 2011 × 1021 pixels, no physical-size metadata. User request: “rebuild [Image #1]”. The image was located and opened despite the attachment error. No manuscript or experimental data was supplied.

Brief: faithful reconstruction of S1, same aspect ratio and white background; editable SVG plus PDF/PNG. Assumed delivery width 14 in (height 7.1079 in); this is a presentation master, not a claim of journal-size readability.

## Source-grounded stages and entities
- `attacker-client`: source x47–344, y33–831. Batman identity, poisoned rabbit/dog image stack, clean rabbit/dog stack. Photographs and logo remain raster.
- `malicious-knowledge`: source x388–1169, y57–459. Malicious Parameter; three-block Singular Value Decomposition; equality with Redundant + Important; No SVD / SVD bars; TAC Decrease / TAC Increase. These bars are schematic with no numeric scale in S1.
- `benign-knowledge`: source x388–1173, y477–808. Clean model; Truth Label / Attack Label bars and Gap; Clean Parameter; client weights W and previous W_g^(t−1); benign/attack branches; global W_g^t and Gap; Global Parameter.
- `alignment-panel`: source x1254–1938, y61–814. Before/after Attack Performance versus Parameter Space; malicious/benign knowledge; initial Δ and projected ΔP; Keep at the same attack-performance height; gray projection connections; Null Space with singular values x_1 … x_n and zero block; projector Ũ_0 Ũ_0^T = P; projection-plane illustration. Preserve equation references (3), (4), (5), (6) as printed. Their definitions are unavailable.
- `federated-training`: source x47–1172, y845–1006. Distribute / Aggregate, two representative Benign Client labels and ellipsis, Global model, teal up/down arrows.
- `legend`: source x1172–1974, y845–1006. Alignment (purple gradient), Projection (gray), Training Flow (blue), Parameter Flow (gold).

## Edges and notation
Blue arrows: poisoned data → malicious parameter; clean data → clean model. Gold arrows: important malicious component → alignment; global parameter → alignment. Gray curves connect left performance plot to the null-space inset and inset to right performance plot. Purple horizontal arrow illustrates alignment; brown Δ points from malicious region toward benign region; ΔP points left at preserved attack performance. Small parameter graph and communication connections retain their pictured endpoints. Paths and positions are enumerated in scene-graph.json.

Symbols are transcribed from S1 without inferring dimensions or proving claims. W_g^(t−1), W_g^t, x_1, x_n, Δ, ΔP, Ũ_0 Ũ_0^T = P are retained with editable text/tspan math. No loop stopping rule or additional algorithm is supplied or invented.

## Reconstruction limits
Coordinates, typefaces, linework, ghost-book outline, and color gradients are estimated from pixels. Fine-grained illustrated details use nine original raster crops, placed 14 times. Background transparency is applied to icon crops. All surrounding labels, matrices, axes, arrows, graphs, and panel outlines are native SVG. Tiny icon lettering remains raster. The original is unchanged. Font identity and original vector topology cannot be recovered from PNG. Scientific accuracy beyond visual transcription is not assessed.
