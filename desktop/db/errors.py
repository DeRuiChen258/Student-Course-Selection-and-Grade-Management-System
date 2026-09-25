"""MySQL 错误码到中文语义的翻译层。"""

import pymysql

CODE_TEXT = {
    2003: "无法连接数据库服务器，请确认实例已启动且端口正确",
    2005: "数据库主机名无法解析",
    1044: "当前账号无权访问该数据库",
    1045: "认证失败：账号或口令不正确",
    1049: "目标数据库不存在",
    1054: "SQL 引用了不存在的列",
    1062: "违反唯一性约束：该记录已存在",
    1064: "SQL 语法错误",
    1142: "权限不足：当前数据库账号无权执行该操作",
    1146: "表或视图不存在",
    1048: "必填字段不能为空",
    1264: "数值超出字段允许范围",
    1406: "数据长度超出字段限制",
    1451: "存在引用该记录的外键，数据库拒绝删除",
    1452: "外键引用的记录不存在，请先创建被引用数据",
    1366: "字段值类型不正确",
    3819: "违反 CHECK 完整性约束，请检查取值范围",
    4025: "违反 CHECK 完整性约束，请检查取值范围",
    1292: "日期或数值格式不正确",
    1644: "触发器校验未通过",
}

PROC_CODES = {
    0: "成功",
    40001: "学生不存在",
    40002: "学籍状态不允许选课",
    40003: "开课不存在",
    40004: "重复选课",
    40005: "名额已满",
    40006: "未选该课",
    40007: "已有成绩，不能退课",
    40008: "成绩必须在 0 到 100 之间",
    40099: "数据库异常，已回滚",
}

SIGNAL_TEXT = {
    "E003": "开课不存在（触发器 trg_enrollment_bi 拦截）",
    "E004": "重复选课（触发器 trg_enrollment_bi 拦截）",
    "E005": "名额已满（触发器 trg_enrollment_bi 拦截）",
    "E007": "成绩越界（触发器 trg_enrollment_bu 拦截）",
}


class DbError(Exception):
    """携带 MySQL 错误码与可读提示的异常。"""

    def __init__(self, code, message, sqlstate=None, hint=None, sql=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.sqlstate = sqlstate
        self.hint = hint
        self.sql = sql

    def __str__(self):
        return f"[{self.code}] {self.message}"


def _signal_hint(message):
    if not message:
        return None
    for tag, text in SIGNAL_TEXT.items():
        if tag in message:
            return text
    return None


def translate(exc, sql=None):
    """把驱动异常翻译成 DbError，保留原始错误码便于答辩对照。"""
    if isinstance(exc, DbError):
        if sql and not exc.sql:
            exc.sql = sql
        return exc
    if isinstance(exc, pymysql.err.MySQLError):
        args = getattr(exc, "args", ())
        code = args[0] if args else -1
        raw = args[1] if len(args) > 1 else str(exc)
        message = CODE_TEXT.get(code, str(raw))
        hint = _signal_hint(str(raw))
        return DbError(code, message, hint=hint or str(raw), sql=sql)
    if isinstance(exc, (ConnectionError, OSError)):
        return DbError(2003, CODE_TEXT[2003], hint=str(exc), sql=sql)
    return DbError(-1, str(exc), sql=sql)
