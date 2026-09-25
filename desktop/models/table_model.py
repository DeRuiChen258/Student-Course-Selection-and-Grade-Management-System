"""基于字典行的通用表格模型，供所有列表页复用。"""

from dataclasses import dataclass
from decimal import Decimal

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from utils.formatters import fmt_value


@dataclass
class Column:
    key: str
    label: str
    width: int = 120
    align: str = "left"
    fmt: str = "text"

    def alignment(self):
        mapping = {
            "left": Qt.AlignLeft | Qt.AlignVCenter,
            "right": Qt.AlignRight | Qt.AlignVCenter,
            "center": Qt.AlignHCenter | Qt.AlignVCenter,
        }
        return mapping.get(self.align, Qt.AlignLeft | Qt.AlignVCenter)


def _sort_key(value):
    if value is None:
        return (2, 0)
    if isinstance(value, (int, float, Decimal)):
        return (0, float(value))
    return (1, str(value))


class DictTableModel(QAbstractTableModel):
    def __init__(self, columns, rows=None, parent=None):
        super().__init__(parent)
        self.columns = list(columns)
        self._rows = list(rows or [])

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows or [])
        self.endResetModel()

    def row_at(self, index):
        if not index or not index.isValid():
            return None
        row = index.row()
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def rows(self):
        return list(self._rows)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        column = self.columns[index.column()]
        value = self._rows[index.row()].get(column.key)
        if role == Qt.DisplayRole:
            return fmt_value(value, column.fmt)
        if role == Qt.TextAlignmentRole:
            return column.alignment()
        if role == Qt.ToolTipRole:
            return None if value is None else str(value)
        if role == Qt.UserRole:
            return value
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.columns[section].label
        return section + 1

    def sort(self, column_index, order=Qt.AscendingOrder):
        if not self.columns:
            return
        key = self.columns[column_index].key
        self.beginResetModel()
        self._rows.sort(key=lambda row: _sort_key(row.get(key)),
                        reverse=order == Qt.DescendingOrder)
        self.endResetModel()

    def export_matrix(self):
        headers = [column.label for column in self.columns]
        rows = [[row.get(column.key) for column in self.columns] for row in self._rows]
        return headers, rows
