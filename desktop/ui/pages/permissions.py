"""权限页：应用账号（sys_account）+ 数据库账号权限矩阵 + 越权实测。"""

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
                               QTabWidget, QVBoxLayout, QWidget)

from models.table_model import Column
from ui.widgets import DataTable, Notifier, PageBase


class PermissionsPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "权限管理", (),
                         "应用层角色（ADMIN / TEACHER / STUDENT）裁剪功能，数据库层账号"
                         "（edu_app / edu_teacher / edu_student / edu_readonly）限制 SQL 权限，"
                         "两层共同构成最小权限模型。", page_key="permissions", parent=parent)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Primary")
        self.add_stretch()
        self.add_action(self.refresh_button)
        self.refresh_button.clicked.connect(self.reload)
        self.tabs = QTabWidget()
        self.account_table = DataTable([
            Column("account_id", "编号", 70, "right", "number"),
            Column("username", "用户名", 130), Column("role", "角色", 100, "center"),
            Column("student_no", "绑定学号", 140), Column("teacher_no", "绑定工号", 130),
            Column("last_login", "最后登录", 150, "center"),
        ])
        self.tabs.addTab(self.account_table, "应用账号（sys_account）")
        self.tabs.addTab(self._privilege_tab(), "数据库账号权限")
        self.root.addWidget(self.tabs, 1)
        self._table_priv = []
        self._routine_priv = []

    def _privilege_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        top = QHBoxLayout()
        self.db_account_box = QComboBox()
        self.db_account_box.setMinimumWidth(200)
        self.test_button = QPushButton("越权实测（edu_teacher 改学生表）")
        self.test_button.setObjectName("Primary")
        hint = QLabel("实测会用对应数据库账号新建临时连接，执行一条被拒绝的 SQL，"
                      "原样回显错误码。")
        hint.setObjectName("HintLabel")
        top.addWidget(QLabel("数据库账号"))
        top.addWidget(self.db_account_box)
        top.addWidget(self.test_button)
        top.addStretch(1)
        layout.addLayout(top)
        self.source_label = QLabel("授权来源：读取中…")
        self.source_label.setObjectName("HintLabel")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        layout.addWidget(hint)
        self.privilege_table = DataTable([
            Column("object_name", "对象", 240), Column("privilege", "权限", 160),
        ])
        self.routine_table = DataTable([
            Column("object_name", "库", 240), Column("privilege", "权限", 160),
        ])
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setFixedHeight(120)
        self.result.setPlaceholderText("越权实测输出")
        layout.addWidget(self.privilege_table, 2)
        note = QLabel("MySQL 8.4 未在 information_schema 暴露例程级授权，"
                      "mysql.procs_priv 对应用账号不可读（实测 1142），"
                      "因此以模式级授权呈现，例程权限通过越权实测间接验证。")
        note.setObjectName("HintLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(QLabel("模式级授权（edu_app 的 EXECUTE 即在此授予）"))
        layout.addWidget(self.routine_table, 1)
        layout.addWidget(self.result)
        self.db_account_box.currentIndexChanged.connect(self._fill_privileges)
        self.test_button.clicked.connect(self.run_overreach)
        return widget

    def on_enter(self, **_):
        self.reload()

    def reload(self):
        self.set_busy(True, "正在读取权限元数据…")
        self.context.runner.run(self._collect, self._apply,
                                lambda code, message: Notifier.error(self, f"[{code}] {message}"),
                                lambda: self.set_busy(False))

    def _collect(self):
        accounts = self.context.auth.accounts()
        privileges = self.context.auth.privileges(self.context.maintenance_db())
        return accounts, privileges

    def _apply(self, payload):
        accounts, privileges = payload
        table_priv = privileges["table"]
        schema_priv = privileges["schema"]
        db_accounts = privileges["accounts"]
        self.account_table.set_rows(accounts, "没有应用账号", "运行 init_db.sh 载入演示数据")
        self._table_priv = table_priv
        self._routine_priv = schema_priv
        current = self.db_account_box.currentData()
        self.db_account_box.blockSignals(True)
        self.db_account_box.clear()
        for name in db_accounts or ["edu_app", "edu_teacher", "edu_student", "edu_readonly"]:
            self.db_account_box.addItem(name, name)
        self.db_account_box.blockSignals(False)
        if current:
            index = self.db_account_box.findData(current)
            if index >= 0:
                self.db_account_box.setCurrentIndex(index)
        self._fill_privileges()
        self.source_label.setText(
            f"授权来源：{privileges['source']} · 表级 {len(table_priv)} 条 · "
            f"模式级 {len(schema_priv)} 条 · 账号 {len(db_accounts)} 个")
        self.emit_status(f"权限矩阵：{len(table_priv)} 条表级授权 · "
                         f"{len(schema_priv)} 条模式级授权（来源：{privileges['source']}）")

    def _fill_privileges(self):
        account = self.db_account_box.currentData()
        if not account:
            return
        table_rows = [row for row in self._table_priv if account in row["grantee"]]
        routine_rows = [row for row in self._routine_priv if account in row["grantee"]]
        self.privilege_table.set_rows(table_rows, f"{account} 没有表级授权",
                                      "该账号的授权是库级（schema）而非表级，见下方")
        self.routine_table.set_rows(routine_rows, f"{account} 没有例程授权",
                                    "例程授权通过 GRANT EXECUTE 授予")

    def run_overreach(self):
        self.result.setPlainText("正在以 edu_teacher 建立临时连接并执行越权 UPDATE…")
        self.test_button.setEnabled(False)
        self.context.runner.run(lambda: self._probe("edu_teacher"), self._probe_ok,
                                self._probe_err,
                                lambda: self.test_button.setEnabled(True))

    def _probe(self, account):
        import pymysql
        from db.errors import translate
        profile = dict(self.context.profile)
        sql = "UPDATE student SET phone = 'x' WHERE student_no = '202301010001'"
        conn = pymysql.connect(host=profile["host"], port=int(profile["port"]),
                               user=account, password=profile.get("password", ""),
                               database=profile.get("database", "edu_system"),
                               charset="utf8mb4", connect_timeout=5, autocommit=True)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
        except Exception as exc:
            error = translate(exc, sql)
            return (f"账号       : {account}\n"
                    f"执行语句   : {sql}\n"
                    f"数据库返回 : {error}\n"
                    f"原始错误号 : {error.code}\n"
                    f"说明       : 该账号仅被授予三个视图的 SELECT、enrollment 的 "
                    f"UPDATE(score, score_time) 与 p_save_score 的 EXECUTE，"
                    f"因此对 student 表的 UPDATE 被数据库拒绝。")
        else:
            return f"未被拒绝（不符合预期）：{sql}"
        finally:
            conn.close()

    def _probe_ok(self, text):
        self.result.setPlainText(text)
        Notifier.success(self, "越权实测完成，结果已显示真实错误码")

    def _probe_err(self, code, message):
        self.result.setPlainText(f"实测失败 [{code}] {message}")
        Notifier.error(self, message)
