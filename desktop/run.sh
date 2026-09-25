#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -x .venv/bin/python ]; then
    echo "[提示] 未找到 .venv，请先执行：" >&2
    echo "  uv venv --python 3.12 .venv && uv pip install -r requirements.txt" >&2
    exit 1
fi

exec .venv/bin/python main.py "$@"
