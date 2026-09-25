"""筛选条：按 FilterSpec 动态生成控件，条件变化后防抖触发查询。"""

from PySide6.QtCore import QDate, QTimer, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget)


class FilterBar(QWidget):
    changed = Signal(dict)

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self._fields = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(350)
        self._debounce.timeout.connect(self.emit_changed)
        self.apply_button = QPushButton("查询")
        self.apply_button.setObjectName("Primary")
        self.reset_button = QPushButton("重置")

    def build(self, specs, entity_key=None):
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._fields = []
        for spec in specs:
            label = QLabel(spec.label)
            label.setObjectName("FilterLabel")
            widget = self._make_widget(spec, entity_key)
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setSpacing(4)
            holder_layout.addWidget(label)
            holder_layout.addWidget(widget)
            self._layout.addWidget(holder)
            self._fields.append((spec, widget))
            if spec.kind == "date" and isinstance(widget, QWidget) and widget.property("date_edit"):
                date_edit = widget.findChild(QDateEdit)
                if date_edit:
                    date_edit.dateChanged.connect(self._debounce.start)
                    check = widget.findChild(QCheckBox)
                    if check:
                        check.toggled.connect(self._debounce.start)
        self._layout.addStretch(1)
        self._layout.addWidget(self.apply_button)
        self._layout.addWidget(self.reset_button)
        self.apply_button.clicked.connect(self.emit_changed)
        self.reset_button.clicked.connect(self.reset)

    def _make_widget(self, spec, entity_key=None):
        if spec.kind == "combo":
            combo = QComboBox()
            combo.setFixedWidth(spec.width)
            combo.addItem("全部", None)
            if spec.choices:
                for choice in spec.choices:
                    combo.addItem(str(choice), choice)
            elif spec.source:
                for row in self.context.entities.lookup(spec.source):
                    combo.addItem(str(row.get("label", row.get("id"))), row.get("id"))
            combo.currentIndexChanged.connect(self._debounce.start)
            return combo
        if spec.kind == "date":
            holder = QWidget()
            holder.setProperty("date_edit", True)
            layout = QHBoxLayout(holder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            check = QCheckBox()
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setDate(QDate.currentDate())
            date_edit.setFixedWidth(spec.width)
            date_edit.setEnabled(False)
            check.toggled.connect(date_edit.setEnabled)
            layout.addWidget(check)
            layout.addWidget(date_edit)
            return holder
        line = QLineEdit()
        line.setClearButtonEnabled(True)
        line.setFixedWidth(max(spec.width, 150))
        line.textChanged.connect(self._debounce.start)
        line.returnPressed.connect(self.emit_changed)
        return line

    def values(self):
        result = {}
        for spec, widget in self._fields:
            if spec.kind == "combo":
                value = widget.currentData()
            elif spec.kind == "date":
                check = widget.findChild(QCheckBox)
                date_edit = widget.findChild(QDateEdit)
                value = date_edit.date().toString("yyyy-MM-dd") if check.isChecked() else None
            else:
                value = widget.text().strip()
            if value not in (None, ""):
                result[spec.name] = value
        return result

    def set_values(self, values):
        values = values or {}
        for spec, widget in self._fields:
            value = values.get(spec.name)
            if spec.kind == "combo":
                index = widget.findData(value)
                widget.setCurrentIndex(index if index >= 0 else 0)
            elif spec.kind == "date":
                check = widget.findChild(QCheckBox)
                date_edit = widget.findChild(QDateEdit)
                check.setChecked(bool(value))
                if value:
                    date_edit.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))
            else:
                widget.setText("" if value is None else str(value))

    def reset(self):
        for spec, widget in self._fields:
            if spec.kind == "combo":
                widget.setCurrentIndex(0)
            elif spec.kind == "date":
                check = widget.findChild(QCheckBox)
                check.setChecked(False)
            else:
                widget.blockSignals(True)
                widget.clear()
                widget.blockSignals(False)
        self.emit_changed()

    def start(self):
        self._debounce.start()

    def emit_changed(self):
        self.changed.emit(self.values())
