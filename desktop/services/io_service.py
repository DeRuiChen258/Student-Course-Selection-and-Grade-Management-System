"""导入导出服务：预览、逐行导入与错误行报告。"""

import logging

from db.dao.meta_dao import ident
from db.errors import DbError, translate
from utils import exporters

log = logging.getLogger(__name__)


def _clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return value


class IoService:
    def __init__(self, db):
        self.db = db

    def export(self, path, columns, rows, fmt="csv", table=None):
        return exporters.export_rows(path, columns, rows, fmt, table)

    def preview(self, path, limit=20):
        return exporters.import_rows(path, limit=limit)

    def table_columns(self, table):
        return [row["name"] for row in self.db.query(
            "SELECT column_name AS name FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s ORDER BY ordinal_position",
            (ident(table),), source="导入: 目标表字段")]

    def import_rows(self, table, mapping, rows, mode="skip"):
        table = ident(table)
        source_keys = [key for key in mapping if mapping.get(key)]
        target_columns = [ident(mapping[key]) for key in source_keys]
        if not target_columns:
            raise DbError(-1, "没有可用的字段映射")
        sql = (f"INSERT INTO {table} ({', '.join(target_columns)}) "
               f"VALUES ({', '.join(['%s'] * len(target_columns))})")
        inserted, failures = 0, []
        conn = self.db._pool.acquire()
        try:
            conn.begin()
            with conn.cursor() as cur:
                for index, row in enumerate(rows, start=1):
                    try:
                        cur.execute(sql, tuple(_clean(row.get(key)) for key in source_keys))
                        inserted += 1
                    except Exception as exc:
                        error = translate(exc, sql)
                        failures.append({"row": index, "error": str(error),
                                         "data": {key: row.get(key) for key in source_keys}})
                        if mode == "atomic":
                            raise error from exc
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise (exc if isinstance(exc, DbError) else translate(exc)) from exc
        finally:
            self.db._pool.release(conn)
        return {"inserted": inserted, "failed": len(failures), "failures": failures[:200],
                "sql": sql}

    def export_failures(self, path, failures):
        columns = [("行号", "row"), ("错误", "error")]
        rows = [{"row": item["row"], "error": item["error"]} for item in failures]
        return exporters.export_rows(path, columns, rows, "csv", "import_failures")
