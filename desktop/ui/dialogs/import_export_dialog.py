"""导入导出向导：CSV / Excel / JSON / SQL INSERT 与字段映射导入。"""

from pathlib import Path

from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox,
                               QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from db.dao.meta_dao import ident
from ui.widgets import Notifier


class ImportExportDialog(QDialog):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self._headers = []
        self._rows = []
        self._failures = []
        self.setWindowTitle("数据导入导出")
        self.resize(960, 660)
        self._objects = list(context.meta.objects())
        layout = QVBoxLayout(self)
        head = QLabel("数据导入导出")
        head.setObjectName("DialogTitle")
        hint = QLabel("导出直接取当前库的真实结果；导入按字段映射逐行写入，成功行提交、"
                      "失败行可导出为 CSV。")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        layout.addWidget(head)
        layout.addWidget(hint)
        tabs = QTabWidget()
        tabs.addTab(self._export_tab(), "导出")
        tabs.addTab(self._import_tab(), "导入")
        layout.addWidget(tabs, 1)
        close = QPushButton("关闭")
        close.setObjectName("Ghost")
        close.clicked.connect(self.accept)
        line = QHBoxLayout()
        line.addStretch(1)
        line.addWidget(close)
        layout.addLayout(line)

    def _export_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.object_box = QComboBox()
        for row in self._objects:
            self.object_box.addItem(f"{row['name']} · {row['kind']}", row["name"])
        self.format_box = QComboBox()
        self.format_box.addItems(["csv", "xlsx", "json", "sql"])
        self.limit_box = QSpinBox()
        self.limit_box.setRange(0, 1000000)
        self.limit_box.setValue(0)
        self.limit_box.setSpecialValueText("全部行")
        self.path_box = QLineEdit()
        self.path_box.setPlaceholderText("选择导出文件路径")
        browse = QPushButton("浏览…")
        browse.setObjectName("Ghost")
        browse.clicked.connect(self._choose_export_path)
        holder = QWidget()
        holder_layout = QHBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(self.path_box, 1)
        holder_layout.addWidget(browse)
        form.addRow("导出对象", self.object_box)
        form.addRow("文件格式", self.format_box)
        form.addRow("行数上限", self.limit_box)
        form.addRow("文件路径", holder)
        layout.addLayout(form)
        self.export_button = QPushButton("开始导出")
        self.export_button.setObjectName("Primary")
        self.export_button.clicked.connect(self.do_export)
        line = QHBoxLayout()
        line.addWidget(self.export_button)
        line.addStretch(1)
        layout.addLayout(line)
        self.export_log = QPlainTextEdit()
        self.export_log.setReadOnly(True)
        self.export_log.setPlaceholderText("导出日志")
        layout.addWidget(self.export_log, 1)
        return widget

    def _import_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        top = QHBoxLayout()
        self.file_box = QLineEdit()
        self.file_box.setPlaceholderText("选择要导入的 CSV / XLSX / JSON 文件")
        pick = QPushButton("选择文件")
        pick.setObjectName("Ghost")
        pick.clicked.connect(self._choose_import_file)
        top.addWidget(self.file_box, 1)
        top.addWidget(pick)
        layout.addLayout(top)
        form = QFormLayout()
        self.target_box = QComboBox()
        for row in self._objects:
            if row["kind"] == "BASE TABLE":
                self.target_box.addItem(row["name"], row["name"])
        self.mode_box = QComboBox()
        self.mode_box.addItem("跳过错误行（保留成功行）", "skip")
        self.mode_box.addItem("任一行失败即整体回滚", "atomic")
        form.addRow("目标基表", self.target_box)
        form.addRow("错误处理", self.mode_box)
        layout.addLayout(form)
        self.mapping = QTableWidget(0, 2)
        self.mapping.setHorizontalHeaderLabels(["文件列", "目标列"])
        self.mapping.verticalHeader().setVisible(False)
        layout.addWidget(self.mapping, 1)
        self.preview_label = QLabel("尚未选择文件")
        self.preview_label.setObjectName("HintLabel")
        layout.addWidget(self.preview_label)
        self.import_button = QPushButton("开始导入")
        self.import_button.setObjectName("Primary")
        self.import_button.clicked.connect(self.do_import)
        self.failure_button = QPushButton("导出失败行")
        self.failure_button.setObjectName("Ghost")
        self.failure_button.setEnabled(False)
        self.failure_button.clicked.connect(self.export_failures)
        line = QHBoxLayout()
        line.addWidget(self.import_button)
        line.addWidget(self.failure_button)
        line.addStretch(1)
        layout.addLayout(line)
        self.import_log = QPlainTextEdit()
        self.import_log.setReadOnly(True)
        self.import_log.setPlaceholderText("导入报告")
        layout.addWidget(self.import_log, 1)
        self.target_box.currentIndexChanged.connect(self._rebuild_mapping)
        return widget

    def _choose_export_path(self):
        fmt = self.format_box.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "导出到", f"{self.object_box.currentData()}.{fmt}",
            f"{fmt.upper()} 文件 (*.{fmt})")
        if path:
            self.path_box.setText(path)

    def do_export(self):
        path = self.path_box.text().strip()
        if not path:
            Notifier.warn(self, "请先选择导出路径")
            return
        table = ident(self.object_box.currentData())
        fmt = self.format_box.currentText()
        limit = self.limit_box.value()
        if limit:
            sql, params = f"SELECT * FROM {table} LIMIT %s", (limit,)
        else:
            sql, params = f"SELECT * FROM {table}", ()
        self.export_button.setEnabled(False)
        self.export_log.setPlainText("正在读取数据…")
        self.context.runner.run(lambda: self._export_job(sql, params, path, table, fmt),
                                self._export_ok, self._export_err,
                                lambda: self.export_button.setEnabled(True))

    def _export_job(self, sql, params, path, table, fmt):
        rows = self.context.db.query(sql, params, source=f"导出 {table}")
        if not rows:
            return 0
        columns = [(key, key) for key in rows[0].keys()]
        return self.context.io.export(path, columns, rows, fmt, table)

    def _export_ok(self, count):
        self.export_log.setPlainText(f"导出完成：{count} 行 → {self.path_box.text()}")
        Notifier.success(self, f"导出完成：{count} 行")

    def _export_err(self, code, message):
        self.export_log.setPlainText(f"导出失败 [{code}] {message}")
        Notifier.error(self, message)

    def _choose_import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择导入文件", "",
                                              "数据文件 (*.csv *.xlsx *.json)")
        if not path:
            return
        self.file_box.setText(path)
        try:
            self._headers, self._rows = self.context.io.preview(path, limit=20)
        except Exception as exc:
            Notifier.error(self, str(exc))
            return
        self.preview_label.setText(
            f"已读取表头 {len(self._headers)} 列，预览 {len(self._rows)} 行")
        self._rebuild_mapping()

    def _rebuild_mapping(self):
        target_columns = self.context.io.table_columns(self.target_box.currentData())
        self.mapping.setRowCount(len(self._headers))
        for row, header in enumerate(self._headers):
            self.mapping.setItem(row, 0, QTableWidgetItem(str(header)))
            box = QComboBox()
            box.addItem("不导入", None)
            for column in target_columns:
                box.addItem(column, column)
            index = box.findData(header)
            if index >= 0:
                box.setCurrentIndex(index)
            self.mapping.setCellWidget(row, 1, box)
        self.mapping.resizeColumnsToContents()

    def do_import(self):
        path = self.file_box.text().strip()
        if not path or not self._headers:
            Notifier.warn(self, "请先选择并预览导入文件")
            return
        mapping = {}
        for row, header in enumerate(self._headers):
            widget = self.mapping.cellWidget(row, 1)
            target = widget.currentData() if widget else None
            if target:
                mapping[str(header)] = target
        if not mapping:
            Notifier.warn(self, "至少映射一列")
            return
        table = self.target_box.currentData()
        mode = self.mode_box.currentData()
        self.import_button.setEnabled(False)
        self.import_log.setPlainText("正在导入…")
        self.context.runner.run(lambda: self._import_job(path, table, mapping, mode),
                                self._import_ok, self._import_err,
                                lambda: self.import_button.setEnabled(True))

    def _import_job(self, path, table, mapping, mode):
        headers, rows = self.context.io.preview(path, limit=None)
        return self.context.io.import_rows(table, mapping, rows, mode)

    def _import_ok(self, report):
        self._failures = report["failures"]
        self.failure_button.setEnabled(bool(self._failures))
        lines = [f"目标表  : {self.target_box.currentData()}",
                 f"成功写入: {report['inserted']} 行",
                 f"失败    : {report['failed']} 行",
                 f"执行语句: {report['sql']}"]
        for item in self._failures[:20]:
            lines.append(f"  第 {item['row']} 行: {item['error']}")
        self.import_log.setPlainText("\n".join(lines))
        Notifier.success(self, f"导入完成：成功 {report['inserted']} 行，"
                               f"失败 {report['failed']} 行")

    def _import_err(self, code, message):
        self.import_log.setPlainText(
            f"导入失败 [{code}] {message}\n事务已回滚，目标表未发生变化")
        Notifier.error(self, message)

    def export_failures(self):
        if not self._failures:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出失败行", "import_failures.csv",
                                              "CSV 文件 (*.csv)")
        if not path:
            return
        count = self.context.io.export_failures(path, self._failures)
        Notifier.success(self, f"已导出 {count} 条失败记录到 {Path(path).name}")
