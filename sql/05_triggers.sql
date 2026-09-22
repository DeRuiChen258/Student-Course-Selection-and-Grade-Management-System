USE edu_system;

DROP TRIGGER IF EXISTS trg_enrollment_bi;
DROP TRIGGER IF EXISTS trg_enrollment_ai;
DROP TRIGGER IF EXISTS trg_enrollment_au;
DROP TRIGGER IF EXISTS trg_enrollment_bu;
DROP TRIGGER IF EXISTS trg_student_ad;

DELIMITER $$

-- 选课前置校验：开课存在、未满、未重复
CREATE TRIGGER trg_enrollment_bi BEFORE INSERT ON enrollment
FOR EACH ROW
BEGIN
    DECLARE v_capacity SMALLINT DEFAULT NULL;
    DECLARE v_enrolled SMALLINT DEFAULT 0;
    DECLARE v_dup INT DEFAULT 0;

    SELECT capacity, enrolled_count INTO v_capacity, v_enrolled
    FROM course_offering WHERE offering_id = NEW.offering_id;
    IF v_capacity IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E003 开课不存在';
    END IF;
    IF v_enrolled >= v_capacity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E005 名额已满';
    END IF;
    SELECT COUNT(*) INTO v_dup FROM enrollment
    WHERE student_id = NEW.student_id AND offering_id = NEW.offering_id;
    IF v_dup > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E004 重复选课';
    END IF;
END$$

-- 选课成功后已选人数 +1
CREATE TRIGGER trg_enrollment_ai AFTER INSERT ON enrollment
FOR EACH ROW
BEGIN
    IF NEW.status = '已选' THEN
        UPDATE course_offering SET enrolled_count = enrolled_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END$$

-- 退课时回补已选人数
CREATE TRIGGER trg_enrollment_au AFTER UPDATE ON enrollment
FOR EACH ROW
BEGIN
    IF OLD.status = '已选' AND NEW.status = '已退' THEN
        UPDATE course_offering SET enrolled_count = enrolled_count - 1
        WHERE offering_id = NEW.offering_id;
    ELSEIF OLD.status = '已退' AND NEW.status = '已选' THEN
        UPDATE course_offering SET enrolled_count = enrolled_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END$$

-- 成绩区间校验，并在改分时刷新时间戳
CREATE TRIGGER trg_enrollment_bu BEFORE UPDATE ON enrollment
FOR EACH ROW
BEGIN
    IF NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > 100) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'E007 成绩越界';
    END IF;
    IF NEW.score IS NOT NULL AND (OLD.score IS NULL OR OLD.score <> NEW.score) THEN
        SET NEW.score_time = NOW();
    END IF;
END$$

-- 删除学生时写审计日志
CREATE TRIGGER trg_student_ad AFTER DELETE ON student
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, action, record_id, operator, detail)
    VALUES ('student', 'DELETE', OLD.student_no, SUBSTRING_INDEX(CURRENT_USER(), '@', 1),
            CONCAT('删除学生 ', OLD.student_name));
END$$

DELIMITER ;

SELECT trigger_name AS 触发器, event_object_table AS 表, action_timing AS 时机, event_manipulation AS 事件
FROM information_schema.triggers
WHERE trigger_schema = 'edu_system' ORDER BY trigger_name;
