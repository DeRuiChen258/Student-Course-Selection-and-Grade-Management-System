package edu.scut.db.tests;

import edu.scut.db.config.AppConfig;
import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.db.Tx;
import edu.scut.db.model.Student;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.GradeService;
import edu.scut.db.service.ReportService;
import edu.scut.db.service.StudentService;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.time.LocalDate;

public final class SmokeTest {

    private static final String STUDENT_NO = "202301019998";

    private SmokeTest() {
    }

    public static void run() throws Exception {
        AppConfig config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        ConnectionProvider provider = ConnectionProvider.of(config);
        Tx tx = new Tx(provider);
        StudentService studentService = new StudentService(tx);
        EnrollmentService enrollmentService = new EnrollmentService(tx);
        GradeService gradeService = new GradeService(tx);
        ReportService reportService = new ReportService(tx);

        clean(config);
        int before = offeringCount(config, 5);
        try {
            Student student = new Student();
            student.setStudentNo(STUDENT_NO);
            student.setStudentName("冒烟同学");
            student.setGender("女");
            student.setBirthDate(LocalDate.of(2005, 3, 3));
            student.setClassId(1);
            student.setEnrollDate(LocalDate.of(2023, 9, 1));
            student.setPhone("13800007777");
            student.setStatus("在读");
            studentService.create(student);

            student.setPhone("13800006666");
            studentService.update(student);
            Assert.assertEquals("13800006666", studentService.findByNo(STUDENT_NO).getPhone(), "电话应更新成功");

            enrollmentService.enroll(STUDENT_NO, 5);
            Assert.assertEquals(before + 1, offeringCount(config, 5), "选课后已选人数应加一");
            enrollmentService.drop(STUDENT_NO, 5);
            Assert.assertEquals(before, offeringCount(config, 5), "退课后已选人数应回补");
            enrollmentService.enroll(STUDENT_NO, 5);
            gradeService.saveScore(STUDENT_NO, 5, new BigDecimal("77"));
            Assert.assertEquals(1, reportService.transcript(STUDENT_NO).size(), "成绩单应有 1 条");

            studentService.delete(STUDENT_NO);
            Assert.assertEquals(0, studentCount(config, STUDENT_NO), "学生应已删除");
            Assert.assertEquals(before, offeringCount(config, 5), "删除学生后已选人数应回补");
            Assert.assertEquals(1, auditCount(config, STUDENT_NO), "删除学生应写入 1 条审计日志");
        } finally {
            clean(config);
            provider.close();
        }
    }

    private static void clean(AppConfig config) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword()); Statement statement = connection.createStatement()) {
            statement.executeUpdate("DELETE FROM enrollment WHERE student_id IN (SELECT student_id FROM student "
                    + "WHERE student_no = '" + STUDENT_NO + "')");
            statement.executeUpdate("DELETE FROM sys_account WHERE student_id IN (SELECT student_id FROM student "
                    + "WHERE student_no = '" + STUDENT_NO + "')");
            statement.executeUpdate("DELETE FROM student WHERE student_no = '" + STUDENT_NO + "'");
            statement.executeUpdate("DELETE FROM audit_log WHERE record_id = '" + STUDENT_NO + "'");
        }
    }

    private static int offeringCount(AppConfig config, int offeringId) throws Exception {
        return scalar(config, "SELECT enrolled_count FROM course_offering WHERE offering_id = " + offeringId);
    }

    private static int studentCount(AppConfig config, String studentNo) throws Exception {
        return scalar(config, "SELECT COUNT(*) FROM student WHERE student_no = '" + studentNo + "'");
    }

    private static int auditCount(AppConfig config, String studentNo) throws Exception {
        return scalar(config, "SELECT COUNT(*) FROM audit_log WHERE record_id = '" + studentNo
                + "' AND action = 'DELETE'");
    }

    private static int scalar(AppConfig config, String sql) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword()); Statement statement = connection.createStatement();
             ResultSet rs = statement.executeQuery(sql)) {
            return rs.next() ? rs.getInt(1) : -1;
        }
    }
}
