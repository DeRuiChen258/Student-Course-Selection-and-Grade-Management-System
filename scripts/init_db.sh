#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="$ROOT_DIR/config/db.properties"

DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="edu_system"
DB_USER="root"
DB_PASS=""
APP_PASS=""
USE_SUDO=0
PASS_GIVEN=0

prop() {
    [ -f "$CONF" ] || return 0
    grep -E "^$1=" "$CONF" | head -1 | cut -d= -f2- || true
}

if [ -f "$CONF" ]; then
    DB_HOST="$(prop db.host)"; DB_PORT="$(prop db.port)"; DB_NAME="$(prop db.name)"
fi

usage() {
    cat <<'EOF'
用法: bash scripts/init_db.sh [-u 用户] [-p [口令]] [-h 主机] [-P 端口] [-n 库名] [--sudo]
  -u 用户   默认 root（建库建账号需要 DDL 权限）
  -p 口令   管理账号口令（root 常为空）；不带值时交互输入
  --app-password 口令  为 edu_app 等四个账号设置的口令（默认取 config/db.properties 的 db.password）
  --sudo    用 sudo mysql（本机 root 为 socket 认证时使用）
说明: 按 sql/00 → sql/07 顺序执行，逐段校验并打印对象与数据行数。
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -u) DB_USER="${2:?缺少用户名}"; shift 2 ;;
        -p)
            if [ $# -ge 2 ] && [ "${2:0:1}" != "-" ]; then DB_PASS="$2"; PASS_GIVEN=1; shift 2;
            else read -r -s -p "请输入 $DB_USER 的口令: " DB_PASS; echo; PASS_GIVEN=1; shift 1; fi ;;
        -h) DB_HOST="$2"; shift 2 ;;
        -P) DB_PORT="$2"; shift 2 ;;
        -n) DB_NAME="$2"; shift 2 ;;
        --app-password) APP_PASS="$2"; shift 2 ;;
        --sudo) USE_SUDO=1; shift ;;
        --help) usage; exit 0 ;;
        *) echo "未知参数: $1"; usage; exit 2 ;;
    esac
done

if [ -z "$APP_PASS" ]; then
    APP_PASS="$(prop db.password)"
fi
if [ -z "$APP_PASS" ]; then
    echo "[提示] 未提供 --app-password 且配置中没有 db.password，将使用 sql/00 中的占位口令" >&2
    APP_PASS="ChangeMe_App_2026"
fi

if [ "$USE_SUDO" = "1" ]; then
    MYSQL_CMD=(sudo mysql)
else
    MYSQL_CMD=(mysql --protocol=TCP -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER")
    export MYSQL_PWD="$DB_PASS"
fi

cd "$ROOT_DIR"
echo "== 目标实例 $DB_HOST:$DB_PORT 库 $DB_NAME 账号 $DB_USER =="

"${MYSQL_CMD[@]}" --init-command="SET @pwd_app='$APP_PASS', @pwd_teacher='$APP_PASS', @pwd_student='$APP_PASS', @pwd_readonly='$APP_PASS'" < sql/00_create_database.sql

for file in 01_schema_tables 02_schema_indexes 03_views 04_procedures 05_triggers 06_privileges 07_seed_data; do
    if ! "${MYSQL_CMD[@]}" "$DB_NAME" < "sql/$file.sql" > /tmp/init_db_step.log 2>&1; then
        echo "[失败] sql/$file.sql" >&2
        tail -5 /tmp/init_db_step.log >&2
        exit 1
    fi
    echo "[完成] sql/$file.sql"
done

"${MYSQL_CMD[@]}" -N "$DB_NAME" -e "
SELECT CONCAT('表=', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_type='BASE TABLE'),
              ' 视图=', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='$DB_NAME'),
              ' 触发器=', (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='$DB_NAME'),
              ' 例程=', (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='$DB_NAME'),
              ' 学生=', (SELECT COUNT(*) FROM student),
              ' 开课=', (SELECT COUNT(*) FROM course_offering),
              ' 选课=', (SELECT COUNT(*) FROM enrollment));"
echo "下一步: bash scripts/build.sh && bash scripts/run.sh"
