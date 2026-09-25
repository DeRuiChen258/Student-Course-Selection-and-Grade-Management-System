"""导入导出页：快捷导出与向导入口。"""

from PySide6.QtWidgets import (QFileDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from ui.dialogs import ImportExportDialog
from ui.widgets import Notifier, PageBase

QUICK_TARGETS = [
    ("student", "学生"), ("course", "课程"), ("teacher", "教师"),
    ("course_offering", "开课"), ("enrollment", "选课与成绩"),
    ("v_student_profile", "视图: 学生档案"), ("v_offering_detail", "视图: 开课详情"),
    ("v_course_stat", "视图: 课程统计"),
]


class ImportExportPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "数据导入导出", (),
                         "快捷导出直接读取当前库的全部行；导入向导支持 CSV / Excel / JSON、"
                         "字段映射与错误行报告。", page_key="io", parent=parent)
        self.wizard_button = QPushButton("打开导入导出向导")
        self.wizard_button.setObjectName("Primary")
        self.summary_button = QPushButton("刷新数据规模")
        self.summary_button.setObjectName("Ghost")
        self.add_action(self.wizard_button)
        self.add_stretch()
        self.add_action(self.summary_button)
        self.wizard_button.clicked.connect(self.open_wizard)
        self.summary_button.clicked.connect(self.reload)
        self.summary = QLabel("—")
        self.summary.setObjectName("InfoPanel")
        self.summary.setWordWrap(True)
        self.root.addWidget(self.summary)
        self.root.addWidget(QLabel("快捷导出（整表导出为 CSV / Excel / JSON / SQL INSERT）"))
        grid = QGridLayout()
        grid.setSpacing(10)
        for index, (table, label) in enumerate(QUICK_TARGETS):
            button = QPushButton(f"导出 {label}")
            button.setObjectName("Ghost")
            button.clicked.connect(lambda _=False, name=table: self.quick_export(name))
            grid.addWidget(button, index // 4, index % 4)
        holder = QWidget()
        holder.setLayout(grid)
        self.root.addWidget(holder)
        self.root.addStretch(1)

    def on_enter(self, **_):
        self.reload()

    def reload(self):
        self.context.runner.run(self.context.meta.overview, self._apply,
                                lambda code, message: Notifier.error(self, f"[{code}] {message}"))

    def _apply(self, counts):
        self.summary.setText(
            f"学生 {counts.get('students', 0)} · 课程 {counts.get('courses', 0)} · "
            f"开课 {counts.get('offerings', 0)} · 选课 {counts.get('enrollments', 0)} · "
            f"已出分 {counts.get('score_ready', 0)} · 总体均分 {counts.get('avg_score') or '—'}")

    def open_wizard(self):
        ImportExportDialog(self.context, self).exec()

    def quick_export(self, table):
        path, selected = QFileDialog.getSaveFileName(
            self, f"导出 {table}", f"{table}.csv",
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;JSON 文件 (*.json);;SQL 脚本 (*.sql)")
        if not path:
            return
        fmt = "csv"
        for candidate in ("xlsx", "json", "sql"):
            if path.endswith(f".{candidate}") or candidate.upper() in selected:
                fmt = candidate
                if not path.endswith(f".{candidate}"):
                    path += f".{candidate}"
                break
        self.set_busy(True, f"正在导出 {table}…")
        self.context.runner.run(
            lambda: self._export_job(table, path, fmt),
            lambda count: (Notifier.success(self, f"已导出 {count} 行到 {path}"),
                           self.emit_status(f"导出 {table}：{count} 行")),
            lambda code, message: Notifier.error(self, f"[{code}] {message}"),
            lambda: self.set_busy(False))

    def _export_job(self, table, path, fmt):
        rows = self.context.db.query(f"SELECT * FROM {table}", source=f"导出 {table}")
        if not rows:
            return 0
        columns = [(key, key) for key in rows[0].keys()]
        return self.context.io.export(path, columns, rows, fmt, table)
