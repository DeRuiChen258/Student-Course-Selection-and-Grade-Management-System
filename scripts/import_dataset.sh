#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="$ROOT_DIR/config/db.properties"
CLEAN_DIR="$ROOT_DIR/data/clean"

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
        --clean-dir) CLEAN_DIR="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 2 ;;
    esac
done

for name in student course offering enrollment; do
    if [ ! -s "$CLEAN_DIR/$name.csv" ]; then
        echo "[失败] 缺少 $CLEAN_DIR/$name.csv，请先执行 python3 tools/prepare_dataset.py" >&2
        exit 2
    fi
done

CLEAN_ROWS=$(( $(wc -l < "$CLEAN_DIR/student.csv") + $(wc -l < "$CLEAN_DIR/course.csv") \
              + $(wc -l < "$CLEAN_DIR/offering.csv") + $(wc -l < "$CLEAN_DIR/enrollment.csv") - 4 ))
echo "待导入 CSV 行数（不含表头）: $CLEAN_ROWS"

echo "== 导入前备份 =="
bash "$ROOT_DIR/scripts/backup.sh" -h "$DB_HOST" -P "$DB_PORT" -n "$DB_NAME" -u "$DB_USER" -p "$DB_PASS"

echo "== 导入开始 =="
export MYSQL_PWD="$DB_PASS"
mysql --protocol=TCP -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" --local-infile=1 "$DB_NAME" <<SQL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

CREATE TEMPORARY TABLE stage_student (
    student_no VARCHAR(20), student_name VARCHAR(40), gender VARCHAR(4), birth_date VARCHAR(20),
    class_code VARCHAR(30), class_name VARCHAR(60), grade_year VARCHAR(6), dept_code VARCHAR(10),
    enroll_date VARCHAR(20), phone VARCHAR(20), email VARCHAR(80), status VARCHAR(6)
);
CREATE TEMPORARY TABLE stage_course (
    course_code VARCHAR(16), course_name VARCHAR(60), credit VARCHAR(10), hours VARCHAR(10),
    course_type VARCHAR(6), dept_code VARCHAR(10)
);
CREATE TEMPORARY TABLE stage_offering (
    course_code VARCHAR(16), teacher_no VARCHAR(8), semester VARCHAR(11), capacity VARCHAR(10),
    classroom VARCHAR(30), open_time VARCHAR(25), class_code VARCHAR(30)
);
CREATE TEMPORARY TABLE stage_enrollment (
    student_no VARCHAR(20), course_code VARCHAR(16), teacher_no VARCHAR(8), semester VARCHAR(11),
    score VARCHAR(10), score_time VARCHAR(25), enroll_time VARCHAR(25), status VARCHAR(6)
);

LOAD DATA LOCAL INFILE '$CLEAN_DIR/student.csv' INTO TABLE stage_student
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE '$CLEAN_DIR/course.csv' INTO TABLE stage_course
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE '$CLEAN_DIR/offering.csv' INTO TABLE stage_offering
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE '$CLEAN_DIR/enrollment.csv' INTO TABLE stage_enrollment
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

INSERT INTO department (dept_code, dept_name, office, phone)
VALUES ('OU', '开放大学教学中心', '线上', '000-00000000')
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO teacher (teacher_no, teacher_name, gender, title, dept_id, hire_date)
SELECT DISTINCT o.teacher_no, CONCAT('数据集教师', RIGHT(o.teacher_no, 2)), '男', '讲师',
       (SELECT dept_id FROM department WHERE dept_code = 'OU'), '2015-09-01'
FROM stage_offering o
ON DUPLICATE KEY UPDATE teacher_name = VALUES(teacher_name);

INSERT INTO class_group (class_code, class_name, dept_id, grade_year, advisor_teacher_id)
SELECT DISTINCT s.class_code, s.class_name, (SELECT dept_id FROM department WHERE dept_code = 'OU'),
       CAST(s.grade_year AS UNSIGNED), NULL
FROM stage_student s
ON DUPLICATE KEY UPDATE class_name = VALUES(class_name), grade_year = VALUES(grade_year);

CREATE TEMPORARY TABLE new_course AS
SELECT t.* FROM stage_course t LEFT JOIN course c ON c.course_code = t.course_code
WHERE c.course_id IS NULL;
INSERT INTO course (course_code, course_name, credit, hours, course_type, dept_id)
SELECT t.course_code, t.course_name, CAST(t.credit AS DECIMAL(3,1)), CAST(t.hours AS UNSIGNED),
       t.course_type, (SELECT dept_id FROM department WHERE dept_code = 'OU')
FROM new_course t;

