"""审计日志查询（表 audit_log，索引 idx_audit_time / idx_audit_table）。"""

from .base import DaoBase


class AuditDao(DaoBase):
    def where(self, table_name=None, action=None, keyword=None):
        clauses = ["1 = 1"]
        params = []
        if table_name:
            clauses.append("table_name = %s")
            params.append(table_name)
        if action:
            clauses.append("action = %s")
            params.append(action)
        if keyword:
            clauses.append("(record_id LIKE %s OR operator LIKE %s OR detail LIKE %s)")
            like = f"%{keyword}%"
            params.extend([like, like, like])
        return " WHERE " + " AND ".join(clauses), tuple(params)

    def page(self, table_name=None, action=None, keyword=None, limit=50, offset=0):
        where, params = self.where(table_name, action, keyword)
        total = int(self.db.scalar(f"SELECT COUNT(*) FROM audit_log {where}", params,
                                   source="审计日志计数") or 0)
        rows = self.db.query(
            "SELECT log_id AS log_id, table_name AS table_name, action AS action, "
            "       record_id AS record_id, operator AS operator, "
            "       DATE_FORMAT(action_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS action_time, "
            f"       detail AS detail FROM audit_log {where} "
            "ORDER BY action_time DESC, log_id DESC LIMIT %s OFFSET %s",
            params + (int(limit), int(offset)), source="审计日志查询")
        return rows, total

    def recent(self, limit=10):
        return self.db.query(
            "SELECT table_name AS table_name, action AS action, record_id AS record_id, "
            "       operator AS operator, "
            "       DATE_FORMAT(action_time, '%%m-%%d %%H:%%i:%%s') AS action_time, detail AS detail "
            "FROM audit_log ORDER BY action_time DESC, log_id DESC LIMIT %s",
            (int(limit),), source="最近审计")

    def tables(self):
        rows = self.db.query("SELECT DISTINCT table_name FROM audit_log ORDER BY table_name",
                             source="审计表名候选")
        return [row["table_name"] for row in rows]
