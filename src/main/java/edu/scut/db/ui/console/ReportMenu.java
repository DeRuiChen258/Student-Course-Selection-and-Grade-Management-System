package edu.scut.db.ui.console;

import edu.scut.db.model.AuditLog;
import edu.scut.db.service.ReportService;
import edu.scut.db.service.dto.CourseStat;
import edu.scut.db.service.dto.GpaRow;
import edu.scut.db.service.dto.StudentTranscript;
import edu.scut.db.util.DateUtils;

import java.util.ArrayList;
import java.util.List;

public class ReportMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final ReportService reportService;

    public ReportMenu(InputReader input, TablePrinter printer, ReportService reportService) {
        this.input = input;
        this.printer = printer;
        this.reportService = reportService;
    }

    public MenuItem menu() {
        return MenuItem.group("统计报表（F16）")
                .add(new MenuItem("课程统计报表", this::courseStats))
                .add(new MenuItem("学生 GPA 排名", this::gpaRanking))
                .add(new MenuItem("学期开课汇总", this::semesterSummary))
                .add(new MenuItem("学生成绩单", this::transcript))
                .add(new MenuItem("审计日志", this::audit));
    }

    private void courseStats() {
        int limit = input.readInt("显示条数（1-50）: ", 1, 50);
        List<String[]> rows = new ArrayList<>();
        for (CourseStat stat : reportService.courseStats(limit)) {
            rows.add(new String[]{stat.getCourseCode(), stat.getCourseName(), stat.getSemester(),
                    String.valueOf(stat.getEnrolledCount()),
                    stat.getAvgScore() == null ? "-" : stat.getAvgScore().toString(),
                    stat.getMaxScore() == null ? "-" : stat.getMaxScore().toString(),
                    stat.getMinScore() == null ? "-" : stat.getMinScore().toString(),
                    stat.getFailCount() + "（" + stat.failRate() + "%）"});
        }
        printer.print(new String[]{"课程代码", "课程名", "学期", "选课人数", "平均分", "最高分", "最低分", "不及格"}, rows);
    }

    private void gpaRanking() {
        int limit = input.readInt("显示条数（1-50）: ", 1, 50);
        List<String[]> rows = new ArrayList<>();
        for (GpaRow row : reportService.gpaRanking(limit)) {
            rows.add(new String[]{String.valueOf(row.getRank()), row.getStudentNo(), row.getStudentName(),
                    row.getGpa() == null ? "-" : row.getGpa().toString(),
                    row.getTotalCredit() == null ? "-" : row.getTotalCredit().toString(),
                    String.valueOf(row.getFailCount())});
        }
        printer.print(new String[]{"名次", "学号", "姓名", "GPA", "已修学分", "不及格门数"}, rows);
    }

    private void semesterSummary() {
        printer.print(new String[]{"学期", "开课数", "课程数", "总容量", "已选人次"}, reportService.semesterSummary());
    }

    private void transcript() {
        String studentNo = input.readNonEmpty("学号: ");
        List<String[]> rows = new ArrayList<>();
        for (StudentTranscript row : reportService.transcript(studentNo)) {
            rows.add(new String[]{row.getSemester(), row.getCourseCode(), row.getCourseName(),
                    String.valueOf(row.getCredit()),
                    row.getScore() == null ? "未出分" : row.getScore().toString(),
                    row.getLevel() == null ? "-" : row.getLevel(),
                    row.getGradePoint() == null ? "-" : row.getGradePoint().toString(),
                    row.getTeacherName()});
        }
        printer.print(new String[]{"学期", "课程代码", "课程名", "学分", "成绩", "等级", "绩点", "教师"}, rows);
    }

    private void audit() {
        int limit = input.readInt("显示条数（1-50）: ", 1, 50);
        List<String[]> rows = new ArrayList<>();
        for (AuditLog log : reportService.recentAudit(limit)) {
            rows.add(new String[]{String.valueOf(log.getLogId()), log.getTableName(), log.getAction(),
                    log.getRecordId(), log.getOperator(), DateUtils.formatDateTime(log.getActionTime()),
                    log.getDetail()});
        }
        printer.print(new String[]{"编号", "表", "动作", "记录", "操作者", "时间", "明细"}, rows);
    }
}
