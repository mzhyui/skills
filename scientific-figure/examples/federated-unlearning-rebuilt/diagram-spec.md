# Figure reconstruction specification

Source: `../图片2.png`, SHA-256 `bdd66580da64f2d098e355be4f93bc62985dadd225acca718998357d0e324b6d`, 2043 × 783 pixels. The image itself supplies all content; no manuscript or implementation was provided. This is a faithful graphical reconstruction, not validation of the depicted algorithm.

Canvas: original aspect ratio, white background; assumed print width 14 inches. Left column has Client 1, Client 2, Client C, databases and neural networks. Client C carries a departure icon. The central server exchanges learning (blue) and unlearning (red) messages. Green connector lines magnify Client 1 into the top privacy panel. The top-right annotation defines arrow colors.

Stages and source anchors:
- privacy (x690–1673, y22–194): update g_t^c → Receive Budget → privacy budget → Gaussion Noise → differential-private update tilde g_t^c. Preserve the source spelling “Gaussion”.
- learning (x689–1993, y208–476): client updates → Aggregate Update → global models → Select Models (lambda) → selected models → Select Updates (gamma) → selected updates.
- unlearning (x686–1993, y493–762): remaining-client updates → Compute Direction Consistency → direction-angle diagram → Calibrate updates → calibrated vector → Aggregate Update → unlearned model.

Notation: preserve tilde/bar/hat distinctions, t/T/T′, C/C′ and C_t^r. Client C update uses uppercase C; requested-client vector superscripts use lowercase c_r. Equations are transcribed in scene-graph.json and the generator. Norms, cosine, inner product and the ratio retain their source placement.

Every listed arrow follows the source direction. No convergence condition or interpretation of lambda/gamma is supplied; none is added. Network connectivity, shaded update cells and hatch strokes are illustrative geometry rather than measured values. Font identity and exact hand-drawn noise strokes are unrecoverable from this raster.
