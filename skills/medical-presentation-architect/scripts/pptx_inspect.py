#!/usr/bin/env python3
"""Factual, non-clinical PPTX inventory; marks observations, never infers audience or intent."""

import argparse
import hashlib
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
EMU = 914400


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(shape):
    return (shape.left, shape.top, shape.width, shape.height)


def overlap(a, b):
    x = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    y = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return x * y / (a[2] * a[3]) if a[2] * a[3] else 0


def inspect(path):
    path = Path(path).resolve()
    prs = Presentation(path)
    hidden = []
    fill_images = {}
    relation_targets = {}
    with ZipFile(path) as z:
        names = set(z.namelist())
        for i in range(1, len(prs.slides) + 1):
            slide_name = f"ppt/slides/slide{i}.xml"
            if slide_name not in names:
                continue
            root = ET.fromstring(z.read(slide_name))
            sl = root if root.tag.endswith("}sld") else root.find(".//p:sld", NS)
            if sl is not None and sl.attrib.get("show") == "0":
                hidden.append(i)
            if any(el.attrib.get("hidden") == "1" for el in root.iter()):
                hidden.append(i)
            relpath = f"ppt/slides/_rels/slide{i}.xml.rels"
            mapping = {}
            if relpath in names:
                relroot = ET.fromstring(z.read(relpath))
                mapping = {el.attrib.get("Id"): el.attrib.get("Target") for el in relroot}
            fill = []
            for blip in root.findall(".//a:blip", NS):
                rid = blip.attrib.get("{%s}embed" % NS["r"])
                if rid:
                    fill.append(mapping.get(rid, rid))
            if fill:
                fill_images[i] = fill
            relation_targets[i] = mapping
    inventory = []
    notes_fingerprints = {}
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        observ = []
        pictures = sum(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slide.shapes)
        tables = sum(bool(getattr(sh, "has_table", False)) for sh in slide.shapes)
        charts = sum(bool(getattr(sh, "has_chart", False)) for sh in slide.shapes)
        ordered = list(slide.shapes)
        for ix, sh in enumerate(ordered):
            if sh.has_text_frame and sh.text.strip():
                texts.append(" ".join(sh.text.split()))
            if sh.has_table:
                for row in sh.table.rows:
                    texts.extend(c.text.strip() for c in row.cells if c.text.strip())
            if sh.has_chart:
                observ.append(f"native chart: {sh.name}")
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                for prior in ordered[:ix]:
                    if prior.has_text_frame and prior.text.strip() and overlap(box(prior), box(sh)) > 0.65:
                        observ.append(f"possible picture over text shape {prior.name}")
        if i in fill_images:
            observ.append(f"picture fills/background relationships: {len(fill_images[i])}")
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            ns = "missing"
        else:
            nh = hashlib.sha256(notes.encode()).hexdigest()
            ns = "present"
            notes_fingerprints.setdefault(nh, []).append(i)
        if i in hidden:
            observ.append("slide/shape marked hidden in OOXML")
        text = " | ".join(texts)
        inventory.append(
            {
                "slide_id": f"S{i:03}",
                "page": i,
                "tags": [],
                "visible_summary": text,
                "sources": [],
                "notes_status": ns,
                "observations": observ
                + [
                    f"structural counts: pictures={pictures}, picture_fills={len(fill_images.get(i, []))}, tables={tables}, charts={charts}, shapes={len(ordered)}"
                ],
            }
        )
    for fp, pages in notes_fingerprints.items():
        if len(pages) > 1:
            for idx in pages:
                inventory[idx - 1]["notes_status"] = "identical_to_other_pages"
                inventory[idx - 1]["observations"].append(
                    "notes content hash shared by pages " + ",".join(map(str, pages))
                )
    return {
        "visual_review": "not_available",
        "files": [
            {
                "path": path.name,
                "sha256": digest(path),
                "kind": "pptx",
                "observed": json.dumps(
                    {
                        "slide_count": len(prs.slides),
                        "hidden_pages": sorted(set(hidden)),
                        "slide_width_in": round(prs.slide_width / EMU, 3),
                        "slide_height_in": round(prs.slide_height / EMU, 3),
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "slides": inventory,
        "notes": "Machine inventory records visible text and OOXML structure only; a human still must inspect rendered pages and interpret content.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pptx", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    data = inspect(a.pptx)
    raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        a.output.write_text(raw, encoding="utf-8")
        print(a.output)
    else:
        print(raw)


if __name__ == "__main__":
    main()
