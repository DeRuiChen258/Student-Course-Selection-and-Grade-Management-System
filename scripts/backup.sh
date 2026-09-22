#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="$ROOT_DIR/config/db.properties"
OUT_DIR="$ROOT_DIR/backup"

DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="edu_system"
DB_USER="edu_app"
DB_PASS=""

prop() {
    [ -f "$CONF" ] || return 0
    grep -E "^$1=" "$CONF" | head -1 | cut -d= -f2- || true
}

if [ -f "$CONF" ]; then
    DB_HOST="$(prop db.host)"; DB_PORT="$(prop db.port)"
    DB_NAME="$(prop db.name)"; DB_USER="$(prop db.user)"; DB_PASS="$(prop db.password)"
fi

while [ $# -gt 0 ]; do
    case "$1" in
        -u) DB_USER="$2"; shift 2 ;;
        -p) if [ $# -ge 2 ] && [ "${2:0:1}" != "-" ]; then DB_PASS="$2"; shift 2;
            else read -r -s -p "请输入 $DB_USER 的口令: " DB_PASS; echo; shift 1; fi ;;
        -h) DB_HOST="$2"; shift 2 ;;
        -P) DB_PORT="$2"; shift 2 ;;
        -n) DB_NAME="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 2 ;;
    esac
done

mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET="$OUT_DIR/${DB_NAME}_${STAMP}.sql"

MYSQL_PWD="$DB_PASS" mysqldump --protocol=TCP -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" \
    --single-transaction --routines --triggers --events --no-tablespaces --set-gtid-purged=OFF \
    "$DB_NAME" > "$TARGET"

SIZE="$(stat -c%s "$TARGET")"
TABLES="$(grep -c '^CREATE TABLE' "$TARGET" || true)"
ROUTINES="$(grep -cE '^CREATE DEFINER=.*(PROCEDURE|FUNCTION) ' "$TARGET" || true)"
TRIGGERS="$(grep -c 'TRIGGER `' "$TARGET" || true)"

if [ "$SIZE" -le 0 ] || [ "$TABLES" -ne 9 ]; then
    echo "[失败] 备份校验不通过：文件 $TARGET 大小 $SIZE，CREATE TABLE $TABLES 条" >&2
    exit 1
fi

echo "备份完成: $TARGET"
echo "文件大小: $SIZE 字节 | 表结构: $TABLES | 存储过程与函数: $ROUTINES | 触发器: $TRIGGERS"
