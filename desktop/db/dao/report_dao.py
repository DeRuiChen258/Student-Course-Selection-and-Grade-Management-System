"""统计报表查询：聚合全部下推到数据库执行。"""

from .base import DaoBase


class ReportDao(DaoBase):
    def course_stat(self, semester=None, dept_id=None, top=20):
        return self.db.query(
            "SELECT v.课程代码 AS code, v.课程名 AS name, v.学期 AS semester, "
            "       v.选课人数 AS students, v.平均分 AS avg_score, "
            "       v.最高分 AS max_score, v.最低分 AS min_score, "
            "       v.不及格人数 AS fail_count, "
            "       ROUND(v.不及格人数 / GREATEST(v.选课人数, 1) * 100, 1) AS fail_rate "
            "FROM v_course_stat v "
            "JOIN course c ON c.course_code = v.课程代码 "
            "WHERE (%s IS NULL OR v.学期 = %s) AND (%s IS NULL OR c.dept_id = %s) "
            "ORDER BY v.选课人数 DESC, v.平均分 DESC LIMIT %s",
            (semester, semester, dept_id, dept_id, int(top)),
            source="F16 课程统计（视图 + 聚合）")

    def score_distribution(self, semester=None, dept_id=None):
        return self.db.query(
            "SELECT CASE WHEN e.score IS NULL THEN '未出分' "
            "            WHEN e.score < 60 THEN '0-59' "
            "            WHEN e.score < 70 THEN '60-69' "
            "            WHEN e.score < 80 THEN '70-79' "
            "            WHEN e.score < 90 THEN '80-89' "
            "            ELSE '90-100' END AS bucket, "
            "       COUNT(*) AS cnt "
            "FROM enrollment e "
            "JOIN course_offering o ON o.offering_id = e.offering_id "
            "JOIN course c ON c.course_id = o.course_id "
            "WHERE e.status = '已选' AND (%s IS NULL OR o.semester = %s) "
            "  AND (%s IS NULL OR c.dept_id = %s) "
            "GROUP BY bucket "
            "ORDER BY FIELD(bucket, '0-59', '60-69', '70-79', '80-89', '90-100', '未出分')",
            (semester, semester, dept_id, dept_id),
            source="F16 成绩分布（CASE 分箱 + GROUP BY）")

    def semester_summary(self):
        return self.db.query(
            "SELECT o.semester AS semester, COUNT(DISTINCT o.offering_id) AS offerings, "
            "       COUNT(DISTINCT o.course_id) AS courses, "
            "       SUM(o.capacity) AS capacity, SUM(o.enrolled_count) AS enrolled, "
            "       IFNULL(ROUND(AVG(e.score), 2), 0) AS avg_score "
            "FROM course_offering o "
            "LEFT JOIN enrollment e ON e.offering_id = o.offering_id AND e.status = '已选' "
            "GROUP BY o.semester ORDER BY o.semester",
            source="F16 学期开课汇总")

    def course_type_share(self, dept_id=None):
        return self.db.query(
            "SELECT c.course_type AS course_type, COUNT(*) AS cnt, SUM(c.credit) AS credits "
            "FROM course c WHERE (%s IS NULL OR c.dept_id = %s) "
            "GROUP BY c.course_type ORDER BY cnt DESC",
            (dept_id, dept_id), source="F16 课程类型占比")

    def gpa_ranking(self, class_id=None, top=20):
        return self.db.query(
            "SELECT s.student_no AS student_no, s.student_name AS student_name, "
            "       cg.class_name AS class_name, s.status AS status, "
            "       f_gpa(s.student_id) AS gpa, "
            "       (SELECT IFNULL(SUM(c.credit), 0) FROM enrollment e "
            "         JOIN course_offering o ON o.offering_id = e.offering_id "
            "         JOIN course c ON c.course_id = o.course_id "
            "        WHERE e.student_id = s.student_id AND e.status = '已选' "
            "          AND e.score IS NOT NULL) AS credits, "
            "       (SELECT COUNT(*) FROM enrollment e "
            "        WHERE e.student_id = s.student_id AND e.status = '已选' "
            "          AND e.score IS NOT NULL AND e.score < 60) AS failed "
            "FROM student s JOIN class_group cg ON cg.class_id = s.class_id "
            "WHERE (%s IS NULL OR cg.class_id = %s) "
            "ORDER BY gpa IS NULL, gpa DESC, student_no LIMIT %s",
            (class_id, class_id, int(top)),
            source="F16 GPA 排名（标量函数 f_gpa）")

    def class_options(self):
        return self.db.query(
            "SELECT class_id AS id, class_name AS name FROM class_group ORDER BY class_id",
            source="班级候选")

    def dept_options(self):
        return self.db.query(
            "SELECT dept_id AS id, dept_name AS name FROM department ORDER BY dept_id",
            source="院系候选")

    def explain_index_compare(self, offering_id):
        with_index = self.db.query(
            "EXPLAIN SELECT score, COUNT(*) FROM enrollment WHERE offering_id = %s GROUP BY score",
            (int(offering_id),), source="F16 索引对比（使用 idx_enroll_offering）")
        without_index = self.db.query(
            "EXPLAIN SELECT score, COUNT(*) FROM enrollment IGNORE INDEX (idx_enroll_offering) "
            "WHERE offering_id = %s GROUP BY score",
            (int(offering_id),), source="F16 索引对比（忽略索引）")
        return with_index, without_index
