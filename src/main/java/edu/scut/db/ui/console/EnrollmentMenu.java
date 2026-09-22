package edu.scut.db.ui.console;

import edu.scut.db.model.CourseOffering;
import edu.scut.db.model.Enrollment;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.OfferingService;
import edu.scut.db.util.DateUtils;

import java.util.ArrayList;
import java.util.List;

public class EnrollmentMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final EnrollmentService enrollmentService;
    private final OfferingService offeringService;

    public EnrollmentMenu(InputReader input, TablePrinter printer, AccountService accountService,
                          EnrollmentService enrollmentService, OfferingService offeringService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.enrollmentService = enrollmentService;
        this.offeringService = offeringService;
    }

    public MenuItem menu() {
        return MenuItem.group("选课管理（F11/F12/F15）")
                .add(new MenuItem("学生选课（F11）", this::enroll))
                .add(new MenuItem("学生退课（F12）", this::drop))
                .add(new MenuItem("按学生查课表（F15）", this::myCourses))
                .add(new MenuItem("按开课查名单（F15）", this::roster));
    }

    private void enroll() {
        accountService.requirePermission(AccountService.Action.READ);
        String studentNo = input.readNonEmpty("学号: ");
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        CourseOffering offering = offeringService.findById(offeringId);
        System.out.println("目标开课：" + offering.getCourseName() + " 已选 " + offering.getEnrolledCount()
                + "/" + offering.getCapacity());
        System.out.println(enrollmentService.enroll(studentNo, offeringId));
    }

    private void drop() {
        accountService.requirePermission(AccountService.Action.READ);
        String studentNo = input.readNonEmpty("学号: ");
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        System.out.println(enrollmentService.drop(studentNo, offeringId));
    }

    private void myCourses() {
        String studentNo = input.readNonEmpty("学号: ");
        List<String[]> rows = new ArrayList<>();
        for (Enrollment enrollment : enrollmentService.myCourses(studentNo)) {
            rows.add(new String[]{enrollment.getSemester(), enrollment.getCourseCode(), enrollment.getCourseName(),
                    enrollment.getTeacherName(), enrollment.getScore() == null ? "未出分"
                            : enrollment.getScore().toString(), enrollment.getStatus()});
        }
        printer.print(new String[]{"学期", "课程代码", "课程名", "教师", "成绩", "状态"}, rows);
    }

    private void roster() {
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        List<String[]> rows = new ArrayList<>();
        for (Enrollment enrollment : enrollmentService.roster(offeringId)) {
            rows.add(new String[]{enrollment.getStudentNo(), enrollment.getStudentName(),
                    enrollment.getScore() == null ? "未出分" : enrollment.getScore().toString(),
                    DateUtils.formatDateTime(enrollment.getScoreTime()), enrollment.getStatus()});
        }
        printer.print(new String[]{"学号", "姓名", "成绩", "成绩时间", "状态"}, rows);
    }
}
