"""四个业务实体的声明式规格：联表列表、筛选条件、表单字段与删除提示。

列表 SQL 中 DATE_FORMAT 的 % 需转义为 %%，因为这些语句始终带参数执行。
"""

from models.spec import EntitySpec, FieldSpec, FilterSpec
from models.table_model import Column

STUDENT = EntitySpec(
    key="student",
    title="学生管理",
    funcs=("F01", "F02", "F03", "F04"),
    subtitle="三层主从：院系 → 班级 → 学生；业务主键 student_no（12 位，UNIQUE）",
    table="student",
    pk="student_id",
    biz_key="student_no",
    list_sql=(
        "SELECT s.student_id AS student_id, s.student_no AS student_no, "
        "       s.student_name AS student_name, s.gender AS gender, "
        "       s.birth_date AS birth_date, s.class_id AS class_id, "
        "       s.enroll_date AS enroll_date, s.status AS status, "
        "       IFNULL(s.phone, '') AS phone, IFNULL(s.email, '') AS email, "
        "       cg.class_name AS class_name, d.dept_name AS dept_name, "
        "       (SELECT COUNT(*) FROM enrollment e WHERE e.student_id = s.student_id) "
        "           AS enrollment_count "
        "FROM student s "
        "JOIN class_group cg ON cg.class_id = s.class_id "
        "JOIN department d ON d.dept_id = cg.dept_id"),
    columns=[
        Column("student_no", "学号", 130),
        Column("student_name", "姓名", 90),
        Column("gender", "性别", 60, "center"),
        Column("class_name", "班级", 210),
        Column("dept_name", "院系", 190),
        Column("status", "学籍状态", 80, "center"),
        Column("enroll_date", "入学日期", 100, "center", "date"),
        Column("phone", "联系电话", 120),
        Column("email", "邮箱", 170),
    ],
    fields=[
        FieldSpec("student_no", "学号", "text", required=True, maxlen=12, hint="12 位数字"),
        FieldSpec("student_name", "姓名", "text", required=True, maxlen=30),
        FieldSpec("gender", "性别", "enum", required=True, choices=("男", "女"), default="男"),
        FieldSpec("birth_date", "出生日期", "date"),
        FieldSpec("class_id", "所属班级", "fk", required=True, source="classes"),
        FieldSpec("enroll_date", "入学日期", "date", required=True),
        FieldSpec("phone", "联系电话", "text", maxlen=20),
        FieldSpec("email", "邮箱", "text", maxlen=60),
        FieldSpec("status", "学籍状态", "enum", required=True, default="在读",
                  choices=("在读", "休学", "退学", "毕业")),
    ],
    filters=[
        FilterSpec("student_no", "学号", "s.student_no LIKE %s", "like", "text"),
        FilterSpec("student_name", "姓名", "s.student_name LIKE %s", "like", "text"),
        FilterSpec("class_id", "班级", "s.class_id = %s", "eq", "combo", source="classes", width=200),
        FilterSpec("status", "学籍状态", "s.status = %s", "eq", "combo",
                   choices=("在读", "休学", "退学", "毕业"), width=120),
        FilterSpec("enroll_from", "入学日期 ≥", "s.enroll_date >= %s", "ge", "date", width=130),
    ],
    order_by="s.student_no",
    delete_note="将级联删除该生 {enrollment_count} 条选课记录（ON DELETE CASCADE），"
                "并由触发器 trg_student_ad 写入审计日志 audit_log",
)

