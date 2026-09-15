#!/usr/bin/env python3
"""Build a sanitized, reproducible ZIP from explicit release allow-lists."""

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = [
    "SKILL.md",
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "prompts",
    "rules",
    "workflows",
    "schemas",
    "scripts",
    "references",
    "adapters",
    "ui",
    "LICENSE",
    "NOTICE",
    "COMMERCIAL-LICENSING.md",
    "THIRD-PARTY-NOTICES.md",
    "CONTRIBUTING.md",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tracked_and_unchanged(path):
    """Allow repair of a stale manifest only when Git proves the generated file is untouched."""
    try:
        rel = path.relative_to(ROOT).as_posix()
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        worktree = subprocess.run(
            ["git", "diff", "--quiet", "--", rel], cwd=ROOT, check=False
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", rel], cwd=ROOT, check=False
        )
        return tracked.returncode == worktree.returncode == staged.returncode == 0
    except (OSError, ValueError):
        return False


def public_files():
    items = []
    for p in ROOT.rglob("*"):
        if (
            not p.is_file()
            or p.is_symlink()
            or any(
                part in {
                    ".git",
                    "__pycache__",
                    ".venv",
                    ".ruff_cache",
                    ".pytest_cache",
                    ".review-cache",
                    "projects",
                    "private",
                    "build",
                    "render",
                    "final",
                    "work",
                }
                for part in p.parts
            )
        ):
            continue
        if p.suffix.lower() == ".pyc" or p.name.endswith(".tmp") or p.name in (
            ".DS_Store",
            "Thumbs.db",
            ".mpa-install.json",
        ):
            continue
        items.append(p)
    return sorted(items)


def sync_codex_skill():
    dest = ROOT / "skills" / "medical-presentation-architect"
    if dest.is_symlink() or dest.resolve().parent != (ROOT / "skills").resolve():
        raise SystemExit("Refusing to write outside the generated Codex skills directory")
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".mpa-generated.json"
    previous = None
    if marker.is_file():
        previous = json.loads(marker.read_text(encoding="utf-8"))
        if previous.get("format") != "mpa-generated-skill-v1":
            raise SystemExit("Unknown generated-skill manifest; refusing to overwrite it")
        for rel, digest in previous.get("files", {}).items():
            target = (dest / rel).resolve()
            if dest.resolve() not in target.parents:
                raise SystemExit(f"Unsafe generated-skill manifest path: {rel}")
            if target.is_file() and sha(target) != digest and not tracked_and_unchanged(target):
                raise SystemExit(f"Generated skill file was changed locally; preserve/resolve before packaging: {rel}")
    copied = set()
    for name in SKILL_FILES:
        source_root = ROOT / name
        if source_root.is_file():
            sources = [source_root]
        elif source_root.is_dir():
            sources = [
                p
                for p in source_root.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"
            ]
        else:
            continue
        for source in sources:
            rel = source.relative_to(ROOT)
            target = dest / rel
            if target.is_symlink():
                raise SystemExit(f"Refusing to replace symlink in generated skill: {rel.as_posix()}")
            if target.exists() and not (previous and rel.as_posix() in previous.get("files", {})) and sha(target) != sha(source):
                raise SystemExit(f"Generated skill path collides with a different local file: {rel.as_posix()}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.add(rel.as_posix())
    if previous:
        for rel in previous.get("files", {}):
            if rel == "agents/openai.yaml" or rel in copied:
                continue
            stale = (dest / rel).resolve()
            if dest.resolve() not in stale.parents:
                raise SystemExit(f"Unsafe generated-skill manifest path: {rel}")
            if stale.is_file():
                stale.unlink()
    meta = dest / "agents" / "openai.yaml"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(
        'interface:\n  display_name: "Medical Presentation Architect"\n  short_description: "Plan, source and review medical presentations"\n  default_prompt: "Plan a medical presentation. Begin by identifying missing intake information."\n',
        encoding="utf-8",
    )
    files = {
        p.relative_to(dest).as_posix(): sha(p)
        for p in dest.rglob("*")
        if p.is_file() and p != marker and "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"
    }
    marker.write_text(
        json.dumps({"format": "mpa-generated-skill-v1", "files": files}, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    sync_codex_skill()
    files = public_files()
    forbidden = {
        ".pptx",
        ".potx",
        ".docx",
        ".pdf",
        ".xls",
        ".xlsx",
        ".db",
        ".dcm",
        ".nii",
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
    bad = [p for p in files if p.suffix.lower() in forbidden and p.name not in ("LICENSE",)]
    if bad:
        raise SystemExit(
            "Unapproved binary/clinical input in release tree: "
            + ", ".join(p.relative_to(ROOT).as_posix() for p in bad)
        )
    out = a.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"medical-presentation-architect-{(ROOT / 'VERSION').read_text(encoding='utf-8').strip()}"
    manifest = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            name = f"{prefix}/{p.relative_to(ROOT).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
        manifest_name = f"{prefix}/MANIFEST.sha256.json"
        info = zipfile.ZipInfo(manifest_name, date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("duplicate archive entries")
        for n in names:
            if any(part in ("work", "projects", "private", ".git") for part in Path(n).parts):
                raise SystemExit(f"unsafe archive path: {n}")
        expected = json.loads(z.read(f"{prefix}/MANIFEST.sha256.json"))
        archived = {Path(n).relative_to(prefix).as_posix() for n in names if n != f"{prefix}/MANIFEST.sha256.json"}
        if set(expected) != archived:
            raise SystemExit("manifest entries do not match archive")
        for rel, digest in expected.items():
            if hashlib.sha256(z.read(f"{prefix}/{rel}")).hexdigest() != digest:
                raise SystemExit(f"archive checksum mismatch: {rel}")
    print(f"Created {out} ({out.stat().st_size} bytes; {len(files)} files plus checksum manifest)")


if __name__ == "__main__":
    main()
