USE edu_system;

CREATE OR REPLACE VIEW v_student_profile AS
SELECT s.student_no     AS 学号,
       s.student_name   AS 姓名,
       s.gender         AS 性别,
       cg.class_name    AS 班级,
       d.dept_name      AS 院系,
       s.status         AS 状态,
       s.enroll_date    AS 入学日期
FROM student s
JOIN class_group cg ON cg.class_id = s.class_id
JOIN department d ON d.dept_id = cg.dept_id;

CREATE OR REPLACE VIEW v_offering_detail AS
SELECT o.offering_id              AS 开课号,
       c.course_code              AS 课程代码,
       c.course_name              AS 课程名,
       c.credit                   AS 学分,
       t.teacher_name             AS 教师,
       o.semester                 AS 学期,
       o.capacity                 AS 容量,
       o.enrolled_count           AS 已选人数,
       o.capacity - o.enrolled_count AS 余量,
       ROUND(AVG(e.score), 2)     AS 均分
FROM course_offering o
JOIN course c ON c.course_id = o.course_id
JOIN teacher t ON t.teacher_id = o.teacher_id
LEFT JOIN enrollment e ON e.offering_id = o.offering_id AND e.status = '已选'
GROUP BY o.offering_id, c.course_code, c.course_name, c.credit, t.teacher_name,
         o.semester, o.capacity, o.enrolled_count;

CREATE OR REPLACE VIEW v_student_transcript AS
SELECT s.student_no   AS 学号,
       s.student_name AS 姓名,
       o.semester     AS 学期,
       c.course_code  AS 课程代码,
       c.course_name  AS 课程名,
       c.credit       AS 学分,
       e.score        AS 成绩,
       CASE WHEN e.score IS NULL THEN NULL
            WHEN e.score >= 90 THEN 'A'
            WHEN e.score >= 80 THEN 'B'
            WHEN e.score >= 70 THEN 'C'
            WHEN e.score >= 60 THEN 'D'
            ELSE 'F' END                        AS 等级,
       CASE WHEN e.score IS NULL THEN NULL
            WHEN e.score >= 90 THEN 4.0
            WHEN e.score >= 80 THEN 3.0
            WHEN e.score >= 70 THEN 2.0
            WHEN e.score >= 60 THEN 1.0
            ELSE 0.0 END                        AS 绩点,
       t.teacher_name AS 教师
FROM enrollment e
JOIN student s ON s.student_id = e.student_id
JOIN course_offering o ON o.offering_id = e.offering_id
JOIN course c ON c.course_id = o.course_id
JOIN teacher t ON t.teacher_id = o.teacher_id
WHERE e.status = '已选';

CREATE OR REPLACE VIEW v_course_stat AS
SELECT c.course_code                              AS 课程代码,
       c.course_name                              AS 课程名,
       o.semester                                 AS 学期,
       COUNT(e.enrollment_id)                     AS 选课人数,
       ROUND(AVG(e.score), 2)                     AS 平均分,
       MAX(e.score)                               AS 最高分,
       MIN(e.score)                               AS 最低分,
       SUM(CASE WHEN e.score < 60 THEN 1 ELSE 0 END) AS 不及格人数
FROM course_offering o
JOIN course c ON c.course_id = o.course_id
LEFT JOIN enrollment e ON e.offering_id = o.offering_id AND e.status = '已选'
GROUP BY c.course_code, c.course_name, o.semester;

SELECT table_name AS 视图, table_comment AS 说明
FROM information_schema.tables
WHERE table_schema = 'edu_system' AND table_type = 'VIEW' ORDER BY table_name;
