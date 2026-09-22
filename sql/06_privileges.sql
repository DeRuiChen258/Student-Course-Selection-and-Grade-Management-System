USE edu_system;

-- 应用账号：运行期最小权限（增删改查 + 调用存储过程 + 导出例程）
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON edu_system.* TO 'edu_app'@'localhost';
-- 维护权限：应用内「一键初始化/重建演示库」与 scripts/init_db.sh 需要 DDL
GRANT CREATE, ALTER, DROP, INDEX, REFERENCES, CREATE VIEW, SHOW VIEW,
      CREATE ROUTINE, ALTER ROUTINE, TRIGGER, LOCK TABLES, CREATE TEMPORARY TABLES
      ON edu_system.* TO 'edu_app'@'localhost';
-- 备份脚本需要读取事件定义（mysqldump --events）
GRANT EVENT ON edu_system.* TO 'edu_app'@'localhost';

-- 教师账号：只读三个视图 + 只改成绩列 + 调用录分过程
GRANT SELECT ON edu_system.v_offering_detail TO 'edu_teacher'@'localhost';
GRANT SELECT ON edu_system.v_student_transcript TO 'edu_teacher'@'localhost';
GRANT SELECT ON edu_system.v_course_stat TO 'edu_teacher'@'localhost';
GRANT UPDATE (score, score_time) ON edu_system.enrollment TO 'edu_teacher'@'localhost';
GRANT EXECUTE ON PROCEDURE edu_system.p_save_score TO 'edu_teacher'@'localhost';

-- 学生账号：只读成绩单与开课详情
GRANT SELECT ON edu_system.v_student_transcript TO 'edu_student'@'localhost';
GRANT SELECT ON edu_system.v_offering_detail TO 'edu_student'@'localhost';

-- 只读账号：报表与演示用
GRANT SELECT ON edu_system.v_student_profile TO 'edu_readonly'@'localhost';
GRANT SELECT ON edu_system.v_offering_detail TO 'edu_readonly'@'localhost';
GRANT SELECT ON edu_system.v_student_transcript TO 'edu_readonly'@'localhost';
GRANT SELECT ON edu_system.v_course_stat TO 'edu_readonly'@'localhost';

FLUSH PRIVILEGES;

-- 越权演示（用 edu_teacher 连接后执行，期望 ERROR 1142）：
-- UPDATE student SET phone = 'x' WHERE student_no = '202301010001';
-- ERROR 1142 (42000): UPDATE command denied to user 'edu_teacher'@'localhost' for table 'student'

SELECT grantee AS 账号, table_name AS 对象, privilege_type AS 权限
FROM information_schema.table_privileges
WHERE table_schema = 'edu_system' AND grantee LIKE "'edu_%"
ORDER BY grantee, table_name, privilege_type;
