#!/usr/bin/env python3
"""Install/uninstall an isolated local skill directory without overwriting user files."""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "medical-presentation-architect"
PAYLOAD = [
    "SKILL.md",
    "README.md",
    "VERSION",
    "LICENSE",
    "NOTICE",
    "COMMERCIAL-LICENSING.md",
    "THIRD-PARTY-NOTICES.md",
    "CHANGELOG.md",
    "prompts",
    "rules",
    "workflows",
    "schemas",
    "scripts",
    "references",
    "adapters",
    "docs",
    "ui",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target_parent(agent, target):
    if target:
        return Path(target).expanduser().resolve()
    home = Path.home()
    if agent == "kimi":
        return Path(os.environ.get("KIMI_CODE_HOME", str(home / ".kimi-code"))).expanduser().resolve() / "skills"
    if agent == "claude":
        return home / ".claude" / "skills"
    if agent == "codex":
        return home / ".agents" / "skills"
    raise ValueError("--target is required when --agent generic")


def files_to_copy():
    out = []
    for name in PAYLOAD:
        p = ROOT / name
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix != ".pyc")
    return sorted(out)


def install(agent, parent):
    parent.mkdir(parents=True, exist_ok=True)
    dest = parent / NAME
    if dest.exists():
        raise FileExistsError(f"Refusing to overwrite existing installation: {dest}")
    dest.mkdir()
    copied = {}
    try:
        for src in files_to_copy():
            rel = src.relative_to(ROOT)
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            copied[rel.as_posix()] = digest(out)
        state = {
            "format": "mpa-install-v1",
            "agent": agent,
            "source_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip()
            if (ROOT / "VERSION").exists()
            else "unknown",
            "files": copied,
        }
        (dest / ".mpa-install.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for p in sorted(dest.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        dest.rmdir()
        raise
    print(f"Installed {NAME} for {agent}: {dest}")
    if agent == "kimi":
        print(f'Start: kimi --skills-dir "{parent}"')
    elif agent == "claude":
        print("Start a new Claude Code session and invoke /medical-presentation-architect")
    elif agent == "codex":
        print("Start a new Codex session and invoke $medical-presentation-architect")


def update(agent, parent):
    dest = parent / NAME
    state_path = dest / ".mpa-install.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"No managed installation manifest found at {state_path}; refusing an unmanaged overwrite")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("format") != "mpa-install-v1" or (agent != "auto" and state.get("agent") != agent):
        raise ValueError("Install manifest does not match requested agent")
    old_files = state.get("files", {})
    sources = files_to_copy()
    for src in sources:
        rel = src.relative_to(ROOT).as_posix()
        target = dest / rel
        if target.is_file() and rel in old_files and digest(target) != old_files[rel] and digest(target) != digest(src):
            raise RuntimeError(f"Refusing to overwrite a locally modified managed file: {rel}")
        if target.exists() and rel not in old_files and (not target.is_file() or digest(target) != digest(src)):
            raise RuntimeError(f"Refusing to overwrite an unmanaged path: {rel}")
    copied = {}
    for src in sources:
        rel = src.relative_to(ROOT)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied[rel.as_posix()] = digest(target)
    new_state = {
        "format": "mpa-install-v1",
        "agent": state.get("agent", agent),
        "source_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "files": copied,
    }
    state_path.write_text(json.dumps(new_state, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {NAME} for {new_state['agent']}: {dest} -> {new_state['source_version']}")


def uninstall(agent, parent):
    dest = parent / NAME
    state_path = dest / ".mpa-install.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"No managed installation manifest found at {state_path}; no files removed")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("format") != "mpa-install-v1" or (agent != "auto" and state.get("agent") != agent):
        raise ValueError("Install manifest does not match requested agent")
    removed, preserved = [], []
    for rel, recorded_hash in state["files"].items():
        p = (dest / rel).resolve()
        if dest.resolve() not in p.parents:
            raise ValueError(f"Unsafe path in install manifest: {rel}")
        if p.is_file() and digest(p) == recorded_hash:
            p.unlink()
            removed.append(rel)
        elif p.exists():
            preserved.append(rel)
    state_path.unlink()
    # Remove only empty directories; preserve added/modified files.
    for p in sorted((p for p in dest.rglob("*") if p.is_dir()), key=lambda x: len(x.parts), reverse=True):
        try:
            p.rmdir()
        except OSError:
            pass
    try:
        dest.rmdir()
    except OSError:
        pass
    print(f"Removed {len(removed)} unchanged managed files from {dest}")
    if preserved:
        print("Preserved user-modified files: " + ", ".join(preserved))
    if dest.exists():
        print(f"Directory kept because it contains user files: {dest}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="action", required=True)
    for action in ("install", "update", "uninstall"):
        p = sub.add_parser(action)
        p.add_argument("--agent", choices=["kimi", "claude", "codex", "generic", "auto"], default="kimi")
        p.add_argument("--target")
    a = ap.parse_args()
    agent = a.agent
    if action_needs_generic(a.action, agent) and not a.target:
        ap.error("--target is required for generic agent")
    parent = target_parent("kimi" if agent == "auto" else agent, a.target)
    if a.action == "install":
        install(agent, parent)
    elif a.action == "update":
        update(agent, parent)
    else:
        uninstall(agent, parent)


def action_needs_generic(action, agent):
    return agent == "generic"


if __name__ == "__main__":
    main()
