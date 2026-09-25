#!/usr/bin/env bash
# 把本目录（桌面端）同步到 GitHub 仓库的 desktop/ 目录并推送。
#
# 只操作临时克隆目录，不触碰本地交付目录 ../学生选课与成绩管理系统/。
# 用法：bash tools/sync_to_github.sh [提交信息]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="https://github.com/DeRuiChen258/Student-Course-Selection-and-Grade-Management-System"
WORK_DIR="${SCUT_REPO_WORK_DIR:-/tmp/scut_repo_push}"
TARGET_SUBDIR="desktop"
COMMIT_MSG="${1:-feat(desktop): 同步 PySide6 桌面端（F01–F16 + 数据库对象可视化）}"

echo "== 1/5 准备仓库副本 =="
if [ -d "$WORK_DIR/.git" ]; then
    git -C "$WORK_DIR" fetch --depth 1 origin main
    git -C "$WORK_DIR" checkout -q main
    git -C "$WORK_DIR" reset -q --hard origin/main
else
    mkdir -p "$(dirname "$WORK_DIR")"
    git clone --depth 1 "$REPO_URL" "$WORK_DIR"
fi
echo "   仓库: $WORK_DIR（提交基线 $(git -C "$WORK_DIR" rev-parse --short HEAD)）"

echo "== 2/5 复制源码（排除运行产物与内部台账）=="
rm -rf "$WORK_DIR/$TARGET_SUBDIR"
mkdir -p "$WORK_DIR/$TARGET_SUBDIR"
tar -C "$ROOT_DIR" \
    --exclude='./.venv' --exclude='./build' --exclude='./dist' --exclude='./logs' \
    --exclude='./out' --exclude='./.agent' --exclude='./TASK.md' \
    --exclude='./config/connection.json' \
    --exclude='__pycache__' --exclude='*.pyc' \
    -cf - . | tar -C "$WORK_DIR/$TARGET_SUBDIR" -xf -

echo "== 3/5 复制页面截图到 docs/screenshots =="
mkdir -p "$WORK_DIR/$TARGET_SUBDIR/docs/screenshots"
cp "$ROOT_DIR"/out/screenshots/*.png "$WORK_DIR/$TARGET_SUBDIR/docs/screenshots/" 2>/dev/null || true
echo "   截图 $(find "$WORK_DIR/$TARGET_SUBDIR/docs/screenshots" -name '*.png' | wc -l) 张"

echo "== 4/5 泄漏检查 =="
# 排除本脚本自身：它含有用于比对的正则常量
LEAKS="$(grep -rIl -E "/home/(violet|codex)|陈德睿|王泓桀|2025308" \
    --exclude="$(basename "${BASH_SOURCE[0]}")" \
    "$WORK_DIR/$TARGET_SUBDIR" 2>/dev/null || true)"
if [ -n "$LEAKS" ]; then
    echo "[失败] 检出本机路径或个人信息，已中止：" >&2
    echo "$LEAKS" >&2
    exit 1
fi
if [ -f "$WORK_DIR/$TARGET_SUBDIR/config/connection.json" ]; then
    echo "[失败] config/connection.json 含真实口令，已中止" >&2
    exit 1
fi
echo "   未发现本机绝对路径、组员信息与本地连接配置"

echo "== 5/5 提交并推送 =="
cd "$WORK_DIR"
git add "$TARGET_SUBDIR"
if git diff --cached --quiet; then
    echo "   工作区无变更，无需推送"
    exit 0
fi
git -c user.name="$(git config user.name)" -c user.email="$(git config user.email)" \
    commit -q -m "$COMMIT_MSG"
git push -q origin main
echo "   已推送：$(git log -1 --format='%h %s')"
echo "   预览：$REPO_URL/tree/main/$TARGET_SUBDIR"
