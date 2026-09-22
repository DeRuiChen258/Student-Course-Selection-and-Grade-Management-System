#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$ROOT_DIR/data/raw"

usage() {
    cat <<'EOF'
用法: bash scripts/fetch_dataset.sh [--dir 目标目录]
说明: 下载 OULAD（Open University Learning Analytics Dataset）核心 CSV 到目标目录，
      默认 data/raw；每个文件下载后用 sha256 校验，校验失败立即退出并保留原文件。
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dir) TARGET_DIR="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "未知参数: $1"; usage; exit 2 ;;
    esac
done

BASE_URL="https://raw.githubusercontent.com/gopi-0707/OULAD-Analysis/main"

FILES=(
    "courses.csv:4f16eee7454b15e109b0a21a0e43be820e6846ed6f9301bb7feb5ab5ad737a75"
    "assessments.csv:8cc738fb88ad760571d6f2a23059bfee0ffcae3bcd830514c9cbd5c6d5a046f1"
    "vle.csv:d1b28303dea802ad87b4484e1196e878e06824850b9a4fe8aa34693439fe87e9"
    "studentInfo.csv:7e6f3e474a5eee00639d2a414a6c7e928745823c2d2c2563ca1780145f99b0d6"
    "studentRegistration.csv:0d32676285372aaf2e7a80304e5b274b4fba24313e2ca4c04317225e1ec90170"
    "studentAssessment.csv:fd5320786328d05af841ee7dd4b5871b9dada3b9fe9d6a3642b2f42635510a6e"
)

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

echo "目标目录: $TARGET_DIR"
for entry in "${FILES[@]}"; do
    name="${entry%%:*}"
    want="${entry##*:}"
    if [ -f "$name" ]; then
        got="$(sha256sum "$name" | awk '{print $1}')"
        if [ "$got" = "$want" ]; then
            echo "[跳过] $name 已存在且校验一致"
            continue
        fi
        echo "[重下] $name 校验不一致，重新下载"
    fi
    if ! curl -fsSL --retry 3 --retry-delay 2 -o "$name.part" "$BASE_URL/$name"; then
        echo "[失败] 下载 $name 失败。离线替代方案：python3 tools/prepare_dataset.py --generate 12000" >&2
        rm -f "$name.part"
        exit 1
    fi
    got="$(sha256sum "$name.part" | awk '{print $1}')"
    if [ "$got" != "$want" ]; then
        echo "[失败] $name sha256 不一致：期望 $want 实际 $got" >&2
        echo "       原文件已保留为 $name.part，请人工核对来源" >&2
        exit 1
    fi
    mv "$name.part" "$name"
    echo "[完成] $name $(stat -c%s "$name") 字节 sha256 校验通过"
done

sha256sum ./*.csv > SHA256SUMS.txt
echo "全部文件校验通过，校验清单：$TARGET_DIR/SHA256SUMS.txt"
