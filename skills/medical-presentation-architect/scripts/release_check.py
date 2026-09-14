#!/usr/bin/env python3
"""Run deterministic repository, schema, link, install and ZIP-safety checks."""

from __future__ import annotations

import json
import hashlib
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
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "prompts/intake.md",
    "prompts/master.md",
    "rules/evidence-policy.md",
    "rules/language.md",
    "rules/medical-integrity.md",
    "workflows/research.md",
    "workflows/export.md",
    "schemas/design-brief.schema.json",
    "schemas/user-notice.schema.json",
    "scripts/mpa.py",
    "scripts/install.py",
    "scripts/package.py",
    "scripts/pptx_lint.py",
    "scripts/release_check.py",
    "tests/test_workflow.py",
    "examples/demo/slide-plan.json",
    "install.sh",
    "install.ps1",
    "uninstall.sh",
    "uninstall.ps1",
    "plugin/manifest.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "adapters/kimi-cli/README.md",
    "adapters/claude-code/README.md",
    "adapters/codex/README.md",
    "docs/usage.md",
    "docs/kimi-cli.md",
    "docs/claude-code.md",
    "docs/codex.md",
    "docs/validation.md",
    "docs/input-audit.md",
]
FORBIDDEN_SUFFIXES = {
    ".pptx",
    ".potx",
    ".docx",
    ".pdf",
    ".xlsx",
    ".xls",
    ".db",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
    ".svg",
    ".mp4",
    ".mov",
    ".mp3",
    ".wav",
    ".ttf",
    ".otf",
    ".zip",
}


def check_links():
    errors = []
    import re

    for md in ROOT.rglob("*.md"):
        if any(part in {"skills", ".git"} for part in md.relative_to(ROOT).parts[:-1]):
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


def main():
    errors = [f"missing required file: {name}" for name in REQUIRED if not (ROOT / name).is_file()]
    for path in ROOT.rglob("*.json"):
        if any(x in {"__pycache__", ".git", ".venv"} for x in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    errors.extend(check_links())
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
        errors.append("jsonschema missing; install requirements.txt before release check")
    except Exception as exc:
        errors.append(f"invalid JSON schema: {exc}")

    with tempfile.TemporaryDirectory(prefix="mpa-release-") as td:
        target = Path(td) / "skills"
        py = sys.executable
        try:
            subprocess.run(
                [py, str(ROOT / "scripts/install.py"), "install", "--agent", "generic", "--target", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            skill = target / "medical-presentation-architect"
            if not (skill / "SKILL.md").is_file():
                errors.append("installer smoke test did not place SKILL.md")
            subprocess.run(
                [py, str(ROOT / "scripts/install.py"), "uninstall", "--agent", "generic", "--target", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            if skill.exists():
                errors.append("installer smoke test did not clean unchanged files")
        except subprocess.CalledProcessError as exc:
            errors.append(f"installer smoke test failed: {exc.stderr or exc.stdout}")
        archive = Path(td) / "release.zip"
        try:
            subprocess.run(
                [py, str(ROOT / "scripts/package.py"), "--output", str(archive)],
                check=True,
                capture_output=True,
                text=True,
            )
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                if len(names) != len(set(names)):
                    errors.append("ZIP contains duplicate entries")
                for name in names:
                    p = Path(name)
                    if p.is_absolute() or ".." in p.parts:
                        errors.append(f"unsafe ZIP path: {name}")
                    if p.suffix.lower() in FORBIDDEN_SUFFIXES:
                        errors.append(f"clinical/document binary should not ship: {name}")
                    if any(x in {"private", "projects", "work", ".git"} for x in p.parts):
                        errors.append(f"private workspace path in ZIP: {name}")
                if not any(name.endswith("/skills/medical-presentation-architect/SKILL.md") for name in names):
                    errors.append("ZIP is missing the synchronized Codex skill payload")
                prefix = f"medical-presentation-architect-{(ROOT / 'VERSION').read_text(encoding='utf-8').strip()}"
                manifest_name = f"{prefix}/MANIFEST.sha256.json"
                if manifest_name not in names:
                    errors.append("ZIP has no SHA-256 manifest")
                else:
                    manifest = json.loads(z.read(manifest_name))
                    archived = {Path(n).relative_to(prefix).as_posix() for n in names if n != manifest_name}
                    if set(manifest) != archived:
                        errors.append("ZIP manifest does not enumerate every other archive file")
                    for rel, expected in manifest.items():
                        if hashlib.sha256(z.read(f"{prefix}/{rel}")).hexdigest() != expected:
                            errors.append(f"ZIP manifest mismatch: {rel}")
        except (subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
            errors.append(f"package smoke test failed: {getattr(exc, 'stderr', '') or exc}")

    if errors:
        print("Release check FAILED")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(
        "Release check passed: required files, local documentation links, JSON/schema validity, Python compilation, installer smoke test and sanitized ZIP."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
