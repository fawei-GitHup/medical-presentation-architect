#!/usr/bin/env python3
"""Validate the source-available skill repository and sanitized release ZIP."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "NOTICE",
    "COMMERCIAL-LICENSING.md",
    "THIRD-PARTY-NOTICES.md",
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    ".gitignore",
    ".gitattributes",
    ".github/ISSUE_TEMPLATE/commercial-license-request.yml",
    "tests/test_workflow.py",
    "tests/test_v140.py",
    "examples/demo/slide-plan.json",
    "install.sh",
    "install.ps1",
    "bootstrap.sh",
    "bootstrap.ps1",
    "start-ui.sh",
    "start-ui.ps1",
    "uninstall.sh",
    "uninstall.ps1",
    "plugin/manifest.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "docs/usage.md",
    "docs/kimi-cli.md",
    "docs/claude-code.md",
    "docs/codex.md",
    "docs/validation.md",
    "docs/input-audit.md",
    "docs/release.md",
    "docs/github.md",
    "prompts/adaptive-intake.md",
    "prompts/intake.md",
    "prompts/master.md",
    "rules/evidence-policy.md",
    "rules/citation-display.md",
    "rules/perceptual-quality.md",
    "rules/failure-gates.md",
    "rules/image-policy.md",
    "rules/language.md",
    "rules/layout.md",
    "rules/medical-integrity.md",
    "rules/privacy.md",
    "rules/visual-policy.md",
    "workflows/source-design-audit.md",
    "workflows/media-intake.md",
    "workflows/execution-graph.md",
    "workflows/design-system.md",
    "workflows/prototype.md",
    "workflows/visual-planning.md",
    "workflows/build.md",
    "workflows/render.md",
    "workflows/qa.md",
    "workflows/export.md",
    "schemas/design-brief.schema.json",
    "schemas/design-fingerprint.schema.json",
    "schemas/design-system.schema.json",
    "schemas/prototype-approval.schema.json",
    "schemas/visual-plan.schema.json",
    "scripts/mpa.py",
    "scripts/design_audit.py",
    "scripts/design_quality.py",
    "scripts/media_index.py",
    "scripts/perceptual_preflight.py",
    "scripts/source_map_check.py",
    "scripts/workflow_state.py",
    "scripts/capture_run.py",
    "scripts/install.py",
    "scripts/package.py",
    "scripts/pptx_lint.py",
    "scripts/release_check.py",
    "adapters/kimi-cli/README.md",
    "adapters/claude-code/README.md",
    "adapters/codex/README.md",
    "ui/index.html",
    "ui/styles.css",
    "ui/app.js",
    "ui/README.md",
]
FORBIDDEN_SUFFIXES = {
    ".pptx", ".potx", ".docx", ".pdf", ".xlsx", ".xls", ".db",
    ".dcm", ".nii", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".tif", ".tiff", ".svg", ".mp4", ".mov", ".mp3", ".wav",
    ".ttf", ".otf", ".zip",
}
IGNORED_PARTS = {"skills", ".git", ".venv", "__pycache__"}


def check_links():
    errors = []
    for md in ROOT.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in md.relative_to(ROOT).parts):
            continue
        text = md.read_text(encoding="utf-8")
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", text):
            target = target.strip().strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = urlsplit(target).path.split("#", 1)[0]
            if not path:
                continue
            resolved = (md.parent / path).resolve()
            if ROOT.resolve() not in resolved.parents and resolved != ROOT.resolve():
                errors.append(f"link escapes package: {md.relative_to(ROOT)} -> {target}")
            elif not resolved.exists():
                errors.append(f"broken local link: {md.relative_to(ROOT)} -> {target}")
    return errors


def check_license():
    errors = []
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8") if (ROOT / "LICENSE").is_file() else ""
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8") if (ROOT / "NOTICE").is_file() else ""
    commercial = (ROOT / "COMMERCIAL-LICENSING.md").read_text(encoding="utf-8") if (ROOT / "COMMERCIAL-LICENSING.md").is_file() else ""
    if "MIT License" in license_text or "sublicense, and/or sell" in license_text:
        errors.append("LICENSE still contains MIT commercial-use permission")
    for required in (
        "Non-Commercial License",
        "Commercial Use Requires Prior Written Authorization",
        "for-profit company",
        "paid services",
    ):
        if required not in license_text:
            errors.append(f"LICENSE missing commercial-control term: {required}")
    if "fawei-GitHup" not in notice:
        errors.append("NOTICE does not identify the copyright holder")
    if "Commercial License Request" not in commercial:
        errors.append("commercial licensing request path is missing")
    return errors


def main():
    errors = [f"missing required file: {name}" for name in REQUIRED if not (ROOT / name).is_file()]
    errors.extend(check_links())
    errors.extend(check_license())

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").is_file() else ""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"invalid VERSION: {version!r}")

    for path in ROOT.rglob("*.json"):
        if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")

    for path in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tests").glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(str(exc))

    try:
        from jsonschema import Draft202012Validator

        for schema in (ROOT / "schemas").glob("*.schema.json"):
            Draft202012Validator.check_schema(json.loads(schema.read_text(encoding="utf-8")))
    except ImportError:
        errors.append("jsonschema missing; install it before running a release check")
    except Exception as exc:
        errors.append(f"invalid JSON schema: {exc}")

    with tempfile.TemporaryDirectory(prefix="mpa-release-") as td:
        temp_root = Path(td)
        target = temp_root / "skills"
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/install.py"), "install", "--agent", "generic", "--target", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            skill = target / "medical-presentation-architect"
            for rel in (
                "SKILL.md",
                "README.md",
                "LICENSE",
                "NOTICE",
                "COMMERCIAL-LICENSING.md",
                "scripts/mpa.py",
                "docs/usage.md",
                "ui/index.html",
            ):
                if not (skill / rel).is_file():
                    errors.append(f"installer smoke test did not place {rel}")
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/install.py"), "uninstall", "--agent", "generic", "--target", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            if skill.exists():
                errors.append("installer smoke test did not clean unchanged files")
        except subprocess.CalledProcessError as exc:
            errors.append(f"installer smoke test failed: {exc.stderr or exc.stdout}")

        archive = temp_root / "release.zip"
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/package.py"), "--output", str(archive)],
                check=True,
                capture_output=True,
                text=True,
            )
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                prefix = f"medical-presentation-architect-{version}"
                manifest_name = f"{prefix}/MANIFEST.sha256.json"
                if len(names) != len(set(names)):
                    errors.append("ZIP contains duplicate entries")
                for name in names:
                    p = Path(name)
                    if p.is_absolute() or ".." in p.parts:
                        errors.append(f"unsafe ZIP path: {name}")
                    if p.suffix.lower() in FORBIDDEN_SUFFIXES:
                        errors.append(f"clinical/document binary should not ship: {name}")
                    if any(part in {"private", "projects", "work", ".git"} for part in p.parts):
                        errors.append(f"private path in ZIP: {name}")
                for rel in ("SKILL.md", "README.md", "LICENSE", "NOTICE", "COMMERCIAL-LICENSING.md"):
                    if f"{prefix}/{rel}" not in names:
                        errors.append(f"ZIP is missing {rel}")
                for rel in (
                    "SKILL.md",
                    "README.md",
                    "LICENSE",
                    "NOTICE",
                    "COMMERCIAL-LICENSING.md",
                    "schemas/design-system.schema.json",
                    "workflows/prototype.md",
                    "docs/usage.md",
                    "docs/release.md",
                ):
                    generated = f"{prefix}/skills/medical-presentation-architect/{rel}"
                    if generated not in names:
                        errors.append(f"ZIP is missing synchronized Codex skill file: {rel}")
                if manifest_name not in names:
                    errors.append("ZIP has no SHA-256 manifest")
                else:
                    manifest = json.loads(z.read(manifest_name))
                    archived = {Path(name).relative_to(prefix).as_posix() for name in names if name != manifest_name}
                    if set(manifest) != archived:
                        errors.append("ZIP manifest does not enumerate every other archive file")
                    for rel, expected in manifest.items():
                        if hashlib.sha256(z.read(f"{prefix}/{rel}")).hexdigest() != expected:
                            errors.append(f"ZIP manifest mismatch: {rel}")
        except (subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
            errors.append(f"package smoke test failed: {getattr(exc, 'stderr', '') or exc}")

    if errors:
        print("Release check FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print("Release check passed: repository structure, non-commercial license controls, links, JSON schemas, Python syntax, installer, and sanitized ZIP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
