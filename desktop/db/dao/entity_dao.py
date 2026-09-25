"""通用实体 CRUD：表名与列名走白名单，值一律参数化。"""

from .base import DaoBase
from .meta_dao import ident


class EntityDao(DaoBase):
    def __init__(self, db, table, pk):
        super().__init__(db)
        self.table = ident(table)
        self.pk = ident(pk)

    def count(self, where="", params=()):
        return int(self.db.scalar(f"SELECT COUNT(*) FROM {self.table} {where}",
                                  tuple(params), source=f"计数 {self.table}") or 0)

    def fetch(self, sql, params=()):
        return self.db.query(sql, tuple(params), source=f"查询 {self.table}")

    def get(self, pk_value):
        return self.db.query_one(
            f"SELECT * FROM {self.table} WHERE {self.pk} = %s",
            (pk_value,), source=f"取单行 {self.table}")

    def insert(self, values):
        cols = [ident(c) for c in values]
        marks = ", ".join(["%s"] * len(cols))
        sql = f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES ({marks})"
        with self.db.transaction(source=f"新增 {self.table}") as tx:
            tx.execute(sql, tuple(values[c] for c in cols))
            new_id = tx.query("SELECT LAST_INSERT_ID() AS id")[0]["id"]
        return int(new_id)

    def update(self, pk_value, values):
        cols = [ident(c) for c in values]
        assignments = ", ".join(f"{c} = %s" for c in cols)
        sql = f"UPDATE {self.table} SET {assignments} WHERE {self.pk} = %s"
        params = tuple(values[c] for c in cols) + (pk_value,)
        with self.db.transaction(source=f"修改 {self.table}") as tx:
            affected = tx.execute(sql, params)
        return int(affected or 0)

    def delete(self, pk_value):
        with self.db.transaction(source=f"删除 {self.table}") as tx:
            affected = tx.execute(f"DELETE FROM {self.table} WHERE {self.pk} = %s", (pk_value,))
        return int(affected or 0)

    def delete_many(self, pk_values):
        pk_values = list(pk_values)
        if not pk_values:
            return 0
        marks = ", ".join(["%s"] * len(pk_values))
        sql = f"DELETE FROM {self.table} WHERE {self.pk} IN ({marks})"
        with self.db.transaction(source=f"批量删除 {self.table}") as tx:
            affected = tx.execute(sql, tuple(pk_values))
        return int(affected or 0)

    def exists(self, column, value, exclude_pk=None):
        col = ident(column)
        if exclude_pk is None:
            sql = f"SELECT COUNT(*) FROM {self.table} WHERE {col} = %s"
            params = (value,)
        else:
            sql = f"SELECT COUNT(*) FROM {self.table} WHERE {col} = %s AND {self.pk} <> %s"
            params = (value, exclude_pk)
        return int(self.db.scalar(sql, params, source=f"唯一性检查 {self.table}.{col}") or 0) > 0
