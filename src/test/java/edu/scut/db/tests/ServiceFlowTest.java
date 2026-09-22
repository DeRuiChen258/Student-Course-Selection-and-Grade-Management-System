package edu.scut.db.tests;

import edu.scut.db.config.AppConfig;
import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.Course;
import edu.scut.db.model.CourseOffering;
import edu.scut.db.model.Student;
import edu.scut.db.model.Teacher;
import edu.scut.db.service.CourseService;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.GradeService;
import edu.scut.db.service.OfferingService;
import edu.scut.db.service.ReportService;
import edu.scut.db.service.StudentService;
import edu.scut.db.service.TeacherService;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.time.LocalDate;

public final class ServiceFlowTest {

    private static final String COURSE_CODE = "ZZFLOW01";
    private static final String TEACHER_NO = "99999002";
    private static final String SEMESTER = "2099-2100-2";

    private ServiceFlowTest() {
    }

    public static void run() throws Exception {
        AppConfig config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        ConnectionProvider provider = ConnectionProvider.of(config);
        Tx tx = new Tx(provider);
        StudentService studentService = new StudentService(tx);
        TeacherService teacherService = new TeacherService(tx);
        CourseService courseService = new CourseService(tx);
        OfferingService offeringService = new OfferingService(tx);
        EnrollmentService enrollmentService = new EnrollmentService(tx);
        GradeService gradeService = new GradeService(tx);
        ReportService reportService = new ReportService(tx);

        cleanup(config);
        try {
            Teacher teacher = new Teacher();
            teacher.setTeacherNo(TEACHER_NO);
            teacher.setTeacherName("流程测试教师");
            teacher.setGender("男");
            teacher.setTitle("讲师");
            teacher.setDeptId(1);
            teacher.setHireDate(LocalDate.of(2020, 1, 1));
            teacherService.create(teacher);

            Course course = new Course();
            course.setCourseCode(COURSE_CODE);
            course.setCourseName("流程测试课程");
            course.setCredit(new BigDecimal("2.0"));
            course.setHours(32);
            course.setCourseType("选修");
            course.setDeptId(1);
            courseService.create(course);

            offeringService.create(COURSE_CODE, TEACHER_NO, SEMESTER, 3, "测试教室");
            CourseOffering offering = offeringService.search(SEMESTER, TEACHER_NO, COURSE_CODE).get(0);
            Assert.assertNotNull(offering, "新建的开课应能查询到");

            String[] studentNos = {"202399900001", "202399900002", "202399900003", "202399900004"};
            for (String studentNo : studentNos) {
                Student student = new Student();
                student.setStudentNo(studentNo);
                student.setStudentName("流程学生" + studentNo.substring(10));
                student.setGender("男");
                student.setBirthDate(LocalDate.of(2005, 1, 1));
                student.setClassId(1);
                student.setEnrollDate(LocalDate.of(2023, 9, 1));
                student.setStatus("在读");
                studentService.create(student);
            }

            enrollmentService.enroll(studentNos[0], offering.getOfferingId());
            Assert.assertThrows(ErrorCode.E004, () -> enrollmentService.enroll(studentNos[0],
                    offering.getOfferingId()));
            enrollmentService.enroll(studentNos[1], offering.getOfferingId());
            enrollmentService.enroll(studentNos[2], offering.getOfferingId());
            Assert.assertThrows(ErrorCode.E005, () -> enrollmentService.enroll(studentNos[3],
                    offering.getOfferingId()));

            gradeService.saveScore(studentNos[0], offering.getOfferingId(), new BigDecimal("88.5"));
            Assert.assertThrows(ErrorCode.E006, () -> enrollmentService.drop(studentNos[0],
                    offering.getOfferingId()));
            enrollmentService.drop(studentNos[1], offering.getOfferingId());
            Assert.assertEquals(2, offeringService.findById(offering.getOfferingId()).getEnrolledCount(),
                    "退课后已选人数应为 2");

            Assert.assertEquals(1, reportService.transcript(studentNos[0]).size(), "成绩单应有 1 条记录");
            Assert.assertTrue(!reportService.gpaRanking(5).isEmpty(), "GPA 排名应有结果");
            Assert.assertTrue(!reportService.courseStats(5).isEmpty(), "课程统计应有结果");
            Assert.assertTrue(!reportService.semesterSummary().isEmpty(), "学期汇总应有结果");

            Assert.assertThrows(ErrorCode.E001, () -> courseService.delete(COURSE_CODE));
            Assert.assertThrows(ErrorCode.E007,
                    () -> gradeService.saveScore(studentNos[1], offering.getOfferingId(), new BigDecimal("120")));
        } finally {
            cleanup(config);
            provider.close();
        }
    }

    private static void cleanup(AppConfig config) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword()); Statement statement = connection.createStatement()) {
            statement.executeUpdate("DELETE FROM enrollment WHERE student_id IN "
                    + "(SELECT student_id FROM student WHERE student_no LIKE '2023999000%')");
            statement.executeUpdate("DELETE FROM sys_account WHERE student_id IN "
                    + "(SELECT student_id FROM student WHERE student_no LIKE '2023999000%')");
            statement.executeUpdate("DELETE FROM student WHERE student_no LIKE '2023999000%'");
            statement.executeUpdate("DELETE FROM course_offering WHERE course_id IN "
                    + "(SELECT course_id FROM course WHERE course_code = '" + COURSE_CODE + "')");
            statement.executeUpdate("DELETE FROM course WHERE course_code = '" + COURSE_CODE + "'");
            statement.executeUpdate("DELETE FROM class_group WHERE advisor_teacher_id IN "
                    + "(SELECT teacher_id FROM teacher WHERE teacher_no = '" + TEACHER_NO + "')");
            statement.executeUpdate("DELETE FROM teacher WHERE teacher_no = '" + TEACHER_NO + "'");
        }
    }
}
