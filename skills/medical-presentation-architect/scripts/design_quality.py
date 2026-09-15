#!/usr/bin/env python3
"""Deterministic design planning and visual-QA helpers for medical presentations."""

from __future__ import annotations

import math
import re
import copy
from collections import Counter
from pathlib import Path


ROLE_BY_LAYOUT = {
    "cover_center": "cover",
    "closing_center": "closing",
    "references_two_col": "reference",
    "number_cards": "evidence",
    "flow_horizontal": "workflow",
    "flow_with_warning": "safety",
    "decision_tree": "decision",
    "checklist_two_col": "assessment",
}

COMPOSITION_BY_LAYOUT = {
    "cover_center": "cover_hero",
    "closing_center": "closing_hero",
    "two_column": "split_editorial",
    "image_right_text_left": "text_image_split",
    "table_full": "evidence_table",
    "bullets_two_group": "paired_boundaries",
    "number_cards": "evidence_numbers",
    "three_images_row": "equipment_triptych",
    "flow_horizontal": "workflow_steps",
    "two_images_with_checks": "evidence_pair",
    "table_with_thumbs": "material_matrix",
    "decision_tree": "decision_tree",
    "flow_with_warning": "safety_protocol",
    "checklist_single": "process_checklist",
    "checklist_two_col": "printable_assessment",
    "three_points": "takeaway_sequence",
    "references_two_col": "references_summary",
}

HIGH_RISK_RE = re.compile(r"氢氟|\bHF\b|禁忌|危急|暴露|腐蚀|中毒|停止|不得|严禁|红线", re.I)
VERSION_RE = re.compile(
    r"\b(?:mg|ml|mm|μm|MPa|°C|min|分钟|秒|%|版|program|speed|IFU|SDS)\b|"
    r"剂量|浓度|温度|时间|材料|设备|软件|程序|指南|共识|灭菌",
    re.I,
)
RECOMMENDATION_RE = re.compile(r"推荐|优先|首选|应选择|更适合|不宜|禁忌|必须|适应证", re.I)


def infer_slide_role(slide: dict) -> str:
    if slide.get("role"):
        return slide["role"]
    layout = slide.get("layout", "")
    if layout in ROLE_BY_LAYOUT:
        return ROLE_BY_LAYOUT[layout]
    text = " ".join(str(slide.get(k, "")) for k in ("title", "content_type", "takeaway"))
    if HIGH_RISK_RE.search(text):
        return "safety"
    if re.search(r"流程|workflow|步骤", text, re.I):
        return "workflow"
    if re.search(r"证据|研究|数字|获益", text, re.I):
        return "evidence"
    return "content"


def infer_composition(slide: dict, visual_group: dict | None = None) -> str:
    visual_group = visual_group or {}
    return visual_group.get("composition") or COMPOSITION_BY_LAYOUT.get(
        slide.get("layout", ""), slide.get("layout", "freeform")
    )


def choose_composition(slide: dict, visual_group: dict, recent_compositions: list[str]) -> str:
    """Choose a content-appropriate composition and avoid a third consecutive repeat."""
    chosen = infer_composition(slide, visual_group)
    if len(recent_compositions) >= 2 and recent_compositions[-2:] == [chosen, chosen]:
        alternatives = {
            "text_image_split": "image_text_split",
            "split_editorial": "editorial_sequence",
            "evidence_table": "evidence_numbers",
            "workflow_steps": "workflow_swimlane",
        }
        return alternatives.get(chosen, chosen)
    return chosen


