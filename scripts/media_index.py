#!/usr/bin/env python3
"""Low-context PPTX media indexing, review batching, and selected extraction."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import posixpath
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MAX_THUMBNAIL = (640, 640)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _slide_number(name: str) -> int | None:
    match = re.search(r"slide(\d+)\.xml\.rels$", name)
    return int(match.group(1)) if match else None


def _media_relationships(archive: zipfile.ZipFile) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = {}
    for name in archive.namelist():
        slide_number = _slide_number(name)
        if slide_number is None:
            continue
        try:
            root = ET.fromstring(archive.read(name))
        except ET.ParseError:
            continue
        slide_dir = posixpath.dirname(posixpath.dirname(name))
        for rel in root.findall(f"{{{REL_NS}}}Relationship"):
            target = rel.attrib.get("Target", "")
            if "/media/" not in f"/{target}" and not target.startswith("../media/"):
                continue
            resolved = posixpath.normpath(posixpath.join(slide_dir, target))
            found.setdefault(resolved, []).append(
                {"slide_id": slide_number, "relationship_id": rel.attrib.get("Id"), "purpose": "unknown"}
            )
    return found


def _purpose_candidate(width: int | None, height: int | None, size: int, extension: str) -> str:
    if extension.lower() in {".emf", ".wmf", ".svg"}:
        return "vector_or_diagram"
    if not width or not height:
        return "unknown"
    ratio = width / height
    if width <= 256 and height <= 256:
        return "icon_or_logo"
    if ratio >= 2.4 or ratio <= 0.42:
        return "banner_or_crop"
    if size > 800_000 and width >= 1200:
        return "photo_or_screenshot"
    return "figure_or_illustration"


def _thumbnail(data: bytes, output: Path) -> tuple[int | None, int | None, str | None]:
    from PIL import Image, ImageOps

    try:
        with Image.open(io.BytesIO(data)) as opened:
            width, height = opened.size
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail(MAX_THUMBNAIL)
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, format="PNG", optimize=True)
            return width, height, image.mode
    except (OSError, ValueError):
        return None, None, None


def _contact_sheets(items: list[dict], root: Path, batch_size: int) -> list[str]:
    from PIL import Image, ImageDraw, ImageFont

    sheet_dir = root / "media-contact-sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    results = []
    usable = [item for item in items if item.get("thumbnail")]
    for batch_index in range(0, len(usable), batch_size):
        batch = usable[batch_index : batch_index + batch_size]
        cell_w, cell_h = 360, 300
        canvas = Image.new("RGB", (cell_w * 2, cell_h * 2), "white")
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        for cell, item in enumerate(batch):
            row, col = divmod(cell, 2)
            x, y = col * cell_w, row * cell_h
            with Image.open(root / item["thumbnail"]) as thumb:
                image = thumb.convert("RGB")
                image.thumbnail((cell_w - 24, cell_h - 54))
                px = x + (cell_w - image.width) // 2
                py = y + 10 + (cell_h - 54 - image.height) // 2
                canvas.paste(image, (px, py))
            label = f"{item['id']}  {item['width'] or '?'}×{item['height'] or '?'}  {item['sha256'][:10]}"
            draw.text((x + 10, y + cell_h - 34), label, fill="#17252A", font=font)
            draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline="#9AAEB2", width=1)
        output = sheet_dir / f"batch-{batch_index // batch_size + 1:03d}.png"
        canvas.save(output, format="PNG", optimize=True)
        results.append(output.relative_to(root).as_posix())
    return results


def index_pptx(pptx_path: Path, output_root: Path, batch_size: int = 4) -> dict:
    """Index embedded media without exposing original bytes in JSON or stdout."""
    if not 1 <= batch_size <= 4:
        raise ValueError("batch_size must be between 1 and 4")
    pptx_path = pptx_path.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    by_hash = {}
    with zipfile.ZipFile(pptx_path) as archive:
        relationships = _media_relationships(archive)
        media_names = sorted(name for name in archive.namelist() if name.startswith("ppt/media/") and not name.endswith("/"))
        for name in media_names:
            data = archive.read(name)
            digest = hashlib.sha256(data).hexdigest()
            if digest in by_hash:
                by_hash[digest]["archive_paths"].append(name)
                by_hash[digest]["occurrences"].extend(relationships.get(name, []))
                continue
            media_id = f"M{len(by_hash) + 1:03d}"
            thumb_rel = Path("media-thumbnails") / f"{digest[:16]}.png"
            width, height, mode = _thumbnail(data, output_root / thumb_rel)
            extension = Path(name).suffix.lower()
            by_hash[digest] = {
                "id": media_id,
                "sha256": digest,
                "bytes": len(data),
                "extension": extension,
                "content_type": mimetypes.guess_type(name)[0] or "application/octet-stream",
                "width": width,
                "height": height,
                "mode": mode,
                "archive_paths": [name],
                "occurrences": relationships.get(name, []),
                "purpose_candidate": _purpose_candidate(width, height, len(data), extension),
                "thumbnail": thumb_rel.as_posix() if (output_root / thumb_rel).is_file() else None,
                "privacy_review": "pending",
                "rights_review": "pending",
                "adoption": "pending",
            }
    items = list(by_hash.values())
    for item in items:
        item["occurrences"] = sorted(
            {(occ.get("slide_id"), occ.get("relationship_id")): occ for occ in item["occurrences"]}.values(),
            key=lambda value: (value.get("slide_id") or 0, value.get("relationship_id") or ""),
        )
    report = {
        "format": "mpa-media-index-v1",
        "generated_at": _now(),
        "source_pptx": str(pptx_path),
        "source_sha256": hashlib.sha256(pptx_path.read_bytes()).hexdigest(),
        "deduplicated": True,
        "contains_original_bytes": False,
        "thumbnail_max_pixels": list(MAX_THUMBNAIL),
        "batch_size": batch_size,
        "media": items,
    }
    report["contact_sheets"] = _contact_sheets(items, output_root, batch_size)
    _write_json(output_root / "media_index.json", report)
    return report


def extract_selected(index: dict, output_dir: Path, selectors: list[str]) -> list[dict]:
    if not selectors:
        raise ValueError("at least one --select ID or SHA-256 is required")
    selected = []
    for item in index.get("media", []):
        if any(value == item["id"] or item["sha256"].startswith(value.lower()) for value in selectors):
            selected.append(item)
    missing = [value for value in selectors if not any(value == item["id"] or item["sha256"].startswith(value.lower()) for item in selected)]
    if missing:
        raise ValueError("unknown media selector(s): " + ", ".join(missing))
    source = Path(index["source_pptx"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != index["source_sha256"]:
        raise RuntimeError("source PPTX hash changed; re-run media-index")
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    with zipfile.ZipFile(source) as archive:
        for item in selected:
            archive_path = item["archive_paths"][0]
            data = archive.read(archive_path)
            digest = hashlib.sha256(data).hexdigest()
            if digest != item["sha256"]:
                raise RuntimeError(f"embedded media hash mismatch for {item['id']}")
            output = output_dir / f"{item['id']}-{digest[:12]}{item['extension']}"
            output.write_bytes(data)
            records.append({"id": item["id"], "sha256": digest, "path": str(output), "bytes": len(data)})
    return records


def prepare_review(index: dict, review_path: Path, batch_size: int = 4) -> dict:
    if not 1 <= batch_size <= 4:
        raise ValueError("batch_size must be between 1 and 4")
    old = json.loads(review_path.read_text(encoding="utf-8")) if review_path.is_file() else {}
    old_decisions = {item["id"]: item for item in old.get("decisions", [])}
    decisions = []
    for item in index.get("media", []):
        decision = old_decisions.get(item["id"], {})
        decisions.append(
            {
                "id": item["id"],
                "sha256": item["sha256"],
                "purpose": decision.get("purpose"),
                "privacy": decision.get("privacy"),
                "rights": decision.get("rights"),
                "adopt": decision.get("adopt"),
                "reviewer": decision.get("reviewer"),
                "reviewed_at": decision.get("reviewed_at"),
            }
        )
    pending = [item["id"] for item in decisions if not all(item.get(key) is not None for key in ("purpose", "privacy", "rights", "adopt"))]
    report = {
        "format": "mpa-media-review-v1",
        "source_sha256": index.get("source_sha256"),
        "batch_size": batch_size,
        "pending": pending,
        "next_batch": pending[:batch_size],
        "complete": not pending,
        "decisions": decisions,
    }
    _write_json(review_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    index_parser = sub.add_parser("index")
    index_parser.add_argument("pptx", type=Path)
    index_parser.add_argument("output", type=Path)
    index_parser.add_argument("--batch-size", type=int, default=4)
    extract_parser = sub.add_parser("extract")
    extract_parser.add_argument("index", type=Path)
    extract_parser.add_argument("output", type=Path)
    extract_parser.add_argument("--select", action="append", required=True)
    review_parser = sub.add_parser("review")
    review_parser.add_argument("index", type=Path)
    review_parser.add_argument("review", type=Path)
    review_parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    if args.command == "index":
        result = index_pptx(args.pptx, args.output, args.batch_size)
    else:
        index = json.loads(args.index.read_text(encoding="utf-8"))
        if args.command == "extract":
            result = extract_selected(index, args.output, args.select)
        else:
            result = prepare_review(index, args.review, args.batch_size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
