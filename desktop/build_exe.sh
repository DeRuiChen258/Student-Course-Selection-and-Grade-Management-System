#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -x .venv/bin/python ]; then
    echo "[失败] 未找到 .venv" >&2
    exit 1
fi

if ! .venv/bin/python -c "import PyInstaller" 2>/dev/null; then
    echo "== 安装 PyInstaller =="
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python .venv/bin/python PyInstaller==6.11.1
    else
        .venv/bin/python -m pip install PyInstaller==6.11.1
    fi
fi

echo "== 清理旧产物 =="
rm -rf build dist

echo "== 开始打包（one-folder）=="
.venv/bin/python -m PyInstaller \
    --noconfirm --clean --windowed \
    --name EduDesktop \
    --icon "resources/icon.png" \
    --add-data "resources:resources" \
    --add-data "config/connection.example.json:config" \
    --collect-submodules pymysql \
    main.py

echo "== 打包完成 =="
echo "产物: $ROOT_DIR/dist/EduDesktop/EduDesktop"
