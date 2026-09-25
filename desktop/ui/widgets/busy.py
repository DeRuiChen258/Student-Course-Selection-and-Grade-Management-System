"""页面级忙指示：遮罩 + 不确定进度条。"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class BusyOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("BusyOverlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        self.label = QLabel("正在查询…")
        self.label.setObjectName("BusyText")
        self.label.setAlignment(Qt.AlignCenter)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setFixedWidth(220)
        self.bar.setTextVisible(False)
        layout.addWidget(self.label)
        layout.addWidget(self.bar, 0, Qt.AlignHCenter)
        self.setVisible(False)
        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() == QEvent.Resize:
            self.setGeometry(self.parentWidget().rect())
        return super().eventFilter(obj, event)

    def show_busy(self, text="正在查询…"):
        self.label.setText(text)
        self.setGeometry(self.parentWidget().rect())
        self.setVisible(True)
        self.raise_()

    def hide_busy(self):
        self.setVisible(False)
