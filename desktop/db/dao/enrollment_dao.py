"""选课、退课、成绩（存储过程）与相关视图查询。"""

from .base import DaoBase


class EnrollmentDao(DaoBase):
    def enroll(self, student_no, offering_id):
        return self.db.call_proc("p_enroll_student", (student_no, int(offering_id)),
                                 source="F11 学生选课（存储过程）")

    def drop(self, student_no, offering_id):
        return self.db.call_proc("p_drop_course", (student_no, int(offering_id)),
                                 source="F12 学生退课（存储过程）")

    def save_score(self, student_no, offering_id, score):
        return self.db.call_proc("p_save_score", (student_no, int(offering_id), float(score)),
                                 source="F13/F14 成绩录入与修改（存储过程）")

    def transcript(self, student_no, semester=None):
        return self.db.query(
            "SELECT 学号 AS student_no, 姓名 AS student_name, 学期 AS semester, "
            "       课程代码 AS course_code, 课程名 AS course_name, 学分 AS credit, "
            "       成绩 AS score, 等级 AS grade, 绩点 AS gpa, 教师 AS teacher "
            "FROM v_student_transcript "
            "WHERE 学号 = %s AND (%s IS NULL OR 学期 = %s) "
            "ORDER BY 学期 DESC, 课程代码",
            (student_no, semester, semester), source="F15 学生课表（视图）")

    def roster(self, offering_id):
        return self.db.query(
            "SELECT s.student_no AS student_no, s.student_name AS student_name, "
            "       cg.class_name AS class_name, e.status AS status, e.score AS score, "
            "       DATE_FORMAT(e.score_time, '%%Y-%%m-%%d %%H:%%i') AS score_time "
            "FROM enrollment e "
            "JOIN student s ON s.student_id = e.student_id "
            "JOIN class_group cg ON cg.class_id = s.class_id "
            "WHERE e.offering_id = %s ORDER BY e.score IS NULL, e.score DESC, s.student_no",
            (int(offering_id),), source="F15 开课名单（联表）")

    def offering_detail(self, offering_id):
        return self.db.query_one(
            "SELECT 开课号 AS offering_id, 课程代码 AS course_code, 课程名 AS course_name, "
            "       学分 AS credit, 教师 AS teacher, 学期 AS semester, 容量 AS capacity, "
            "       已选人数 AS enrolled, 余量 AS remain, 均分 AS avg_score "
            "FROM v_offering_detail WHERE 开课号 = %s",
            (int(offering_id),), source="开课详情（视图）")

    def offering_options(self, semester=None, keyword=None, only_open=True):
        sql = ("SELECT o.offering_id AS id, c.course_code AS code, c.course_name AS name, "
               "       t.teacher_name AS teacher, o.semester AS semester, "
               "       o.capacity AS capacity, o.enrolled_count AS enrolled "
               "FROM course_offering o "
               "JOIN course c ON c.course_id = o.course_id "
               "JOIN teacher t ON t.teacher_id = o.teacher_id "
               "WHERE (%s IS NULL OR o.semester = %s) "
               "  AND (%s IS NULL OR c.course_code LIKE %s OR c.course_name LIKE %s)")
        params = [semester, semester, keyword,
                  f"%{keyword}%" if keyword else None, f"%{keyword}%" if keyword else None]
        if only_open:
            sql += " AND o.enrolled_count < o.capacity"
        sql += " ORDER BY o.semester DESC, c.course_code"
        return self.db.query(sql, tuple(params), source="开课候选")

    def student_options(self, keyword=None, limit=300):
        return self.db.query(
            "SELECT s.student_no AS student_no, s.student_name AS student_name, "
            "       cg.class_name AS class_name, s.status AS status "
            "FROM student s JOIN class_group cg ON cg.class_id = s.class_id "
            "WHERE (%s IS NULL OR s.student_no LIKE %s OR s.student_name LIKE %s) "
            "ORDER BY s.student_no LIMIT %s",
            (keyword, f"%{keyword}%" if keyword else None,
             f"%{keyword}%" if keyword else None, int(limit)),
            source="学生候选")

    def semester_options(self):
        rows = self.db.query("SELECT DISTINCT semester FROM course_offering ORDER BY semester DESC",
                             source="学期候选")
        return [row["semester"] for row in rows]

    def by_student(self, student_no):
        return self.db.query(
            "SELECT e.enrollment_id AS enrollment_id, c.course_code AS course_code, "
            "       c.course_name AS course_name, t.teacher_name AS teacher, "
            "       o.semester AS semester, o.offering_id AS offering_id, "
            "       e.score AS score, e.status AS status "
            "FROM enrollment e "
            "JOIN student s ON s.student_id = e.student_id "
            "JOIN course_offering o ON o.offering_id = e.offering_id "
            "JOIN course c ON c.course_id = o.course_id "
            "JOIN teacher t ON t.teacher_id = o.teacher_id "
            "WHERE s.student_no = %s ORDER BY o.semester DESC, c.course_code",
            (student_no,), source="学生选课记录")

    def student_summary(self, student_no):
        return self.db.query_one(
            "SELECT s.student_no AS student_no, s.student_name AS student_name, "
            "       cg.class_name AS class_name, d.dept_name AS dept_name, s.status AS status, "
            "       f_gpa(s.student_id) AS gpa, "
            "       (SELECT COUNT(*) FROM enrollment e "
            "         WHERE e.student_id = s.student_id AND e.status = '已选') AS course_count, "
            "       (SELECT IFNULL(SUM(c.credit), 0) FROM enrollment e "
            "         JOIN course_offering o ON o.offering_id = e.offering_id "
            "         JOIN course c ON c.course_id = o.course_id "
            "        WHERE e.student_id = s.student_id AND e.status = '已选' "
            "          AND e.score IS NOT NULL) AS credits, "
            "       (SELECT COUNT(*) FROM enrollment e "
            "         WHERE e.student_id = s.student_id AND e.status = '已选' "
            "           AND e.score IS NOT NULL AND e.score < 60) AS failed "
            "FROM student s "
            "JOIN class_group cg ON cg.class_id = s.class_id "
            "JOIN department d ON d.dept_id = cg.dept_id "
            "WHERE s.student_no = %s",
            (student_no,), source="学生学业概况（标量函数 f_gpa）")

    def roster_stats(self, offering_id):
        return self.db.query_one(
            "SELECT COUNT(*) AS total, "
            "       SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) AS scored, "
            "       ROUND(AVG(score), 2) AS avg_score, MAX(score) AS max_score, "
            "       MIN(score) AS min_score, "
            "       SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) AS failed "
            "FROM enrollment WHERE offering_id = %s AND status = '已选'",
            (int(offering_id),), source="开课成绩统计")

    def page(self, semester=None, keyword=None, status=None, score_state=None,
             limit=20, offset=0):
        where = (" WHERE (%s IS NULL OR o.semester = %s) "
                 "   AND (%s IS NULL OR s.student_no LIKE %s OR s.student_name LIKE %s "
                 "        OR c.course_code LIKE %s OR c.course_name LIKE %s) "
                 "   AND (%s IS NULL OR e.status = %s) "
                 "   AND (%s IS NULL OR (%s = '未出分' AND e.score IS NULL) "
                 "        OR (%s = '已出分' AND e.score IS NOT NULL))")
        params = [semester, semester,
                  keyword, f"%{keyword}%" if keyword else None,
                  f"%{keyword}%" if keyword else None,
                  f"%{keyword}%" if keyword else None,
                  f"%{keyword}%" if keyword else None,
                  status, status,
                  score_state, score_state, score_state]
        base = ("FROM enrollment e "
                "JOIN student s ON s.student_id = e.student_id "
                "JOIN class_group cg ON cg.class_id = s.class_id "
                "JOIN course_offering o ON o.offering_id = e.offering_id "
                "JOIN course c ON c.course_id = o.course_id "
                "JOIN teacher t ON t.teacher_id = o.teacher_id")
        total = int(self.db.scalar(f"SELECT COUNT(*) {base} {where}", tuple(params),
                                   source="选课记录计数") or 0)
        rows = self.db.query(
            "SELECT e.enrollment_id AS enrollment_id, e.offering_id AS offering_id, "
            "       s.student_no AS student_no, s.student_name AS student_name, "
            "       cg.class_name AS class_name, c.course_code AS course_code, "
            "       c.course_name AS course_name, t.teacher_name AS teacher_name, "
            "       o.semester AS semester, e.score AS score, e.status AS status, "
            "       DATE_FORMAT(e.enroll_time, '%%Y-%%m-%%d %%H:%%i') AS enroll_time, "
            "       DATE_FORMAT(e.score_time, '%%Y-%%m-%%d %%H:%%i') AS score_time "
            f"{base} {where} "
            "ORDER BY o.semester DESC, c.course_code, s.student_no LIMIT %s OFFSET %s",
            tuple(params) + (int(limit), int(offset)), source="选课记录查询")
        return rows, total
