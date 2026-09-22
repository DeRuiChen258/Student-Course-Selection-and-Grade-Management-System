package edu.scut.db.ui.console;

import edu.scut.db.model.SysAccount;
import edu.scut.db.service.AccountService;
import edu.scut.db.util.DateUtils;

public class AccountMenu {

    private final InputReader input;
    private final TablePrinter printer;
    private final AccountService accountService;

    public AccountMenu(InputReader input, TablePrinter printer, AccountService accountService) {
        this.input = input;
        this.printer = printer;
        this.accountService = accountService;
    }

    public MenuItem menu() {
        return MenuItem.group("账号与权限")
                .add(new MenuItem("登录", this::login))
                .add(new MenuItem("查看当前身份", this::whoami))
                .add(new MenuItem("查看权限矩阵", this::matrix))
                .add(new MenuItem("退出登录", this::logout));
    }

    private void login() {
        String username = input.readNonEmpty("用户名: ");
        String password = input.readNonEmpty("口令: ");
        SysAccount account = accountService.login(username, password);
        System.out.println("登录成功：" + account + "，上次登录 "
                + DateUtils.formatDateTime(account.getLastLogin()));
    }

    private void whoami() {
        SysAccount account = accountService.current();
        if (account == null) {
            System.out.println("当前未登录（游客只能浏览，写操作会被拒绝）");
            return;
        }
        printer.printSingle(new String[]{"用户名", "角色", "绑定学生", "绑定教师"}, new String[]{
                account.getUsername(), account.getRole(),
                account.getStudentId() == null ? "-" : String.valueOf(account.getStudentId()),
                account.getTeacherId() == null ? "-" : String.valueOf(account.getTeacherId())});
    }

    private void matrix() {
        System.out.println(accountService.describeMatrix());
    }

    private void logout() {
        accountService.logout();
        System.out.println("已退出登录");
    }
}
