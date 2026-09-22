#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="$ROOT_DIR/config/db.properties"

DB_HOST="$(grep -E '^db.host=' "$CONF" | cut -d= -f2-)"
DB_PORT="$(grep -E '^db.port=' "$CONF" | cut -d= -f2-)"
DB_NAME="$(grep -E '^db.name=' "$CONF" | cut -d= -f2-)"
DB_USER="$(grep -E '^db.user=' "$CONF" | cut -d= -f2-)"
DB_PASS="$(grep -E '^db.password=' "$CONF" | cut -d= -f2-)"

export MYSQL_PWD="$DB_PASS"
MYSQL=(mysql --protocol=TCP -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -N "$DB_NAME")

fail() { echo "[FAIL] $1" >&2; exit 1; }

cd "$ROOT_DIR"
echo "== 第一步：编译 =="
bash scripts/build.sh | tail -2

echo "== 清理上一次冒烟残留 =="
"${MYSQL[@]}" -e "DELETE FROM audit_log WHERE record_id = '202301019999';"

echo "== 第二步：回放固定演示用例（--demo）=="
bash scripts/run.sh --demo | tail -25

echo "== 第三步：断言数据库终态 =="
check() {
    local label="$1" expect="$2" sql="$3"
    local got
    got="$("${MYSQL[@]}" -e "$sql")"
    if [ "$got" = "$expect" ]; then
        echo "[PASS] $label = $got"
    else
        fail "$label 期望 $expect 实际 $got"
    fi
}

check "演示学生已删除" "0" "SELECT COUNT(*) FROM student WHERE student_no='202301019999';"
check "删除学生写入审计日志" "1" "SELECT COUNT(*) FROM audit_log WHERE record_id='202301019999' AND action='DELETE';"
check "退课后不再占用名额" "0" "SELECT COUNT(*) FROM enrollment e JOIN student s ON s.student_id=e.student_id WHERE s.student_no='202301019999';"
check "开课5计数回到基线" "5" "SELECT enrolled_count FROM course_offering WHERE offering_id=5;"
check "演示产生的成绩单已随学生删除" "0" "SELECT COUNT(*) FROM enrollment e JOIN student s ON s.student_id=e.student_id WHERE s.student_no='202301019999' AND e.score IS NOT NULL;"

echo "== 冒烟测试全部通过（退出码 0）=="
