#!/usr/bin/env python3
"""Hash-bound stage checkpoints and dependency-aware resume planning."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DEPENDENCIES = {
    "intake": [],
    "design_audit": ["intake"],
    "media": ["intake"],
    "assets": ["intake"],
    "research": ["intake"],
    "doctor": ["intake"],
    "narrative": ["intake", "research"],
    "architecture": ["narrative"],
    "design_system": ["intake"],
    "visual_plan": ["architecture"],
    "evidence": ["architecture", "research"],
    "notes": ["architecture"],
    "citation_plan": ["architecture", "research"],
    "prototype": ["architecture", "design_system"],
    "build": ["prototype", "visual_plan", "evidence"],
    "pptx_lint": ["build"],
    "source_map": ["build", "citation_plan"],
    "perceptual_structure": ["build"],
    "notes_check": ["build", "notes"],
    "privacy_check": ["build", "assets"],
    "render": ["build"],
    "contact_sheet_review": ["render"],
    "visual_review": ["render"],
    "render_verify": ["render"],
    "qa": [
        "pptx_lint",
        "source_map",
        "perceptual_structure",
        "notes_check",
        "privacy_check",
        "contact_sheet_review",
        "visual_review",
        "render_verify",
    ],
    "export": ["qa"],
}
PHASES = tuple(DEPENDENCIES)
STATUSES = ("started", "completed", "failed", "invalidated")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_artifact(project: Path, artifact: Path) -> Path:
    path = artifact if artifact.is_absolute() else project / artifact
    resolved = path.resolve()
    root = project.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"stage artifact escapes the project: {artifact}")
    if not resolved.is_file():
        raise FileNotFoundError(f"stage artifact does not exist: {artifact}")
    return resolved


def _load(project: Path) -> dict:
    path = project / "run/stages.json"
    if not path.is_file():
        return {"format": "mpa-stages-v1", "updated_at": _now(), "stages": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("format") != "mpa-stages-v1" or not isinstance(value.get("stages"), dict):
        raise ValueError("unsupported run/stages.json format")
    return value


def _save(project: Path, state: dict) -> None:
    path = project / "run/stages.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_stage(project: Path, phase: str, status: str, artifacts: list[Path] | None = None) -> dict:
    if phase not in DEPENDENCIES:
        raise ValueError(f"unknown phase: {phase}")
    if status not in STATUSES:
        raise ValueError(f"unknown stage status: {status}")
    state = _load(project)
    artifact_records = []
    for artifact in artifacts or []:
        resolved = _safe_artifact(project, artifact)
        artifact_records.append(
            {"path": resolved.relative_to(project.resolve()).as_posix(), "sha256": _sha(resolved), "bytes": resolved.stat().st_size}
        )
    record = {
        "phase": phase,
        "status": status,
        "updated_at": _now(),
        "dependencies": DEPENDENCIES[phase],
        "artifacts": artifact_records,
    }
    state["stages"][phase] = record
    state["updated_at"] = record["updated_at"]
    _save(project, state)
    checkpoint = project / "run/checkpoints" / f"{phase}.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def resume_plan(project: Path) -> dict:
    state = _load(project)
    invalid: dict[str, list[str]] = {}
    valid_completed = set()
    for phase, record in state["stages"].items():
        if phase not in DEPENDENCIES or record.get("status") != "completed":
            continue
        reasons = []
        for artifact in record.get("artifacts", []):
            path = project / artifact["path"]
            if not path.is_file():
                reasons.append(f"missing artifact {artifact['path']}")
            elif _sha(path) != artifact.get("sha256"):
                reasons.append(f"changed artifact {artifact['path']}")
        if reasons:
            invalid[phase] = reasons
        else:
            valid_completed.add(phase)
    changed = True
    while changed:
        changed = False
        for phase in list(valid_completed):
            failed_dependencies = [dep for dep in DEPENDENCIES[phase] if dep in invalid]
            if failed_dependencies:
                valid_completed.remove(phase)
                invalid[phase] = ["stale dependency " + ", ".join(failed_dependencies)]
                changed = True
    ready = [
        phase
        for phase in PHASES
        if phase not in valid_completed
        and phase not in invalid
        and all(dependency in valid_completed for dependency in DEPENDENCIES[phase])
    ]
    blocked = {
        phase: [dependency for dependency in DEPENDENCIES[phase] if dependency not in valid_completed]
        for phase in PHASES
        if phase not in valid_completed and phase not in ready and phase not in invalid
    }
    return {
        "format": "mpa-resume-plan-v1",
        "valid_completed": [phase for phase in PHASES if phase in valid_completed],
        "stale": invalid,
        "ready": ready,
        "resume_from": ready[0] if ready else None,
        "blocked": blocked,
    }
