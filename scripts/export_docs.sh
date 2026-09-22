#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SRC="docs/设计说明书.md"
OUT_DIR="docs/out"
DOCX="$OUT_DIR/设计说明书.docx"
PDF="$OUT_DIR/设计说明书.pdf"

python3 - <<'PY' || { echo "[提示] 缺少 python-docx，正在安装..." >&2; python3 -m pip install --break-system-packages -q python-docx; }
import docx
PY

echo "== 生成图表 =="
python3 tools/gen_figs.py

echo "== Markdown → docx =="
python3 tools/md2docx.py --input "$SRC" --output "$DOCX" --title "学生选课与成绩管理系统设计说明书"

echo "== 第一遍 docx → pdf（用于定位目录页码）=="
mkdir -p "$OUT_DIR"
soffice --headless --convert-to pdf --outdir "$OUT_DIR" "$DOCX" > /dev/null
python3 tools/md2docx.py --input "$SRC" --output "$DOCX" --scan-pdf "$PDF" --toc-json "$OUT_DIR/toc.json"

echo "== 第二遍 docx（写入真实页码）→ pdf =="
python3 tools/md2docx.py --input "$SRC" --output "$DOCX" --title "学生选课与成绩管理系统设计说明书" \
    --toc-json "$OUT_DIR/toc.json"
soffice --headless --convert-to pdf --outdir "$OUT_DIR" "$DOCX" > /dev/null

if [ ! -s "$PDF" ]; then
    echo "[失败] PDF 未生成" >&2
    exit 1
fi

PAGES="$(pdfinfo "$PDF" | awk '/^Pages/{print $2}')"
echo "交付物: $DOCX ($(stat -c%s "$DOCX") 字节)"
echo "交付物: $PDF ($(stat -c%s "$PDF") 字节, $PAGES 页)"
if [ "$PAGES" -lt 30 ] || [ "$PAGES" -gt 48 ]; then
    echo "[提示] 当前 $PAGES 页，正文页数要求 30–45 页（封面与目录不计）" >&2
fi
