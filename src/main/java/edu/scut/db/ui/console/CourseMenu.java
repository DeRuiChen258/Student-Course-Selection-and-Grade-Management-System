package edu.scut.db.ui.console;

import edu.scut.db.model.Course;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.CourseService;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class CourseMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final CourseService courseService;

    public CourseMenu(InputReader input, TablePrinter printer, AccountService accountService,
                      CourseService courseService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.courseService = courseService;
    }

    public MenuItem menu() {
        return MenuItem.group("课程管理（F05-F08）")
                .add(new MenuItem("课程录入（F05）", this::create))
                .add(new MenuItem("课程信息修改（F06）", this::update))
                .add(new MenuItem("课程信息删除（F07）", this::delete))
                .add(new MenuItem("课程信息查询（F08）", this::search));
    }

    private void create() {
        accountService.requirePermission(AccountService.Action.COURSE_WRITE);
        Course course = new Course();
        course.setCourseCode(input.readNonEmpty("课程代码（2-16 位大写字母或数字）: ").toUpperCase());
        course.setCourseName(input.readNonEmpty("课程名称: "));
        course.setCredit(input.readDecimal("学分（0.5-10.0）: ", new BigDecimal("0.5"), new BigDecimal("10.0")));
        course.setHours(input.readInt("学时（8-200）: ", 8, 200));
        course.setCourseType(input.readEnum("课程类型", "必修", "选修", "通识"));
        course.setDeptId(input.readInt("开课院系编号（1=计算机 2=电子 3=数学）: ", 1, 3));
        courseService.create(course);
        System.out.println("课程录入成功：" + course.getCourseCode());
    }

    private void update() {
        accountService.requirePermission(AccountService.Action.COURSE_WRITE);
        Course course = courseService.findByCode(input.readNonEmpty("课程代码: ").toUpperCase());
        String name = input.readOptional("新课程名称（回车保持不变）: ");
        if (!name.isEmpty()) {
            course.setCourseName(name);
        }
        String credit = input.readOptional("新学分（回车保持不变）: ");
        if (!credit.isEmpty()) {
            course.setCredit(new BigDecimal(credit));
        }
        String hours = input.readOptional("新学时（回车保持不变）: ");
        if (!hours.isEmpty()) {
            course.setHours(Integer.parseInt(hours));
        }
        courseService.update(course);
        System.out.println("修改成功");
    }

    private void delete() {
        accountService.requirePermission(AccountService.Action.COURSE_WRITE);
        String courseCode = input.readNonEmpty("课程代码: ").toUpperCase();
        Course course = courseService.findByCode(courseCode);
        if (!input.readConfirm("确认删除课程 " + course.getCourseName())) {
            System.out.println("已取消");
            return;
        }
        courseService.delete(courseCode);
        System.out.println("删除成功");
    }

    private void search() {
        String keyword = input.readOptional("课程代码或名称关键字（可空）: ");
        String deptCode = input.readOptional("院系代码（CS/EE/MA/OU，可空）: ");
        String type = input.readOptional("课程类型（必修/选修/通识，可空）: ");
        List<String[]> rows = new ArrayList<>();
        for (Course course : courseService.search(keyword, deptCode, type)) {
            rows.add(new String[]{course.getCourseCode(), course.getCourseName(), String.valueOf(course.getCredit()),
                    String.valueOf(course.getHours()), course.getCourseType(), course.getDeptName()});
        }
        printer.print(new String[]{"课程代码", "课程名称", "学分", "学时", "类型", "开课院系"}, rows);
    }
}
