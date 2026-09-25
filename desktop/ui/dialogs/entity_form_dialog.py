"""实体表单对话框：由 EntitySpec 动态生成控件，负责校验与落库。"""

import datetime as dt

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QDialog, QDoubleSpinBox,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from ui.widgets import Notifier


class EntityFormDialog(QDialog):
    def __init__(self, context, spec, mode="create", row=None, parent=None):
        super().__init__(parent)
        self.context = context
        self.spec = spec
        self.mode = mode
        self.row = row or {}
        self.current = None
        self._getters = {}
        self._widgets = {}
        self.pending_values = None
        title = "新增" if mode == "create" else "编辑"
        self.setWindowTitle(f"{title} · {spec.title}")
        self.resize(620, 620)
        root = QVBoxLayout(self)
        root.setSpacing(10)
        head = QLabel(f"{title}{spec.title}")
        head.setObjectName("DialogTitle")
        root.addWidget(head)
        hint = QLabel("字段顺序与约束来自 information_schema；提交后可在 SQL 面板查看"
                      "真实执行的 INSERT / UPDATE 语句。")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form = QFormLayout(container)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        comments = {}
        try:
            comments = context.meta.columns_meta(spec.table)
        except Exception:
            comments = {}
        for field in spec.fields:
            widget = self._make_widget(field)
            self._widgets[field.name] = widget
            label = field.label + (" *" if field.required else "")
            meta = comments.get(field.name) or {}
            tooltip = "；".join(filter(None, [
                meta.get("type", ""), meta.get("comment", ""),
                "主键" if meta.get("key_type") == "PRI" else "",
                "不允许为空" if meta.get("nullable") == "NO" else "允许为空",
            ]))
            label_widget = QLabel(label)
            if tooltip:
                label_widget.setToolTip(tooltip)
                widget.setToolTip(tooltip)
            self.form.addRow(label_widget, widget)
        if mode == "edit":
            self._load_current()

        self.error = QLabel("")
        self.error.setObjectName("ErrorText")
        self.error.setWordWrap(True)
        self.error.setVisible(False)
        root.addWidget(self.error)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("Ghost")
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("Primary")
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)
        root.addLayout(buttons)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.submit)

    def _make_widget(self, field):
        kind = field.kind
        if kind == "int":
            box = QSpinBox()
            box.setRange(int(field.minimum if field.minimum is not None else -999999),
                         int(field.maximum if field.maximum is not None else 999999))
            if field.default is not None:
                box.setValue(int(field.default))
            self._getters[field.name] = box.value
            return box
        if kind == "decimal":
            box = QDoubleSpinBox()
            box.setDecimals(field.decimals)
            box.setRange(float(field.minimum if field.minimum is not None else -999999),
                         float(field.maximum if field.maximum is not None else 999999))
            box.setSingleStep(0.5)
            if field.default is not None:
                box.setValue(float(field.default))
            self._getters[field.name] = box.value
            return box
        if kind == "enum":
            box = QComboBox()
            for choice in field.choices:
                box.addItem(str(choice), choice)
            if field.default:
                box.setCurrentText(str(field.default))
            self._getters[field.name] = box.currentData
            return box
        if kind == "fk":
            box = QComboBox()
            box.addItem("请选择…", None)
            for option in self.context.entities.fk_options(self.spec, field.name):
                box.addItem(str(option.get("label")), option.get("id"))
            self._getters[field.name] = box.currentData
            return box
        if kind == "date":
            return self._make_date_widget(field)
        line = QLineEdit()
        if field.maxlen:
            line.setMaxLength(field.maxlen)
        if field.hint:
            line.setPlaceholderText(field.hint)
        if field.default:
            line.setText(str(field.default))
        self._getters[field.name] = lambda: line.text().strip()
        return line

    def _make_date_widget(self, field):
        holder = QWidget()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("yyyy-MM-dd")
        edit.setDate(QDate.currentDate())
        check = None
        if not field.required:
            check = QCheckBox("填写")
            edit.setEnabled(False)
            check.toggled.connect(edit.setEnabled)
            layout.addWidget(check)
        layout.addWidget(edit, 1)
        self._getters[field.name] = (
            lambda: edit.date().toString("yyyy-MM-dd")
            if (check is None or check.isChecked()) else None)
        holder._check = check
        holder._edit = edit
        return holder

    def _load_current(self):
        pk_value = self.row.get(self.spec.pk)
        self.current = self.context.entities.get(self.spec.key, pk_value) if pk_value else dict(self.row)
        self._fill(self.current)

    def _fill(self, values):
        for field in self.spec.fields:
            value = values.get(field.name)
            widget = self._widgets[field.name]
            if field.kind in ("int", "decimal"):
                if value is not None:
                    widget.setValue(float(value) if field.kind == "decimal" else int(value))
            elif field.kind in ("enum", "fk"):
                index = widget.findData(value) if field.kind == "fk" else widget.findText(str(value or ""))
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif field.kind == "date":
                if value:
                    date = value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value)[:10])
                    widget._edit.setDate(QDate(date.year, date.month, date.day))
                    if widget._check is not None:
                        widget._check.setChecked(True)
            else:
                widget.setText("" if value is None else str(value))
        if self.spec.key in ("student", "teacher"):
            for name in (self.spec.biz_key,):
                widget = self._widgets.get(name)
                if widget is not None and self.mode == "edit":
                    widget.setReadOnly(True)

    def collect(self):
        return {name: getter() for name, getter in self._getters.items()}

    def _diff_text(self, values):
        lines = []
        for field in self.spec.fields:
            old = (self.current or {}).get(field.name)
            new = values.get(field.name)
            if str(old) != str(new):
                lines.append(f"{field.label}: {old if old is not None else '空'} → "
                             f"{new if new is not None else '空'}")
        return "\n".join(lines)

    def submit(self):
        self.error.setVisible(False)
        values = self.collect()
        if self.mode == "edit" and self._diff_text(values):
            if not Notifier.confirm(self, "确认修改",
                                    f"提交后 {self.spec.table} 表将发生以下变更：",
                                    self._diff_text(values)):
                return
        self.save_button.setEnabled(False)
        self.save_button.setText("保存中…")
        pk_value = self.row.get(self.spec.pk)
        if self.mode == "create":
            runner = lambda: self.context.entities.create(self.spec.key, values)
        else:
            runner = lambda: self.context.entities.update(self.spec.key, pk_value, values,
                                                          self.current)
        self.context.runner.run(runner, self._on_ok, self._on_err, self._on_done)

    def _on_done(self):
        self.save_button.setEnabled(True)
        self.save_button.setText("保存")

    def _on_ok(self, result):
        self.pending_values = result
        self.accept()

    def _on_err(self, code, message):
        self.error.setText(f"[{code}] {message}")
        self.error.setVisible(True)
        Notifier.error(self, message)
