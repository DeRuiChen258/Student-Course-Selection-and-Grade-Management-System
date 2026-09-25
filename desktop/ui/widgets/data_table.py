"""数据表格：统一列宽、选择行为与空状态切换。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QStackedLayout, QTableView,
                               QWidget)

from models.table_model import DictTableModel
from .empty_state import EmptyState


class DataTable(QWidget):
    rowActivated = Signal(dict)
    selectionChanged = Signal(object)

    def __init__(self, columns=None, parent=None):
        super().__init__(parent)
        self.model = DictTableModel(columns or [])
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setSortingEnabled(True)
        self.view.verticalHeader().setDefaultSectionSize(30)
        self.view.verticalHeader().setVisible(False)
        self.view.setWordWrap(False)
        self.view.doubleClicked.connect(self._on_double_click)
        self.view.selectionModel().selectionChanged.connect(self._on_selection)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.empty = EmptyState()
        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.view)
        self.stack.addWidget(self.empty)
        self.set_columns(columns or [])

    def set_columns(self, columns):
        self.model.columns = list(columns)
        if columns:
            self.model.beginResetModel()
            self.model.endResetModel()
        header = self.view.horizontalHeader()
        for index, column in enumerate(columns):
            self.view.setColumnWidth(index, column.width)
            header.setSectionResizeMode(index, QHeaderView.Interactive)

    def set_rows(self, rows, empty_title="没有匹配的记录", empty_hint="调整筛选条件后重试"):
        self.model.set_rows(rows)
        if rows:
            self.stack.setCurrentWidget(self.view)
        else:
            self.empty.update_text(empty_title, empty_hint)
            self.stack.setCurrentWidget(self.empty)

    def rows(self):
        return self.model.rows()

    def selected_row(self):
        indexes = self.view.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.row_at(indexes[0])

    def selected_rows(self):
        return [self.model.row_at(index) for index in self.view.selectionModel().selectedRows()]

    def select_first(self):
        if self.model.rowCount():
            self.view.selectRow(0)

    def _on_double_click(self, index):
        row = self.model.row_at(index)
        if row:
            self.rowActivated.emit(row)

    def _on_selection(self, *_):
        self.selectionChanged.emit(self.selected_row())
