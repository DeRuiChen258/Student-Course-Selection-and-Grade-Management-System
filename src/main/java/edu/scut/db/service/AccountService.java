package edu.scut.db.service;

import edu.scut.db.dao.SysAccountDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.SysAccount;
import edu.scut.db.util.PasswordUtils;

import java.util.EnumSet;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class AccountService {

    public enum Action {
        READ, STUDENT_WRITE, TEACHER_WRITE, COURSE_WRITE, OFFERING_WRITE, GRADE_WRITE, REPORT_READ, DB_MAINTENANCE
    }

    private static final Map<String, Set<Action>> MATRIX = new HashMap<>();

    static {
        MATRIX.put("ADMIN", EnumSet.allOf(Action.class));
        MATRIX.put("TEACHER", EnumSet.of(Action.READ, Action.GRADE_WRITE, Action.REPORT_READ));
        MATRIX.put("STUDENT", EnumSet.of(Action.READ));
    }

    private final Tx tx;
    private final SysAccountDao accountDao;
    private SysAccount current;

    public AccountService(Tx tx) {
        this.tx = tx;
        this.accountDao = new SysAccountDao(tx.provider());
    }

    public SysAccount login(String username, String password) {
        SysAccount account = accountDao.findByUsername(username);
        if (account == null || !PasswordUtils.verify(password, account.getPasswordHash())) {
            throw BizException.of(ErrorCode.E008, "用户名或密码错误");
        }
        tx.runInTx(connection -> accountDao.updateLastLogin(connection, username));
        current = account;
        return account;
    }

    public void logout() {
        current = null;
    }

    public SysAccount current() {
        return current;
    }

    public String currentRole() {
        return current == null ? "未登录" : current.getRole();
    }

    public void requirePermission(Action action) {
        if (current == null) {
            throw BizException.of(ErrorCode.E008, "尚未登录，请先在「账号与权限」中登录");
        }
        Set<Action> allowed = MATRIX.getOrDefault(current.getRole(), Set.of());
        if (!allowed.contains(action)) {
            throw BizException.of(ErrorCode.E008,
                    "当前角色 " + current.getRole() + " 不能执行 " + action + " 操作");
        }
    }

    public String describeMatrix() {
        StringBuilder text = new StringBuilder("角色权限矩阵：");
        MATRIX.forEach((role, actions) -> text.append("\n  ").append(role).append(" -> ").append(actions));
        return text.toString();
    }
}