def enrich_visual_plan(plan: dict, visual: list[dict]) -> list[dict]:
    """Add explicit semantics to a legacy visual plan without changing its content or source bindings."""
    slides = {slide["id"]: slide for slide in plan.get("slides", [])}
    enriched = []
    recent = []
    for original in visual:
        group = copy.deepcopy(original)
        slide = slides.get(group["slide_id"], {"id": group["slide_id"], "layout": "freeform"})
        role = infer_slide_role(slide)
        composition = choose_composition(slide, group, recent)
        group.setdefault("role", role)
        group.setdefault("composition", composition)
        group.setdefault("background", "ink" if role in {"cover", "section", "closing"} else "paper")
        group.setdefault("visual_anchor", slide.get("visual_question") or slide.get("takeaway") or slide.get("title", ""))
        group.setdefault("reading_order", [element["id"] for element in sorted(group.get("elements", []), key=lambda e: e.get("z", 0))])
        group.setdefault("intentional_whitespace", "保留页边距与标题区，不用装饰填满空白")
        if role == "safety":
            group.setdefault("safety", {"severity": "high", "requires_visible_warning": True})
        for element in group.get("elements", []):
            purpose = str(element.get("purpose", ""))
            style = element.setdefault("style", {})
            if element["type"] == "number":
                style.setdefault("fill_token", "white")
                style.setdefault("border_token", "line")
                style.setdefault("font_role", "number")
                style.setdefault("weight", 700)
            elif element["type"] == "checklist":
                style.setdefault("fill_token", "white")
                style.setdefault("border_token", "line")
                style.setdefault("font_role", "body")
            elif role != "safety" and re.search(r"图注|署名|来源|脚注|编号|版权|局限|兜底|行动提示|总原则", purpose):
                style.setdefault("font_role", "caption")
                style.setdefault("text_token", "muted")
            elif role == "safety" and re.search(r"警示|红线|停止|暴露|氢氟|\bHF\b", str(element), re.I):
                style.setdefault("fill_token", "warning_pale")
                style.setdefault("border_token", "warning")
                style.setdefault("text_token", "warning")
                style.setdefault("font_role", "body")
                style.setdefault("weight", 700)
                style.setdefault("emphasis", "critical")
            elif composition in {"split_editorial", "paired_boundaries", "takeaway_sequence"} and element["type"] == "text":
                style.setdefault("fill_token", "white")
                style.setdefault("border_token", "line")
            if element["type"] == "image":
                image = element.setdefault("image", {})
                image.setdefault("fit", "contain")
                image.setdefault("focal_point", [0.5, 0.5])
                image.setdefault("show_frame", True)
            if element["type"] == "table":
                element.setdefault("table_style", {}).setdefault("banded_rows", True)
            if element.get("font_size") is not None:
                if style.get("font_role") in {"caption", "citation"}:
                    minimum = 10
                elif element["type"] == "table":
                    minimum = 13
                elif role in {"cover", "closing", "reference"}:
                    minimum = 12
                else:
                    minimum = 17
                element["font_size"] = max(float(element["font_size"]), minimum)
        if role == "assessment":
            assessment_text = " ".join(str(element.get("text", "")) for element in group.get("elements", []))
            if any(label not in assessment_text for label in ("姓名", "日期", "评价", "结果")):
                meta_id = f"{group['slide_id']}_assessment_meta"
                group["elements"].append(
                    {
                        "id": meta_id,
                        "type": "text",
                        "x": 1.25,
                        "y": 1.09,
                        "w": 11.45,
                        "h": 0.28,
                        "z": 3,
                        "purpose": "可打印考核信息栏",
                        "alt": "姓名、科室、日期、评价和结果填写栏",
                        "claim_ids": [],
                        "text": "姓名：________  科室：________  日期：____/____/____  评价：□通过 □需复训  结果：________",
                        "font_size": 11,
                        "style": {"font_role": "caption", "text_token": "muted", "align": "right"},
                    }
                )
                group["reading_order"] = [meta_id, *group.get("reading_order", [])]
        recent.append(composition)
        enriched.append(group)
    return enriched


def allocate_slide_content_budget(role: str, duration_seconds: int, visual_type: str = "") -> dict:
    body_chars = {
        "cover": 55,
        "section": 70,
        "closing": 55,
        "evidence": 260,
        "workflow": 300,
        "safety": 360,
        "assessment": 440,
        "reference": 900,
        "content": 330,
    }.get(role, 330)
    if visual_type in {"table", "chart", "image"}:
        body_chars = int(body_chars * 0.86)
    # Chinese teaching speech normally remains understandable around 3.2–4.0 characters/s.
    notes_chars = max(90, int(duration_seconds * 3.6))
    return {
        "title_chars": 28 if role not in {"cover", "closing"} else 42,
        "body_chars": body_chars,
        "notes_chars": notes_chars,
        "minimum_body_font_pt": 12 if role in {"cover", "closing", "reference"} else 17,
    }


def delivery_notes_text(slide: dict) -> str:
    structured = slide.get("speaker_notes")
    if isinstance(structured, dict):
        value = structured.get("delivery_notes", "")
        return "\n".join(value) if isinstance(value, list) else str(value)
    notes = str(slide.get("notes", ""))
    notes = re.split(r"\n\s*(?:证据|引用|Evidence|Sources|Claims)\s*[:：]", notes, 1, flags=re.I)[0]
    lines = [line.strip() for line in notes.splitlines() if line.strip()]
    if any(re.match(r"^(?:目标|讲述|互动提问|过渡|时间|图片归属)[:：]", line) for line in lines):
        spoken = [
            re.sub(r"^(?:讲述|互动提问)[:：]\s*", "", line)
            for line in lines
            if re.match(r"^(?:讲述|互动提问)[:：]", line)
        ]
        return "\n".join(spoken)
    return notes


