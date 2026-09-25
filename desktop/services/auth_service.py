"""登录与角色：校验 sys_account 的 salt$hash 口令。"""

import hashlib
import logging

from db.errors import DbError

log = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db):
        self.db = db

    def hash_password(self, salt, password):
        return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

    def verify(self, password, stored):
        if not stored or "$" not in stored:
            return False
        salt, digest = stored.split("$", 1)
        return self.hash_password(salt, password) == digest

    def login(self, username, password):
        from db.dao import AccountDao
        dao = AccountDao(self.db)
        row = dao.find_by_username(username)
        if not row:
            raise DbError(1045, "账号不存在", hint="可用演示账号：admin / teacher01 / student01")
        if not self.verify(password, row["password_hash"]):
            raise DbError(1045, "口令不正确", hint="口令按 salt$SHA-256(salt+口令) 校验")
        dao.touch_login(row["account_id"])
        account = {"account_id": row["account_id"], "username": row["username"],
                   "role": row["role"], "student_id": row["student_id"],
                   "teacher_id": row["teacher_id"]}
        binding = dao.bindings(row["account_id"]) or {}
        for key in ("student_no", "student_name", "teacher_no", "teacher_name"):
            account[key] = binding.get(key)
        log.info("登录成功: %s(%s)", account["username"], account["role"])
        return account

    def accounts(self):
        from db.dao import AccountDao
        return AccountDao(self.db).accounts()

    def privileges(self, admin_db=None):
        from db.dao import AccountDao
        db = admin_db or self.db
        dao = AccountDao(db)
        return {
            "table": dao.privileges(),
            "schema": dao.schema_privileges(),
            "global": dao.global_privileges(),
            "accounts": dao.db_accounts(),
            "source": "维护连接" if admin_db is not None else "应用账号（可见范围受限）",
        }