CREATE TEMPORARY TABLE tmp_offering AS
SELECT o.course_code, o.teacher_no, o.semester, CAST(o.capacity AS UNSIGNED) AS capacity,
       o.classroom, o.open_time
FROM stage_offering o;

UPDATE course_offering co
JOIN tmp_offering t JOIN course c ON c.course_code = t.course_code
     JOIN teacher te ON te.teacher_no = t.teacher_no
  ON co.course_id = c.course_id AND co.teacher_id = te.teacher_id AND co.semester = t.semester
SET co.capacity = t.capacity, co.classroom = t.classroom;

INSERT INTO course_offering (course_id, teacher_id, semester, capacity, enrolled_count, classroom, open_time)
SELECT c.course_id, te.teacher_id, t.semester, t.capacity, 0, t.classroom, t.open_time
FROM tmp_offering t
JOIN course c ON c.course_code = t.course_code
JOIN teacher te ON te.teacher_no = t.teacher_no
WHERE NOT EXISTS (SELECT 1 FROM course_offering co
                  WHERE co.course_id = c.course_id AND co.teacher_id = te.teacher_id AND co.semester = t.semester);

CREATE TEMPORARY TABLE tmp_student AS
SELECT t.student_no, t.student_name, t.gender, NULLIF(t.birth_date, '') AS birth_date,
       cg.class_id, t.enroll_date, t.phone, t.email, t.status
FROM stage_student t JOIN class_group cg ON cg.class_code = t.class_code;

UPDATE student s
JOIN tmp_student t ON t.student_no = s.student_no
SET s.student_name = t.student_name, s.gender = t.gender, s.birth_date = t.birth_date,
    s.class_id = t.class_id, s.enroll_date = t.enroll_date, s.phone = t.phone,
    s.email = t.email, s.status = t.status;

INSERT INTO student (student_no, student_name, gender, birth_date, class_id, enroll_date, phone, email, status)
SELECT t.student_no, t.student_name, t.gender, t.birth_date, t.class_id, t.enroll_date, t.phone, t.email, t.status
FROM tmp_student t
WHERE NOT EXISTS (SELECT 1 FROM student s WHERE s.student_no = t.student_no);

CREATE TEMPORARY TABLE tmp_enroll (
    student_id INT NOT NULL, offering_id INT NOT NULL, score DECIMAL(5,2) NULL,
    score_time DATETIME NULL, enroll_time DATETIME NOT NULL, status ENUM('已选','已退') NOT NULL,
    PRIMARY KEY (student_id, offering_id)
);
INSERT IGNORE INTO tmp_enroll (student_id, offering_id, score, score_time, enroll_time, status)
SELECT s.student_id, co.offering_id, CAST(NULLIF(e.score, '') AS DECIMAL(5,2)),
       NULLIF(e.score_time, ''), e.enroll_time, e.status
FROM stage_enrollment e
JOIN student s ON s.student_no = e.student_no
JOIN course c ON c.course_code = e.course_code
JOIN teacher te ON te.teacher_no = e.teacher_no
JOIN course_offering co ON co.course_id = c.course_id AND co.teacher_id = te.teacher_id AND co.semester = e.semester;

UPDATE enrollment en
JOIN tmp_enroll t ON t.student_id = en.student_id AND t.offering_id = en.offering_id
SET en.score = t.score, en.status = t.status;

INSERT INTO enrollment (student_id, offering_id, score, score_time, enroll_time, status)
SELECT t.student_id, t.offering_id, t.score, t.score_time, t.enroll_time, t.status
FROM tmp_enroll t
WHERE NOT EXISTS (SELECT 1 FROM enrollment en
                  WHERE en.student_id = t.student_id AND en.offering_id = t.offering_id);

UPDATE course_offering o
LEFT JOIN (SELECT offering_id, COUNT(*) AS cnt FROM enrollment WHERE status = '已选' GROUP BY offering_id) x
       ON x.offering_id = o.offering_id
SET o.enrolled_count = IFNULL(x.cnt, 0);

ANALYZE TABLE student, course, course_offering, enrollment;

SELECT CONCAT('学生=', (SELECT COUNT(*) FROM student),
              ' 课程=', (SELECT COUNT(*) FROM course),
              ' 开课=', (SELECT COUNT(*) FROM course_offering),
              ' 选课=', (SELECT COUNT(*) FROM enrollment),
              ' 导入行数=', (SELECT COUNT(*) FROM student WHERE student_no LIKE '90%'));
SQL

echo "== 导入后备份 =="
bash "$ROOT_DIR/scripts/backup.sh" -h "$DB_HOST" -P "$DB_PORT" -n "$DB_NAME" -u "$DB_USER" -p "$DB_PASS"
echo "== 导入结束：重复执行本脚本不会新增行（先更新后插入 + 唯一键）=="
