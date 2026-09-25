"""操作日志页：audit_log 的筛选、分页与导出。"""

from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton

from models.table_model import Column
from ui.widgets import DataTable, Notifier, PageBase, Pager


class LogsPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "操作日志", ("F03", "F13", "F14"),
                         "audit_log 由触发器 trg_student_ad 等写入；查询命中 idx_audit_time 与 "
                         "idx_audit_table 两条索引。", page_key="logs", parent=parent)
        self.table_box = QComboBox()
        self.table_box.addItem("全部表", None)
        for name in context.report.audit_tables():
            self.table_box.addItem(name, name)
        self.action_box = QComboBox()
        self.action_box.addItem("全部操作", None)
        for action in ("INSERT", "UPDATE", "DELETE"):
            self.action_box.addItem(action, action)
        self.keyword_box = QLineEdit()
        self.keyword_box.setPlaceholderText("记录标识 / 操作者 / 明细关键字")
        self.keyword_box.setMinimumWidth(240)
        self.query_button = QPushButton("查询")
        self.query_button.setObjectName("Primary")
        self.export_button = QPushButton("导出")
        self.export_button.setObjectName("Ghost")
        self.add_action(QLabel("表"))
        self.add_action(self.table_box)
        self.add_action(self.action_box)
        self.add_action(self.keyword_box)
        self.add_stretch()
        self.add_action(self.export_button)
        self.add_action(self.query_button)
        columns = [
            Column("action_time", "时间", 150, "center"),
            Column("table_name", "表", 120), Column("action", "操作", 80, "center"),
            Column("record_id", "记录标识", 140), Column("operator", "操作者", 110),
            Column("detail", "明细", 380),
        ]
        self.table = DataTable(columns)
        self.pager = Pager(page_size=50)
        self.root.addWidget(self.table, 1)
        self.root.addWidget(self.pager)
        self.query_button.clicked.connect(lambda: self.reload(reset_page=True))
        self.table_box.currentIndexChanged.connect(lambda: self.reload(reset_page=True))
        self.action_box.currentIndexChanged.connect(lambda: self.reload(reset_page=True))
        self.keyword_box.returnPressed.connect(lambda: self.reload(reset_page=True))
        self.export_button.clicked.connect(self.export_rows)
        self.pager.pageChanged.connect(self.load)
        self._rows = []

    def on_enter(self, **_):
        self.reload()

    def reload(self, reset_page=False):
        if reset_page:
            self.pager.reset()
        self.load(self.pager.page, self.pager.page_size)

    def load(self, page=1, page_size=None):
        page_size = int(page_size or self.pager.page_size)
        offset = max(0, (page - 1) * page_size)
        table_name = self.table_box.currentData()
        action = self.action_box.currentData()
        keyword = self.keyword_box.text().strip() or None
        self.set_busy(True, "正在查询审计日志…")
        self.context.runner.run(
            lambda: self.context.report.audit_page(table_name, action, keyword,
                                                   page_size, offset),
            self._apply, lambda code, message: Notifier.error(self, f"[{code}] {message}"),
            lambda: self.set_busy(False))

    def _apply(self, payload):
        rows, total = payload
        self._rows = rows
        self.table.set_rows(rows, "没有匹配的审计记录",
                            "执行删除学生或修改成绩操作后，触发器会写入审计日志")
        self.pager.update_state(total, self.pager.page, self.pager.page_size)
        self.emit_status(f"审计日志：命中 {total} 条")

    def export_rows(self):
        if not self._rows:
            Notifier.warn(self, "当前没有可导出的日志")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出审计日志", "audit_log.csv",
                                              "CSV 文件 (*.csv)")
        if not path:
            return
        columns = [(column.label, column.key) for column in self.table.model.columns]
        count = self.context.io.export(path, columns, self._rows, "csv", "audit_log")
        Notifier.success(self, f"已导出 {count} 行到 {path}")
