USE edu_system;

-- 考点：查看当前会话隔离级别
SELECT @@transaction_isolation AS 当前隔离级别;

-- 考点：会话级切换隔离级别，切换后立刻查看
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT @@transaction_isolation AS 切换后隔离级别;
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- 考点：显式事务提交，修改前后对比
START TRANSACTION;
SELECT student_name, phone FROM student WHERE student_no = '202301010004';
UPDATE student SET phone = '13800009999' WHERE student_no = '202301010004';
SELECT student_name, phone FROM student WHERE student_no = '202301010004';
ROLLBACK;
SELECT student_name, phone AS 回滚后电话 FROM student WHERE student_no = '202301010004';

-- 考点：行锁，锁定开课行后再取容量
START TRANSACTION;
SELECT offering_id, capacity, enrolled_count FROM course_offering WHERE offering_id = 1 FOR UPDATE;
ROLLBACK;

-- 考点：只读事务快照
START TRANSACTION READ ONLY;
SELECT COUNT(*) AS 事务内学生数 FROM student;
COMMIT;

-- 以下为两会话锁等待演示，需两个客户端按顺序执行：
-- 会话 A：START TRANSACTION; SELECT capacity, enrolled_count FROM course_offering WHERE offering_id = 1 FOR UPDATE;
-- 会话 B：START TRANSACTION; SELECT capacity, enrolled_count FROM course_offering WHERE offering_id = 1 FOR UPDATE;
--         会话 B 阻塞，等待 innodb_lock_wait_timeout（默认 50 秒）或会话 A 提交
-- 会话 A：UPDATE course_offering SET capacity = capacity WHERE offering_id = 1; COMMIT;
-- 会话 B：解除阻塞后拿到最新数据，随后 ROLLBACK;
-- 考点：查看锁等待超时设置与正在等待的事务
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';
SELECT trx_id, trx_state, trx_started, trx_rows_locked FROM information_schema.innodb_trx;
