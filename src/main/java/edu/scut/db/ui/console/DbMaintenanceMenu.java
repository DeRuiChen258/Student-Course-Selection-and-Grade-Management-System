package edu.scut.db.ui.console;

import edu.scut.db.db.SqlScriptRunner;
import edu.scut.db.service.AccountService;

import java.nio.file.Path;
import java.nio.file.Paths;

public class DbMaintenanceMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;
    private final SqlScriptRunner scriptRunner;

    public DbMaintenanceMenu(InputReader input, TablePrinter printer, AccountService accountService,
                             SqlScriptRunner scriptRunner) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
        this.scriptRunner = scriptRunner;
    }

    public MenuItem menu() {
        return MenuItem.group("数据库维护")
                .add(new MenuItem("一键初始化（重载演示数据）", this::initialize))
                .add(new MenuItem("完整重建命令提示", this::rebuildHint))
                .add(new MenuItem("执行只读查询", this::query))
                .add(new MenuItem("备份命令提示", this::backupHint));
    }

    private void initialize() {
        accountService.requirePermission(AccountService.Action.DB_MAINTENANCE);
        Path script = Paths.get("sql", "07_seed_data.sql");
        int statements = scriptRunner.runFile(script);
        System.out.println("演示数据重载完成，执行语句 " + statements + " 条");
    }

    private void rebuildHint() {
        System.out.println("完整重建会删除并重建 edu_system，需 DBA 执行：");
        System.out.println("  sudo mysql < sql/00_create_database.sql   # 建库与 4 个账号");
        System.out.println("  bash scripts/init_db.sh -u edu_app -p     # 重建 9 表 4 视图 5 触发器并装载演示数据");
        System.out.println("  或在 mysql 客户端内执行：SOURCE sql/99_rebuild_all.sql;");
    }

    private void backupHint() {
        System.out.println("备份命令：bash scripts/backup.sh（输出到 backup/edu_system_时间戳.sql）");
        System.out.println("恢复命令：mysql -u edu_app -p edu_system < backup/edu_system_时间戳.sql");
    }

    private void query() {
        accountService.requirePermission(AccountService.Action.DB_MAINTENANCE);
        String sql = input.readNonEmpty("只读 SQL（仅允许 SELECT）: ");
        java.util.List<String[]> rows = scriptRunner.query(sql);
        String[] header = rows.isEmpty() ? new String[]{"结果"} : rows.get(0);
        java.util.List<String[]> body = rows.isEmpty() ? java.util.List.of()
                : new java.util.ArrayList<>(rows.subList(1, rows.size()));
        printer.print(header, body);
    }
}
