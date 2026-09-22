USE edu_system;

DROP PROCEDURE IF EXISTS p_enroll_student;
DROP PROCEDURE IF EXISTS p_drop_course;
DROP PROCEDURE IF EXISTS p_save_score;
DROP FUNCTION IF EXISTS f_gpa;
DROP FUNCTION IF EXISTS f_offering_avg;

DELIMITER $$

-- 选课：行锁后校验并写入，计数由触发器联动
CREATE PROCEDURE p_enroll_student(
    IN  p_student_no VARCHAR(12),
    IN  p_offering_id INT,
    OUT p_code INT,
    OUT p_msg VARCHAR(100)
)
BEGIN
    DECLARE v_student_id INT DEFAULT NULL;
    DECLARE v_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_capacity SMALLINT DEFAULT NULL;
    DECLARE v_enrolled SMALLINT DEFAULT 0;
    DECLARE v_dup INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_code = 40099, p_msg = '数据库异常，已回滚';
    END;

    SET p_code = 0, p_msg = 'OK';
    START TRANSACTION;

    SELECT student_id, status INTO v_student_id, v_status
    FROM student WHERE student_no = p_student_no;
    IF v_student_id IS NULL THEN
        SET p_code = 40001, p_msg = '学生不存在';
    ELSEIF v_status <> '在读' THEN
        SET p_code = 40002, p_msg = '学籍状态不允许选课';
    ELSE
        SELECT capacity, enrolled_count INTO v_capacity, v_enrolled
        FROM course_offering WHERE offering_id = p_offering_id FOR UPDATE;
        IF v_capacity IS NULL THEN
            SET p_code = 40003, p_msg = '开课不存在';
        ELSE
            SELECT COUNT(*) INTO v_dup FROM enrollment
            WHERE student_id = v_student_id AND offering_id = p_offering_id AND status = '已选';
            IF v_dup > 0 THEN
                SET p_code = 40004, p_msg = '重复选课';
            ELSEIF v_enrolled >= v_capacity THEN
                SET p_code = 40005, p_msg = '名额已满';
            ELSE
                INSERT INTO enrollment (student_id, offering_id) VALUES (v_student_id, p_offering_id);
            END IF;
        END IF;
    END IF;

    IF p_code = 0 THEN
        COMMIT;
    ELSE
        ROLLBACK;
    END IF;
END$$

-- 退课：已出分不允许退，状态置已退并回补计数
CREATE PROCEDURE p_drop_course(
    IN  p_student_no VARCHAR(12),
    IN  p_offering_id INT,
    OUT p_code INT,
    OUT p_msg VARCHAR(100)
)
BEGIN
    DECLARE v_student_id INT DEFAULT NULL;
    DECLARE v_enroll_id INT DEFAULT NULL;
    DECLARE v_score DECIMAL(5,2) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_code = 40099, p_msg = '数据库异常，已回滚';
    END;

    SET p_code = 0, p_msg = 'OK';
    START TRANSACTION;

    SELECT student_id INTO v_student_id FROM student WHERE student_no = p_student_no;
    IF v_student_id IS NULL THEN
        SET p_code = 40001, p_msg = '学生不存在';
    ELSE
        SELECT enrollment_id, score INTO v_enroll_id, v_score
        FROM enrollment
        WHERE student_id = v_student_id AND offering_id = p_offering_id AND status = '已选'
        FOR UPDATE;
        IF v_enroll_id IS NULL THEN
            SET p_code = 40006, p_msg = '未选该课';
        ELSEIF v_score IS NOT NULL THEN
            SET p_code = 40007, p_msg = '已有成绩，不能退课';
        ELSE
            UPDATE enrollment SET status = '已退' WHERE enrollment_id = v_enroll_id;
        END IF;
    END IF;

    IF p_code = 0 THEN
        COMMIT;
    ELSE
        ROLLBACK;
    END IF;
END$$

-- 成绩录入：区间校验后写分数与时间戳
CREATE PROCEDURE p_save_score(
    IN  p_student_no VARCHAR(12),
    IN  p_offering_id INT,
    IN  p_score DECIMAL(5,2),
    OUT p_code INT,
    OUT p_msg VARCHAR(100)
)
BEGIN
    DECLARE v_student_id INT DEFAULT NULL;
    DECLARE v_enroll_id INT DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_code = 40099, p_msg = '数据库异常，已回滚';
    END;

    SET p_code = 0, p_msg = 'OK';
    IF p_score IS NULL OR p_score < 0 OR p_score > 100 THEN
        SET p_code = 40008, p_msg = '成绩必须在 0 到 100 之间';
    ELSE
        START TRANSACTION;
        SELECT student_id INTO v_student_id FROM student WHERE student_no = p_student_no;
        IF v_student_id IS NULL THEN
            SET p_code = 40001, p_msg = '学生不存在';
        ELSE
            SELECT enrollment_id INTO v_enroll_id FROM enrollment
            WHERE student_id = v_student_id AND offering_id = p_offering_id AND status = '已选'
            FOR UPDATE;
            IF v_enroll_id IS NULL THEN
                SET p_code = 40006, p_msg = '未选该课';
            ELSE
                UPDATE enrollment SET score = p_score WHERE enrollment_id = v_enroll_id;
            END IF;
        END IF;
        IF p_code = 0 THEN
            COMMIT;
        ELSE
            ROLLBACK;
        END IF;
    END IF;
END$$

-- 绩点：∑(绩点×学分)/∑学分，无成绩返回 NULL
CREATE FUNCTION f_gpa(p_student_id INT)
RETURNS DECIMAL(3,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_gpa DECIMAL(3,2) DEFAULT NULL;
    SELECT ROUND(SUM(CASE WHEN e.score >= 90 THEN 4.0 WHEN e.score >= 80 THEN 3.0
                          WHEN e.score >= 70 THEN 2.0 WHEN e.score >= 60 THEN 1.0
                          ELSE 0.0 END * c.credit) / SUM(c.credit), 2)
    INTO v_gpa
    FROM enrollment e
    JOIN course_offering o ON o.offering_id = e.offering_id
    JOIN course c ON c.course_id = o.course_id
    WHERE e.student_id = p_student_id AND e.status = '已选' AND e.score IS NOT NULL;
    RETURN v_gpa;
END$$

-- 开课均分：只统计已出分记录
CREATE FUNCTION f_offering_avg(p_offering_id INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(5,2) DEFAULT NULL;
    SELECT ROUND(AVG(score), 2) INTO v_avg
    FROM enrollment
    WHERE offering_id = p_offering_id AND status = '已选' AND score IS NOT NULL;
    RETURN v_avg;
END$$

DELIMITER ;

SELECT routine_name AS 例程, routine_type AS 类型
FROM information_schema.routines
WHERE routine_schema = 'edu_system' ORDER BY routine_type, routine_name;