TEACHER = EntitySpec(
    key="teacher",
    title="教师管理",
    funcs=("F09",),
    subtitle="teacher.dept_id → department（RESTRICT）；工号 teacher_no 唯一（8 位）",
    table="teacher",
    pk="teacher_id",
    biz_key="teacher_no",
    list_sql=(
        "SELECT t.teacher_id AS teacher_id, t.teacher_no AS teacher_no, "
        "       t.teacher_name AS teacher_name, t.gender AS gender, t.title AS title, "
        "       t.dept_id AS dept_id, t.hire_date AS hire_date, "
        "       IFNULL(t.phone, '') AS phone, IFNULL(t.email, '') AS email, "
        "       d.dept_name AS dept_name, "
        "       (SELECT COUNT(*) FROM course_offering o WHERE o.teacher_id = t.teacher_id) "
        "           AS offering_count "
        "FROM teacher t JOIN department d ON d.dept_id = t.dept_id"),
    columns=[
        Column("teacher_no", "工号", 110),
        Column("teacher_name", "姓名", 90),
        Column("gender", "性别", 60, "center"),
        Column("title", "职称", 90, "center"),
        Column("dept_name", "院系", 200),
        Column("hire_date", "入职日期", 100, "center", "date"),
        Column("phone", "联系电话", 120),
        Column("email", "邮箱", 180),
    ],
    fields=[
        FieldSpec("teacher_no", "工号", "text", required=True, maxlen=8, hint="8 位数字"),
        FieldSpec("teacher_name", "姓名", "text", required=True, maxlen=30),
        FieldSpec("gender", "性别", "enum", required=True, choices=("男", "女"), default="男"),
        FieldSpec("title", "职称", "enum", required=True, default="讲师",
                  choices=("助教", "讲师", "副教授", "教授")),
        FieldSpec("dept_id", "所属院系", "fk", required=True, source="depts"),
        FieldSpec("hire_date", "入职日期", "date", required=True),
        FieldSpec("phone", "联系电话", "text", maxlen=20),
        FieldSpec("email", "邮箱", "text", maxlen=60),
    ],
    filters=[
        FilterSpec("teacher_no", "工号", "t.teacher_no LIKE %s", "like", "text"),
        FilterSpec("teacher_name", "姓名", "t.teacher_name LIKE %s", "like", "text"),
        FilterSpec("dept_id", "院系", "t.dept_id = %s", "eq", "combo", source="depts", width=200),
        FilterSpec("title", "职称", "t.title = %s", "eq", "combo",
                   choices=("助教", "讲师", "副教授", "教授"), width=110),
    ],
    order_by="t.teacher_no",
    delete_note="该教师已有 {offering_count} 条开课记录；外键 fk_offering_teacher"
                "为 ON DELETE RESTRICT，数据库将拒绝删除",
)

COURSE = EntitySpec(
    key="course",
    title="课程管理",
    funcs=("F05", "F06", "F07", "F08"),
    subtitle="CHECK ck_course_credit(0.5–10)、ck_course_hours(8–200)；course_code 唯一",
    table="course",
    pk="course_id",
    biz_key="course_code",
    list_sql=(
        "SELECT c.course_id AS course_id, c.course_code AS course_code, "
        "       c.course_name AS course_name, c.credit AS credit, c.hours AS hours, "
        "       c.course_type AS course_type, c.dept_id AS dept_id, "
        "       d.dept_name AS dept_name, "
        "       (SELECT COUNT(*) FROM course_offering o WHERE o.course_id = c.course_id) "
        "           AS offering_count, "
        "       (SELECT COUNT(*) FROM enrollment e "
        "         JOIN course_offering o2 ON o2.offering_id = e.offering_id "
        "        WHERE o2.course_id = c.course_id) AS enrollment_count "
        "FROM course c JOIN department d ON d.dept_id = c.dept_id"),
    columns=[
        Column("course_code", "课程代码", 110),
        Column("course_name", "课程名", 190),
        Column("credit", "学分", 70, "right", "decimal"),
        Column("hours", "学时", 70, "right", "number"),
        Column("course_type", "类型", 80, "center"),
        Column("dept_name", "开课院系", 200),
    ],
    fields=[
        FieldSpec("course_code", "课程代码", "text", required=True, maxlen=16,
                  hint="大写字母与数字"),
        FieldSpec("course_name", "课程名", "text", required=True, maxlen=60),
        FieldSpec("credit", "学分", "decimal", required=True, minimum=0.5, maximum=10.0,
                  decimals=1),
        FieldSpec("hours", "学时", "int", required=True, minimum=8, maximum=200),
        FieldSpec("course_type", "课程类型", "enum", required=True, default="选修",
                  choices=("必修", "选修", "通识")),
        FieldSpec("dept_id", "开课院系", "fk", required=True, source="depts"),
    ],
    filters=[
        FilterSpec("course_code", "课程代码", "c.course_code LIKE %s", "like", "text"),
        FilterSpec("course_name", "课程名", "c.course_name LIKE %s", "like", "text"),
        FilterSpec("dept_id", "开课院系", "c.dept_id = %s", "eq", "combo", source="depts", width=200),
        FilterSpec("course_type", "类型", "c.course_type = %s", "eq", "combo",
                   choices=("必修", "选修", "通识"), width=110),
    ],
    order_by="c.course_code",
    delete_note="该课程已有 {offering_count} 条开课记录、涉及 {enrollment_count} 条选课；"
                "外键 fk_offering_course 为 ON DELETE RESTRICT，数据库将拒绝删除",
)

