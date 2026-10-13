# Archival examples

These five bundles were imported from the plot project's `examples/` directory. All 93 original files are preserved byte-for-byte, including generators, exports, provenance records, comparison images, assets, and historical validation. This index is new integration documentation.

| Bundle | Preview | Editable source | PDF | Generator status |
| --- | --- | --- | --- | --- |
| Workflow | [PNG](workflow/exports/figure.png) | [SVG](workflow/figure.svg) | [PDF](workflow/exports/figure.pdf) | Self-contained [workflow generator](../assets/example-workflow.py) |
| FU-framework | [PNG](fu-framework-rebuilt/preview.png) | [SVG](fu-framework-rebuilt/figure.svg) | [PDF](fu-framework-rebuilt/exports/figure.pdf) | Rebuildable from bundled `source/fu_framework.svg` |
| Federated unlearning | [PNG](federated-unlearning-rebuilt/preview.png) | [SVG](federated-unlearning-rebuilt/figure.svg) | [PDF](federated-unlearning-rebuilt/exports/figure.pdf) | Original `examples/图片2.png` is missing |
| Batman | [PNG](batman-rebuilt/preview.png) | [SVG](batman-rebuilt/figure.svg) | [PDF](batman-rebuilt/exports/figure.pdf) | Original `examples/图片.png` is missing; cropped raster assets are bundled |
| GBHINDER | [PNG](gbhinder-rebuilt/preview.png) | [SVG](gbhinder-rebuilt/figure.svg) | [PDF](gbhinder-rebuilt/exports/figure.pdf) | Original `examples/图片4.png` is missing |

The missing paths above are relative to the skill directory. Each affected generator expects its original PNG in its parent directory, alongside the example subdirectories. Finished SVGs and exports remain available and can be rendered independently of these missing references. Preserved source hashes describe the originals; comparisons and cropped assets are not substitutes for the missing files.

Use the [current usage guide](../README.md) for portable commands. The READMEs, generator-emitted documentation, validation records, and render reports inside each bundle are historical. Their `figures/`, `skills/scientific-figure/`, and absolute paths refer to the source project's layout. They are preserved as provenance, not current commands or instructions to write back into that layout. Historical checks are not newly performed checks of this integration.

Run generators only in working copies. In particular, do not follow the FU-framework archive's historical instruction to copy its output to a parent `fu_framework.svg`; the bundled editable master is already linked above. All reconstructed research figures retain their original limitations and do not establish scientific correctness of the depicted methods.
