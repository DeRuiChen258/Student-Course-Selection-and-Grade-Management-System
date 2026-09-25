"""页面基类与页头：页头显式标注 F 编号。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from app.labels import func_text
from .busy import BusyOverlay
from .message import Notifier


class PageHeader(QWidget):
    def __init__(self, title, funcs=(), subtitle="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("PageTitle")
        top.addWidget(self.title_label)
        for code in funcs:
            chip = QLabel(func_text(code))
            chip.setObjectName("FuncChip")
            chip.setToolTip(func_text(code))
            top.addWidget(chip)
        top.addStretch(1)
        layout.addLayout(top)
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("PageSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        layout.addWidget(self.subtitle_label)

    def set_subtitle(self, text):
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))


class PageBase(QWidget):
    statusMessage = Signal(str)
    rowSelected = Signal(dict, dict)

    def __init__(self, context, title, funcs=(), subtitle="", page_key="", parent=None):
        super().__init__(parent)
        self.context = context
        self.page_key = page_key
        self.setObjectName("PageRoot")
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(20, 16, 20, 16)
        self.root.setSpacing(12)
        self.header = PageHeader(title, funcs, subtitle)
        self.root.addWidget(self.header)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        self.action_bar = QFrame()
        self.action_bar.setLayout(self.actions)
        self.action_bar.setVisible(False)
        self.root.addWidget(self.action_bar)
        self.busy = BusyOverlay(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def add_action(self, widget, align_left=False):
        self.action_bar.setVisible(True)
        if align_left:
            self.actions.addWidget(widget)
        else:
            self.actions.addWidget(widget)
        return widget

    def add_stretch(self):
        self.actions.addStretch(1)

    def on_enter(self, **_):
        pass

    def set_busy(self, busy, text="正在查询…"):
        if busy:
            self.busy.show_busy(text)
        else:
            self.busy.hide_busy()

    def notify(self, text, level="info"):
        Notifier._toast(self, text, level)
        self.statusMessage.emit(text)

    def emit_status(self, text):
        self.statusMessage.emit(text)
