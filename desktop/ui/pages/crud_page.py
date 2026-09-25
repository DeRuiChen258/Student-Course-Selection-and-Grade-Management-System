"""通用实体列表页：筛选 + 分页 + 新增 / 编辑 / 删除 / 导出（F01–F10 复用）。"""

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ui.dialogs.entity_form_dialog import EntityFormDialog
from ui.widgets import DataTable, FilterBar, Notifier, PageBase, Pager


class EntityListPage(PageBase):
    def __init__(self, context, spec, parent=None):
        super().__init__(context, spec.title, spec.funcs, spec.subtitle,
                         page_key=spec.key, parent=parent)
        self.spec = spec
        self.filter_bar = FilterBar(context)
        self.filter_bar.build(spec.filters, spec.key)
        self.root.insertWidget(2, self.filter_bar)
        self.table = DataTable(spec.columns)
        self.pager = Pager(page_size=int(context.profile.get("page_size", 20)))
        self.root.addWidget(self.table, 1)
        self.root.addWidget(self.pager)
        self._build_actions()
        self.filter_bar.changed.connect(self.on_filters_changed)
        self.pager.pageChanged.connect(self._on_page_changed)
        self.table.selectionChanged.connect(self._on_selection)
        self.table.rowActivated.connect(lambda _: self.edit())
        self._rows = []

    def _build_actions(self):
        self.add_button = QPushButton("新增")
        self.add_button.setObjectName("Primary")
        self.edit_button = QPushButton("编辑")
        self.delete_button = QPushButton("删除")
        self.batch_button = QPushButton("批量删除")
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Ghost")
        self.export_button = QPushButton("导出结果")
        self.export_button.setObjectName("Ghost")
        self.count_label = QLabel("")
        self.count_label.setObjectName("HintLabel")
        for button in (self.add_button, self.edit_button, self.delete_button,
                       self.batch_button):
            self.add_action(button)
        self.add_stretch()
        self.add_action(self.count_label)
        for button in (self.refresh_button, self.export_button):
            self.add_action(button)
        self.add_button.clicked.connect(self.create)
        self.edit_button.clicked.connect(self.edit)
        self.delete_button.clicked.connect(self.delete)
        self.batch_button.clicked.connect(self.batch_delete)
        self.refresh_button.clicked.connect(lambda: self.reload(reset_page=True))
        self.export_button.clicked.connect(self.export_rows)
        role_create = self.context.can_do("create")
        self.add_button.setEnabled(role_create)
        self.edit_button.setEnabled(self.context.can_do("update"))
        self.delete_button.setEnabled(self.context.can_do("delete"))
        self.batch_button.setEnabled(self.context.can_do("delete"))
        self.add_button.setToolTip(f"当前角色 {self.context.role_label}："
                                   f"{'允许新增' if role_create else '不允许新增'}")

    def on_enter(self, **kwargs):
        if kwargs.get("filters"):
            self.filter_bar.set_values(kwargs["filters"])
        self.reload(reset_page=kwargs.get("reset", True))

    def on_filters_changed(self, _values):
        self.pager.reset()
        self.reload()

    def _on_page_changed(self, page, size):
        self.load(page, size)

    def reload(self, reset_page=False):
        if reset_page:
            self.pager.reset()
        self.load(self.pager.page, self.pager.page_size)

    def load(self, page, page_size):
        filters = self.filter_bar.values()
        self.set_busy(True, f"正在查询 {self.spec.table}…")
        self.context.runner.run(
            lambda: self.context.entities.page(self.spec.key, filters, page, page_size),
            self._on_loaded, self._on_error, lambda: self.set_busy(False))

    def _on_loaded(self, result):
        rows, total = result
        self._rows = rows
        self.table.set_rows(rows, f"{self.spec.title}没有匹配记录",
                            "调整筛选条件，或点击「新增」录入一条数据")
        self.pager.update_state(total, self.pager.page, self.pager.page_size)
        self.count_label.setText(f"命中 {total} 条 · 当前页 {len(rows)} 条")
        self.emit_status(f"{self.spec.title}：命中 {total} 条记录")

    def _on_error(self, code, message):
        Notifier.error(self, f"[{code}] {message}")
        self.table.set_rows([], "查询失败", message)

    def _on_selection(self, row):
        if row:
            self.rowSelected.emit(row, {"table": self.spec.table, "pk": self.spec.pk,
                                        "title": self.spec.title})

    def create(self):
        dialog = EntityFormDialog(self.context, self.spec, "create", parent=self)
        if dialog.exec():
            Notifier.success(self, f"新增成功：{self.spec.title}")
            self.reload(reset_page=True)

    def edit(self):
        row = self.table.selected_row()
        if not row:
            Notifier.warn(self, "请先在列表中选择一行")
            return
        dialog = EntityFormDialog(self.context, self.spec, "edit", row, parent=self)
        if dialog.exec():
            Notifier.success(self, "修改成功，可在 SQL 面板查看实际 UPDATE 语句")
            self.reload()

    def delete(self):
        row = self.table.selected_row()
        if not row:
            Notifier.warn(self, "请先选择要删除的行")
            return
        note = self.spec.delete_note.format(**row) if self.spec.delete_note else ""
        title = row.get(self.spec.biz_key) or row.get(self.spec.pk)
        if not Notifier.confirm(self, f"删除 {self.spec.title}",
                                f"确认删除 {self.spec.title}「{title}」？", note, danger=True):
            return
        pk_value = row.get(self.spec.pk)
        self.context.runner.run(
            lambda: self.context.entities.delete(self.spec.key, pk_value),
            self._on_deleted, self._on_delete_error)

    def _on_deleted(self, affected):
        Notifier.success(self, f"删除成功，影响 {affected} 行（触发器已写入审计日志）")
        self.reload()

    def _on_delete_error(self, code, message):
        Notifier.error(self, f"删除失败 [{code}] {message}")
        Notifier._toast(self, message, "error")

    def batch_delete(self):
        rows = self.table.selected_rows()
        if len(rows) < 2:
            Notifier.warn(self, "批量删除需要先选中多行（Ctrl / Shift 多选）")
            return
        keys = [row.get(self.spec.pk) for row in rows]
        if not Notifier.confirm(self, "批量删除",
                                f"确认删除选中的 {len(keys)} 条记录？",
                                "所有记录在同一事务内删除，任一条失败则整体回滚",
                                danger=True):
            return
        self.context.runner.run(
            lambda: self.context.entities.delete_many(self.spec.key, keys),
            lambda affected: (Notifier.success(self, f"批量删除完成，影响 {affected} 行"),
                              self.reload()),
            self._on_delete_error)

    def export_rows(self):
        rows = self._rows
        if not rows:
            Notifier.warn(self, "当前没有可导出的数据")
            return
        path, selected = QFileDialog.getSaveFileName(
            self, "导出查询结果", f"{self.spec.table}.csv",
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;JSON 文件 (*.json)")
        if not path:
            return
        fmt = "csv"
        if path.endswith(".xlsx") or "Excel" in selected:
            fmt = "xlsx"
            if not path.endswith(".xlsx"):
                path += ".xlsx"
        elif path.endswith(".json") or "JSON" in selected:
            fmt = "json"
        columns = [(column.label, column.key) for column in self.spec.columns]
        count = self.context.io.export(path, columns, rows, fmt, self.spec.table)
        Notifier.success(self, f"已导出当前页 {count} 行到 {path}")
