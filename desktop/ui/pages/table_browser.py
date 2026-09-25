"""数据表浏览：数据 / 结构 / 索引 / 外键 / CHECK 五个页签。"""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QTabWidget, QWidget

from app.labels import table_label
from models.table_model import Column
from ui.widgets import DataTable, Notifier, PageBase, Pager


class TableBrowserPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "数据表浏览", ("F04", "F08", "F15"),
                         "结构页签读 information_schema.columns，索引 / 外键 / CHECK 页签分别对应"
                         "statistics、key_column_usage、check_constraints。",
                         page_key="tables", parent=parent)
        self.object_box = QComboBox()
        self.object_box.setMinimumWidth(280)
        self.reload_objects()
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Ghost")
        self.export_button = QPushButton("导出当前页")
        self.export_button.setObjectName("Ghost")
        self.add_action(self.object_box)
        self.add_stretch()
        self.add_action(self.refresh_button)
        self.add_action(self.export_button)
        self.object_box.currentIndexChanged.connect(self.reload)
        self.refresh_button.clicked.connect(self.reload)
        self.export_button.clicked.connect(self.export_rows)

        self.tabs = QTabWidget()
        self.data_table = DataTable()
        data_page = QWidget()
        from PySide6.QtWidgets import QVBoxLayout
        data_layout = QVBoxLayout(data_page)
        data_layout.setContentsMargins(0, 8, 0, 0)
        data_layout.addWidget(self.data_table, 1)
        self.pager = Pager(page_size=int(context.profile.get("page_size", 20)))
        data_layout.addWidget(self.pager)
        self.tabs.addTab(data_page, "数据")
        self.structure_table = DataTable([
            Column("name", "字段", 150), Column("type", "类型", 140),
            Column("nullable", "可空", 60, "center"), Column("key_type", "键", 60, "center"),
            Column("default_value", "默认值", 110), Column("extra", "额外", 130),
            Column("comment", "注释", 300),
        ])
        self.tabs.addTab(self.structure_table, "结构")
        self.index_table = DataTable([
            Column("name", "索引名", 190), Column("columns", "列", 220),
            Column("kind", "类型", 80, "center"), Column("cardinality", "基数", 100, "right",
                                                          "number"),
            Column("note", "说明", 90, "center"),
        ])
        self.tabs.addTab(self.index_table, "索引")
        self.fk_table = DataTable([
            Column("name", "约束名", 200), Column("column_name", "列", 130),
            Column("ref_table", "引用表", 150), Column("ref_column", "引用列", 130),
            Column("delete_rule", "删除规则", 110, "center"),
            Column("update_rule", "更新规则", 110, "center"),
        ])
        self.tabs.addTab(self.fk_table, "外键")
        self.check_table = DataTable([
            Column("name", "约束名", 220), Column("clause", "CHECK 表达式", 520),
        ])
        self.tabs.addTab(self.check_table, "CHECK 约束")
        self.root.addWidget(self.tabs, 1)
        self.pager.pageChanged.connect(lambda page, size: self.load_data(page, size))
        self._rows = []

    def reload_objects(self):
        self.objects = self.context.meta.objects()
        current = self.object_box.currentData()
        self.object_box.blockSignals(True)
        self.object_box.clear()
        for row in self.objects:
            kind = "表" if row["kind"] == "BASE TABLE" else "视图"
            self.object_box.addItem(f"{row['name']}（{kind}）· {table_label(row['name'])}",
                                    row["name"])
        self.object_box.blockSignals(False)
        if current:
            index = self.object_box.findData(current)
            if index >= 0:
                self.object_box.setCurrentIndex(index)

    def on_enter(self, **_):
        self.reload()

    def reload(self):
        table = self.object_box.currentData()
        if not table:
            return
        self.pager.reset()
        self.set_busy(True, f"正在读取 {table}…")
        self.context.runner.run(lambda: self._collect(table), self._apply,
                                lambda code, message: Notifier.error(
                                    self, f"[{code}] {message}"),
                                lambda: self.set_busy(False))

    def _collect(self, table):
        structure = self.context.meta.structure_report(table)
        kind = next((row["kind"] for row in self.objects if row["name"] == table), "BASE TABLE")
        count_sql = f"SELECT COUNT(*) FROM {table}"
        total = int(self.context.db.scalar(count_sql, source=f"计数 {table}") or 0)
        offset = (self.pager.page - 1) * self.pager.page_size
        rows = self.context.db.query(
            f"SELECT * FROM {table} LIMIT %s OFFSET %s",
            (self.pager.page_size, offset), source=f"浏览 {table}")
        return table, kind, structure, rows, total

    def _apply(self, payload):
        table, kind, structure, rows, total = payload
        columns = [Column(row["name"], self._label(kind, row),
                          150 if row["data_type"] in ("varchar", "char", "text") else 120)
                   for row in structure["columns"]]
        self.data_table.set_columns(columns)
        self._rows = rows
        self.data_table.set_rows(rows, f"{table} 暂无数据", "可通过导入向导写入数据")
        self.pager.update_state(total, self.pager.page, self.pager.page_size)
        self.structure_table.set_rows(structure["columns"])
        self.index_table.set_rows(structure["indexes"])
        self.fk_table.set_rows(structure["foreign_keys"], "该表没有外键", "当前对象为独立表或视图")
        self.check_table.set_rows(structure["checks"], "该表没有 CHECK 约束",
                                  "MySQL 8 支持列级与表级 CHECK")
        self.emit_status(f"{table}：{total} 行 · 字段 {len(structure['columns'])} · "
                         f"索引 {len(structure['indexes'])} · 外键 {len(structure['foreign_keys'])}")

    def _label(self, kind, column_row):
        if kind == "VIEW":
            return column_row["name"]
        comment = (column_row.get("comment") or "").split("，")[0].strip()
        return comment or column_row["name"]

    def load_data(self, page, size):
        table = self.object_box.currentData()
        if not table:
            return
        offset = (page - 1) * size
        self.context.runner.run(
            lambda: self.context.db.query(f"SELECT * FROM {table} LIMIT %s OFFSET %s",
                                          (size, offset), source=f"浏览 {table}"),
            lambda rows: (self.data_table.set_rows(rows), self._set_rows_ref(rows)),
            lambda code, message: Notifier.error(self, f"[{code}] {message}"))

    def _set_rows_ref(self, rows):
        self._rows = rows

    def export_rows(self):
        if not self._rows:
            Notifier.warn(self, "当前没有可导出的数据")
            return
        from PySide6.QtWidgets import QFileDialog
        table = self.object_box.currentData()
        path, _ = QFileDialog.getSaveFileName(self, "导出当前页", f"{table}.csv",
                                              "CSV 文件 (*.csv);;Excel 文件 (*.xlsx)")
        if not path:
            return
        fmt = "xlsx" if path.endswith(".xlsx") else "csv"
        columns = [(key, key) for key in self._rows[0].keys()]
        count = self.context.io.export(path, columns, self._rows, fmt, table)
        Notifier.success(self, f"已导出 {count} 行到 {path}")