def validate_notes_timing(slide: dict, language: str = "zh") -> list[str]:
    notes = re.sub(r"\s+", "", delivery_notes_text(slide))
    budget = allocate_slide_content_budget(
        infer_slide_role(slide), int(slide.get("duration_seconds", 60)), slide.get("content_type", "")
    )["notes_chars"]
    if len(notes) > budget:
        return [f"speaker notes {len(notes)} chars exceed the {budget}-char delivery budget"]
    return []


def split_speaker_and_evidence_notes(slide: dict, claims: dict, sources: dict) -> dict:
    """Return concise delivery notes plus auditable source references without duplicating ledgers."""
    delivery = delivery_notes_text(slide).strip()
    source_ids = sorted(
        {sid for cid in slide.get("claim_ids", []) for sid in claims.get(cid, {}).get("source_ids", [])}
    )
    evidence = []
    for sid in source_ids:
        source = sources.get(sid, {})
        ref = f"[{sid}] {source.get('title', '').strip()}"
        if source.get("year"):
            ref += f" ({source['year']})"
        locator = source.get("locator") or source.get("doi") or source.get("url")
        if locator:
            ref += f" — {locator}"
        evidence.append(ref)
    return {"delivery_notes": delivery, "evidence_notes": evidence, "claim_ids": slide.get("claim_ids", [])}


def geometry_signature(group: dict, width: float = 13.333, height: float = 7.5) -> tuple:
    records = []
    for element in group.get("elements", []):
        x = min(3, int((float(element.get("x", 0)) / width) * 4))
        y = min(2, int((float(element.get("y", 0)) / height) * 3))
        w = min(3, int((float(element.get("w", 0)) / width) * 4))
        h = min(2, int((float(element.get("h", 0)) / height) * 3))
        records.append((element.get("type"), x, y, w, h))
    return (group.get("composition", "legacy"), tuple(sorted(records)))


def occupied_area_ratio(group: dict, width: float = 13.333, height: float = 7.5) -> float:
    """Approximate visual occupancy on a coarse grid so overlapping elements are not double counted."""
    cols, rows = 32, 18
    grid = set()
    for element in group.get("elements", []):
        if element.get("purpose", "").lower() in {"background", "footer"}:
            continue
        x0 = max(0, min(cols, math.floor(float(element.get("x", 0)) / width * cols)))
        y0 = max(0, min(rows, math.floor(float(element.get("y", 0)) / height * rows)))
        x1 = max(0, min(cols, math.ceil((float(element.get("x", 0)) + float(element.get("w", 0))) / width * cols)))
        y1 = max(0, min(rows, math.ceil((float(element.get("y", 0)) + float(element.get("h", 0))) / height * rows)))
        for gx in range(x0, x1):
            for gy in range(y0, y1):
                grid.add((gx, gy))
    return round(len(grid) / (cols * rows), 3)


def visual_area_ratio(group: dict, width: float = 13.333, height: float = 7.5) -> float:
    visual_types = {"image", "table", "chart", "flow", "timeline", "decision"}
    area = sum(
        float(e.get("w", 0)) * float(e.get("h", 0))
        for e in group.get("elements", [])
        if e.get("type") in visual_types
    )
    return round(min(1.0, area / (width * height)), 3)


def has_visible_warning(group: dict) -> bool:
    if group.get("safety", {}).get("requires_visible_warning"):
        return True
    for element in group.get("elements", []):
        style = element.get("style", {})
        tokens = " ".join(str(style.get(k, "")) for k in ("fill_token", "text_token", "border_token"))
        if re.search(r"warn|danger|critical|red|amber", tokens, re.I):
            return True
        if re.search(r"⚠|警告|停止|科室确认项", str(element.get("text", "")), re.I):
            return True
    return False


def validate_printable_assessment(slide: dict, group: dict) -> list[str]:
    role = group.get("role") or infer_slide_role(slide)
    if role != "assessment" and not re.search(r"考核|核查清单|assessment", slide.get("title", ""), re.I):
        return []
    text = " ".join(str(e.get("text", "")) for e in group.get("elements", []))
    missing = [label for label in ("姓名", "日期", "评价", "结果") if label not in text]
    if not re.search(r"□|☐|☑|check", text, re.I):
        missing.append("checkboxes")
    if missing:
        return ["printable assessment missing " + ", ".join(missing)]
    return []