OFFERING = EntitySpec(
    key="offering",
    title="开课管理",
    funcs=("F10",),
    subtitle="UNIQUE uk_offering(course,teacher,semester)；CHECK ck_offering_enrolled"
             "(已选人数 ≤ 容量)",
    table="course_offering",
    pk="offering_id",
    biz_key="offering_id",
    list_sql=(
        "SELECT o.offering_id AS offering_id, o.course_id AS course_id, "
        "       o.teacher_id AS teacher_id, o.semester AS semester, "
        "       o.capacity AS capacity, o.enrolled_count AS enrolled_count, "
        "       o.capacity - o.enrolled_count AS remain, "
        "       IFNULL(o.classroom, '') AS classroom, "
        "       DATE_FORMAT(o.open_time, '%%Y-%%m-%%d %%H:%%i') AS open_time, "
        "       c.course_code AS course_code, c.course_name AS course_name, "
        "       t.teacher_name AS teacher_name, "
        "       (SELECT IFNULL(ROUND(AVG(e.score), 2), 0) FROM enrollment e "
        "        WHERE e.offering_id = o.offering_id AND e.status = '已选') AS avg_score "
        "FROM course_offering o "
        "JOIN course c ON c.course_id = o.course_id "
        "JOIN teacher t ON t.teacher_id = o.teacher_id"),
    columns=[
        Column("offering_id", "开课号", 70, "right", "number"),
        Column("course_code", "课程代码", 100),
        Column("course_name", "课程名", 180),
        Column("teacher_name", "教师", 90),
        Column("semester", "学期", 110, "center"),
        Column("capacity", "容量", 70, "right", "number"),
        Column("enrolled_count", "已选", 70, "right", "number"),
        Column("remain", "余量", 70, "right", "number"),
        Column("avg_score", "均分", 80, "right", "decimal"),
        Column("classroom", "上课地点", 120),
    ],
    fields=[
        FieldSpec("course_id", "课程", "fk", required=True, source="courses"),
        FieldSpec("teacher_id", "任课教师", "fk", required=True, source="teachers"),
        FieldSpec("semester", "学期", "text", required=True, maxlen=11, hint="形如 2026-2027-1"),
        FieldSpec("capacity", "容量", "int", required=True, minimum=1, maximum=300, default=40),
        FieldSpec("classroom", "上课地点", "text", maxlen=30),
    ],
    filters=[
        FilterSpec("semester", "学期", "o.semester = %s", "eq", "combo", source="semesters",
                   width=130),
        FilterSpec("course_code", "课程代码", "c.course_code LIKE %s", "like", "text"),
        FilterSpec("teacher_id", "任课教师", "o.teacher_id = %s", "eq", "combo", source="teachers",
                   width=180),
    ],
    order_by="o.semester DESC, o.offering_id",
    delete_note="删除该开课将影响 {enrolled_count} 条选课记录；"
                "外键 fk_enroll_offering 为 ON DELETE RESTRICT，非空时数据库将拒绝删除",
)

ALL_SPECS = (STUDENT, TEACHER, COURSE, OFFERING)


def register(service):
    for spec in ALL_SPECS:
        service.register(spec)
    return {spec.key: spec for spec in ALL_SPECS}
