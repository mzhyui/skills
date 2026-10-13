#!/usr/bin/env python3
"""Export a self-contained SVG with Inkscape; report bounded mechanical checks.

Python standard library only. Exit 0: rendered (warnings still need review).
Exit 1: runtime/export failure. Exit 2: invalid input or existing output.
This is not a security sanitizer or a scientific/visual correctness certificate.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
NONDISPLAY = {"defs", "marker", "pattern", "clipPath", "mask", "symbol", "metadata"}
GRAPHICS = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "image", "use"}


def tag(element):
    return element.tag.rsplit("}", 1)[-1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def run(command, env):
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=90)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stderr[-2000:]}")
    return result.stdout.strip(), result.stderr.strip()


def inspect_svg(root, width_in, min_font):
    errors, warnings, samples = [], [], []
    if root.tag != f"{{{SVG}}}svg":
        raise ValueError("Root must be SVG in the standard SVG namespace")
    try:
        viewbox = [float(v) for v in re.split(r"[\s,]+", root.attrib["viewBox"].strip())]
    except (KeyError, ValueError) as exc:
        raise ValueError("A numeric viewBox is required") from exc
    if len(viewbox) != 4 or not all(map(math.isfinite, viewbox)) or min(viewbox[2:]) <= 0:
        raise ValueError("viewBox must have four finite values and positive width/height")
    ids = [e.get("id") for e in root.iter() if e.get("id")]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append("Duplicate IDs: " + ", ".join(duplicates))
    id_set = set(ids)
    refs = []
    has_css = any(tag(e) == "style" for e in root.iter())
    if has_css:
        warnings.append("Stylesheets present: font-size checks skipped; review computed typography manually.")
    for e in root.iter():
        kind = tag(e)
        if kind in {"script", "foreignObject"}:
            errors.append(f"Unsupported element: {kind}")
        if kind == "image":
            warnings.append("Raster image present; check effective resolution and disclose mixed vector/raster content.")
        values = list(e.attrib.values()) + ([e.text or ""] if kind == "style" else [])
        for key, value in e.attrib.items():
            if key.rsplit("}", 1)[-1] == "href":
                if value.startswith("#"):
                    refs.append(value[1:])
                elif not (kind == "image" and re.match(r"^data:image/(png|jpeg|webp);base64,", value)):
                    errors.append(f"Nonlocal or unsupported href on {e.get('id', kind)}; embed the asset first")
        for value in values:
            if "@import" in value.lower():
                errors.append("CSS imports are unsupported; make the SVG self-contained")
            for ref in re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", value, re.I):
                ref = ref.strip()
                if ref.startswith("#"):
                    refs.append(ref[1:])
                else:
                    errors.append("External CSS URL is unsupported; embed the asset first")
    for ref in sorted(set(refs) - id_set):
        errors.append(f"Unresolved local reference: #{ref}")

    # IDs on visible objects allow Inkscape's rendered bounds to be reconciled.
    visible, texts = [], []
    units = {"": 1, "px": 1, "pt": 96 / 72, "pc": 16, "in": 96, "cm": 96 / 2.54, "mm": 96 / 25.4}

    def walk(e, inherited, transformed=False, hidden=False):
        style = dict(inherited)
        for key in ("font-size", "display", "visibility"):
            if key in e.attrib:
                style[key] = e.attrib[key]
        style.update(dict(part.split(":", 1) for part in e.get("style", "").split(";") if ":" in part))
        style = {k.strip(): v.strip() for k, v in style.items()}
        transformed = transformed or bool(e.get("transform")) or "transform" in style or (e is not root and tag(e) == "svg")
        hidden = hidden or tag(e) in NONDISPLAY or style.get("display") == "none"
        shown = not hidden and style.get("visibility") not in {"hidden", "collapse"}
        if tag(e) in GRAPHICS and shown:
            if not e.get("id"):
                identifier = f"render-check-{len(visible) + 1}"
                while identifier in id_set:
                    identifier += "x"
                e.set("id", identifier)
                id_set.add(identifier)
            visible.append(e.get("id"))
            if tag(e) == "text":
                texts.append(e.get("id"))
        if tag(e) in {"text", "tspan"} and shown and not has_css:
            size = style.get("font-size", "16")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]*)?|\.[0-9]+)([a-z]*)", size)
            if transformed or not match or match[2] not in units:
                warnings.append(f"Manual font-size check needed: {e.get('id', tag(e))} (transform or relative/unsupported size)")
            else:
                points = float(match[1]) * units[match[2]] * 72 * width_in / viewbox[2]
                samples.append({"id": e.get("id", tag(e)), "size_pt": round(points, 3)})
                if points < min_font - 0.01:
                    warnings.append(f"Small text: {e.get('id', tag(e))} is {points:.2f} pt; target minimum {min_font:g} pt")
        for child in e:
            walk(child, style, transformed, hidden)

    walk(root, {})
    if not texts:
        warnings.append("No editable visible text elements found; check whether labels are outlined or rasterized.")
    return viewbox, visible, texts, samples, errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--width-in", type=positive, default=7)
    parser.add_argument("--dpi", type=positive, default=300)
    parser.add_argument("--min-font-pt", type=positive, default=8)
    parser.add_argument("--overwrite", action="store_true", help="replace named exports, never the input SVG")
    args = parser.parse_args()
    source = args.svg.resolve()
    out = args.out_dir.resolve()
    outputs = {key: out / name for key, name in {
        "svg": "figure.svg", "pdf": "figure.pdf", "png": "figure.png",
        "size_preview": "figure-size-preview.png", "report": "render-report.json"}.items()}
    if source in outputs.values():
        parser.error("output paths must not replace the input SVG")
    existing = [str(p) for p in outputs.values() if p.exists()]
    if existing and not args.overwrite:
        parser.error("outputs already exist; choose a fresh directory or use --overwrite: " + ", ".join(existing))
    report = {
        "source": str(source), "status": "not_rendered", "errors": [], "warnings": [],
        "scientific_review": "not_performed", "visual_review": "not_performed",
        "limitations": [
            "Checks do not establish scientific fidelity or visual quality.",
            "Font audit handles presentation/inline absolute sizes without transforms; CSS and relative sizes require manual review.",
            "Bounds and text intersections are heuristics; masks, clipping, hidden CSS, filters, strokes, and markers require visual inspection.",
            "Font availability/substitution, glyph correctness, arrows, scene-graph consistency, and raster resolution need separate review.",
            "The 96 dpi preview approximates manuscript scale; actual display zoom/density can differ."
        ]}
    out.mkdir(parents=True, exist_ok=True)
    try:
        report["source_sha256"] = sha(source)
        raw = source.read_bytes()
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ValueError("SVG doctypes/entities are unsupported; use a standalone plain SVG")
        root = ET.fromstring(raw)
        vb, visible, texts, fonts, errors, warnings = inspect_svg(root, args.width_in, args.min_font_pt)
        report.update(errors=errors, warnings=warnings, font_samples=fonts, editable_text_count=len(texts))
        if errors:
            report["status"] = "invalid_input"
            return 2
        height_in = args.width_in * vb[3] / vb[2]
        report["target"] = {"width_in": args.width_in, "height_in": height_in, "dpi": args.dpi, "min_font_pt": args.min_font_pt}
        root.set("width", f"{args.width_in:.10g}in")
        root.set("height", f"{height_in:.10g}in")
        # Root CSS width/height could otherwise override physical dimensions.
        root_style_keys = {part.split(":", 1)[0].strip() for part in root.get("style", "").split(";") if ":" in part}
        if root_style_keys & {"width", "height"}:
            raise ValueError("Remove root CSS width/height before normalizing physical size")
        if any(tag(e) == "style" and re.search(r"(?:^|[;{\s])(?:width|height)\s*:", e.text or "") for e in root.iter()):
            raise ValueError("Stylesheet width/height rules require manual normalization")
        ET.ElementTree(root).write(outputs["svg"], encoding="utf-8", xml_declaration=True)
        inkscape = shutil.which("inkscape")
        if not inkscape:
            raise RuntimeError("Inkscape is required for this helper; install it or use a documented alternative exporter")
        with tempfile.TemporaryDirectory(prefix="scientific-figure-inkscape-") as profile:
            env = dict(os.environ, INKSCAPE_PROFILE_DIR=profile, XDG_CACHE_HOME=profile)
            report["renderer"], _ = run([inkscape, "--version"], env)
            commands, messages = [], []
            for key, extra in [("pdf", []), ("png", [f"--export-dpi={args.dpi}"]), ("size_preview", ["--export-dpi=96"])]:
                command = [inkscape, str(outputs["svg"]), "--export-area-page", f"--export-filename={outputs[key]}", *extra]
                commands.append(command)
                _, stderr = run(command, env)
                if stderr:
                    messages.append(stderr)
                if not outputs[key].exists() or not outputs[key].stat().st_size:
                    raise RuntimeError(f"Export missing or empty: {outputs[key]}")
            query, stderr = run([inkscape, str(outputs["svg"]), "--query-all"], env)
            if stderr:
                messages.append(stderr)
            report["commands"] = commands
            report["renderer_messages"] = sorted(set(messages))
        bounds = {}
        for line in query.splitlines():
            parts = line.rsplit(",", 4)
            if len(parts) == 5:
                try:
                    box = list(map(float, parts[1:]))
                    if all(map(math.isfinite, box)):
                        bounds[parts[0]] = box
                except ValueError:
                    pass
        report["rendered_bounds_px"] = {k: bounds[k] for k in visible if k in bounds}
        missing = set(visible) - set(bounds)
        if missing:
            report["warnings"].append("Bounds unavailable for: " + ", ".join(sorted(missing)))
        for key in visible:
            if key in bounds:
                x, y, w, h = bounds[key]
                if x < -0.5 or y < -0.5 or x + w > args.width_in * 96 + 0.5 or y + h > height_in * 96 + 0.5:
                    report["warnings"].append(f"Possible canvas overflow: {key}")
        for i, first in enumerate(texts):
            for second in texts[i + 1:]:
                if first not in bounds or second not in bounds:
                    continue
                x1, y1, w1, h1 = bounds[first]
                x2, y2, w2, h2 = bounds[second]
                if min(x1 + w1, x2 + w2) - max(x1, x2) > 0.5 and min(y1 + h1, y2 + h2) - max(y1, y2) > 0.5:
                    report["warnings"].append(f"Possible text overlap: {first} / {second}")
        report["outputs"] = {k: {"file": p.name, "sha256": sha(p)} for k, p in outputs.items() if k != "report"}
        report["warnings"] = sorted(set(report["warnings"]))
        report["status"] = "rendered_with_warnings" if report["warnings"] else "mechanical_checks_passed"
        return 0
    except (ValueError, ET.ParseError) as exc:
        report["errors"].append(str(exc))
        report["status"] = "invalid_input"
        return 2
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report["errors"].append(str(exc))
        report["status"] = "export_failed"
        return 1
    finally:
        outputs["report"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{report['status']}: {outputs['report']}")
        for error in report["errors"]:
            print(error, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