def detect_version_sensitive_claims(claims: list[dict]) -> list[str]:
    return [c.get("id", "") for c in claims if VERSION_RE.search(str(c.get("text") or c.get("claim") or ""))]


def separate_public_evidence_from_local_sop(claims: list[dict]) -> dict:
    public, local, unknown = [], [], []
    for claim in claims:
        scope = str(claim.get("scope", ""))
        kind = str(claim.get("kind", ""))
        if re.search(r"科室|本院|local|SOP|设备管理员|上报", scope + " " + str(claim), re.I):
            local.append(claim.get("id"))
        elif kind in {"clinical", "numeric", "guideline", "device"}:
            public.append(claim.get("id"))
        else:
            unknown.append(claim.get("id"))
    return {"public_evidence": public, "local_sop": local, "other": unknown}


def validate_recommendation_scope(slide: dict, claims: dict) -> list[str]:
    text = " ".join(str(slide.get(k, "")) for k in ("title", "takeaway", "notes"))
    if not RECOMMENDATION_RE.search(text):
        return []
    if not slide.get("claim_ids"):
        return ["recommendation language has no claim mapping"]
    weak = []
    for cid in slide.get("claim_ids", []):
        claim = claims.get(cid, {})
        if claim.get("status") not in {"verified", "synthetic"} or not str(claim.get("scope", "")).strip():
            weak.append(cid)
    return ["recommendation scope is unverified for " + ", ".join(weak)] if weak else []


def validate_decision_evidence(slide: dict, claims: dict, role: str | None = None) -> list[str]:
    """Block clinical decision trees that turn product specifications into treatment recommendations."""
    if (role or infer_slide_role(slide)) != "decision":
        return []
    bound = [claims.get(cid, {}) for cid in slide.get("claim_ids", [])]
    decision_grade = [
        claim
        for claim in bound
        if claim.get("status") == "verified"
        and (
            claim.get("kind") == "guideline"
            or re.search(r"指南|共识|比较|适应证|选择依据|临床决策", str(claim.get("scope", "")), re.I)
        )
    ]
    if not decision_grade:
        return ["clinical decision logic is supported only by product/specification evidence; convert it to a verification path or add decision-grade evidence"]
    return []


