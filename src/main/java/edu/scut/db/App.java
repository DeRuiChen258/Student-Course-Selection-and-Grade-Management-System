package edu.scut.db;

import edu.scut.db.config.AppConfig;
import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.db.SqlScriptRunner;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.DataAccessException;
import edu.scut.db.service.AccountService;
import edu.scut.db.service.CourseService;
import edu.scut.db.service.EnrollmentService;
import edu.scut.db.service.GradeService;
import edu.scut.db.service.OfferingService;
import edu.scut.db.service.ReportService;
import edu.scut.db.service.StudentService;
import edu.scut.db.service.TeacherService;
import edu.scut.db.ui.console.ConsoleUI;
import edu.scut.db.util.Logger;

import java.util.Arrays;

public final class App {

    private App() {
    }

    public static void main(String[] args) {
        int exitCode = run(args);
        if (exitCode != 0) {
            System.exit(exitCode);
        }
    }

    static int run(String[] args) {
        AppConfig config;
        try {
            config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        } catch (Exception e) {
            System.err.println("[E009] 配置读取失败：" + e.getMessage());
            return 2;
        }
        Logger.configure(config.getLogLevel());

        ConnectionProvider provider;
        try {
            provider = ConnectionProvider.of(config);
            provider.getConnection();
        } catch (DataAccessException e) {
            System.err.println("[E009] " + e.getMessage());
            return 2;
        }

        Logger.info("目标库 " + provider.describeTarget() + " 连接成功");

        Tx tx = new Tx(provider);
        AccountService accountService = new AccountService(tx);
        StudentService studentService = new StudentService(tx);
        TeacherService teacherService = new TeacherService(tx);
        CourseService courseService = new CourseService(tx);
        OfferingService offeringService = new OfferingService(tx);
        EnrollmentService enrollmentService = new EnrollmentService(tx);
        GradeService gradeService = new GradeService(tx);
        ReportService reportService = new ReportService(tx);
        SqlScriptRunner scriptRunner = new SqlScriptRunner(provider);

        ConsoleUI ui = new ConsoleUI(config, accountService, studentService, teacherService, courseService,
                offeringService, enrollmentService, gradeService, reportService, scriptRunner);
        try {
            if (Arrays.asList(args).contains("--demo")) {
                ui.runDemo();
            } else {
                ui.run();
            }
            return 0;
        } catch (BizException e) {
            System.err.println(e.getMessage());
            return 1;
        } catch (Exception e) {
            System.err.println("[E009] 程序异常结束：" + e.getMessage());
            return 1;
        } finally {
            provider.close();
        }
    }
}
