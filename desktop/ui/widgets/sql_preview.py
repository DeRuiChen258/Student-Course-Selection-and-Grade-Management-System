"""SQL 预览面板：展示 DatabaseManager 记录的每一条真实执行语句。"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)


class SqlPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._traces = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        top = QHBoxLayout()
        self.caption = QLabel("每次操作的真实 SQL（参数已内联显示）")
        self.caption.setObjectName("HintLabel")
        self.copy_button = QPushButton("复制 SQL")
        self.copy_button.setObjectName("Ghost")
        self.copy_button.setFixedHeight(26)
        self.copy_button.clicked.connect(self._copy)
        self.compare_button = QPushButton("EXPLAIN 对比")
        self.compare_button.setObjectName("Ghost")
        self.compare_button.setFixedHeight(26)
        self.compare_button.setVisible(False)
        top.addWidget(self.caption)
        top.addStretch(1)
        top.addWidget(self.compare_button)
        top.addWidget(self.copy_button)
        layout.addLayout(top)
        body = QHBoxLayout()
        body.setSpacing(8)
        self.history = QListWidget()
        self.history.setFixedWidth(280)
        self.history.currentRowChanged.connect(self._show_row)
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(QFont("JetBrains Mono, Consolas, monospace", 10))
        self.editor.setPlaceholderText("执行任意查询后，这里显示数据库真正收到的语句")
        body.addWidget(self.history)
        body.addWidget(self.editor, 1)
        layout.addLayout(body)
        self.meta = QLabel("等待执行…")
        self.meta.setObjectName("HintLabel")
        layout.addWidget(self.meta)

    def add_trace(self, trace):
        self._traces.append(trace)
        prefix = "✔" if trace.ok else "✘"
        item = QListWidgetItem(f"{prefix} {trace.at} · {trace.elapsed_ms} ms · "
                               f"{' '.join(trace.sql.split())[:46]}")
        item.setData(Qt.UserRole, trace)
        item.setToolTip(trace.source or trace.sql)
        self.history.insertItem(0, item)
        while self.history.count() > 120:
            self.history.takeItem(self.history.count() - 1)
        self.history.setCurrentRow(0)

    def _show_row(self, row):
        if row < 0:
            return
        item = self.history.item(row)
        trace = item.data(Qt.UserRole)
        if trace is None:
            return
        self.editor.setPlainText(trace.rendered())
        state = "成功" if trace.ok else f"失败：{trace.error}"
        self.meta.setText(f"#{trace.seq} · {trace.at} · {trace.source or '未标注'} · "
                          f"返回 {trace.rows} 行 · 耗时 {trace.elapsed_ms} ms · {state}")

    def _copy(self):
        QGuiApplication.clipboard().setText(self.editor.toPlainText())
        self.meta.setText("已复制到剪贴板")
