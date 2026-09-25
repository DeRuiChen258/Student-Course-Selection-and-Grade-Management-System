"""账号与权限：应用账号（sys_account）与数据库账号（table_privileges）。"""

from .base import DaoBase


class AccountDao(DaoBase):
    def find_by_username(self, username):
        return self.db.query_one(
            "SELECT account_id, username, password_hash, role, student_id, teacher_id, last_login "
            "FROM sys_account WHERE username = %s",
            (username,), source="登录校验")

    def touch_login(self, account_id):
        return self.db.execute(
            "UPDATE sys_account SET last_login = NOW() WHERE account_id = %s",
            (int(account_id),), source="登录时间")

    def accounts(self):
        return self.db.query(
            "SELECT a.account_id AS account_id, a.username AS username, a.role AS role, "
            "       IFNULL(s.student_no, '-') AS student_no, "
            "       IFNULL(t.teacher_no, '-') AS teacher_no, "
            "       IFNULL(DATE_FORMAT(a.last_login, '%%m-%%d %%H:%%i'), '未登录') AS last_login "
            "FROM sys_account a "
            "LEFT JOIN student s ON s.student_id = a.student_id "
            "LEFT JOIN teacher t ON t.teacher_id = a.teacher_id "
            "ORDER BY a.account_id",
            source="应用账号清单")

    def bindings(self, account_id):
        return self.db.query_one(
            "SELECT a.account_id, a.role, s.student_no, s.student_name, "
            "       t.teacher_no, t.teacher_name "
            "FROM sys_account a "
            "LEFT JOIN student s ON s.student_id = a.student_id "
            "LEFT JOIN teacher t ON t.teacher_id = a.teacher_id "
            "WHERE a.account_id = %s",
            (int(account_id),), source="账号绑定信息")

    def privileges(self):
        return self.db.query(
            "SELECT grantee AS grantee, table_name AS object_name, privilege_type AS privilege "
            "FROM information_schema.table_privileges "
            "WHERE table_schema = DATABASE() AND grantee LIKE \"'edu_%\" "
            "ORDER BY grantee, table_name, privilege_type",
            source="权限矩阵")

    def schema_privileges(self):
        """MySQL 8.4 未暴露例程级授权（mysql.procs_priv 需额外权限），此处取模式级授权，
        EXECUTE 即以 edu_system.* 为单位授予。"""
        return self.db.query(
            "SELECT grantee AS grantee, table_schema AS object_name, privilege_type AS privilege "
            "FROM information_schema.schema_privileges "
            "WHERE grantee LIKE \"'edu_%\" "
            "ORDER BY grantee, privilege_type",
            source="模式级权限矩阵")

    def db_accounts(self):
        rows = self.db.query(
            "SELECT DISTINCT grantee AS grantee FROM information_schema.schema_privileges "
            "WHERE grantee LIKE \"'edu_%\" "
            "UNION SELECT DISTINCT grantee FROM information_schema.table_privileges "
            "WHERE grantee LIKE \"'edu_%\" ORDER BY grantee",
            source="数据库账号清单")
        return [row["grantee"].split("@")[0].strip("'") for row in rows]

    def global_privileges(self):
        return self.db.query(
            "SELECT grantee AS grantee, privilege_type AS privilege "
            "FROM information_schema.user_privileges "
            "WHERE grantee LIKE \"'edu_%\" ORDER BY grantee, privilege_type",
            source="全局权限")
