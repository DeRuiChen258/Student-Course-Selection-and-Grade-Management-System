package edu.scut.db.ui.console;

import edu.scut.db.model.Department;
import edu.scut.db.model.Teacher;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.TeacherService;
import edu.scut.db.util.DateUtils;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class TeacherMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final TeacherService teacherService;

    public TeacherMenu(InputReader input, TablePrinter printer, AccountService accountService,
                       TeacherService teacherService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.teacherService = teacherService;
    }

    public MenuItem menu() {
        return MenuItem.group("教师管理（F09）")
                .add(new MenuItem("教师新增", this::create))
                .add(new MenuItem("教师信息修改", this::update))
                .add(new MenuItem("教师删除", this::delete))
                .add(new MenuItem("教师查询", this::search));
    }

    private void create() {
        accountService.requirePermission(AccountService.Action.TEACHER_WRITE);
        Teacher teacher = new Teacher();
        teacher.setTeacherNo(input.readNonEmpty("工号（8 位数字）: "));
        teacher.setTeacherName(input.readNonEmpty("姓名: "));
        teacher.setGender(input.readEnum("性别", "男", "女"));
        teacher.setTitle(input.readEnum("职称", "助教", "讲师", "副教授", "教授"));
        teacher.setDeptId(input.readInt("院系编号（1=计算机 2=电子 3=数学）: ", 1, 3));
        teacher.setHireDate(input.readDate("入职日期（yyyy-MM-dd）: ", false));
        teacher.setPhone(input.readOptional("电话（可空）: "));
        teacher.setEmail(input.readOptional("邮箱（可空）: "));
        teacherService.create(teacher);
        System.out.println("教师新增成功：" + teacher.getTeacherNo());
    }

    private void update() {
        accountService.requirePermission(AccountService.Action.TEACHER_WRITE);
        Teacher teacher = teacherService.findByNo(input.readNonEmpty("工号: "));
        String name = input.readOptional("新姓名（回车保持不变）: ");
        if (!name.isEmpty()) {
            teacher.setTeacherName(name);
        }
        String title = input.readOptional("新职称（回车保持不变）: ");
        if (!title.isEmpty()) {
            teacher.setTitle(title);
        }
        teacherService.update(teacher);
        System.out.println("修改成功");
    }

    private void delete() {
        accountService.requirePermission(AccountService.Action.TEACHER_WRITE);
        String teacherNo = input.readNonEmpty("工号: ");
        Teacher teacher = teacherService.findByNo(teacherNo);
        if (!input.readConfirm("确认删除教师 " + teacher.getTeacherName())) {
            System.out.println("已取消");
            return;
        }
        teacherService.delete(teacherNo);
        System.out.println("删除成功");
    }

    private void search() {
        String keyword = input.readOptional("工号或姓名关键字（可空）: ");
        String deptCode = input.readOptional("院系代码（CS/EE/MA/OU，可空）: ");
        String title = input.readOptional("职称（可空）: ");
        List<String[]> rows = new ArrayList<>();
        for (Teacher teacher : teacherService.search(keyword, deptCode, title)) {
            rows.add(new String[]{teacher.getTeacherNo(), teacher.getTeacherName(), teacher.getGender(),
                    teacher.getTitle(), teacher.getDeptName(), DateUtils.format(teacher.getHireDate()),
                    teacher.getPhone()});
        }
        printer.print(new String[]{"工号", "姓名", "性别", "职称", "院系", "入职日期", "电话"}, rows);
    }
}
