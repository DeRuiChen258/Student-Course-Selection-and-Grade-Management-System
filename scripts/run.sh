#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d out/classes ]; then
    echo "[提示] 尚未编译，先执行 bash scripts/build.sh" >&2
    exit 2
fi

exec java -Dfile.encoding=UTF-8 -cp "out/classes:lib/*" edu.scut.db.App "$@"