def run_design_quality_checks(plan: dict, visual: list[dict], claims: list[dict] | None = None) -> dict:
    groups = {g["slide_id"]: g for g in visual}
    claim_map = {c.get("id"): c for c in (claims or [])}
    warnings = []
    compositions = []
    signatures = []
    metrics = []
    for slide in plan.get("slides", []):
        sid = slide["id"]
        group = groups.get(sid, {"slide_id": sid, "elements": []})
        role = group.get("role") or infer_slide_role(slide)
        composition = infer_composition(slide, group)
        compositions.append((sid, composition))
        signatures.append((sid, geometry_signature(group, plan.get("width", 13.333), plan.get("height", 7.5))))
        body_chars = sum(len(str(e.get("text", ""))) for e in group.get("elements", []))
        font_elements = [
            e
            for e in group.get("elements", [])
            if e.get("type") in {"text", "number", "checklist", "table"} and e.get("font_size") is not None
        ]
        body_font_elements = [
            e
            for e in font_elements
            if e.get("style", {}).get("font_role") not in {"caption", "citation"}
            and not re.search(r"图注|署名|来源|脚注|版权", str(e.get("purpose", "")))
        ]
        min_font = min([float(e["font_size"]) for e in body_font_elements] or [999])
        occupancy = occupied_area_ratio(group, plan.get("width", 13.333), plan.get("height", 7.5))
        visual_ratio = visual_area_ratio(group, plan.get("width", 13.333), plan.get("height", 7.5))
        metrics.append(
            {
                "slide_id": sid,
                "role": role,
                "composition": composition,
                "body_chars": body_chars,
                "minimum_font_pt": None if min_font == 999 else min_font,
                "occupied_area_ratio": occupancy,
                "visual_area_ratio": visual_ratio,
            }
        )
        budget = allocate_slide_content_budget(role, int(slide.get("duration_seconds", 60)), slide.get("content_type", ""))
        if body_chars > budget["body_chars"]:
            warnings.append({"id": f"content-budget:{sid}", "message": f"slide {sid}: {body_chars} characters exceed the {budget['body_chars']}-character content budget"})
        font_violations = []
        for element in font_elements:
            font_role = element.get("style", {}).get("font_role")
            if font_role in {"caption", "citation"} or re.search(
                r"图注|署名|来源|脚注|版权", str(element.get("purpose", ""))
            ):
                threshold = 10
            elif element.get("type") == "table":
                threshold = 13
            else:
                threshold = budget["minimum_body_font_pt"]
            if float(element["font_size"]) < threshold:
                font_violations.append(f"{element.get('id')} {float(element['font_size']):g}pt<{threshold}pt")
        if font_violations:
            warnings.append(
                {
                    "id": f"small-text:{sid}",
                    "message": f"slide {sid}: undersized text: " + ", ".join(font_violations),
                }
            )
        for msg in validate_notes_timing(slide):
            warnings.append({"id": f"notes-timing:{sid}", "message": f"slide {sid}: {msg}"})
        slide_text = " ".join(str(slide.get(k, "")) for k in ("title", "takeaway"))
        if HIGH_RISK_RE.search(slide_text) and not has_visible_warning(group):
            warnings.append({"id": f"risk-hierarchy:{sid}", "message": f"slide {sid}: high-risk content lacks a visible warning treatment"})
        for msg in validate_printable_assessment(slide, group):
            warnings.append({"id": f"assessment:{sid}", "message": f"slide {sid}: {msg}"})
        for msg in validate_recommendation_scope(slide, claim_map):
            warnings.append({"id": f"recommendation-scope:{sid}", "message": f"slide {sid}: {msg}"})
        for msg in validate_decision_evidence(slide, claim_map, role):
            warnings.append({"id": f"decision-evidence:{sid}", "message": f"slide {sid}: {msg}"})
        evidence_images = [
            e
            for e in group.get("elements", [])
            if e.get("type") == "image"
            and re.search(
                r"截图|影像|病理|口内扫描|screen(?:shot)?|\bscan\b|clinical",
                " ".join(str(e.get(key, "")) for key in ("purpose", "alt"))
                + " "
                + str(e.get("image", {}).get("caption", "")),
                re.I,
            )
        ]
        for element in evidence_images:
            ratio = float(element.get("w", 0)) * float(element.get("h", 0)) / (plan.get("width", 13.333) * plan.get("height", 7.5))
            if ratio < 0.18:
                warnings.append({"id": f"evidence-image-size:{sid}:{element.get('id')}", "message": f"slide {sid}: evidence image {element.get('id')} occupies only {ratio:.0%} of the slide"})

    for idx in range(2, len(compositions)):
        window = compositions[idx - 2 : idx + 1]
        if len({x[1] for x in window}) == 1:
            sid = window[-1][0]
            warnings.append({"id": f"consecutive-composition:{sid}", "message": f"slide {sid}: composition {window[-1][1]} repeats for 3 consecutive slides"})
    composition_counts = Counter(c for _, c in compositions)
    if len(plan.get("slides", [])) >= 15 and len(composition_counts) < 6:
        warnings.append({"id": "deck-composition-variety", "message": f"deck uses only {len(composition_counts)} composition families; at least 6 are expected for this length"})
    signature_counts = Counter(sig for _, sig in signatures)
    for sid, sig in signatures:
        if signature_counts[sig] >= 5:
            warnings.append({"id": f"repeated-geometry:{sid}", "message": f"slide {sid}: near-identical element geometry appears on {signature_counts[sig]} slides"})
    return {
        "passed": not warnings,
        "warnings": warnings,
        "metrics": metrics,
        "composition_counts": dict(composition_counts),
    }


def build_contact_sheet(page_paths: list[Path], output_path: Path, columns: int = 5, thumb_width: int = 320) -> Path:
    from PIL import Image, ImageDraw

    if not page_paths:
        raise ValueError("No rendered pages supplied")
    opened = [Image.open(p).convert("RGB") for p in page_paths]
    ratio = opened[0].height / opened[0].width
    thumb_height = int(thumb_width * ratio)
    label_height, gap = 24, 12
    rows = math.ceil(len(opened) / columns)
    canvas = Image.new("RGB", (columns * (thumb_width + gap) + gap, rows * (thumb_height + label_height + gap) + gap), "#E8EEED")
    draw = ImageDraw.Draw(canvas)
    for index, image in enumerate(opened):
        col, row = index % columns, index // columns
        x = gap + col * (thumb_width + gap)
        y = gap + row * (thumb_height + label_height + gap)
        image.thumbnail((thumb_width, thumb_height))
        canvas.paste(image, (x, y))
        draw.text((x, y + thumb_height + 4), f"slide-{index + 1:03}", fill="#213038")
        image.close()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path
