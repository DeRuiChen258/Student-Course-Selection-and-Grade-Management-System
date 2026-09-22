USE edu_system;

DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS sys_account;
DROP TABLE IF EXISTS course_offering;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS class_group;
DROP TABLE IF EXISTS teacher;
DROP TABLE IF EXISTS department;

CREATE TABLE department (
    dept_id    INT AUTO_INCREMENT PRIMARY KEY,
    dept_code  VARCHAR(10) NOT NULL COMMENT '院系代码，如 CS',
    dept_name  VARCHAR(50) NOT NULL COMMENT '院系名称',
    office     VARCHAR(50) NULL COMMENT '办公地点',
    phone      VARCHAR(20) NULL COMMENT '联系电话',
    UNIQUE KEY uk_dept_code (dept_code),
    UNIQUE KEY uk_dept_name (dept_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='院系';

CREATE TABLE teacher (
    teacher_id   INT AUTO_INCREMENT PRIMARY KEY,
    teacher_no   VARCHAR(8) NOT NULL COMMENT '工号，8 位数字',
    teacher_name VARCHAR(30) NOT NULL COMMENT '姓名',
    gender       ENUM('男','女') NOT NULL COMMENT '性别',
    title        ENUM('助教','讲师','副教授','教授') NOT NULL DEFAULT '讲师' COMMENT '职称',
    dept_id      INT NOT NULL COMMENT '所属院系',
    hire_date    DATE NOT NULL COMMENT '入职日期',
    phone        VARCHAR(20) NULL COMMENT '联系电话',
    email        VARCHAR(60) NULL COMMENT '邮箱',
    UNIQUE KEY uk_teacher_no (teacher_no),
    CONSTRAINT fk_teacher_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师';

CREATE TABLE class_group (
    class_id           INT AUTO_INCREMENT PRIMARY KEY,
    class_code         VARCHAR(20) NOT NULL COMMENT '班级代码',
    class_name         VARCHAR(50) NOT NULL COMMENT '班级名称',
    dept_id            INT NOT NULL COMMENT '所属院系',
    grade_year         SMALLINT NOT NULL COMMENT '年级',
    advisor_teacher_id INT NULL COMMENT '班主任',
    UNIQUE KEY uk_class_code (class_code),
    CONSTRAINT fk_class_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_class_advisor FOREIGN KEY (advisor_teacher_id) REFERENCES teacher (teacher_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT ck_class_year CHECK (grade_year BETWEEN 2000 AND 2100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级';

CREATE TABLE student (
    student_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_no   CHAR(12) NOT NULL COMMENT '学号，12 位数字',
    student_name VARCHAR(30) NOT NULL COMMENT '姓名',
    gender       ENUM('男','女') NOT NULL COMMENT '性别',
    birth_date   DATE NULL COMMENT '出生日期',
    class_id     INT NOT NULL COMMENT '所属班级',
    enroll_date  DATE NOT NULL COMMENT '入学日期',
    phone        VARCHAR(20) NULL COMMENT '联系电话',
    email        VARCHAR(60) NULL COMMENT '邮箱',
    status       ENUM('在读','休学','退学','毕业') NOT NULL DEFAULT '在读' COMMENT '学籍状态',
    UNIQUE KEY uk_student_no (student_no),
    CONSTRAINT fk_student_class FOREIGN KEY (class_id) REFERENCES class_group (class_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生';

CREATE TABLE course (
    course_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(16) NOT NULL COMMENT '课程代码，大写字母与数字',
    course_name VARCHAR(60) NOT NULL COMMENT '课程名称',
    credit      DECIMAL(3,1) NOT NULL COMMENT '学分',
    hours       SMALLINT NOT NULL COMMENT '学时',
    course_type ENUM('必修','选修','通识') NOT NULL DEFAULT '选修' COMMENT '课程类型',
    dept_id     INT NOT NULL COMMENT '开课院系',
    UNIQUE KEY uk_course_code (course_code),
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_course_credit CHECK (credit BETWEEN 0.5 AND 10.0),
    CONSTRAINT ck_course_hours CHECK (hours BETWEEN 8 AND 200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程';

CREATE TABLE course_offering (
    offering_id    INT AUTO_INCREMENT PRIMARY KEY,
    course_id      INT NOT NULL COMMENT '课程',
    teacher_id     INT NOT NULL COMMENT '任课教师',
    semester       CHAR(11) NOT NULL COMMENT '学期，如 2026-2027-1',
    capacity       SMALLINT NOT NULL COMMENT '容量',
    enrolled_count SMALLINT NOT NULL DEFAULT 0 COMMENT '已选人数',
    classroom      VARCHAR(30) NULL COMMENT '上课地点',
    open_time      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开课时间',
    UNIQUE KEY uk_offering (course_id, teacher_id, semester),
    CONSTRAINT fk_offering_course FOREIGN KEY (course_id) REFERENCES course (course_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_offering_teacher FOREIGN KEY (teacher_id) REFERENCES teacher (teacher_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_offering_capacity CHECK (capacity BETWEEN 1 AND 300),
    CONSTRAINT ck_offering_enrolled CHECK (enrolled_count >= 0 AND enrolled_count <= capacity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开课';

CREATE TABLE enrollment (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT NOT NULL COMMENT '学生',
    offering_id   INT NOT NULL COMMENT '开课',
    enroll_time   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
    score         DECIMAL(5,2) NULL COMMENT '成绩，空表示未出分',
    score_time    DATETIME NULL COMMENT '成绩录入或修改时间',
    status        ENUM('已选','已退') NOT NULL DEFAULT '已选' COMMENT '选课状态',
    UNIQUE KEY uk_enroll (student_id, offering_id),
    CONSTRAINT fk_enroll_student FOREIGN KEY (student_id) REFERENCES student (student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_enroll_offering FOREIGN KEY (offering_id) REFERENCES course_offering (offering_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_enroll_score CHECK (score IS NULL OR (score >= 0 AND score <= 100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='选课与成绩';

CREATE TABLE sys_account (
    account_id    INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(30) NOT NULL COMMENT '登录名',
    password_hash VARCHAR(120) NOT NULL COMMENT '口令散列，格式 salt$hash',
    role          ENUM('ADMIN','TEACHER','STUDENT') NOT NULL COMMENT '角色',
    student_id    INT NULL COMMENT '绑定学生',
    teacher_id    INT NULL COMMENT '绑定教师',
    last_login    DATETIME NULL COMMENT '最后登录时间',
    bind_ok       TINYINT GENERATED ALWAYS AS (
        (role = 'STUDENT' AND student_id IS NOT NULL AND teacher_id IS NULL)
        OR (role = 'TEACHER' AND teacher_id IS NOT NULL AND student_id IS NULL)
        OR (role = 'ADMIN' AND student_id IS NULL AND teacher_id IS NULL)
    ) VIRTUAL COMMENT '绑定一致性派生列',
    UNIQUE KEY uk_account_username (username),
    CONSTRAINT fk_account_student FOREIGN KEY (student_id) REFERENCES student (student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_account_teacher FOREIGN KEY (teacher_id) REFERENCES teacher (teacher_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_account_binding CHECK (bind_ok = 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账号与角色';

CREATE TABLE audit_log (
    log_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name  VARCHAR(32) NOT NULL COMMENT '被操作的表名',
    action      ENUM('INSERT','UPDATE','DELETE') NOT NULL COMMENT '操作类型',
    record_id   VARCHAR(32) NOT NULL COMMENT '被操作记录的主键或业务键',
    operator    VARCHAR(30) NOT NULL DEFAULT 'system' COMMENT '操作者',
    action_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    detail      VARCHAR(255) NULL COMMENT '变更明细'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志';
