package edu.scut.db.ui.console;

import edu.scut.db.config.AppConfig;
import edu.scut.db.model.ClassGroup;
import edu.scut.db.model.Student;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.StudentService;
import edu.scut.db.util.DateUtils;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class StudentMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final StudentService studentService;
    private final int pageSize;

    public StudentMenu(InputReader input, TablePrinter printer, AccountService accountService,
                       StudentService studentService, AppConfig config) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.studentService = studentService;
        this.pageSize = config.getPageSize();
    }

    public MenuItem menu() {
        return MenuItem.group("学生管理（F01-F04）")
                .add(new MenuItem("新生入学（F01）", this::create))
                .add(new MenuItem("学生信息修改（F02）", this::update))
                .add(new MenuItem("学生信息删除（F03）", this::delete))
                .add(new MenuItem("学生信息查询（F04）", this::search));
    }

    private void create() {
        accountService.requirePermission(AccountService.Action.STUDENT_WRITE);
        Student student = new Student();
        student.setStudentNo(input.readNonEmpty("学号（12 位数字）: "));
        student.setStudentName(input.readNonEmpty("姓名: "));
        student.setGender(input.readEnum("性别", "男", "女"));
        student.setBirthDate(input.readDate("出生日期（yyyy-MM-dd，可空）: ", true));
        student.setClassId(chooseClass());
        student.setEnrollDate(input.readDate("入学日期（yyyy-MM-dd）: ", false));
        student.setPhone(input.readOptional("联系电话（可空）: "));
        student.setEmail(input.readOptional("邮箱（可空）: "));
        student.setStatus("在读");
        studentService.create(student);
        System.out.println("新生入学成功：" + student.getStudentNo() + " " + student.getStudentName());
    }

    private void update() {
        accountService.requirePermission(AccountService.Action.STUDENT_WRITE);
        String studentNo = input.readNonEmpty("学号: ");
        Student student = studentService.findByNo(studentNo);
        System.out.println("当前值：" + student.getStudentName() + " / " + student.getPhone() + " / " + student.getStatus());
        String name = input.readOptional("新姓名（回车保持不变）: ");
        if (!name.isEmpty()) {
            student.setStudentName(name);
        }
        String phone = input.readOptional("新电话（回车保持不变）: ");
        if (!phone.isEmpty()) {
            student.setPhone(phone);
        }
        String status = input.readOptional("新状态（在读/休学/退学/毕业，回车保持不变）: ");
        if (!status.isEmpty()) {
            student.setStatus(status);
        }
        studentService.update(student);
        System.out.println("修改成功");
    }

    private void delete() {
        accountService.requirePermission(AccountService.Action.STUDENT_WRITE);
        String studentNo = input.readNonEmpty("学号: ");
        Student student = studentService.findByNo(studentNo);
        System.out.println("该生当前选课记录将由数据库统计：学生 " + student.getStudentName()
                + "，班级 " + student.getClassName() + "，状态 " + student.getStatus());
        if (!input.readConfirm("确认删除该学生及其选课记录")) {
            System.out.println("已取消");
            return;
        }
        int cleaned = studentService.delete(studentNo);
        System.out.println("删除成功，同时清理选课记录 " + cleaned + " 条（触发器已写入审计日志）");
    }

    private void search() {
        String studentNo = input.readOptional("学号（精确，可空）: ");
        String name = input.readOptional("姓名关键字（模糊，可空）: ");
        String classCode = input.readOptional("班级代码（可空）: ");
        String status = input.readOptional("状态（在读/休学/退学/毕业，可空）: ");
        int page = 1;
        while (true) {
            List<Student> list = studentService.search(studentNo, name, classCode, status, page, pageSize);
            List<String[]> rows = new ArrayList<>();
            for (Student student : list) {
                rows.add(new String[]{student.getStudentNo(), student.getStudentName(), student.getGender(),
                        DateUtils.format(student.getBirthDate()), student.getClassName(), student.getStatus(),
                        student.getPhone()});
            }
            printer.print(new String[]{"学号", "姓名", "性别", "出生日期", "班级", "状态", "电话"}, rows);
            int total = studentService.count(studentNo, name, classCode, status);
            int pages = Math.max(1, (total + pageSize - 1) / pageSize);
            System.out.println("第 " + page + "/" + pages + " 页，共 " + total + " 条（输入 n 下一页，p 上一页，回车结束）");
            String command = input.readOptional("翻页: ").toLowerCase();
            if (command.equals("n") && page < pages) {
                page++;
            } else if (command.equals("p") && page > 1) {
                page--;
            } else {
                return;
            }
        }
    }

    private Integer chooseClass() {
        List<ClassGroup> groups = studentService.classGroups();
        List<String[]> rows = new ArrayList<>();
        for (ClassGroup group : groups) {
            rows.add(new String[]{String.valueOf(group.getClassId()), group.getClassCode(), group.getClassName(),
                    group.getDeptName(), String.valueOf(group.getGradeYear())});
        }
        printer.print(new String[]{"编号", "班级代码", "班级名称", "院系", "年级"}, rows);
        return input.readInt("请选择班级编号: ", 1, Math.max(1, groups.size()));
    }
}
