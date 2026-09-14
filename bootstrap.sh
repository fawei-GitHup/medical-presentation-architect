#!/usr/bin/env sh
set -eu

VERSION=${MPA_VERSION:-1.1.3}
AGENT=${MPA_AGENT:-kimi}
BASE=${MPA_BASE_URL:-"https://github.com/fawei-GitHup/medical-presentation-architect/releases/download/v$VERSION"}
BASE=${BASE%/}
ARCHIVE_NAME="medical-presentation-architect-v$VERSION.zip"
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/mpa-install.XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM

download() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$1" -O "$2"
  else
    echo "curl or wget is required" >&2
    exit 1
  fi
}

download "$BASE/$ARCHIVE_NAME" "$TEMP_ROOT/$ARCHIVE_NAME"
download "$BASE/$ARCHIVE_NAME.sha256" "$TEMP_ROOT/$ARCHIVE_NAME.sha256"
EXPECTED=$(awk '{print tolower($1)}' "$TEMP_ROOT/$ARCHIVE_NAME.sha256")
if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL=$(sha256sum "$TEMP_ROOT/$ARCHIVE_NAME" | awk '{print tolower($1)}')
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL=$(shasum -a 256 "$TEMP_ROOT/$ARCHIVE_NAME" | awk '{print tolower($1)}')
else
  echo "sha256sum or shasum is required" >&2
  exit 1
fi
[ "$EXPECTED" = "$ACTUAL" ] || { echo "SHA-256 mismatch; installation stopped" >&2; exit 1; }

command -v unzip >/dev/null 2>&1 || { echo "unzip is required" >&2; exit 1; }
unzip -q "$TEMP_ROOT/$ARCHIVE_NAME" -d "$TEMP_ROOT/expanded"
SOURCE="$TEMP_ROOT/expanded/medical-presentation-architect-$VERSION"
if [ -n "${MPA_TARGET:-}" ]; then
  python3 "$SOURCE/scripts/install.py" install --agent "$AGENT" --target "$MPA_TARGET"
else
  python3 "$SOURCE/scripts/install.py" install --agent "$AGENT"
fi

echo "Installed Medical Presentation Architect $VERSION for $AGENT."
if [ "$AGENT" = "kimi" ]; then
  echo "Start Kimi and enter: /skill:medical-presentation-architect"
fi
