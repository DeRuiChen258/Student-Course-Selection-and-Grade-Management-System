"""分页条：服务端 LIMIT / OFFSET 分页的唯一入口。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QWidget)


class Pager(QWidget):
    pageChanged = Signal(int, int)

    def __init__(self, page_size=20, parent=None):
        super().__init__(parent)
        self._total = 0
        self._page = 1
        self._page_size = int(page_size)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        self.summary = QLabel("共 0 条记录")
        self.summary.setObjectName("PagerSummary")
        self.first = QPushButton("首页")
        self.prev = QPushButton("上一页")
        self.next = QPushButton("下一页")
        self.last = QPushButton("末页")
        for button in (self.first, self.prev, self.next, self.last):
            button.setObjectName("Ghost")
            button.setFixedHeight(28)
        self.jump = QSpinBox()
        self.jump.setRange(1, 1)
        self.jump.setFixedWidth(72)
        self.page_label = QLabel("1")
        self.size_box = QComboBox()
        self.size_box.addItems(["10", "20", "50", "100"])
        self.size_box.setCurrentText(str(page_size))
        self.size_box.setFixedWidth(72)
        layout.addWidget(self.summary)
        layout.addStretch(1)
        layout.addWidget(self.first)
        layout.addWidget(self.prev)
        layout.addWidget(self.jump)
        layout.addWidget(QLabel("/"))
        layout.addWidget(self.page_label)
        layout.addWidget(self.next)
        layout.addWidget(self.last)
        layout.addSpacing(10)
        layout.addWidget(QLabel("每页"))
        layout.addWidget(self.size_box)

        self.first.clicked.connect(lambda: self.go_to(1))
        self.prev.clicked.connect(lambda: self.go_to(self._page - 1))
        self.next.clicked.connect(lambda: self.go_to(self._page + 1))
        self.last.clicked.connect(lambda: self.go_to(self.page_count()))
        self.jump.editingFinished.connect(lambda: self.go_to(self.jump.value()))
        self.size_box.currentTextChanged.connect(self._on_size_changed)

    def page_count(self):
        if not self._total:
            return 1
        return max(1, (self._total + self._page_size - 1) // self._page_size)

    def _on_size_changed(self, text):
        self._page_size = int(text)
        self._page = 1
        self.pageChanged.emit(self._page, self._page_size)

    def go_to(self, page):
        page = max(1, min(int(page), self.page_count()))
        if page == self._page:
            self.jump.setValue(self._page)
            return
        self._page = page
        self.pageChanged.emit(self._page, self._page_size)

    def reset(self):
        self._page = 1

    def update_state(self, total, page, page_size):
        self._total = int(total or 0)
        self._page_size = int(page_size)
        self._page = max(1, int(page))
        pages = self.page_count()
        self.summary.setText(f"共 {self._total} 条记录")
        self.page_label.setText(str(pages))
        self.jump.setRange(1, pages)
        self.jump.setValue(self._page)
        self.first.setEnabled(self._page > 1)
        self.prev.setEnabled(self._page > 1)
        self.next.setEnabled(self._page < pages)
        self.last.setEnabled(self._page < pages)
        if self.size_box.currentText() != str(self._page_size):
            self.size_box.blockSignals(True)
            self.size_box.setCurrentText(str(self._page_size))
            self.size_box.blockSignals(False)

    @property
    def page(self):
        return self._page

    @property
    def page_size(self):
        return self._page_size
