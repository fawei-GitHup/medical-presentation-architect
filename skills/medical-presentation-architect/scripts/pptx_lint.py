#!/usr/bin/env python3
"""Inspect OOXML structure, hidden elements, text/image occlusion and note similarity."""

import argparse
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def overlap(a, b):
    ix = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return ix * iy / (a[2] * a[3]) if a[2] * a[3] else 0


def lint(path):
    prs = Presentation(path)
    errors = []
    warnings = []
    shape_count = 0
    hidden = []
    covers = []
    with ZipFile(path) as z:
        for name in z.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                root = ET.fromstring(z.read(name))
                slide_node = root if root.tag.endswith("}sld") else root.find(".//p:sld", NS)
                if slide_node is not None and slide_node.get("show", "1") == "0":
                    hidden.append(name)
                for sh in root.findall('.//*[@hidden="1"]'):
                    hidden.append(name + ":hidden-shape")
                tree = root.find(".//p:spTree", NS)
                xml_shapes = []
                if tree is not None:
                    for node in list(tree):
                        if node.tag.rsplit("}", 1)[-1] not in ("sp", "pic"):
                            continue
                        xfrm = node.find("./p:spPr/a:xfrm", NS)
                        if xfrm is None:
                            xfrm = node.find(".//a:xfrm", NS)
                        off = xfrm.find("a:off", NS) if xfrm is not None else None
                        ext = xfrm.find("a:ext", NS) if xfrm is not None else None
                        if off is None or ext is None:
                            continue
                        rect = tuple(int(off.attrib[k]) for k in ("x", "y")) + tuple(
                            int(ext.attrib[k]) for k in ("cx", "cy")
                        )
                        text = " ".join((x.text or "") for x in node.findall(".//a:t", NS)).strip()
                        is_image = (
                            node.tag.rsplit("}", 1)[-1] == "pic" or node.find("./p:spPr/a:blipFill", NS) is not None
                        )
                        xml_shapes.append((rect, text, is_image))
                    for ix, (rect, text, is_image) in enumerate(xml_shapes):
                        if is_image:
                            continue
                        for cover_rect, _, cover_is_image in xml_shapes[ix + 1 :]:
                            if cover_is_image and overlap(rect, cover_rect) > 0.65:
                                errors.append(f"{name}: picture/image fill may cover earlier text")
                relname = name.replace("slides/", "slides/_rels/") + ".rels"
                if relname in z.namelist():
                    relroot = ET.fromstring(z.read(relname))
                    relation_ids = {x.attrib.get("Id") for x in relroot}
                    for blip in root.findall(".//a:blip", NS):
                        rid = blip.attrib.get("{%s}embed" % NS["r"])
                        if rid and rid not in relation_ids:
                            errors.append(f"{name}: missing image relationship {rid}")
    if hidden:
        errors.append("hidden slides/shapes need explicit inclusion or removal: " + ", ".join(sorted(set(hidden))))
    for i, slide in enumerate(prs.slides, 1):
        ordered = list(slide.shapes)
        shape_count += len(ordered)
        for sh in ordered:
            if (
                sh.left < 0
                or sh.top < 0
                or sh.left + sh.width > prs.slide_width
                or sh.top + sh.height > prs.slide_height
            ):
                errors.append(f"slide {i} shape {sh.name}: outside canvas")
        # Drawing order follows shape order; later image on top of a text box may hide the words.
        for ti, t in enumerate(ordered):
            if not (t.has_text_frame and t.text.strip()):
                continue
            box = (t.left, t.top, t.width, t.height)
            for later in ordered[ti + 1 :]:
                if (
                    later.shape_type == MSO_SHAPE_TYPE.PICTURE
                    and overlap(box, (later.left, later.top, later.width, later.height)) > 0.65
                ):
                    covers.append(f'slide {i} text "{t.text[:45]}" is covered by {later.name}')
        note = slide.notes_slide.notes_text_frame.text.strip()
        if not note:
            warnings.append(f"slide {i}: speaker notes empty")
    if covers:
        errors.extend(covers)
    # Hidden content from a native table/chart can be overlooked by a screenshot; report structural presence.
    return {
        "path": str(Path(path).resolve()),
        "slides": len(prs.slides),
        "shapes": shape_count,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pptx", type=Path)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    r = lint(a.pptx)
    print(
        json.dumps(r, ensure_ascii=False, indent=2)
        if a.json
        else f"slides={r['slides']} shapes={r['shapes']} errors={len(r['errors'])} warnings={len(r['warnings'])}"
    )
    for x in r["errors"] + r["warnings"]:
        print(x)
    raise SystemExit(0 if r["passed"] else 1)


if __name__ == "__main__":
    main()
