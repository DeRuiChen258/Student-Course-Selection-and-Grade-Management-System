package edu.scut.db.ui.console;

import edu.scut.db.model.CourseOffering;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.CourseService;
import edu.scut.db.service.OfferingService;
import edu.scut.db.service.TeacherService;
import edu.scut.db.util.DateUtils;

import java.util.ArrayList;
import java.util.List;

public class OfferingMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final OfferingService offeringService;
    private final CourseService courseService;
    private final TeacherService teacherService;

    public OfferingMenu(InputReader input, TablePrinter printer, AccountService accountService,
                        OfferingService offeringService, CourseService courseService,
                        TeacherService teacherService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.offeringService = offeringService;
        this.courseService = courseService;
        this.teacherService = teacherService;
    }

    public MenuItem menu() {
        return MenuItem.group("开课管理（F10）")
                .add(new MenuItem("新建开课", this::create))
                .add(new MenuItem("调整容量", this::adjustCapacity))
                .add(new MenuItem("开课查询", this::search));
    }

    private void create() {
        accountService.requirePermission(AccountService.Action.OFFERING_WRITE);
        String courseCode = input.readNonEmpty("课程代码: ").toUpperCase();
        courseService.findByCode(courseCode);
        String teacherNo = input.readNonEmpty("任课教师工号: ");
        teacherService.findByNo(teacherNo);
        String semester = input.readNonEmpty("学期（如 " + DateUtils.currentSemester() + "）: ");
        Integer capacity = input.readOptionalInt("容量（1-300）: ", 1, 300);
        String classroom = input.readOptional("上课地点（可空）: ");
        offeringService.create(courseCode, teacherNo, semester, capacity, classroom);
        System.out.println("开课成功：" + courseCode + " / " + semester);
    }

    private void adjustCapacity() {
        accountService.requirePermission(AccountService.Action.OFFERING_WRITE);
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        CourseOffering offering = offeringService.findById(offeringId);
        System.out.println("当前容量 " + offering.getCapacity() + "，已选 " + offering.getEnrolledCount());
        Integer capacity = input.readOptionalInt("新容量（1-300）: ", 1, 300);
        offeringService.adjustCapacity(offeringId, capacity);
        System.out.println("容量调整成功");
    }

    private void search() {
        String semester = input.readOptional("学期（可空）: ");
        String teacherNo = input.readOptional("教师工号（可空）: ");
        String courseCode = input.readOptional("课程代码（可空）: ");
        List<String[]> rows = new ArrayList<>();
        for (CourseOffering offering : offeringService.search(semester, teacherNo, courseCode)) {
            rows.add(new String[]{String.valueOf(offering.getOfferingId()), offering.getCourseCode(),
                    offering.getCourseName(), offering.getTeacherName(), offering.getSemester(),
                    offering.getEnrolledCount() + "/" + offering.getCapacity(),
                    String.valueOf(offering.remaining()), offering.getClassroom()});
        }
        printer.print(new String[]{"开课号", "课程代码", "课程名", "教师", "学期", "已选/容量", "余量", "教室"}, rows);
    }
}
