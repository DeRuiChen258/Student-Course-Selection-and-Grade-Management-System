package edu.scut.db.ui.console;

import edu.scut.db.config.AppConfig;
import edu.scut.db.db.SqlScriptRunner;
import edu.scut.db.exception.BizException;
import edu.scut.db.model.Student;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.CourseService;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.GradeService;
import edu.scut.db.service.OfferingService;
import edu.scut.db.service.ReportService;
import edu.scut.db.service.StudentService;
import edu.scut.db.service.TeacherService;
import edu.scut.db.util.Logger;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public class ConsoleUI {

    private final InputReader input = new InputReader();
    private final TablePrinter printer = new TablePrinter();
    private final MenuItem root = MenuItem.group("主菜单");

    private final AccountService accountService;
    private final StudentService studentService;
    private final TeacherService teacherService;
    private final CourseService courseService;
    private final OfferingService offeringService;
    private final EnrollmentService enrollmentService;
    private final GradeService gradeService;
    private final ReportService reportService;

    public ConsoleUI(AppConfig config, AccountService accountService, StudentService studentService,
                     TeacherService teacherService, CourseService courseService, OfferingService offeringService,
                     EnrollmentService enrollmentService, GradeService gradeService, ReportService reportService,
                     SqlScriptRunner scriptRunner) {
        this.accountService = accountService;
        this.studentService = studentService;
        this.teacherService = teacherService;
        this.courseService = courseService;
        this.offeringService = offeringService;
        this.enrollmentService = enrollmentService;
        this.gradeService = gradeService;
        this.reportService = reportService;

        root.add(new StudentMenu(input, printer, accountService, studentService, config).menu());
        root.add(new TeacherMenu(input, printer, accountService, teacherService).menu());
        root.add(new CourseMenu(input, printer, accountService, courseService).menu());
        root.add(new OfferingMenu(input, printer, accountService, offeringService, courseService,
                teacherService).menu());
        root.add(new EnrollmentMenu(input, printer, accountService, enrollmentService, offeringService).menu());
        root.add(new GradeMenu(input, printer, accountService, gradeService, enrollmentService).menu());
        root.add(new ReportMenu(input, printer, reportService).menu());
        root.add(new AccountMenu(input, printer, accountService).menu());
        root.add(new DbMaintenanceMenu(input, printer, accountService, scriptRunner).menu());
        root.add(new MenuItem("退出系统", () -> System.out.println("再见")));
    }

    public void run() {
        System.out.println("学生选课与成绩管理系统（控制台版）");
        while (true) {
            MenuItem selected = showMenu(root, null);
            if (selected == null) {
                return;
            }
        }
    }

    private MenuItem showMenu(MenuItem menu, MenuItem parent) {
        while (true) {
            System.out.println();
            System.out.println("===== " + menu.getTitle() + " =====");
            List<MenuItem> items = menu.getChildren();
            for (int i = 0; i < items.size(); i++) {
                System.out.printf("%2d. %s%n", i + 1, items.get(i).getTitle());
            }
            if (parent != null) {
                System.out.println(" 0. 返回上级");
            } else {
                System.out.println(" 0. 退出");
            }
            int choice = input.readInt("请输入编号: ", 0, items.size());
            if (choice == 0) {
                return null;
            }
            MenuItem selected = items.get(choice - 1);
            try {
                if (selected.isGroup()) {
                    showMenu(selected, menu);
                } else if (selected.getAction() != null) {
                    selected.getAction().execute();
                }
            } catch (BizException e) {
                System.out.println(e.getMessage());
                Logger.warn("业务异常：" + e.getMessage());
            } catch (RuntimeException e) {
                System.out.println("[E009] 操作失败：" + e.getMessage());
                Logger.error("运行异常：" + e.getMessage());
            }
            if (selected.getTitle().startsWith("退出")) {
                return null;
            }
        }
    }

    public void runDemo() {
        System.out.println("== 演示模式：按固定顺序执行 F01/F02/F11/F12/F13/F16/F03 ==");
        String studentNo = "202301019999";

        Student student = new Student();
        student.setStudentNo(studentNo);
        student.setStudentName("演示同学");
        student.setGender("男");
        student.setBirthDate(LocalDate.of(2005, 5, 5));
        student.setClassId(1);
        student.setEnrollDate(LocalDate.of(2023, 9, 1));
        student.setPhone("13800009999");
        student.setEmail("s202301019999@scut.edu.cn");
        student.setStatus("在读");
        studentService.create(student);
        System.out.println("[F01] 新增学生 " + studentNo + " 成功");

        student.setPhone("13800008888");
        studentService.update(student);
        System.out.println("[F02] 修改联系电话 13800009999 -> 13800008888 成功");

        System.out.println("[F11] " + enrollmentService.enroll(studentNo, 5));
        System.out.println("[F12] " + enrollmentService.drop(studentNo, 5));
        System.out.println("[F11] " + enrollmentService.enroll(studentNo, 5));
        System.out.println("[F13] " + gradeService.saveScore(studentNo, 5, new BigDecimal("88.5")));

        System.out.println("[F15] 成绩单行数 = " + reportService.transcript(studentNo).size());
        System.out.println("[F13] 成绩等级 = " + gradeService.gradeOf(new BigDecimal("88.5")));

        try {
            gradeService.saveScore(studentNo, 5, new BigDecimal("101"));
        } catch (BizException e) {
            System.out.println("[边界] 越界成绩被拒绝 -> " + e.getMessage());
        }
        try {
            enrollmentService.enroll(studentNo, 5);
        } catch (BizException e) {
            System.out.println("[边界] 重复选课被拒绝 -> " + e.getMessage());
        }

        int enrollments = studentService.delete(studentNo);
        System.out.println("[F03] 删除学生 " + studentNo + " 成功，清理选课 " + enrollments + " 条");
        System.out.println("== 演示结束 ==");
    }
}
