"""查询与筛选页：条件构建器 + 服务端分页 + 排序，SQL 由参数化拼装。"""

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from db.dao.meta_dao import ident
from models.table_model import Column
from ui.widgets import DataTable, Notifier, PageBase, Pager

OPERATORS = {
    "=": "=", "<>": "<>", ">": ">", ">=": ">=", "<": "<", "<=": "<=",
    "包含": "LIKE", "不包含": "NOT LIKE", "为空": "IS NULL", "非空": "IS NOT NULL",
    "属于": "IN",
}
NO_VALUE = ("为空", "非空")


class QueryPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "查询与筛选", ("F04", "F08", "F15"),
                         "条件值一律参数化，排序字段走白名单校验；分页由 LIMIT / OFFSET 完成，"
                         "完整语句见下方 SQL 面板。", page_key="query", parent=parent)
        self.conditions = []
        self.source_box = QComboBox()
        self.source_box.setMinimumWidth(240)
        self._fill_sources()
        self.field_box = QComboBox()
        self.field_box.setMinimumWidth(170)
        self.operator_box = QComboBox()
        self.operator_box.addItems(list(OPERATORS))
        self.operator_box.setFixedWidth(110)
        self.value_box = QLineEdit()
        self.value_box.setPlaceholderText("输入条件值；「属于」用英文逗号分隔多个值")
        self.value_box.setMinimumWidth(240)
        self.add_button = QPushButton("添加条件")
        self.add_button.setObjectName("Primary")
        self.run_button = QPushButton("查询")
        self.clear_button = QPushButton("清空条件")
        self.clear_button.setObjectName("Ghost")
        self.add_action(QLabel("数据源"))
        self.add_action(self.source_box)
        self.add_action(self.field_box)
        self.add_action(self.operator_box)
        self.add_action(self.value_box)
        self.add_action(self.add_button)
        self.add_stretch()
        self.add_action(self.clear_button)
        self.add_action(self.run_button)

        self.condition_table = QTableWidget(0, 4)
        self.condition_table.setHorizontalHeaderLabels(["字段", "运算符", "值", "操作"])
        self.condition_table.verticalHeader().setVisible(False)
        self.condition_table.setMaximumHeight(140)
        self.condition_table.horizontalHeader().setStretchLastSection(True)
        self.root.addWidget(self.condition_table)

        order_line = QHBoxLayout()
        order_line.addWidget(QLabel("排序字段"))
        self.order_box = QComboBox()
        self.order_box.setMinimumWidth(190)
        self.direction_box = QComboBox()
        self.direction_box.addItems(["升序", "降序"])
        self.direction_box.setFixedWidth(90)
        self.info_label = QLabel("尚未执行查询")
        self.info_label.setObjectName("HintLabel")
        order_line.addWidget(self.order_box)
        order_line.addWidget(self.direction_box)
        order_line.addStretch(1)
        order_line.addWidget(self.info_label)
        self.root.addLayout(order_line)

        self.table = DataTable()
        self.pager = Pager(page_size=int(context.profile.get("page_size", 20)))
        self.root.addWidget(self.table, 1)
        self.root.addWidget(self.pager)

        self.source_box.currentIndexChanged.connect(self._on_source_changed)
        self.operator_box.currentTextChanged.connect(self._on_operator_changed)
        self.add_button.clicked.connect(self.add_condition)
        self.run_button.clicked.connect(lambda: self.run(reset_page=True))
        self.clear_button.clicked.connect(self.clear_conditions)
        self.value_box.returnPressed.connect(self.add_condition)
        self.pager.pageChanged.connect(lambda page, size: self.run(page, size))
        self._on_source_changed()

    def _fill_sources(self):
        self.sources = self.context.meta.objects()
        for row in self.sources:
            kind = "表" if row["kind"] == "BASE TABLE" else "视图"
            self.source_box.addItem(f"{row['name']}（{kind}）", row["name"])

    def _on_source_changed(self):
        source = self.source_box.currentData()
        self.columns = self.context.meta.columns(source) if source else []
        self.field_box.clear()
        self.order_box.clear()
        self.order_box.addItem("不排序", None)
        for row in self.columns:
            label = (row.get("comment") or "").split("，")[0].strip() or row["name"]
            self.field_box.addItem(f"{row['name']}（{label}）", row["name"])
            self.order_box.addItem(f"{row['name']}（{label}）", row["name"])
        self.clear_conditions()

    def _on_operator_changed(self, text):
        self.value_box.setEnabled(text not in NO_VALUE)

    def add_condition(self):
        field = self.field_box.currentData()
        operator = self.operator_box.currentText()
        value = self.value_box.text().strip()
        if not field:
            return
        if operator not in NO_VALUE and not value:
            Notifier.warn(self, "请先填写条件值")
            return
        self.conditions.append({"field": field, "op": operator,
                                "value": None if operator in NO_VALUE else value})
        self._refresh_condition_table()
        self.value_box.clear()

    def remove_condition(self, index):
        if 0 <= index < len(self.conditions):
            self.conditions.pop(index)
            self._refresh_condition_table()

    def _refresh_condition_table(self):
        self.condition_table.setRowCount(len(self.conditions))
        for row, condition in enumerate(self.conditions):
            self.condition_table.setItem(row, 0, QTableWidgetItem(condition["field"]))
            self.condition_table.setItem(row, 1, QTableWidgetItem(condition["op"]))
            self.condition_table.setItem(row, 2, QTableWidgetItem(
                condition["value"] if condition["value"] is not None else "—"))
            button = QPushButton("移除")
            button.setObjectName("Ghost")
            button.clicked.connect(lambda _=False, index=row: self.remove_condition(index))
            self.condition_table.setCellWidget(row, 3, button)
        self.condition_table.resizeColumnsToContents()

    def clear_conditions(self):
        self.conditions = []
        self._refresh_condition_table()
        self.table.set_rows([], "尚未执行查询", "添加条件后点击「查询」，或直接查询全表")
        self.pager.update_state(0, 1, self.pager.page_size)
        self.info_label.setText("尚未执行查询")

    def _build(self):
        source = ident(self.source_box.currentData())
        clauses, params = [], []
        for condition in self.conditions:
            column = ident(condition["field"])
            operator = OPERATORS[condition["op"]]
            if operator in ("IS NULL", "IS NOT NULL"):
                clauses.append(f"{column} {operator}")
            elif operator == "IN":
                values = [item.strip() for item in str(condition["value"]).split(",") if item.strip()]
                if not values:
                    continue
                clauses.append(f"{column} IN ({', '.join(['%s'] * len(values))})")
                params.extend(values)
            elif operator in ("LIKE", "NOT LIKE"):
                clauses.append(f"{column} {operator} %s")
                params.append(f"%{condition['value']}%")
            else:
                clauses.append(f"{column} {operator} %s")
                params.append(condition["value"])
        where = " AND ".join(clauses) if clauses else "1 = 1"
        order_field = self.order_box.currentData()
        direction = "DESC" if self.direction_box.currentText() == "降序" else "ASC"
        order = f"ORDER BY {ident(order_field)} {direction}" if order_field else ""
        return source, where, tuple(params), order

    def run(self, page=1, page_size=None):
        page_size = int(page_size or self.pager.page_size)
        source, where, params, order = self._build()
        offset = max(0, (int(page) - 1) * page_size)
        self.set_busy(True, "正在执行查询…")
        self.context.runner.run(
            lambda: self._execute(source, where, params, order, page_size, offset),
            self._apply, lambda code, message: Notifier.error(self, f"[{code}] {message}"),
            lambda: self.set_busy(False))

    def _execute(self, source, where, params, order, page_size, offset):
        total = int(self.context.db.scalar(
            f"SELECT COUNT(*) FROM {source} WHERE {where}", params,
            source="查询: 计数") or 0)
        sql = f"SELECT * FROM {source} WHERE {where} {order} LIMIT %s OFFSET %s"
        rows = self.context.db.query(sql, params + (page_size, offset), source="查询: 分页结果")
        return rows, total

    def _apply(self, payload):
        rows, total = payload
        if rows:
            columns = [Column(key, self._label_for(key),
                              150 if isinstance(rows[0].get(key), str) else 120) for key in rows[0]]
            self.table.set_columns(columns)
        self.table.set_rows(rows, "查询没有命中任何记录", "放宽条件或清空条件后重试")
        self.pager.update_state(total, self.pager.page if total else 1, self.pager.page_size)
        self.info_label.setText(f"命中 {total} 条 · 条件 {len(self.conditions)} 个 · "
                                f"当前页 {len(rows)} 条")
        self.emit_status(f"查询命中 {total} 条记录")

    def _label_for(self, key):
        for row in self.columns:
            if row["name"] == key:
                return (row.get("comment") or "").split("，")[0].strip() or key
        return key
