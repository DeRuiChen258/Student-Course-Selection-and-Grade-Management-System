#!/usr/bin/env bash
# 安装应用图标与桌面启动器（应用菜单 + 桌面图标）。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

APP_ID="edu-desktop"
APP_NAME="学生选课与成绩管理系统"
COMMENT="数据库大作业桌面端 · Python + Qt + MySQL 8（edu_system）"
ICON_MASTER="$ROOT_DIR/resources/icon.png"
ICON_DIR="$ROOT_DIR/resources/icons"
APPLICATIONS_DIR="$HOME/.local/share/applications"
ICONS_ROOT="$HOME/.local/share/icons/hicolor"

if [ ! -x .venv/bin/python ]; then
    echo "[失败] 未找到 .venv，请先按 README 第二节安装依赖" >&2
    exit 1
fi

if [ ! -f "$ICON_MASTER" ]; then
    echo "== 生成应用图标 =="
    .venv/bin/python tools/make_icon.py "${1:-}"
fi

echo "== 安装 hicolor 图标 =="
for size in 16 24 32 48 64 128 256 512; do
    source_png="$ICON_DIR/${APP_ID}_${size}.png"
    [ -f "$source_png" ] || continue
    target_dir="$ICONS_ROOT/${size}x${size}/apps"
    mkdir -p "$target_dir"
    cp -f "$source_png" "$target_dir/${APP_ID}.png"
done
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f "$ICONS_ROOT" >/dev/null 2>&1 || true
fi

echo "== 写入启动器 =="
mkdir -p "$APPLICATIONS_DIR"
ENTRY_FILE="$APPLICATIONS_DIR/${APP_ID}.desktop"
cat > "$ENTRY_FILE" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=${APP_NAME}
Name[zh_CN]=${APP_NAME}
Comment=${COMMENT}
Comment[zh_CN]=${COMMENT}
Exec=${ROOT_DIR}/run.sh
Path=${ROOT_DIR}
Icon=${ICON_MASTER}
Terminal=false
Categories=Education;Engineering;
Keywords=MySQL;SQL;Qt;PySide6;数据库;选课;成绩;
StartupNotify=true
StartupWMClass=${APP_ID}
EOF
chmod 755 "$ENTRY_FILE"

# 桌面图标：XDG_DESKTOP_DIR 指向家目录时放 $HOME，否则放 $HOME/Desktop；两处都放以兼容
for desktop_dir in "$HOME" "$HOME/Desktop"; do
    [ -d "$desktop_dir" ] || continue
    cp -f "$ENTRY_FILE" "$desktop_dir/${APP_NAME}.desktop"
    chmod 755 "$desktop_dir/${APP_NAME}.desktop"
    if command -v gio >/dev/null 2>&1; then
        gio set "$desktop_dir/${APP_NAME}.desktop" metadata::trusted true >/dev/null 2>&1 || true
    fi
done

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$ENTRY_FILE" && echo "[校验] desktop-file-validate 通过"
fi

echo "== 安装完成 =="
echo "应用菜单项 : $ENTRY_FILE"
echo "桌面图标   : $HOME/${APP_NAME}.desktop"
echo "启动命令   : $ROOT_DIR/run.sh"
