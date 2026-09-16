#!/usr/bin/env python3
"""Run a long command with scrubbed logs and idle heartbeats."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_URI_RE = re.compile(r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\r\n]{16,})")
LONG_BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{2048,}={0,2})(?![A-Za-z0-9+/=])")
RETRY_RE = re.compile(r"\b(retry|retrying|重试)\b", re.I)
SENSITIVE_OPTION_RE = re.compile(r"^--?(api[-_]?key|token|secret|password)(?:=(.*))?$", re.I)


def _image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            return image.size
    except (OSError, ValueError):
        return None, None


def _replacement(encoded: str, mime: str | None = None) -> str:
    compact = re.sub(r"\s+", "", encoded)
    try:
        data = base64.b64decode(compact, validate=True)
    except (ValueError, base64.binascii.Error):
        data = compact.encode("ascii", errors="ignore")
    width, height = _image_dimensions(data)
    dimensions = f"{width}x{height}" if width and height else "unknown"
    return (
        "[SCRUBBED_IMAGE "
        f"mime={mime or 'unknown'} sha256={hashlib.sha256(data).hexdigest()} dimensions={dimensions} "
        f"encoded_chars={len(encoded)} decoded_bytes={len(data)}]"
    )


def scrub_text(text: str) -> tuple[str, list[dict]]:
    records = []

    def replace_data_uri(match):
        replacement = _replacement(match.group(2), match.group(1))
        records.append({"kind": "data_uri", "removed_characters": len(match.group(0)), "replacement": replacement})
        return replacement

    cleaned = DATA_URI_RE.sub(replace_data_uri, text)

    def replace_long_token(match):
        replacement = _replacement(match.group(1))
        records.append({"kind": "base64_token", "removed_characters": len(match.group(1)), "replacement": replacement})
        return replacement

    cleaned = LONG_BASE64_RE.sub(replace_long_token, cleaned)
    return cleaned, records


def redact_command(command: list[str]) -> list[str]:
    """Keep the audit command useful without copying credentials into the log."""
    redacted = []
    hide_next = False
    for value in command:
        if hide_next:
            redacted.append("[REDACTED]")
            hide_next = False
            continue
        match = SENSITIVE_OPTION_RE.match(value)
        if match:
            if "=" in value:
                redacted.append(value.split("=", 1)[0] + "=[REDACTED]")
            else:
                redacted.append(value)
                hide_next = True
            continue
        redacted.append(value)
    return redacted


def _latest_file(root: Path) -> str | None:
    try:
        candidates = [path for path in root.rglob("*") if path.is_file()]
        latest = max(candidates, key=lambda path: path.stat().st_mtime, default=None)
        return str(latest) if latest else None
    except OSError:
        return None


def _reader(stream, label: str, output_queue: queue.Queue) -> None:
    try:
        for line in iter(stream.readline, ""):
            output_queue.put((label, line))
    finally:
        output_queue.put((label, None))


def capture(command: list[str], output: Path, heartbeat: float, scrub_images: bool, phase: str, watch_dir: Path) -> int:
    if heartbeat <= 0:
        raise ValueError("heartbeat must be greater than zero")
    output.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    messages: queue.Queue = queue.Queue()
    threads = [
        threading.Thread(target=_reader, args=(process.stdout, "stdout", messages), daemon=True),
        threading.Thread(target=_reader, args=(process.stderr, "stderr", messages), daemon=True),
    ]
    for thread in threads:
        thread.start()
    started = time.monotonic()
    last_output = started
    streams_open = 2
    retries = 0
    scrubbed_blocks = 0
    with output.open("w", encoding="utf-8") as log:
        header = {
            "event": "start",
            "at": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "command": redact_command(command),
            "scrub_images": scrub_images,
        }
        log.write(json.dumps(header, ensure_ascii=False) + "\n")
        while streams_open or process.poll() is None:
            timeout = max(0.05, heartbeat - (time.monotonic() - last_output))
            try:
                label, line = messages.get(timeout=timeout)
            except queue.Empty:
                elapsed = int(time.monotonic() - started)
                message = (
                    f"[heartbeat] phase={phase} elapsed={elapsed}s latest_file={_latest_file(watch_dir) or 'none'} "
                    f"retries={retries}"
                )
                print(message, flush=True)
                log.write(json.dumps({"event": "heartbeat", "message": message}, ensure_ascii=False) + "\n")
                log.flush()
                last_output = time.monotonic()
                continue
            if line is None:
                streams_open -= 1
                continue
            retries += len(RETRY_RE.findall(line))
            cleaned, records = scrub_text(line) if scrub_images else (line, [])
            scrubbed_blocks += len(records)
            target = sys.stderr if label == "stderr" else sys.stdout
            target.write(cleaned)
            target.flush()
            log.write(json.dumps({"event": label, "text": cleaned.rstrip("\n"), "scrubbed": records}, ensure_ascii=False) + "\n")
            log.flush()
            last_output = time.monotonic()
        return_code = process.wait()
        footer = {
            "event": "finish",
            "at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "return_code": return_code,
            "retries": retries,
            "scrubbed_blocks": scrubbed_blocks,
        }
        log.write(json.dumps(footer, ensure_ascii=False) + "\n")
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--heartbeat", type=float, default=60.0)
    parser.add_argument("--scrub-images", action="store_true")
    parser.add_argument("--phase", default="running")
    parser.add_argument("--watch-dir", type=Path, default=Path.cwd())
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a command is required after --")
    return capture(command, args.output, args.heartbeat, args.scrub_images, args.phase, args.watch_dir)


if __name__ == "__main__":
    raise SystemExit(main())
