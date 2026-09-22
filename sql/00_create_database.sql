-- 须用 sudo mysql 执行一次：sudo mysql < sql/00_create_database.sql
-- 四个默认口令是占位值，首次使用请改成自己的口令；也可用 scripts/init_db.sh 注入（--init-command）
SET @pwd_app      = IFNULL(@pwd_app,      'ChangeMe_App_2026');
SET @pwd_teacher  = IFNULL(@pwd_teacher,  'ChangeMe_Teacher_2026');
SET @pwd_student  = IFNULL(@pwd_student,  'ChangeMe_Student_2026');
SET @pwd_readonly = IFNULL(@pwd_readonly, 'ChangeMe_Readonly_2026');

DROP DATABASE IF EXISTS edu_system;
CREATE DATABASE edu_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

SET @ddl = CONCAT('CREATE USER IF NOT EXISTS ''edu_app''@''localhost'' IDENTIFIED BY ''', @pwd_app, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;
SET @ddl = CONCAT('ALTER USER ''edu_app''@''localhost'' IDENTIFIED BY ''', @pwd_app, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;

SET @ddl = CONCAT('CREATE USER IF NOT EXISTS ''edu_teacher''@''localhost'' IDENTIFIED BY ''', @pwd_teacher, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;
SET @ddl = CONCAT('ALTER USER ''edu_teacher''@''localhost'' IDENTIFIED BY ''', @pwd_teacher, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;

SET @ddl = CONCAT('CREATE USER IF NOT EXISTS ''edu_student''@''localhost'' IDENTIFIED BY ''', @pwd_student, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;
SET @ddl = CONCAT('ALTER USER ''edu_student''@''localhost'' IDENTIFIED BY ''', @pwd_student, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;

SET @ddl = CONCAT('CREATE USER IF NOT EXISTS ''edu_readonly''@''localhost'' IDENTIFIED BY ''', @pwd_readonly, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;
SET @ddl = CONCAT('ALTER USER ''edu_readonly''@''localhost'' IDENTIFIED BY ''', @pwd_readonly, '''');
PREPARE st FROM @ddl; EXECUTE st; DEALLOCATE PREPARE st;

GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON edu_system.* TO 'edu_app'@'localhost';
GRANT SHOW_ROUTINE ON *.* TO 'edu_app'@'localhost';

SELECT user AS 账号, host AS 主机 FROM mysql.user
WHERE user IN ('edu_app','edu_teacher','edu_student','edu_readonly') ORDER BY user;
