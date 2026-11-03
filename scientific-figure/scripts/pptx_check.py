#!/usr/bin/env python3
"""Inventory PowerPoint object editability without claiming visual validation."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
KINDS = {"sp": "shape", "cxnSp": "connector", "pic": "picture",
         "grpSp": "group", "graphicFrame": "graphic_frame"}


def inspect_pptx(path: Path) -> dict:
    """Read slide order and inventory DrawingML objects, including grouped parts."""
    report = {
        "source": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "inspected",
        "slides": [],
        "errors": [],
        "warnings": [],
        "visual_review": "not_performed",
        "application_edit_test": "not_performed",
        "scientific_fidelity": "not_performed",
        "limitations": [
            "Counts describe DrawingML structure, not visual fidelity or ease of editing.",
            "Connector targets are checked; interactive reattachment is not tested.",
            "Text fonts and geometry inherited from masters/themes are not resolved.",
            "Master/layout/background artwork and notes are outside the slide-object inventory.",
            "Pictures (including SVG) are not counted as native component geometry.",
            "Graphic frames may contain tables/charts; their editability is not assessed.",
        ],
    }
    with ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        relationships = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        targets = {rel.attrib["Id"]: rel for rel in relationships}
        size = presentation.find("p:sldSz", NS)
        if size is not None:
            report["size_in"] = [int(size.attrib[key]) / 914400 for key in ("cx", "cy")]
        for number, slide_id in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            relationship = targets[slide_id.attrib[f"{{{NS['r']}}}id"]]
            if relationship.get("TargetMode") == "External":
                raise ValueError("external slide relationships are unsupported")
            target = relationship.attrib["Target"]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("ppt", target))
            if not member.startswith("ppt/slides/"):
                raise ValueError(f"unexpected slide target: {member}")
            root = ET.fromstring(archive.read(member))
            tree = root.find("p:cSld/p:spTree", NS)
            if tree is None:
                raise ValueError(f"missing shape tree: {member}")
            objects = []

            def walk(parent, group: str | None = None) -> None:
                for element in parent:
                    tag = element.tag.rsplit("}", 1)[-1]
                    if tag not in KINDS:
                        continue
                    properties = element.find("./*/p:cNvPr", NS)
                    if properties is None:
                        raise ValueError(f"object without cNvPr: {member}")
                    body = element.find("p:txBody", NS)
                    paragraphs = [] if body is None else body.findall("a:p", NS)
                    # Read only text runs and explicit line breaks, not XML whitespace.
                    value = "\n".join(
                        "".join((node.text or "") if node.tag == f"{{{NS['a']}}}t" else "\n"
                                for node in paragraph.iter()
                                if node.tag in {f"{{{NS['a']}}}t", f"{{{NS['a']}}}br"})
                        for paragraph in paragraphs)
                    kind = KINDS[tag]
                    nonvisual = element.find("p:nvSpPr/p:cNvSpPr", NS)
                    if kind == "shape" and nonvisual is not None and nonvisual.get("txBox") in {"1", "true"}:
                        kind = "text_box"
                    item = {"id": properties.attrib["id"], "name": properties.get("name", ""),
                            "kind": kind, "parent_group": group, "text": value}
                    if tag == "cxnSp":
                        item["connections"] = {
                            end: conn.attrib
                            for end in ("stCxn", "endCxn")
                            if (conn := element.find(f"p:nvCxnSpPr/p:cNvCxnSpPr/a:{end}", NS)) is not None
                        }
                    objects.append(item)
                    if tag == "grpSp":
                        walk(element, item["id"])

            walk(tree)
            counts = Counter(item["kind"] for item in objects)
            counts["editable_text_objects"] = sum(bool(item["text"].strip()) for item in objects)
            counts["attached_connectors"] = sum(
                len(item.get("connections", {})) == 2 for item in objects)
            ids = [item["id"] for item in objects]
            for identifier, count in Counter(ids).items():
                if count > 1:
                    report["errors"].append(f"Slide {number}: duplicate object ID {identifier}")
            for item in objects:
                if not item["name"]:
                    report["warnings"].append(f"Slide {number}: unnamed {item['kind']} {item['id']}")
                for connection in item.get("connections", {}).values():
                    if connection.get("id") not in ids:
                        report["errors"].append(f"Slide {number}: {item['name']} has missing connection target {connection.get('id')}")
            if not counts["editable_text_objects"]:
                report["warnings"].append(f"Slide {number}: no native editable text found")
            if not (counts["shape"] or counts["connector"]):
                report["warnings"].append(f"Slide {number}: no native diagram geometry found")
            if counts["picture"]:
                report["warnings"].append(f"Slide {number}: {counts['picture']} picture objects need editability disclosure")
            report["slides"].append({"number": number, "part": member,
                                     "counts": dict(counts), "objects": objects})
    if not report["slides"]:
        report["errors"].append("Presentation contains no slides")
    if report["errors"]:
        report["status"] = "invalid"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--output", type=Path, help="write JSON to a new file; default: stdout")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("report output already exists; choose a new path")
    try:
        report = inspect_pptx(args.pptx)
    except (OSError, BadZipFile, ET.ParseError, KeyError, ValueError) as exc:
        parser.error(f"cannot inspect PPTX: {exc}")
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        sys.stdout.write(payload)
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
