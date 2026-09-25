"""统一提示组件：Toast 非阻塞提示与 Notifier 弹窗。"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QMessageBox

LEVEL_STYLE = {
    "info": ("#2563EB", "#EFF6FF"),
    "success": ("#16A34A", "#F0FDF4"),
    "warn": ("#D97706", "#FFFBEB"),
    "error": ("#DC2626", "#FEF2F2"),
}


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setMaximumWidth(520)
        self.setVisible(False)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text, level="info", timeout=3600):
        border, background = LEVEL_STYLE.get(level, LEVEL_STYLE["info"])
        self.setStyleSheet(
            f"#Toast {{ background: {background}; border: 1px solid {border};"
            f" border-left: 4px solid {border}; border-radius: 6px;"
            f" padding: 10px 14px; color: #111827; }}")
        self.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        if parent:
            self.move(parent.width() - self.width() - 28, parent.height() - self.height() - 28)
        self.setVisible(True)
        self.raise_()
        self._timer.start(timeout)


class Notifier:
    @staticmethod
    def _toast(parent, text, level):
        window = parent.window() if parent is not None else None
        if window is None:
            return
        toast = getattr(window, "_toast", None)
        if toast is None:
            toast = Toast(window)
            window._toast = toast
        toast.show_message(text, level)

    @staticmethod
    def info(parent, text):
        Notifier._toast(parent, text, "info")

    @staticmethod
    def success(parent, text):
        Notifier._toast(parent, text, "success")

    @staticmethod
    def warn(parent, text):
        Notifier._toast(parent, text, "warn")

    @staticmethod
    def error(parent, text):
        Notifier._toast(parent, text, "error")

    @staticmethod
    def confirm(parent, title, text, detail="", danger=False):
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Warning if danger else QMessageBox.Question)
        box.setText(text)
        if detail:
            box.setInformativeText(detail)
        yes = box.addButton("确认执行", QMessageBox.AcceptRole)
        cancel = box.addButton("取消", QMessageBox.RejectRole)
        box.setDefaultButton(cancel)
        box.exec()
        return box.clickedButton() is yes

    @staticmethod
    def alert(parent, title, text, detail="", level="info"):
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        icons = {"info": QMessageBox.Information, "warn": QMessageBox.Warning,
                 "error": QMessageBox.Critical}
        box.setIcon(icons.get(level, QMessageBox.Information))
        box.setText(text)
        if detail:
            box.setDetailedText(detail)
        box.addButton("知道了", QMessageBox.AcceptRole)
        box.exec()
