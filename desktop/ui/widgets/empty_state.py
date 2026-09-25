"""空状态占位：无数据、无结果、未连接时统一呈现。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyState(QWidget):
    def __init__(self, title="暂无数据", hint="", action_text=None, parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        self.icon = QLabel("□")
        self.icon.setObjectName("EmptyIcon")
        self.icon.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("EmptyTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName("EmptyHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.button = QPushButton(action_text or "")
        self.button.setObjectName("Primary")
        self.button.setVisible(bool(action_text))
        self.button.setMaximumWidth(200)
        layout.addWidget(self.icon)
        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)
        layout.addSpacing(4)
        layout.addWidget(self.button, 0, Qt.AlignHCenter)

    def update_text(self, title=None, hint=None):
        if title is not None:
            self.title_label.setText(title)
        if hint is not None:
            self.hint_label.setText(hint)
