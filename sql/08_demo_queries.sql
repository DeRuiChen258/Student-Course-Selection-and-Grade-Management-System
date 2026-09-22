USE edu_system;

-- 考点：三表连接，列出学生所属班级与院系
SELECT s.student_no, s.student_name, cg.class_name, d.dept_name
FROM student s
JOIN class_group cg ON cg.class_id = s.class_id
JOIN department d ON d.dept_id = cg.dept_id
ORDER BY s.student_no LIMIT 10;

-- 考点：分组聚合 + HAVING，筛出均分低于 75 的开课
SELECT o.offering_id, c.course_name, ROUND(AVG(e.score), 2) AS avg_score, COUNT(e.score) AS scored
FROM course_offering o
JOIN course c ON c.course_id = o.course_id
JOIN enrollment e ON e.offering_id = o.offering_id AND e.score IS NOT NULL
GROUP BY o.offering_id, c.course_name
HAVING AVG(e.score) < 75
ORDER BY avg_score;

-- 考点：相关子查询，找出选课门数高于本院系平均的学生
SELECT s.student_no, s.student_name, COUNT(e.enrollment_id) AS course_count
FROM student s
JOIN enrollment e ON e.student_id = s.student_id AND e.status = '已选'
GROUP BY s.student_id, s.student_no, s.student_name
HAVING COUNT(e.enrollment_id) > (
    SELECT AVG(cnt) FROM (
        SELECT COUNT(e2.enrollment_id) AS cnt
        FROM student s2 JOIN enrollment e2 ON e2.student_id = s2.student_id AND e2.status = '已选'
        GROUP BY s2.student_id) t)
ORDER BY course_count DESC, s.student_no;

-- 考点：EXISTS 半连接，找出从未选过课的学生
SELECT s.student_no, s.student_name
FROM student s
WHERE NOT EXISTS (SELECT 1 FROM enrollment e WHERE e.student_id = s.student_id AND e.status = '已选');

-- 考点：窗口函数，按开课对成绩排名并取前 3 名
SELECT * FROM (
    SELECT o.offering_id, c.course_name, s.student_no, e.score,
           RANK() OVER (PARTITION BY o.offering_id ORDER BY e.score DESC) AS rk
    FROM enrollment e
    JOIN student s ON s.student_id = e.student_id
    JOIN course_offering o ON o.offering_id = e.offering_id
    JOIN course c ON c.course_id = o.course_id
    WHERE e.score IS NOT NULL) r
WHERE rk <= 3
ORDER BY offering_id, rk LIMIT 15;

-- 考点：窗口函数累计，按学期统计开课数累计值
SELECT semester, course_cnt,
       SUM(course_cnt) OVER (ORDER BY semester) AS 累计开课数
FROM (SELECT semester, COUNT(*) AS course_cnt FROM course_offering GROUP BY semester) t
ORDER BY semester;

-- 考点：视图调用，直接读课程统计视图
SELECT * FROM v_course_stat ORDER BY 平均分 DESC LIMIT 5;

-- 考点：视图 + 过滤，读成绩单视图中不及格记录
SELECT 学号, 姓名, 课程名, 成绩, 等级 FROM v_student_transcript WHERE 成绩 < 60 ORDER BY 成绩;

-- 考点：GROUP_CONCAT，把每名学生已选课程拼成一行
SELECT s.student_no, s.student_name,
       GROUP_CONCAT(c.course_code ORDER BY c.course_code SEPARATOR ',') AS 已选课程
FROM student s
JOIN enrollment e ON e.student_id = s.student_id AND e.status = '已选'
JOIN course_offering o ON o.offering_id = e.offering_id
JOIN course c ON c.course_id = o.course_id
GROUP BY s.student_id, s.student_no, s.student_name
ORDER BY s.student_no LIMIT 10;

-- 考点：自定义函数，按学生计算绩点（无成绩返回 NULL）
SELECT student_no, student_name, f_gpa(student_id) AS gpa
FROM student ORDER BY gpa DESC LIMIT 10;

-- 考点：多表连接 + 混合排序，查询某开课的完整名单
SELECT s.student_no, s.student_name, cg.class_name, e.score, e.status
FROM enrollment e
JOIN student s ON s.student_id = e.student_id
JOIN class_group cg ON cg.class_id = s.class_id
WHERE e.offering_id = 3
ORDER BY e.score IS NULL, e.score DESC;

-- 考点：CASE 分组统计，按分数段统计人数
SELECT CASE WHEN score IS NULL THEN '未出分'
            WHEN score >= 90 THEN '90-100'
            WHEN score >= 80 THEN '80-89'
            WHEN score >= 70 THEN '70-79'
            WHEN score >= 60 THEN '60-69'
            ELSE '60 分以下' END AS 分数段,
       COUNT(*) AS 人数
FROM enrollment WHERE status = '已选'
GROUP BY 分数段 ORDER BY 人数 DESC;

-- 考点：左连接统计，列出每门课程的选课人数（含 0 人）
SELECT c.course_code, c.course_name, COUNT(e.enrollment_id) AS 选课人数
FROM course c
LEFT JOIN course_offering o ON o.course_id = c.course_id
LEFT JOIN enrollment e ON e.offering_id = o.offering_id AND e.status = '已选'
GROUP BY c.course_id, c.course_code, c.course_name
ORDER BY 选课人数 DESC;

-- 考点：审计日志查询，按时间倒序看最近的学生删除记录
SELECT log_id, table_name, action, record_id, operator, action_time
FROM audit_log ORDER BY action_time DESC LIMIT 10;

-- 考点：EXPLAIN 观察索引命中（按班级查学生）
EXPLAIN SELECT * FROM student WHERE class_id = 1;

-- 考点：EXPLAIN 观察索引命中（按学期查开课）
EXPLAIN SELECT * FROM course_offering WHERE semester = '2026-2027-1';

-- 考点：EXPLAIN 观察覆盖索引（按开课查成绩分布）
EXPLAIN SELECT score, COUNT(*) FROM enrollment WHERE offering_id = 3 GROUP BY score;
