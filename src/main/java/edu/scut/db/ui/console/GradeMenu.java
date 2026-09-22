package edu.scut.db.ui.console;

import edu.scut.db.model.Enrollment;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.GradeService;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class GradeMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final GradeService gradeService;
    private final EnrollmentService enrollmentService;

    public GradeMenu(InputReader input, TablePrinter printer, AccountService accountService,
                     GradeService gradeService, EnrollmentService enrollmentService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.gradeService = gradeService;
        this.enrollmentService = enrollmentService;
    }

    public MenuItem menu() {
        return MenuItem.group("成绩管理（F13/F14）")
                .add(new MenuItem("成绩录入（F13）", this::save))
                .add(new MenuItem("成绩修改（F14）", this::save))
                .add(new MenuItem("成绩分布统计", this::distribution))
                .add(new MenuItem("批量导入成绩", this::batch));
    }

    private void save() {
        accountService.requirePermission(AccountService.Action.GRADE_WRITE);
        String studentNo = input.readNonEmpty("学号: ");
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        BigDecimal score = input.readDecimal("成绩（0-100）: ", BigDecimal.ZERO, new BigDecimal("100"));
        System.out.println(gradeService.saveScore(studentNo, offeringId, score));
    }

    private void batch() {
        accountService.requirePermission(AccountService.Action.GRADE_WRITE);
        System.out.println("每行格式：学号,开课号,成绩；输入 end 结束");
        List<String[]> rows = new ArrayList<>();
        while (true) {
            String line = input.readOptional("> ");
            if (line.equalsIgnoreCase("end") || line.isEmpty()) {
                break;
            }
            String[] parts = line.split(",");
            if (parts.length != 3) {
                System.out.println("[E001] 该行格式不正确，已跳过");
                continue;
            }
            rows.add(parts);
        }
        List<String> failures = gradeService.batchImport(rows);
        System.out.println("批量导入完成：成功 " + (rows.size() - failures.size()) + " 条，失败 " + failures.size() + " 条");
        failures.forEach(failure -> System.out.println("  失败行：" + failure));
    }

    private void distribution() {
        Integer offeringId = input.readOptionalInt("开课号: ", 1, Integer.MAX_VALUE);
        printer.print(new String[]{"分数段", "人数"}, scoreBands(offeringId));
    }

    private List<String[]> scoreBands(Integer offeringId) {
        List<Enrollment> list = enrollmentService.roster(offeringId);
        int[] bands = new int[6];
        for (Enrollment enrollment : list) {
            BigDecimal score = enrollment.getScore();
            if (score == null) {
                bands[5]++;
            } else if (score.intValue() >= 90) {
                bands[0]++;
            } else if (score.intValue() >= 80) {
                bands[1]++;
            } else if (score.intValue() >= 70) {
                bands[2]++;
            } else if (score.intValue() >= 60) {
                bands[3]++;
            } else {
                bands[4]++;
            }
        }
        String[] labels = {"90-100", "80-89", "70-79", "60-69", "60 以下", "未出分"};
        List<String[]> rows = new ArrayList<>();
        for (int i = 0; i < labels.length; i++) {
            rows.add(new String[]{labels[i], String.valueOf(bands[i])});
        }
        return rows;
    }
}
