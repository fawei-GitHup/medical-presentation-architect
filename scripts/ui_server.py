#!/usr/bin/env python3
"""Local-only web interface for Medical Presentation Architect."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import mpa


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT / "ui"
DEFAULT_WORKSPACE = ROOT / "projects"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
ALLOWED_UPLOADS = {
    ".pptx",
    ".potx",
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".tsv",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".svg",
    ".txt",
    ".md",
    ".json",
}


def safe_project_name(value: str) -> str:
    name = value.strip()
    if (
        not name
        or len(name) > 64
        or name in {".", ".."}
        or name[-1] in {".", " "}
        or any(ord(c) < 32 or c in '<>:"/\\|?*' for c in name)
        or name.split(".", 1)[0].upper() in WINDOWS_RESERVED
    ):
        raise ValueError("项目标识长度应为 1–64，且不能包含路径符号、控制字符或系统保留名称。")
    return name


def safe_upload_name(value: str) -> str:
    name = Path(value.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."} or any(ord(c) < 32 for c in name):
        raise ValueError("文件名无效。")
    if Path(name).suffix.lower() not in ALLOWED_UPLOADS:
        raise ValueError("不支持此文件类型。允许 PPT/PDF/Office/图片及文本资料。")
    return name[:180]


def resolve_project(workspace: Path, name: str) -> Path:
    workspace = workspace.resolve()
    project = (workspace / safe_project_name(name)).resolve()
    if project.parent != workspace:
        raise ValueError("项目路径越过工作区边界。")
    return project


def split_lines(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value or "").replace("；", "\n").splitlines() if x.strip()]


def provided(value) -> bool:
    return value not in (None, "", [], {})


def normalize_fields(data: dict) -> dict:
    """Map UI values to the canonical design-brief field model."""
    fields = dict(data.get("fields") or {})
    minutes = fields.pop("duration_minutes", None)
    slide_count = fields.pop("slide_count", None)
    web_allowed = fields.pop("allow_public_web", None)
    patient_materials = fields.pop("patient_materials", None)
    public_distribution = fields.pop("public_distribution", None)
    outputs = fields.pop("outputs", None)

    if minutes not in (None, ""):
        minutes = int(minutes)
        if not 1 <= minutes <= 480:
            raise ValueError("演讲时长应为 1–480 分钟。")
        fields["duration"] = {"minutes": minutes, "interaction_minutes": None}
    if slide_count not in (None, ""):
        slide_count = int(slide_count)
        if not 1 <= slide_count <= 200:
            raise ValueError("页数应为 1–200。")
        fields["slide_count_policy"] = {"mode": "exact", "count": slide_count}
    if web_allowed is not None:
        allowed = bool(web_allowed)
        fields["network_policy"] = {"allow_public_web": allowed, "local_only": not allowed}
    if any(x is not None for x in (patient_materials, public_distribution)):
        fields["privacy_constraints"] = {
            "processing": "仅在本机处理",
            "case_materials": patient_materials or "未提供",
            "public_distribution": public_distribution or "未决定",
        }
    if outputs:
        fields["deliverables"] = split_lines(outputs)

    for key in ("learning_outcomes", "assets_available", "acceptance_criteria", "existing_materials"):
        if key in fields:
            fields[key] = split_lines(fields[key])
    return {key: value for key, value in fields.items() if key in mpa.BRIEF_FIELDS and provided(value)}


def apply_ui_fields(project: Path, values: dict) -> dict:
    brief_path = project / "intake" / "design_brief.json"
    brief = mpa.read_json(brief_path)
    origin = {"type": "user_message", "locator": "local web intake"}
    for key, value in values.items():
        field = brief["fields"][key]
        field.update(value=value, status="provided", origin=origin, confidence=1.0)
    brief["version"] += 1
    brief["status"] = "intake"
    mpa.write_json(brief_path, brief)
    mpa.update_brief_hash(project)
    brief = mpa.read_json(brief_path)
    errors = mpa.schema_validate("design-brief", brief)
    if errors:
        raise ValueError("设计简报未通过校验：" + "; ".join(errors[:4]))
    return brief


def project_summary(project: Path) -> dict:
    brief = mpa.read_json(project / "intake" / "design_brief.json")
    prompt = project / "intake" / "execution_prompt.md"
    questions = mpa.missing_questions(brief)
    return {
        "name": project.name,
        "path": str(project),
        "briefId": brief["brief_id"],
        "briefVersion": brief["version"],
        "briefHash": brief.get("brief_hash"),
        "status": brief["status"],
        "route": brief["route"],
        "blockingQuestions": questions,
        "promptPath": str(prompt),
        "files": [x.name for x in sorted((project / "assets").glob("*")) if x.is_file()],
    }


def kimi_command(project: Path) -> str:
    skill_parent = ROOT / "skills"
    prompt = (
        "使用 medical-presentation-architect，继续项目 "
        + str(project)
        + "；读取 intake/execution_prompt.md。先展示其中的用户通知，只询问仍未解决的阻断项。"
    )
    args = ["kimi", "--skills-dir", str(skill_parent), "-p", prompt]
    return subprocess.list2cmdline(args) if sys.platform == "win32" else " ".join(shlex_quote(x) for x in args)


def shlex_quote(value: str) -> str:
    import shlex

    return shlex.quote(value)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "MPA-Local-UI/1.0"

    @property
    def workspace(self) -> Path:
        return self.server.workspace  # type: ignore[attr-defined]

    def log_message(self, fmt, *args):
        sys.stderr.write("[local-ui] " + fmt % args + "\n")

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        super().end_headers()

    def json_response(self, data, status=HTTPStatus.OK):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def error_response(self, message, status=HTTPStatus.BAD_REQUEST):
        self.json_response({"ok": False, "error": str(message)}, status)

    def read_body(self, maximum):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length 无效。") from exc
        if length <= 0 or length > maximum:
            raise ValueError(f"请求大小必须在 1–{maximum // (1024 * 1024)} MB。")
        return self.rfile.read(length)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.json_response(
                {"ok": True, "localOnly": True, "workspace": str(self.workspace), "maxUploadMB": 50}
            )
        if parsed.path == "/api/projects":
            items = []
            for p in sorted(self.workspace.glob("*")) if self.workspace.exists() else []:
                if p.is_dir() and (p / "intake/design_brief.json").is_file():
                    items.append(project_summary(p))
            return self.json_response({"ok": True, "projects": items})
        match = re.fullmatch(r"/api/projects/([^/]+)", parsed.path)
        if match:
            try:
                project = resolve_project(self.workspace, unquote(match.group(1)))
                return self.json_response({"ok": True, "project": project_summary(project)})
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
                return self.error_response(exc, HTTPStatus.NOT_FOUND)
        match = re.fullmatch(r"/api/projects/([^/]+)/command", parsed.path)
        if match:
            try:
                project = resolve_project(self.workspace, unquote(match.group(1)))
                if not (project / "intake/design_brief.json").is_file():
                    raise FileNotFoundError("项目不存在。")
                return self.json_response({"ok": True, "command": kimi_command(project)})
            except (ValueError, FileNotFoundError) as exc:
                return self.error_response(exc, HTTPStatus.NOT_FOUND)
        return self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/projects":
            return self.create_project()
        match = re.fullmatch(r"/api/projects/([^/]+)/files", parsed.path)
        if match:
            return self.upload_file(unquote(match.group(1)), parse_qs(parsed.query))
        return self.error_response("接口不存在。", HTTPStatus.NOT_FOUND)

    def create_project(self):
        try:
            data = json.loads(self.read_body(MAX_JSON_BYTES))
            name = safe_project_name(str(data.get("projectName", "")))
            project = resolve_project(self.workspace, name)
            if project.exists():
                raise FileExistsError("同名项目已存在，请换一个项目标识。")
            fields = normalize_fields(data)
            topic = fields.get("topic")
            mpa.init_project(project, str(data.get("route") or "clear"), str(topic or ""), str(topic or ""))
            brief = apply_ui_fields(project, fields)
            return self.json_response(
                {"ok": True, "project": project_summary(project), "brief": brief, "command": kimi_command(project)},
                HTTPStatus.CREATED,
            )
        except FileExistsError as exc:
            return self.error_response(exc, HTTPStatus.CONFLICT)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.error_response(exc)

    def upload_file(self, project_name, query):
        try:
            project = resolve_project(self.workspace, project_name)
            if not (project / "intake/design_brief.json").is_file():
                raise FileNotFoundError("项目不存在。")
            requested = self.headers.get("X-Filename") or (query.get("name") or [""])[0]
            name = safe_upload_name(unquote(requested))
            content = self.read_body(MAX_UPLOAD_BYTES)
            dest = project / "assets" / name
            if dest.exists():
                raise FileExistsError("项目中已有同名文件。")
            temp = dest.with_suffix(dest.suffix + ".uploading")
            temp.write_bytes(content)
            temp.replace(dest)
            return self.json_response(
                {"ok": True, "file": {"name": name, "size": len(content)}, "project": project_summary(project)},
                HTTPStatus.CREATED,
            )
        except FileExistsError as exc:
            return self.error_response(exc, HTTPStatus.CONFLICT)
        except FileNotFoundError as exc:
            return self.error_response(exc, HTTPStatus.NOT_FOUND)
        except (ValueError, OSError) as exc:
            return self.error_response(exc)

    def serve_static(self, request_path):
        rel = "index.html" if request_path in ("", "/") else unquote(request_path.lstrip("/"))
        target = (UI_ROOT / rel).resolve()
        if UI_ROOT.resolve() not in target.parents or not target.is_file():
            return self.error_response("页面不存在。", HTTPStatus.NOT_FOUND)
        content = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def parse_args():
    ap = argparse.ArgumentParser(description="启动仅在本机运行的 Medical Presentation Architect 中文界面")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--allow-remote", action="store_true", help="明确允许监听非回环地址；可能暴露病例材料")
    return ap.parse_args()


def main():
    args = parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not args.allow_remote:
        raise SystemExit("为保护病例和机构资料，默认只允许本机地址。非本机监听必须显式加 --allow-remote。")
    if not UI_ROOT.is_dir():
        raise SystemExit(f"界面资源缺失：{UI_ROOT}")
    workspace = args.workspace.expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    server.workspace = workspace
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Medical Presentation Architect 本地界面：{url}")
    print(f"项目仅写入：{workspace}")
    print("按 Ctrl+C 停止。")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n本地界面已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
