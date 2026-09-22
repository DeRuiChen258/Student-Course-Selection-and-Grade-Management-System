package edu.scut.db.tests;

import edu.scut.db.config.AppConfig;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public final class DaoCrudTest {

    private DaoCrudTest() {
    }

    public static void run() throws Exception {
        AppConfig config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword())) {
            connection.setAutoCommit(false);
            int studentsBefore = count(connection, "SELECT COUNT(*) FROM student");
            int enrollmentsBefore = count(connection, "SELECT COUNT(*) FROM enrollment");

            execute(connection, "INSERT INTO department (dept_code, dept_name, office, phone) "
                    + "VALUES ('ZZ', '单元测试院系', 'T1', '000')");
            int deptId = queryInt(connection, "SELECT dept_id FROM department WHERE dept_code = 'ZZ'");
            Assert.assertTrue(deptId > 0, "院系插入应返回自增主键");
            execute(connection, "UPDATE department SET office = 'T2' WHERE dept_id = " + deptId);
            Assert.assertEquals("T2", queryString(connection, "SELECT office FROM department WHERE dept_id = " + deptId));

            execute(connection, "INSERT INTO teacher (teacher_no, teacher_name, gender, title, dept_id, hire_date) "
                    + "VALUES ('99999001', '测试教师', '男', '讲师', " + deptId + ", '2020-01-01')");
            int teacherId = queryInt(connection, "SELECT teacher_id FROM teacher WHERE teacher_no = '99999001'");
            Assert.assertTrue(teacherId > 0, "教师插入应成功");

            execute(connection, "INSERT INTO class_group (class_code, class_name, dept_id, grade_year, "
                    + "advisor_teacher_id) VALUES ('ZZ0001', '测试班级', " + deptId + ", 2023, " + teacherId + ")");
            int classId = queryInt(connection, "SELECT class_id FROM class_group WHERE class_code = 'ZZ0001'");
            Assert.assertTrue(classId > 0, "班级插入应成功");

            execute(connection, "INSERT INTO student (student_no, student_name, gender, birth_date, class_id, "
                    + "enroll_date, status) VALUES ('202399900009', '测试学生', '女', '2005-01-01', " + classId
                    + ", '2023-09-01', '在读')");
            int studentId = queryInt(connection, "SELECT student_id FROM student WHERE student_no = '202399900009'");
            Assert.assertTrue(studentId > 0, "学生插入应成功");

            execute(connection, "INSERT INTO course (course_code, course_name, credit, hours, course_type, dept_id) "
                    + "VALUES ('ZZTEST09', '测试课程', 2.0, 32, '选修', " + deptId + ")");
            int courseId = queryInt(connection, "SELECT course_id FROM course WHERE course_code = 'ZZTEST09'");
            Assert.assertTrue(courseId > 0, "课程插入应成功");

            execute(connection, "INSERT INTO course_offering (course_id, teacher_id, semester, capacity, "
                    + "classroom) VALUES (" + courseId + ", " + teacherId + ", '2099-2100-1', 5, 'T101')");
            int offeringId = queryInt(connection, "SELECT offering_id FROM course_offering WHERE course_id = "
                    + courseId + " AND teacher_id = " + teacherId);
            Assert.assertTrue(offeringId > 0, "开课插入应成功");

            execute(connection, "INSERT INTO enrollment (student_id, offering_id) VALUES (" + studentId + ", "
                    + offeringId + ")");
            Assert.assertEquals(1, queryInt(connection, "SELECT enrolled_count FROM course_offering "
                    + "WHERE offering_id = " + offeringId), "选课触发器应把已选人数加一");
            execute(connection, "UPDATE enrollment SET status = '已退' WHERE student_id = " + studentId
                    + " AND offering_id = " + offeringId);
            Assert.assertEquals(0, queryInt(connection, "SELECT enrolled_count FROM course_offering "
                    + "WHERE offering_id = " + offeringId), "退课触发器应把已选人数减一");

            execute(connection, "INSERT INTO sys_account (username, password_hash, role) "
                    + "VALUES ('zz_test_admin', 'salt$hash', 'ADMIN')");
            Assert.assertEquals(1, queryInt(connection, "SELECT COUNT(*) FROM sys_account "
                    + "WHERE username = 'zz_test_admin'"), "账号插入应成功");

            execute(connection, "INSERT INTO audit_log (table_name, action, record_id, operator, detail) "
                    + "VALUES ('student', 'UPDATE', '202399900009', 'tester', '单元测试')");
            Assert.assertEquals(1, queryInt(connection, "SELECT COUNT(*) FROM audit_log "
                    + "WHERE record_id = '202399900009' AND operator = 'tester'"), "审计日志插入应成功");

            execute(connection, "DELETE FROM student WHERE student_no = '202399900009'");
            Assert.assertEquals(0, queryInt(connection, "SELECT COUNT(*) FROM enrollment WHERE student_id = "
                    + studentId), "删除学生应级联删除选课记录");
            execute(connection, "DELETE FROM course_offering WHERE offering_id = " + offeringId);
            execute(connection, "DELETE FROM course WHERE course_code = 'ZZTEST09'");
            execute(connection, "DELETE FROM class_group WHERE class_code = 'ZZ0001'");
            execute(connection, "DELETE FROM teacher WHERE teacher_no = '99999001'");
            execute(connection, "DELETE FROM department WHERE dept_code = 'ZZ'");

            connection.rollback();

            Assert.assertEquals(studentsBefore, count(connection, "SELECT COUNT(*) FROM student"),
                    "回滚后学生行数应回到测试前");
            Assert.assertEquals(enrollmentsBefore, count(connection, "SELECT COUNT(*) FROM enrollment"),
                    "回滚后选课行数应回到测试前");
            Assert.assertEquals(0, queryInt(connection, "SELECT COUNT(*) FROM department WHERE dept_code = 'ZZ'"),
                    "回滚后测试院系不应存在");
        }
    }

    private static void execute(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate(sql);
        }
    }

    private static int count(Connection connection, String sql) throws Exception {
        return queryInt(connection, sql);
    }

    private static int queryInt(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement(); ResultSet rs = statement.executeQuery(sql)) {
            return rs.next() ? rs.getInt(1) : -1;
        }
    }

    private static String queryString(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement(); ResultSet rs = statement.executeQuery(sql)) {
            return rs.next() ? rs.getString(1) : null;
        }
    }
}
