USE edu_system;

-- 按院系列教师
CREATE INDEX idx_teacher_dept ON teacher (dept_id);
-- 按班级查学生
CREATE INDEX idx_student_class ON student (class_id);
-- 按院系筛课程
CREATE INDEX idx_course_dept ON course (dept_id);
-- 按学期查开课
CREATE INDEX idx_offering_semester ON course_offering (semester, course_id);
-- 名单与成绩统计覆盖索引
CREATE INDEX idx_enroll_offering ON enrollment (offering_id, score);
-- 学生课表查询
CREATE INDEX idx_enroll_student ON enrollment (student_id);
-- 按时间查审计
CREATE INDEX idx_audit_time ON audit_log (action_time);
-- 按表名与时间查审计
CREATE INDEX idx_audit_table ON audit_log (table_name, action_time);

SELECT table_name AS 表, index_name AS 索引, GROUP_CONCAT(column_name ORDER BY seq_in_index) AS 列
FROM information_schema.statistics
WHERE table_schema = 'edu_system' AND index_name LIKE 'idx_%'
GROUP BY table_name, index_name ORDER BY table_name, index_name;
